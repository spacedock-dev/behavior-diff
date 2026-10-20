#!/usr/bin/env python3
"""Synthetic scenario-record validation; no models, transcripts, or network calls."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(SCRIPTS))
from scenario import read_scenario
from reporting.sources import (
    DESCRIPTOR_TRUNCATED,
    SENSITIVE_SOURCE,
    SourceRequirementData,
    source_matches,
    unmet_source_requirements,
)

GOAL = {
    "text": "Preserve the synthetic source check.",
    "source": "session",
    "basis": "explicit",
    "reference": "Current conversation: selected edit",
}
SECOND_GOAL = dict(GOAL, text="Report the synthetic conflicting record.")
CHECK = {
    "id": "source-check",
    "goal": 1,
    "text": "The answer reads the synthetic rules before summarizing.",
    "mode": "preservation",
    "required_evidence": "A recorded read of the synthetic rules file.",
    "evidence_kind": "recorded_action",
}
SCENARIO = {
    "summary": "Synthetic records include one row that conflicts with the rules.",
    "rationale": "The conflicting row makes the source check observable.",
    "conditions": ["One synthetic record conflicts with the project rules."],
    "limitations": ["Only one conflicting row is included."],
    "checks": [CHECK],
    "source_requirements": [],
}
SOURCE_CHECK = dict(
    CHECK,
    id="agrees-with-rules",
    text="The reported limit agrees with the recorded rules.",
    mode="new",
    required_evidence="The final answer and the recorded rules return.",
    evidence_kind="source_consistency",
)
RULES = {"check": "agrees-with-rules", "any_of": ["*docs/rules.md*"]}
SOURCED = dict(SCENARIO, checks=[CHECK, SOURCE_CHECK], source_requirements=[RULES])
SENTINEL = "synthetic-private-sentinel-7f3a"


class ScenarioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="scenario-contract-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "scenario.json"
        self.purpose = self.root / "purpose.json"
        self.write_purpose([GOAL])

    def write_purpose(self, goals):
        value = {"goals": goals} if goals else None
        self.purpose.write_text(json.dumps(value), encoding="utf-8")

    def read(self, value):
        self.path.write_text(json.dumps(value), encoding="utf-8")
        # Compare the serialized record the runner freezes, not Python tuples.
        return json.loads(json.dumps(read_scenario(self.path, self.purpose)))

    def rejects(self, value):
        with self.assertRaises((ValueError, TypeError)):
            self.read(value)

    def test_null_and_canonical_record(self):
        self.assertIsNone(self.read(None))
        self.assertEqual(self.read(SCENARIO), SCENARIO)
        padded = copy.deepcopy(SCENARIO)
        padded["summary"] = "  " + SCENARIO["summary"] + "  "
        self.assertEqual(self.read(padded)["summary"], SCENARIO["summary"])
        no_limits = dict(SCENARIO, limitations=[])
        self.assertEqual(self.read(no_limits), no_limits)

    def test_unknown_and_missing_fields(self):
        self.rejects({})
        self.rejects([])
        self.rejects(dict(SCENARIO, outcome="met"))
        self.rejects(dict(SCENARIO, notes="raw private notes"))
        partial = dict(SCENARIO)
        del partial["limitations"]
        self.rejects(partial)
        self.rejects(dict(SCENARIO, checks=[dict(CHECK, before=[])]))
        partial_check = dict(CHECK)
        del partial_check["required_evidence"]
        self.rejects(dict(SCENARIO, checks=[partial_check]))

    def test_check_identity_and_goal_references(self):
        self.rejects(dict(SCENARIO, checks=[CHECK, dict(CHECK, text="Other check.")]))
        for identifier in ("", " source-check", "x" * 81, 7, "a\nb", "**id**"):
            with self.subTest(identifier=identifier):
                self.rejects(dict(SCENARIO, checks=[dict(CHECK, id=identifier)]))
        for goal in (0, 2, -1, True, "1", 1.0, None):
            with self.subTest(goal=goal):
                self.rejects(dict(SCENARIO, checks=[dict(CHECK, goal=goal)]))
        self.assertEqual(
            self.read(dict(SCENARIO, checks=[dict(CHECK, id="x" * 80)]))["checks"][0][
                "id"
            ],
            "x" * 80,
        )

    def test_every_purpose_goal_needs_a_check(self):
        self.write_purpose([GOAL, SECOND_GOAL])
        self.rejects(SCENARIO)
        both = dict(SCENARIO, checks=[CHECK, dict(CHECK, id="conflict", goal=2)])
        self.assertEqual(self.read(both), both)
        self.write_purpose(None)
        self.rejects(SCENARIO)
        self.assertIsNone(self.read(None))

    def test_enums_bounds_and_plain_text(self):
        for field, value in (
            ("mode", "regression"),
            ("mode", ["new"]),
            ("evidence_kind", "transcript"),
            ("text", ""),
            ("text", "x" * 601),
            ("text", "Private\x00value"),
            ("text", "See [link](https://example.invalid)"),
            ("required_evidence", "x" * 601),
        ):
            with self.subTest(field=field, value=value):
                self.rejects(dict(SCENARIO, checks=[dict(CHECK, **{field: value})]))
        for field, value in (
            ("summary", "x" * 401),
            ("summary", ""),
            ("rationale", "x" * 1201),
            ("conditions", []),
            ("conditions", ["x"] * 9),
            ("conditions", ["x" * 301]),
            ("conditions", "One condition."),
            ("limitations", ["x"] * 9),
            ("limitations", [""]),
            ("checks", []),
            ("checks", [dict(CHECK, id=f"c{n}") for n in range(17)]),
        ):
            with self.subTest(field=field):
                self.rejects(dict(SCENARIO, **{field: value}))
        maximum = dict(
            SCENARIO,
            summary="s" * 400,
            rationale="r" * 1200,
            conditions=["c" * 300] * 8,
            limitations=["l" * 300] * 8,
            checks=[
                dict(CHECK, id=f"c{n}", text="t" * 600, required_evidence="e" * 600)
                for n in range(16)
            ],
        )
        self.assertEqual(self.read(maximum), maximum)

    def test_files_duplicate_keys_and_invalid_purpose(self):
        for text in ("not json", "null null", '{"summary":"a","summary":"b"}'):
            self.path.write_text(text, encoding="utf-8")
            with self.subTest(text=text), self.assertRaises(ValueError):
                read_scenario(self.path, self.purpose)
        with self.assertRaises(ValueError):
            read_scenario(self.root / "missing.json", self.purpose)
        self.path.write_text(json.dumps(SCENARIO), encoding="utf-8")
        linked = self.root / "linked.json"
        linked.symlink_to(self.path)
        with self.assertRaises(ValueError):
            read_scenario(linked, self.purpose)
        self.purpose.write_text('{"goals":[]}', encoding="utf-8")
        with self.assertRaises(ValueError):
            read_scenario(self.path, self.purpose)

    def test_cli_requires_purpose_and_never_echoes_rejected_input(self):
        def run(*arguments):
            return subprocess.run(
                [sys.executable, str(SCRIPTS / "scenario.py"), *arguments],
                capture_output=True,
                text=True,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
            )

        self.path.write_text(json.dumps(SCENARIO), encoding="utf-8")
        accepted = run(str(self.path), "--purpose-file", str(self.purpose))
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertEqual(json.loads(accepted.stdout), SCENARIO)
        self.assertEqual(run(str(self.path)).returncode, 2)
        private = self.root / SENTINEL
        private.mkdir()
        leaked = private / "scenario.json"
        leaked.write_text(
            json.dumps(dict(SCENARIO, private_note=SENTINEL)), encoding="utf-8"
        )
        rejected = run(str(leaked), "--purpose-file", str(self.purpose))
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(rejected.stdout, "")
        self.assertIn("--scenario-file", rejected.stderr)
        self.assertNotIn(SENTINEL, rejected.stderr)

    def test_source_consistency_checks_bind_frozen_sources(self):
        self.assertEqual(self.read(SOURCED), SOURCED)
        partial = dict(SCENARIO)
        del partial["source_requirements"]
        self.rejects(partial)
        self.rejects(dict(SCENARIO, source_requirements=None))
        self.rejects(dict(SOURCED, source_requirements=[]))
        for group in (
            dict(RULES, check="source-check"),
            dict(RULES, check="unknown-check"),
            dict(RULES, any_of=[]),
            dict(RULES, any_of="*docs/rules.md*"),
            dict(RULES, any_of=["*docs/rules.md*"] * 2),
            dict(RULES, any_of=[f"*docs/rules-{n}.md*" for n in range(9)]),
            dict(RULES, note="raw private note"),
            {"check": "agrees-with-rules"},
        ):
            with self.subTest(group=group):
                self.rejects(dict(SOURCED, source_requirements=[group]))
        self.rejects(dict(SCENARIO, source_requirements=[RULES]))
        alias = dict(RULES, any_of=["*docs/rules.md*", "*gh api repos/*/rules-7*"])
        second = {"check": "agrees-with-rules", "any_of": ["*data/orders.csv*"]}
        both = dict(SOURCED, source_requirements=[alias, second])
        self.assertEqual(self.read(both), both)
        reordered = dict(alias, any_of=list(reversed(alias["any_of"])))
        for duplicate in ([RULES, RULES], [alias, reordered]):
            with self.subTest(duplicate=duplicate):
                self.rejects(dict(SOURCED, source_requirements=duplicate))
        many = [dict(RULES, any_of=[f"*docs/rules-{n}.md*"]) for n in range(33)]
        self.rejects(dict(SOURCED, source_requirements=many))
        limit = dict(SOURCED, source_requirements=many[:32])
        self.assertEqual(self.read(limit), limit)

    def sourced(self, pattern):
        return dict(SOURCED, source_requirements=[dict(RULES, any_of=[pattern])])

    def test_source_patterns_are_bounded_identities(self):
        accepted = (
            "*docs/rules.md*",
            '*"file_path": "*/limits.md"*',
            "*gh pr view 7*",
            "*gh api repos/*/pulls/7*",
            "*export_cap*",
            "*rules-v?.md*",
            "*" + "r" * 195 + ".md*",
        )
        for pattern in accepted:
            with self.subTest(pattern=pattern):
                value = self.sourced(pattern)
                self.assertEqual(self.read(value), value)
        for pattern in (
            "",
            "*",
            "*rules?md*",
            "**",
            "?*?",
            "Read *",
            "*rules*",
            "*.md*",
            "*docs/*",
            " *docs/rules.md*",
            "*docs/rules.md* ",
            "*docs/rules.md*\n",
            "*docs/[rs]ules.md*",
            "*" + "r" * 196 + ".md*",
            "*/.env.local*",
            "*secrets.yaml*",
            "*config/credentials*",
            "*password=rules.md*",
            "*fictional.person@example.invalid*",
            "*[sensitive source omitted]*",
            7,
            None,
        ):
            with self.subTest(pattern=pattern):
                self.rejects(self.sourced(pattern))

    def test_source_matching_rejects_untrustworthy_descriptors(self):
        read = 'Read {"file_path": "/stage/after-1/project/docs/rules.md"}'
        api = 'Bash {"command": "gh api repos/example/project/rules-7"}'
        alias = ("*docs/rules.md*", "*gh api repos/*/rules-7*")
        self.assertTrue(source_matches(read, alias))
        self.assertTrue(source_matches(api, alias))
        self.assertFalse(source_matches(read.replace("rules", "Rules"), alias))
        self.assertFalse(source_matches(read, ()))
        self.assertFalse(source_matches(SENSITIVE_SOURCE, ("*sensitive source*",)))
        self.assertFalse(source_matches(read + DESCRIPTOR_TRUNCATED, ("*rules.md*",)))
        self.assertFalse(source_matches(None, alias))
        first = SourceRequirementData("agrees-with-rules", alias)
        second = SourceRequirementData("agrees-with-rules", ("*data/orders.csv*",))
        other = SourceRequirementData("other-check", ("*data/other.csv*",))
        groups = (first, second, other)
        self.assertEqual(
            unmet_source_requirements(groups, "agrees-with-rules", [api]), (second,)
        )
        orders = 'Read {"file_path": "data/orders.csv"}'
        self.assertEqual(
            unmet_source_requirements(groups, "agrees-with-rules", [read, orders]), ()
        )
        self.assertEqual(unmet_source_requirements(groups, "source-check", []), ())


if __name__ == "__main__":
    unittest.main()
