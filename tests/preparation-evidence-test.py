#!/usr/bin/env python3
"""Synthetic native preparation records only; no host processes or model calls."""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(SCRIPTS))
from preparation_evidence import validate_preparation_evidence


class NativePreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.input = self.root / "input.txt"
        self.input.write_text("Synthetic historical sources only.\n")
        self.record = self.root / "native.json"
        self.reference = {
            "host": "codex",
            "record_file": str(self.record),
            "input_file": str(self.input),
            "thread_id": "synthetic-thread",
            "turn_id": "synthetic-turn",
        }
        self.native = {
            "thread": {
                "id": "synthetic-thread",
                "sessionId": "synthetic-session",
                "forkedFromId": None,
                "parentThreadId": None,
                "model": "synthetic-current-model-not-execution-proof",
                "historyMode": "legacy",
                "turns": [
                    {
                        "id": "synthetic-turn",
                        "status": "completed",
                        "error": None,
                        "itemsView": "full",
                        "items": [
                            {
                                "id": "synthetic-input",
                                "type": "userMessage",
                                "content": [
                                    {"type": "text", "text": self.input.read_text()}
                                ],
                            }
                        ],
                    }
                ],
            },
        }

    def validate(self, native=None):
        self.record.write_text(json.dumps(self.native if native is None else native))
        return validate_preparation_evidence(self.reference)

    def test_available_facets_never_prove_model_or_full_context(self):
        facts = self.validate()
        self.assertEqual(facts["supplied_user_input"], "verified")
        self.assertEqual(facts["completion"], "verified")
        self.assertEqual(facts["resolved_model"], "unavailable")
        self.assertEqual(facts["historical_boundary"], "unavailable")
        self.assertEqual(facts["status"], "unverified")
        self.assertNotIn(self.input.read_text(), json.dumps(facts))
        self.assertNotIn(self.native["thread"]["model"], json.dumps(facts))

    def test_current_model_never_changes_native_fact_availability(self):
        original = self.validate()
        self.native["thread"]["model"] = "another-requested-model"
        self.assertEqual(self.validate(), original)
        self.native["thread"].pop("model")
        self.assertEqual(self.validate(), original)

    def paginated_record(self):
        metadata = copy.deepcopy(self.native)
        turns = metadata["thread"].pop("turns")
        metadata["thread"].update(historyMode="paginated", turns=[])
        return {
            "thread_read": metadata,
            "turn_pages": [
                {
                    "request": {
                        "threadId": self.reference["thread_id"],
                        "cursor": None,
                        "sortDirection": "asc",
                        "itemsView": "full",
                    },
                    "response": {"data": turns, "nextCursor": None},
                }
            ],
        }

    def test_complete_paginated_history_preserves_native_facet_limits(self):
        self.assertEqual(self.validate(self.paginated_record()), self.validate())

    def test_paginated_cursor_chain_reaches_the_full_turn(self):
        native = self.paginated_record()
        second = copy.deepcopy(native["turn_pages"][0])
        native["turn_pages"][0]["response"] = {
            "data": [],
            "nextCursor": "page-two",
        }
        second["request"]["cursor"] = "page-two"
        native["turn_pages"].append(second)
        self.assertEqual(self.validate(native), self.validate())
        second["request"]["cursor"] = "wrong-cursor"
        with self.assertRaises(ValueError):
            self.validate(native)
        second["request"]["cursor"] = "page-two"
        second["response"]["nextCursor"] = "page-two"
        with self.assertRaises(ValueError):
            self.validate(native)

    def test_paginated_history_requires_complete_unfiltered_cursor_chain(self):
        mutations = [
            lambda n: n["turn_pages"][0]["request"].update(cursor="skipped-page"),
            lambda n: n.update(turn_pages=None),
            lambda n: n["thread_read"]["thread"].update(historyMode="legacy"),
            lambda n: n["turn_pages"][0]["request"].update(threadId="wrong-thread"),
            lambda n: n["turn_pages"][0]["request"].update(itemsView="summary"),
            lambda n: n["turn_pages"][0]["request"].update(turnId="filtered-turn"),
            lambda n: n["turn_pages"][0]["response"].pop("nextCursor"),
            lambda n: n["turn_pages"][0]["response"].update(nextCursor="more"),
            lambda n: n["turn_pages"].append(copy.deepcopy(n["turn_pages"][0])),
            lambda n: n["thread_read"]["thread"].update(
                turns=copy.deepcopy(self.native["thread"]["turns"])
            ),
            lambda n: n["turn_pages"][0]["response"]["data"][0].update(
                itemsView="summary"
            ),
            lambda n: n["thread_read"]["thread"].update(parentThreadId="inherited"),
            lambda n: n["turn_pages"][0]["response"]["data"][0]["items"][0]["content"][
                0
            ].update(text="unreviewed input"),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                native = self.paginated_record()
                mutate(native)
                with self.assertRaises(ValueError):
                    self.validate(native)

    def test_paginated_history_does_not_hide_an_additional_turn(self):
        native = self.paginated_record()
        first = native["turn_pages"][0]
        first["response"]["nextCursor"] = "page-two"
        second = copy.deepcopy(first)
        second["request"]["cursor"] = "page-two"
        second["response"]["nextCursor"] = None
        second["response"]["data"][0]["id"] = "another-turn"
        native["turn_pages"].append(second)
        with self.assertRaises(ValueError):
            self.validate(native)

    def test_truncated_and_duplicate_native_json_are_rejected(self):
        for content in (
            '{"thread":',
            '{"thread": {}, "thread": {}}',
        ):
            with self.subTest(content=content):
                self.record.write_text(content)
                with self.assertRaises(ValueError):
                    validate_preparation_evidence(self.reference)

    def test_missing_wrong_failed_partial_and_forked_records_rejected(self):
        mutations = [
            lambda n: n["thread"].pop("turns"),
            lambda n: n["thread"].pop("sessionId"),
            lambda n: n["thread"].pop("forkedFromId"),
            lambda n: n["thread"]["turns"][0].pop("error"),
            lambda n: n["thread"].update(id="wrong-thread"),
            lambda n: n["thread"]["turns"][0].update(id="wrong-turn"),
            lambda n: n["thread"].update(forkedFromId="prior-thread"),
            lambda n: n["thread"].update(parentThreadId="prior-thread"),
            lambda n: n["thread"].update(historyMode="paginated"),
            lambda n: n["thread"]["turns"].append(
                copy.deepcopy(n["thread"]["turns"][0])
            ),
            lambda n: n["thread"]["turns"][0].update(status="failed"),
            lambda n: n["thread"]["turns"][0].update(error={"message": "synthetic"}),
            lambda n: n["thread"]["turns"][0].update(itemsView="summary"),
            lambda n: n["thread"]["turns"][0].update(items=[]),
            lambda n: n["thread"]["turns"][0]["items"].append(
                copy.deepcopy(n["thread"]["turns"][0]["items"][0])
            ),
            lambda n: n["thread"]["turns"][0]["items"].append(
                {"id": "compact", "type": "contextCompaction"}
            ),
            lambda n: n["thread"]["turns"][0]["items"][0]["content"][0].update(
                text="altered"
            ),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                native = copy.deepcopy(self.native)
                mutate(native)
                with self.assertRaises(ValueError):
                    self.validate(native)

    def test_unsupported_host_explicitly_unavailable(self):
        for host in ("claude", "pi", "omp"):
            with self.subTest(host=host):
                self.reference["host"] = host
                facts = self.validate()
                self.assertEqual(facts["supplied_user_input"], "unavailable")
                self.assertEqual(facts["completion"], "unavailable")


if __name__ == "__main__":
    unittest.main()
