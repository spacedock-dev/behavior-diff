#!/usr/bin/env python3
"""Synthetic Jev transport and CLI checks; no provider or host model calls."""

from contextlib import ExitStack
import copy
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error

SCRIPTS = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(SCRIPTS))
import jev

KEY = "synthetic-key-SENTINEL"
EVIDENCE = "synthetic-private-evidence-SENTINEL"
QUESTIONS = {
    "classification": {
        "type": "choice",
        "criteria": {"difference": "Changed", "unknown": "Missing"},
    },
    "criterion": {
        "type": "choice",
        "criteria": {"supports": "Supported", "contradicts": "Contradicted"},
    },
    "hypothesis": {
        "type": "noul",
        "instructions": "Does the observation support the hypothesis?",
    },
    "alternative": {
        "type": "noul",
        "instructions": "Does it support the competing hypothesis?",
    },
}
RANKING = {"relevance": {"type": "score", "criteria": ["Unrelated", "Direct evidence"]}}


def reply(payload):
    answers = {}
    for name, question in payload["questions"].items():
        kind = question["type"]
        if kind == "noul":
            answers[name] = {"type": kind, "noul": 0.8}
            continue
        criteria = question["criteria"]
        labels = (
            criteria
            if kind == "choice"
            else {str(i): c for i, c in enumerate(criteria)}
        )
        answer = {
            "type": kind,
            "confidence": 0.9,
            "probabilities": {key: int(i == 0) for i, key in enumerate(labels)},
        }
        answer[kind] = next(iter(labels)) if kind == "choice" else 0
        if kind == "score":
            answer["legend"] = labels
        answers[name] = answer
    return {
        "model": "jev-test",
        "answers": answers,
        "usage": {"input_tokens": 10, "output_tokens": 2},
    }


def child(path, scenario):
    """Run shipped main/post in a subprocess with network blocked and fake HTTP."""
    calls = []

    class Response(io.BytesIO):
        status = 200

    class Opener:
        def open(self, request, timeout):
            calls.append(request)
            assert request.full_url == jev.ENDPOINT and timeout == jev.TIMEOUT
            assert request.get_header("Authorization") == "Bearer " + KEY
            assert request.get_method() == "POST"
            payload = json.loads(request.data)
            assert set(payload) == {"model", "state", "questions"}
            if scenario.isdigit():
                raise urllib.error.HTTPError(
                    jev.ENDPOINT, int(scenario), EVIDENCE, {}, io.BytesIO(KEY.encode())
                )
            if scenario == "timeout":
                raise TimeoutError(EVIDENCE + KEY)
            if scenario == "malformed":
                return Response((EVIDENCE + KEY).encode())
            response = reply(payload)
            if scenario == "partial":
                response["answers"].pop("criterion")
            if scenario == "non-jev":
                response["model"] = "another-provider"
            response["debug"] = EVIDENCE + KEY
            return Response(json.dumps(response).encode())

    def opener(*handlers):
        assert any(isinstance(h, jev.NoRedirect) for h in handlers)
        assert any(
            isinstance(h, jev.urllib.request.ProxyHandler) and h.proxies == {}
            for h in handlers
        )
        return Opener()

    with (
        patch.object(
            socket.socket, "connect", side_effect=AssertionError("network forbidden")
        ),
        patch.object(jev.urllib.request, "build_opener", side_effect=opener),
    ):
        code = jev.main([path])
    print("attempts=" + str(len(calls)), file=sys.stderr)
    return code


class JevTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, {}, clear=True))
        self.stack.enter_context(
            patch.object(
                socket.socket,
                "connect",
                side_effect=AssertionError("network forbidden"),
            )
        )
        self.temp = self.stack.enter_context(
            tempfile.TemporaryDirectory(prefix="jev-contract-")
        )
        self.path = Path(self.temp) / "request.json"
        self.request = {
            "operation": "judge",
            "state": {"observation": EVIDENCE},
            "questions": copy.deepcopy(QUESTIONS),
        }
        self.config = {"TYPESAFE_API_KEY": KEY}

    def cli(self, scenario="ok", env=None, request=None):
        self.path.write_text(
            json.dumps(self.request if request is None else request), encoding="utf-8"
        )
        self.path.chmod(0o600)
        proc = subprocess.run(
            [sys.executable, __file__, "--child", str(self.path), scenario],
            env=self.config if env is None else env,
            capture_output=True,
            text=True,
        )
        self.assertNotIn(KEY, proc.stdout + proc.stderr)
        self.assertNotIn(EVIDENCE, proc.stdout + proc.stderr)
        self.assertEqual(list(Path(self.temp).iterdir()), [self.path])
        return json.loads(proc.stdout), proc.returncode, proc.stderr

    def test_single_state_all_questions_and_primary_observations_preserved(self):
        self.request["state"].update(check_exit=1, approval=False)
        original = copy.deepcopy(self.request)
        calls = []

        def transport(payload, key):
            calls.append(payload)
            self.assertEqual(key, KEY)
            return reply(payload)

        result, code = jev.run(self.request, self.config, transport)
        self.assertEqual(code, 0)
        self.assertEqual(result["answers"]["criterion"]["choice"], "supports")
        self.assertEqual(set(result["answers"]), set(QUESTIONS))
        self.assertEqual(result["model"], "jev-test")
        self.assertEqual(result["usage"]["input_tokens"], 10)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["questions"], QUESTIONS)
        self.assertEqual(self.request, original)  # Not proof of agent compliance.

    def test_batch_association_out_of_order_and_four_worker_bound(self):
        states = {str(i): {"id": i} for i in range(9)}
        lock, started = threading.Lock(), threading.Event()
        active = maximum = 0
        calls, completed = [], []

        def transport(payload, key):
            nonlocal active, maximum
            index = payload["state"]["id"]
            with lock:
                active += 1
                maximum = max(maximum, active)
                calls.append(payload)
                if active == 4:
                    started.set()
            self.assertTrue(started.wait(5))
            time.sleep(0.05 if index == 0 else 0.001)
            result = reply(payload)
            result["usage"]["input_tokens"] = index
            with lock:
                active -= 1
                completed.append(index)
            return result

        request = {"operation": "judge_batch", "states": states, "questions": RANKING}
        result, code = jev.run(request, self.config, transport)
        self.assertEqual(code, 0)
        self.assertEqual(maximum, 4)
        self.assertNotEqual(completed[0], 0)
        self.assertEqual(len(calls), len(states))
        self.assertTrue(all(c["questions"] == RANKING for c in calls))
        self.assertEqual(list(result["results"]), list(states))
        for name, item in result["results"].items():
            self.assertEqual(item["usage"]["input_tokens"], int(name))
            self.assertEqual(item["answers"]["relevance"]["score"], 0)

    def test_configuration_skips_without_network(self):
        for env, status, reason in (
            ({}, "unconfigured", "missing_key"),
            ({"TYPESAFE_API_KEY": "  "}, "unconfigured", "missing_key"),
            ({"TYPESAFE_API_KEY": "bad key"}, "unavailable", "invalid_key"),
            ({"TYPESAFE_API_KEY": "bad\x7fkey"}, "unavailable", "invalid_key"),
            ({"TYPESAFE_API_KEY": "é"}, "unavailable", "invalid_key"),
            (
                dict(self.config, TYPESAFE_BASE_URL="https://other.invalid"),
                "unavailable",
                "unsupported_endpoint",
            ),
            (
                dict(self.config, TYPESAFE_DEFAULT_MODEL="other"),
                "unavailable",
                "unsupported_model",
            ),
        ):
            with self.subTest(reason=reason, status=status):
                result, code, stderr = self.cli(env=env)
                self.assertEqual(result, {"status": status, "reason": reason})
                self.assertEqual(code, 0)
                self.assertIn("attempts=0", stderr)

    def test_cli_success_and_sanitized_failures_one_attempt(self):
        result, code, stderr = self.cli(
            env=dict(self.config, TYPESAFE_API_KEY=" " + KEY + "\n")
        )
        self.assertEqual((result["status"], code), ("ok", 0))
        self.assertIn("attempts=1", stderr)
        for scenario, reason in (
            ("401", "authentication"),
            ("429", "rate_limit"),
            ("529", "overload"),
            ("302", "redirect"),
            ("timeout", "timeout"),
            ("malformed", "invalid_response"),
            ("partial", "invalid_response"),
            ("non-jev", "invalid_response"),
        ):
            with self.subTest(scenario=scenario):
                result, code, stderr = self.cli(scenario)
                self.assertEqual(result, {"status": "failed", "reason": reason})
                self.assertEqual(code, 1)
                self.assertIn("attempts=1", stderr)

    def test_redirect_handler_refuses_forwarding(self):
        handler = jev.NoRedirect()
        self.assertIsNone(
            handler.redirect_request(None, None, 302, "", {}, "https://other.invalid")
        )

    def test_mixed_batch_retains_success_and_failure(self):
        request = {
            "operation": "judge_batch",
            "states": {"first": "ok", "second": "fail"},
            "questions": QUESTIONS,
        }
        calls = []

        def transport(payload, key):
            calls.append(payload)
            if payload["state"] == "fail":
                raise TimeoutError(KEY)
            return reply(payload)

        result, code = jev.run(request, self.config, transport)
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["results"]["first"]["status"], "ok")
        self.assertEqual(
            result["results"]["second"], {"status": "failed", "reason": "timeout"}
        )
        self.assertEqual(len(calls), 2)
        skipped, code = jev.run(request, {}, transport)
        self.assertEqual(code, 0)
        self.assertTrue(
            all(
                item["status"] == "unconfigured" for item in skipped["results"].values()
            )
        )
        self.assertEqual(len(calls), 2)

    def test_complete_input_validation_precedes_network(self):
        invalid = [
            None,
            {},
            dict(self.request, operation="other"),
            dict(self.request, state=2),
            dict(self.request, questions={}),
            dict(self.request, state=float("nan")),
            dict(self.request, state="x" * jev.MAX_BYTES),
        ]
        for question in (
            {"type": "box"},
            {"type": "choice", "criteria": {}},
            {"type": "score", "criteria": ["x"] * 11},
            {"type": "noul", "criteria": {"bad": "x"}},
            {"type": "noul", "assets": {}},
            {"type": "noul", "instructions": 3},
        ):
            invalid.append(dict(self.request, questions={"q": question}))
        invalid.append(
            {
                "operation": "judge_batch",
                "states": {"good": "ok", "bad": 42},
                "questions": QUESTIONS,
            }
        )
        for request in invalid:
            with self.subTest(request=request):
                result, code = jev.run(
                    request,
                    self.config,
                    lambda *args: self.fail("invalid request sent"),
                )
                self.assertEqual((result["reason"], code), ("invalid_request", 1))
        with self.assertRaises(ValueError):
            jev.decode('{"state":1,"state":2}')

    def test_invalid_answers_never_become_success(self):
        payload = {"questions": dict(QUESTIONS, **RANKING)}
        for field, value in (("noul", float("nan")), ("noul", True), ("noul", 1.1)):
            response = reply(payload)
            response["answers"]["hypothesis"][field] = value
            with self.assertRaises(ValueError):
                jev.validate_response(response, payload["questions"])
        for name, field, value in (
            ("classification", "choice", "invented"),
            ("classification", "type", "score"),
            ("classification", "confidence", -1),
            ("classification", "probabilities", {"difference": 1}),
            ("relevance", "score", 2),
            ("relevance", "legend", {}),
        ):
            response = reply(payload)
            response["answers"][name][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                jev.validate_response(response, payload["questions"])
        response = reply(payload)
        response["usage"]["input_tokens"] = True
        with self.assertRaises(ValueError):
            jev.validate_response(response, payload["questions"])

    def test_actual_cli_unconfigured_smoke(self):
        self.path.write_text(json.dumps(self.request), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "jev.py"), str(self.path)],
            env={},
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(
            json.loads(proc.stdout), {"status": "unconfigured", "reason": "missing_key"}
        )
        self.assertEqual(proc.stderr, "")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        sys.exit(child(sys.argv[2], sys.argv[3]))
    unittest.main()
