"""Validate available native preparation facets, never asserted isolation or model proof.

Codex 0.165 ThreadReadResponse exposes supplied user input and turn completion,
but Thread.model is explicitly not per-turn execution telemetry. Raw records
remain private; this module returns only facet availability and identities.
"""

import json
from pathlib import Path

from purpose import unique_object


FIELDS = {"host", "record_file", "input_file", "thread_id", "turn_id"}
MODEL_LIMIT = "Native thread model is not resolved per-turn execution telemetry."
CONTEXT_LIMIT = "Native user input does not enumerate all ambient or system context."


def validate_preparation_evidence(reference):
    if type(reference) is not dict or reference.keys() != FIELDS:
        raise ValueError("invalid native preparation evidence reference")
    if any(
        type(value) is not str or not value or "\0" in value
        for value in reference.values()
    ):
        raise ValueError("native preparation evidence fields must be nonempty strings")
    result = {
        "host": reference["host"],
        "status": "unverified",
        "supplied_user_input": "unavailable",
        "completion": "unavailable",
        "resolved_model": "unavailable",
        "historical_boundary": "unavailable",
        "limitations": [MODEL_LIMIT, CONTEXT_LIMIT],
    }
    if reference["host"] != "codex":
        result["limitations"] = [
            "No validated native preparation record format for this host."
        ]
        return result
    raw = json.loads(
        Path(reference["record_file"]).read_text(), object_pairs_hook=unique_object
    )
    if type(raw) is not dict or not {"thread"} <= raw.keys() <= {"thread", "readState"}:
        raise ValueError("expected a full native Codex ThreadReadResponse")
    thread = raw["thread"]
    if type(thread) is not dict:
        raise ValueError("native preparation thread is missing")
    if thread.get("id") != reference["thread_id"]:
        raise ValueError("native preparation thread identity mismatch")
    if type(thread.get("sessionId")) is not str or not thread["sessionId"]:
        raise ValueError("native preparation session identity is unavailable")
    if (
        "forkedFromId" not in thread
        or thread["forkedFromId"] is not None
        or "parentThreadId" not in thread
        or thread["parentThreadId"] is not None
    ):
        raise ValueError("forked or inherited native preparation history is unverified")
    if thread.get("historyMode", "legacy") != "legacy":
        raise ValueError(
            "paginated native preparation history is unverified; full legacy history required"
        )
    turns = thread.get("turns")
    if type(turns) is not list or len(turns) != 1:
        raise ValueError("fresh native preparation requires one complete turn")
    turn = turns[0]
    if type(turn) is not dict or turn.get("id") != reference["turn_id"]:
        raise ValueError("native preparation turn identity mismatch")
    if turn.get("itemsView", "full") != "full":
        raise ValueError("partial native preparation items are unverified")
    if (
        turn.get("status") != "completed"
        or "error" not in turn
        or turn["error"] is not None
    ):
        raise ValueError("native preparation did not complete successfully")
    items = turn.get("items")
    if type(items) is not list or not items:
        raise ValueError("native preparation items are unavailable")
    identities = set()
    messages = []
    for item in items:
        if (
            type(item) is not dict
            or type(item.get("id")) is not str
            or not item["id"]
            or item["id"] in identities
        ):
            raise ValueError("ambiguous native preparation item identities")
        identities.add(item["id"])
        if item.get("type") in ("contextCompaction", "hookPrompt"):
            raise ValueError(
                "compacted or hook-augmented preparation input is unverified"
            )
        if item.get("type") == "userMessage":
            messages.append(item.get("content"))
    if len(messages) != 1 or type(messages[0]) is not list or not messages[0]:
        raise ValueError(
            "native preparation supplied input is unavailable or ambiguous"
        )
    if len(messages[0]) != 1:
        raise ValueError("multi-part native preparation input is ambiguous")
    text = []
    for content in messages[0]:
        if (
            type(content) is not dict
            or content.get("type") != "text"
            or type(content.get("text")) is not str
            or content.get("text_elements", []) != []
        ):
            raise ValueError(
                "native preparation non-text or annotated context is unverified"
            )
        text.append(content["text"])
    expected = Path(reference["input_file"]).read_text()
    if not expected.strip() or "".join(text) != expected:
        raise ValueError(
            "native preparation supplied input differs from reviewed input"
        )
    result.update(
        supplied_user_input="verified",
        completion="verified",
        thread_id=reference["thread_id"],
        turn_id=reference["turn_id"],
    )
    return result
