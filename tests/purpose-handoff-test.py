#!/usr/bin/env python3
"""Synthetic purpose-file validation; no models, transcripts, or network calls."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts")
)
from purpose import read_purpose


class PurposeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="purpose-contract-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "purpose.json"
        self.goal = {
            "text": "Preserve the synthetic source check.",
            "source": "session",
            "basis": "explicit",
            "reference": "Current conversation: selected edit",
        }

    def read(self, value):
        self.path.write_text(json.dumps(value), encoding="utf-8")
        return read_purpose(self.path)

    def test_nullable_and_all_provenance(self):
        self.assertIsNone(self.read(None))
        for source in ("session", "commit", "diff"):
            goal = dict(self.goal, source=source, basis="inferred")
            self.assertEqual(self.read({"goals": [goal]}), {"goals": [goal]})

    def test_strict_shape_and_distinct_goals(self):
        for value in (
            {},
            [],
            {"goals": []},
            {"goals": [self.goal], "session": "raw"},
            {"goals": [dict(self.goal, extra="raw")]},
            {"goals": [self.goal] * 9},
            {"goals": [self.goal, dict(self.goal, text=self.goal["text"].upper())]},
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.read(value)

    def test_invalid_provenance_and_bounded_plain_text(self):
        for field, value in (
            ("source", "transcript"),
            ("source", []),
            ("basis", "observed"),
            ("basis", {}),
            ("text", ""),
            ("text", "x" * 1201),
            ("text", "Private\x00value"),
            ("reference", "x" * 241),
            ("reference", ""),
        ):
            with (
                self.subTest(field=field, value=value),
                self.assertRaises((ValueError, TypeError)),
            ):
                self.read({"goals": [dict(self.goal, **{field: value})]})
        with self.assertRaises(ValueError):
            self.read({"goals": [dict(self.goal, source="diff")]})
        maximum = dict(self.goal, text="x" * 1200, reference="r" * 240)
        self.assertEqual(self.read({"goals": [maximum]}), {"goals": [maximum]})

    def test_invalid_json_multiple_values_duplicate_keys_and_missing_file(self):
        for text in ("not json", "null null", '{"goals":[],"goals":[]}'):
            self.path.write_text(text, encoding="utf-8")
            with self.subTest(text=text), self.assertRaises(ValueError):
                read_purpose(self.path)
        with self.assertRaises(ValueError):
            read_purpose(self.path.parent / "missing.json")
        linked = self.path.parent / "linked.json"
        linked.symlink_to(self.path)
        with self.assertRaises(ValueError):
            read_purpose(linked)


if __name__ == "__main__":
    unittest.main()
