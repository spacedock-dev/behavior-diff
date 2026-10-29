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
