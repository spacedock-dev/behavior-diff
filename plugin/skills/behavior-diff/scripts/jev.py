#!/usr/bin/env python3
"""Optional Jev advisory judgments. No retries, cache, or alternate provider."""

from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import math
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

BASE_URL = "https://api.typesafe.ai"
ENDPOINT = BASE_URL + "/v1/systemone"
TIMEOUT = 30
MAX_BYTES = 256 * 1024
MODEL = re.compile(r"jev-[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")


def require(condition):
    if not condition:
        raise ValueError("invalid shape")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def decode(data):
    return json.loads(data, object_pairs_hook=unique_object)


def content(value, nullable=False):
    return (nullable and value is None) or isinstance(value, (str, dict, list))


def keyed(value):
    return (
        isinstance(value, dict)
        and bool(value)
        and all(isinstance(k, str) and k.strip() and k.isprintable() for k in value)
    )


def validate_request(request):
    require(isinstance(request, dict))
    operation = request.get("operation")
    require(operation in ("judge", "judge_batch"))
    field = "state" if operation == "judge" else "states"
    require(set(request) == {"operation", field, "questions"})
    states = {"single": request[field]} if operation == "judge" else request[field]
    require(keyed(states) and all(content(state) for state in states.values()))
    questions = request["questions"]
    require(keyed(questions))
    # Reject non-JSON/nonfinite nested values before any state is submitted.
    require(len(json.dumps(request, allow_nan=False).encode()) <= MAX_BYTES)
    for question in questions.values():
        require(isinstance(question, dict))
        require(set(question) <= {"type", "instructions", "criteria"})
        require(content(question.get("instructions"), nullable=True))
        kind, criteria = question.get("type"), question.get("criteria")
        require(kind in ("choice", "score", "noul"))
        if kind == "choice":
            require(keyed(criteria) and len(criteria) <= 255)
            require(all(content(c, nullable=True) for c in criteria.values()))
        elif kind == "score":
            require(isinstance(criteria, list) and 1 <= len(criteria) <= 10)
            require(all(content(c) for c in criteria))
        elif criteria is not None:
            require(isinstance(criteria, dict) and set(criteria) <= {"true", "false"})
            require(all(content(c, nullable=True) for c in criteria.values()))
    return states, questions


def outcome(status, reason):
    return {"status": status, "reason": reason}


def configuration(environ):
    key = environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        return None, outcome("unconfigured", "missing_key")
    if not key.isascii() or any(ord(c) <= 32 or ord(c) == 127 for c in key):
        return None, outcome("unavailable", "invalid_key")
    if environ.get("TYPESAFE_BASE_URL", BASE_URL) != BASE_URL:
        return None, outcome("unavailable", "unsupported_endpoint")
    model = environ.get("TYPESAFE_DEFAULT_MODEL", "jev-latest")
    if not MODEL.fullmatch(model):
        return None, outcome("unavailable", "unsupported_model")
    return (key, model), None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def post(payload, key):
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, allow_nan=False).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    # Do not inherit proxy settings that could reroute this credentialed request.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=TIMEOUT) as response:
        require(response.status == 200)
        data = response.read(MAX_BYTES + 1)
        require(len(data) <= MAX_BYTES)
        return decode(data)


def number(value, maximum=1):
    return (
        type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum
    )


def validate_response(response, questions):
    require(isinstance(response, dict))
    model = response.get("model")
    require(isinstance(model, str) and MODEL.fullmatch(model))
    answers, usage = response.get("answers"), response.get("usage")
    require(isinstance(answers, dict) and set(answers) == set(questions))
    require(isinstance(usage, dict))
    require(
        all(
            type(usage.get(k)) is int and usage[k] >= 0
            for k in ("input_tokens", "output_tokens")
        )
    )
    clean = {}
    for name, question in questions.items():
        answer = answers[name]
        kind = question["type"]
        require(isinstance(answer, dict) and answer.get("type") == kind)
        if kind == "noul":
            require(number(answer.get("noul")))
            clean[name] = {"type": kind, "noul": answer["noul"]}
            continue
        criteria = question["criteria"]
        labels = (
            criteria
            if kind == "choice"
            else {str(i): c for i, c in enumerate(criteria)}
        )
        probabilities = answer.get("probabilities")
        require(isinstance(probabilities, dict) and set(probabilities) == set(labels))
        require(all(number(p) for p in probabilities.values()))
        require(math.isclose(sum(probabilities.values()), 1, abs_tol=0.01))
        require(number(answer.get("confidence")))
        if kind == "choice":
            require(
                isinstance(answer.get("choice"), str) and answer["choice"] in labels
            )
        else:
            require(number(answer.get("score"), len(criteria) - 1))
            require(answer.get("legend") == labels)
        clean[name] = {
            "type": kind,
            kind: answer[kind],
            "confidence": answer["confidence"],
            "probabilities": probabilities,
        }
        if kind == "score":
            clean[name]["legend"] = labels
    return {
        "status": "ok",
        "model": model,
        "answers": clean,
        "usage": {k: usage[k] for k in ("input_tokens", "output_tokens")},
    }


def judge(state, questions, config, transport):
    key, model = config
    try:
        response = transport(
            {"model": model, "state": state, "questions": questions}, key
        )
        return validate_response(response, questions)
    except urllib.error.HTTPError as error:
        code = error.code
        error.close()
        reason = (
            "redirect"
            if 300 <= code < 400
            else "authentication"
            if code in (401, 403)
            else "rate_limit"
            if code == 429
            else "overload"
            if code in (503, 529)
            else "http_error"
        )
        return outcome("failed", reason)
    except TimeoutError:
        return outcome("failed", "timeout")
    except (urllib.error.URLError, OSError, http.client.HTTPException):
        return outcome("failed", "transport")
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        return outcome("failed", "invalid_response")


def run(request, environ=None, transport=None):
    try:
        states, questions = validate_request(request)
    except (ValueError, TypeError, OverflowError, RecursionError):
        return outcome("failed", "invalid_request"), 1
    config, skip = configuration(os.environ if environ is None else environ)
    if skip:
        if request["operation"] == "judge_batch":
            skip = dict(skip, results={name: dict(skip) for name in states})
        return skip, 0
    transport = post if transport is None else transport
    if request["operation"] == "judge":
        result = judge(states["single"], questions, config, transport)
    else:
        with ThreadPoolExecutor(max_workers=min(4, len(states))) as pool:
            futures = {
                name: pool.submit(judge, state, questions, config, transport)
                for name, state in states.items()
            }
            results = {name: future.result() for name, future in futures.items()}
        result = {
            "status": "ok"
            if all(r["status"] == "ok" for r in results.values())
            else "failed",
            "results": results,
        }
    return result, int(result["status"] == "failed")


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        result, code = outcome("failed", "invalid_request"), 1
    else:
        try:
            with Path(args[0]).open("rb") as source:
                data = source.read(MAX_BYTES + 1)
            require(len(data) <= MAX_BYTES)
            result, code = run(decode(data))
        except (OSError, ValueError, TypeError, OverflowError, RecursionError):
            result, code = outcome("failed", "invalid_request"), 1
    print(json.dumps(result, allow_nan=False))
    if code:
        print(
            "Jev assistance failed; continue the existing evidence assessment.",
            file=sys.stderr,
        )
    return code


if __name__ == "__main__":
    sys.exit(main())
