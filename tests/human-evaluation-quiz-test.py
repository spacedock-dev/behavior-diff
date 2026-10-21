#!/usr/bin/env python3
"""Deterministic private-quiz contracts, with authored synthetic product reports."""

import copy
from concurrent.futures import ThreadPoolExecutor
import contextlib
import http.client
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch

from report_fixtures import build_reports


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".agents/skills/run-behavior-diff-human-evaluation/scripts/quiz.py"
spec = importlib.util.spec_from_file_location("human_evaluation_quiz", HELPER)
quiz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quiz)


def write_json(path, value):
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def visible(node):
    """Plain report text a quiz reader sees, without evidence navigation links."""
    return "".join(
        child
        if not isinstance(child, quiz._Node)
        else ("" if child.has_class("evidence-links") else visible(child))
        for child in node.children
    )


def question():
    return {
        "stem": "Which statement describes the bounded synthetic comparison?",
        "scope": "Only the observed synthetic review decision, not general reliability.",
        "options": [
            {
                "statement": "The observed verdict changes.",
                "correct": True,
                "rationale": "The authored comparison establishes a changed verdict.",
            },
            {
                "statement": "The verdict is the same in every observed trial.",
                "correct": False,
                "rationale": "The synthetic fixture includes a changed verdict.",
            },
            {
                "statement": "No review record is available.",
                "correct": False,
                "rationale": "Synthetic review records are retained.",
            },
            {
                "statement": "The review proves general reliability.",
                "correct": False,
                "rationale": "A bounded synthetic comparison cannot establish general reliability.",
            },
        ],
    }


def session_at(path, identity="synthetic-session", seed=29):
    path.mkdir(mode=0o700)
    manifest = {
        "schema_version": 1,
        "id": identity,
        "source_repo": "DataRecce/recce-team",
        "source_tip": "a" * 40,
        "seed": seed,
        "code": {"root": str(ROOT), "head": "b" * 40, "fingerprint": "synthetic"},
        "trials": 3,
        "trial_model": "opus",
        "extract_model": "sonnet",
        "cases": [
            {
                "id": number,
                "sha": str(number) * 40,
                "before_sha": "0" * 40,
                "skill_path": f"skills/synthetic-{number}/SKILL.md",
            }
            for number in range(1, 6)
        ],
    }
    write_json(path / "session.json", manifest)
    for case in manifest["cases"]:
        directory = path / f"case-{case['id']}"
        directory.mkdir()
        write_json(directory / "question.json", question())
    return manifest


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.session = self.root / "one"
        self.manifest = session_at(self.session)

    def test_deterministic_shuffle_and_no_public_answers(self):
        quiz.freeze_questions(self.session, self.manifest)
        another = self.root / "two"
        manifest = session_at(another)
        quiz.freeze_questions(another, manifest)
        self.assertEqual(
            (self.session / "answer-key.json").read_bytes(),
            (another / "answer-key.json").read_bytes(),
        )
        visible = json.loads((self.session / "public/questions.json").read_text())
        key = json.loads((self.session / "answer-key.json").read_text())
        self.assertEqual(len(visible), 5)
        for public, private in zip(visible, key["questions"]):
            self.assertEqual(set(public), {"id", "stem", "options"})
            self.assertEqual(
                [option["letter"] for option in public["options"]], list("ABCD")
            )
            self.assertTrue(
                all(
                    set(option) == {"letter", "statement"}
                    for option in public["options"]
                )
            )
            self.assertEqual(sum(option["correct"] for option in private["options"]), 1)
            self.assertEqual(
                private["correct"],
                next(
                    option["letter"]
                    for option in private["options"]
                    if option["correct"]
                ),
            )
        self.assertEqual(
            (self.session / "answer-key.json").stat().st_mode & 0o777, 0o600
        )
        self.assertEqual(
            json.loads((self.session / "case-1/question.json").read_text()), question()
        )
        with self.assertRaises(ValueError):
            quiz.freeze_questions(self.session, self.manifest)

    def test_all_inputs_validated_before_any_key_written(self):
        variants = []
        bad = question()
        bad["options"][0]["correct"] = 1
        variants.append(bad)
        bad = question()
        bad["options"][1]["correct"] = True
        variants.append(bad)
        bad = question()
        bad["options"][0]["correct"] = False
        variants.append(bad)
        bad = question()
        bad["options"][1]["statement"] = " THE observed verdict changes. "
        variants.append(bad)
        bad = question()
        bad["options"].pop()
        variants.append(bad)
        bad = question()
        bad["options"][0]["rationale"] = " "
        variants.append(bad)
        bad = question()
        bad["options"][0]["statement"] = "x" * 601
        variants.append(bad)
        bad = question()
        del bad["scope"]
        variants.append(bad)
        bad = question()
        bad["stem"] = ""
        variants.append(bad)
        for bad in variants:
            with self.subTest(question=bad):
                write_json(self.session / "case-5/question.json", bad)
                with self.assertRaises(ValueError):
                    quiz.freeze_questions(self.session, self.manifest)
                self.assertFalse((self.session / "answer-key.json").exists())
                self.assertFalse((self.session / "public/questions.json").exists())
        (self.session / "case-5/question.json").unlink()
        with self.assertRaises(FileNotFoundError):
            quiz.freeze_questions(self.session, self.manifest)

    def test_report_before_freeze_is_rejected(self):
        run = self.session / "case-1/state/runs/synthetic"
        run.mkdir(parents=True)
        (run / "report.html").write_text("Already generated")
        with self.assertRaises(ValueError):
            quiz.freeze_questions(self.session, self.manifest)
        (run / "report.html").unlink()
        (run / "trace.json").write_text("{}")
        with self.assertRaises(ValueError):
            quiz.freeze_questions(self.session, self.manifest)

    def test_manifest_and_session_identity_are_required(self):
        for field, value in [
            ("source_repo", "another/repo"),
            ("seed", True),
            ("id", ""),
        ]:
            manifest = copy.deepcopy(self.manifest)
            manifest[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                quiz.freeze_questions(self.session, manifest)
        other = self.root / "other"
        manifest = session_at(other, identity="another-session")
        quiz.freeze_questions(self.session, self.manifest)
        quiz.freeze_questions(other, manifest)
        self.assertNotEqual(
            json.loads((self.session / "answer-key.json").read_text())["session_id"],
            json.loads((other / "answer-key.json").read_text())["session_id"],
        )


class ReportAndServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gallery_temp = tempfile.TemporaryDirectory()
        cls.gallery = Path(cls.gallery_temp.name)
        build_reports(cls.gallery)

    @classmethod
    def tearDownClass(cls):
        cls.gallery_temp.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.session = self.root / "session"
        self.manifest = session_at(self.session)
        quiz.freeze_questions(self.session, self.manifest)
        self.copy_reports()

    def copy_reports(self, scenario="changed-result"):
        for number in range(1, 6):
            run = self.session / f"case-{number}/state/runs/synthetic"
            run.mkdir(parents=True, exist_ok=True)
            for name in (
                "report.html",
                "report.md",
                "decisions.json",
                "report-data.json",
            ):
                source = self.gallery / scenario / name
                destination = run / name
                if source.exists():
                    shutil.copyfile(source, destination)
                else:
                    destination.unlink(missing_ok=True)

    def build(self):
        quiz.build_quiz(self.session, ROOT)

    @contextlib.contextmanager
    def running(self):
        self.build()
        server = quiz.make_server(self.session, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def request(self, server, path, method="GET", payload=None, headers=None):
        connection = http.client.HTTPConnection(
            "127.0.0.1", server.server_port, timeout=5
        )
        body = (
            payload
            if isinstance(payload, bytes)
            else (None if payload is None else json.dumps(payload).encode())
        )
        sent = dict(headers or {})
        if method == "POST":
            sent.setdefault("Content-Type", "application/json")
            sent.setdefault("Origin", f"http://127.0.0.1:{server.server_port}")
        connection.request(method, path, body=body, headers=sent)
        response = connection.getresponse()
        data = response.read()
        result = response.status, dict(response.getheaders()), data
        connection.close()
        return result

    def payload(self, all_correct=True):
        key = json.loads((self.session / "answer-key.json").read_text())
        return {
            "session_id": self.manifest["id"],
            "answers": [
                {
                    "id": question["id"],
                    "letter": question["correct"]
                    if all_correct
                    else next(
                        letter for letter in "ABCD" if letter != question["correct"]
                    ),
                    "confidence": ["low", "medium", "high"][question["id"] % 3],
                    "insufficient": question["id"] == 3,
                    "note": "Synthetic ambiguity note" if question["id"] == 3 else "",
                }
                for question in key["questions"]
            ],
        }

    def test_actual_synthetic_report_blinding_preserves_wording(self):
        self.build()
        original = (self.gallery / "changed-result/report.html").read_text()
        root = quiz._ReportParser().finish(original)
        nodes = list(quiz._walk(root))
        panel = quiz._single(
            [node for node in nodes if node.attrs.get("id") == "panel-summary"],
            "summary panel",
        )
        blinded = (self.session / "public/summary-1.html").read_text()
        blind_root = quiz._ReportParser().finish(blinded)
        text = quiz._plain(blind_root)
        for name in (
            "summary-before",
            "summary-after",
            "summary-why",
            "summary-caution",
            "evidence-limits",
        ):
            for node in quiz._walk(panel):
                if node.has_class(name):
                    # Navigation is excluded; generated supported-claim text remains unchanged.
                    self.assertIn(visible(node), text)
        for name in (
            "story-intent",
            "purpose-goal-text",
            "purpose-provenance",
            "intent-heading",
            "scenario-context",
            "scenario-prompt",
            "summary-checks",
            "summary-status",
            "summary-state",
            "summary-diagnostics",
            "summary-expect-observe",
            "summary-change-scope",
            "summary-change-sides",
            "summary-change-note",
            "summary-other-changes",
            "summary-open",
            "summary-method-grid",
            "summary-method-caveats",
            "summary-check-digest",
            "summary-finding-meaning",
            "summary-next-action",
        ):
            for node in nodes:
                if node.has_class(name) and quiz._plain(node).strip():
                    self.assertNotIn(quiz._plain(node), text)
        self.assertFalse(
            any(
                node.has_class(name)
                for node in quiz._walk(blind_root)
                for name in (
                    "intent-heading",
                    "story-intent",
                    "purpose-goal-text",
                    "purpose-provenance",
                )
            )
        )
        self.assertNotIn('id="panel-instruction"', blinded)
        self.assertNotIn("<script", blinded)
        self.assertNotIn("<nav", blinded)
        self.assertNotIn("<a ", blinded)
        self.assertFalse(any("href" in node.attrs for node in quiz._walk(blind_root)))
        self.assertNotIn("https://", blinded)
        self.assertNotIn("<button", blinded)
        self.assertNotIn("data-attention-", blinded)
        self.assertNotIn("<link", blinded)
        self.assertEqual(
            (self.session / "case-1/state/runs/synthetic/report.html").read_text(),
            original,
        )
        receipt = json.loads((self.session / "quiz-build.json").read_text())
        self.assertEqual(
            receipt["reports"]["1"]["report.html"]["sha256"],
            quiz._hash(original.encode()),
        )

    def test_attention_findings_states_and_steps_survive_blinding(self):
        for scenario, state in (
            ("attention-mixed", "attention-finding"),
            ("attention-self-reported", "attention-finding"),
            ("attention-plans", "attention-finding"),
            ("attention-quiet", "attention-empty"),
            ("attention-unavailable", "attention-unavailable"),
            ("attention-multiple", "attention-finding"),
            ("target-mixed", "attention-target-gap"),
        ):
            with self.subTest(scenario=scenario):
                source = (self.gallery / scenario / "report.html").read_text()
                original = quiz._ReportParser().finish(source)
                blinded_html = quiz._blinded_report(source)
                blinded = quiz._ReportParser().finish(blinded_html)
                attention = quiz._single(
                    [
                        node
                        for node in quiz._walk(original)
                        if node.has_class("story-attention")
                    ],
                    "original attention step",
                )
                retained = quiz._single(
                    [
                        node
                        for node in quiz._walk(blinded)
                        if node.has_class("story-attention")
                    ],
                    "blinded attention step",
                )
                self.assertEqual(
                    quiz._safe_fragment(attention), quiz._safe_fragment(retained)
                )
                original_nodes = list(quiz._walk(attention))
                retained_nodes = list(quiz._walk(retained))
                self.assertTrue(any(node.has_class(state) for node in retained_nodes))
                for name in (
                    "attention-assessment",
                    "attention-consequence",
                    "attention-evidence-kind",
                    "attention-limit",
                    "attention-next",
                    "attention-target-result",
                    "attention-empty",
                    "attention-unavailable",
                ):
                    self.assertEqual(
                        [
                            quiz._plain(node)
                            for node in original_nodes
                            if node.has_class(name)
                        ],
                        [
                            quiz._plain(node)
                            for node in retained_nodes
                            if node.has_class(name)
                        ],
                    )
                self.assertEqual(
                    [quiz._plain(node) for node in original_nodes if node.tag == "h4"],
                    [quiz._plain(node) for node in retained_nodes if node.tag == "h4"],
                )
                for relationship in (
                    node
                    for node in original_nodes
                    if node.has_class("attention-relationship")
                ):
                    self.assertNotIn(quiz._plain(relationship), quiz._plain(retained))
                self.assertFalse(
                    any(
                        node.has_class("attention-relationship")
                        for node in retained_nodes
                    )
                )
                for svg in (node for node in quiz._walk(blinded) if node.tag == "svg"):
                    self.assertEqual(svg.attrs["aria-hidden"], "true")
                    self.assertEqual(svg.attrs["focusable"], "false")
                    self.assertIn("viewbox", svg.attrs)
                    self.assertTrue(quiz._children(svg))
                self.assertFalse(
                    any(
                        node.tag in ("a", "nav", "button")
                        or any(
                            name == "href" or name.startswith("data-")
                            for name in node.attrs
                        )
                        for node in quiz._walk(blinded)
                    )
                )

    def test_assessment_setup_and_next_actions_do_not_reveal_quiz_key(self):
        source = (self.gallery / "target-mixed/report.html").read_text()
        root = quiz._ReportParser().finish(source)
        hidden = (
            "summary-headline",
            "summary-expected",
            "summary-check-details",
            "summary-method-grid",
            "summary-next-action",
        )
        secrets = []
        for index, name in enumerate(hidden):
            node = quiz._single(
                [node for node in quiz._walk(root) if node.has_class(name)],
                name,
            )
            secret = f"PRIVATE-ANSWER-KEY-{index}"
            secrets.append(secret)
            node.children.append(secret)
        with patch.object(quiz._ReportParser, "finish", return_value=root):
            blinded = quiz._blinded_report(source)
        for secret in secrets:
            self.assertNotIn(secret, blinded)
        self.assertIn("summary-before", blinded)
        self.assertIn("summary-after", blinded)

    def test_old_summary_shapes_and_wrapper_recovery_are_rejected(self):
        source = (self.gallery / "changed-result/report.html").read_text()
        # Unknown layouts must fail closed rather than exposing unreviewed sections.
        for legacy in (
            "missing-step",
            "unknown-step",
            "target-table",
            "other-findings",
        ):
            with self.subTest(legacy=legacy):
                root = quiz._ReportParser().finish(source)
                panel = quiz._single(
                    [
                        node
                        for node in quiz._walk(root)
                        if node.attrs.get("id") == "panel-summary"
                    ],
                    "summary panel",
                )
                steps = quiz._single(
                    [
                        node
                        for node in quiz._walk(panel)
                        if node.has_class("story-steps")
                    ],
                    "story steps",
                )
                if legacy == "missing-step":
                    steps.children = [
                        child
                        for child in steps.children
                        if not isinstance(child, quiz._Node)
                        or not child.has_class("story-method")
                    ]
                elif legacy == "unknown-step":
                    quiz._children(steps)[3].attrs["class"] = "story-step"
                elif legacy == "target-table":
                    evidence = quiz._single(
                        [
                            node
                            for node in quiz._walk(panel)
                            if node.has_class("summary-observations")
                        ],
                        "observations",
                    )
                    evidence.children.insert(
                        len(evidence.children) - 1,
                        quiz._Node("div", [("class", "target-checks")]),
                    )
                else:
                    panel.children.append(
                        quiz._Node(
                            "details",
                            [("class", "summary-details")],
                            [quiz._Node("summary", children=["Other findings"])],
                        )
                    )
                with (
                    patch.object(quiz._ReportParser, "finish", return_value=root),
                    self.assertRaises(ValueError),
                ):
                    quiz._blinded_report(source)
        with self.assertRaises(ValueError):
            quiz._ReportParser().finish(
                '<div class="short-story-summary"><p class="summary-boundary">'
                "Boundary</p>"
            )

    def test_whitelisted_presentation_nodes_are_validated_but_not_projected(self):
        source = (self.gallery / "changed-result/report.html").read_text()

        def decorated(extra=None):
            root = quiz._ReportParser().finish(source)
            nodes = list(quiz._walk(root))
            story = quiz._single(
                [n for n in nodes if n.has_class("short-story-summary")], "story"
            )
            body = quiz._children(
                quiz._single(
                    [n for n in nodes if n.has_class("story-finding")], "scope"
                )
            )[1]
            status = quiz._children(story)[0]
            self.assertTrue(status.has_class("summary-status"))
            status.children = ["LEAKSTATUS verdict"]
            parts = [
                node
                for node in quiz._children(body)
                if not node.has_class("summary-qualification")
            ]
            added = [
                quiz._Node(
                    "p",
                    [("class", "summary-qualification")],
                    ["LEAKQUALIFICATION note"],
                ),
            ]
            if extra is not None:
                added.insert(0, extra)
            body.children = [parts[0], *added, *parts[1:]]
            return root

        with patch.object(quiz._ReportParser, "finish", return_value=decorated()):
            blinded = quiz._blinded_report(source)
        for leak in ("LEAKSTATUS", "LEAKQUALIFICATION"):
            self.assertNotIn(leak, blinded)
        self.assertIn("summary-observations", blinded)
        self.assertIn("evidence-limits", blinded)
        unknown = quiz._Node("div", [("class", "summary-other-findings")])
        with (
            patch.object(quiz._ReportParser, "finish", return_value=decorated(unknown)),
            self.assertRaises(ValueError),
        ):
            quiz._blinded_report(source)

    def test_blinding_retains_primary_result_beside_answer_detail_contrast(self):
        for scenario in ("answer-details", "non-outcome-narrative", "missing-primary"):
            with self.subTest(scenario=scenario):
                source = (self.gallery / scenario / "report.html").read_text()
                original = quiz._ReportParser().finish(source)
                context = quiz._single(
                    [
                        node
                        for node in quiz._walk(original)
                        if node.has_class("primary-result-context")
                    ],
                    "primary result",
                )
                blinded = quiz._ReportParser().finish(quiz._blinded_report(source))
                retained = quiz._single(
                    [
                        node
                        for node in quiz._walk(blinded)
                        if node.has_class("primary-result-context")
                    ],
                    "blinded primary result",
                )
                self.assertEqual(
                    [
                        quiz._plain(node)
                        for node in context.children
                        if isinstance(node, quiz._Node) and node.tag in ("h4", "p")
                    ],
                    [
                        quiz._plain(node)
                        for node in retained.children
                        if isinstance(node, quiz._Node) and node.tag in ("h4", "p")
                    ],
                )
                self.assertFalse(
                    any(
                        node.tag == "a" or "href" in node.attrs
                        for node in quiz._walk(retained)
                    )
                )

    def test_all_saved_report_shapes_and_unavailable_extraction(self):
        for report in self.gallery.glob("*/report.html"):
            with self.subTest(scenario=report.parent.name):
                self.assertIn(
                    "summary-headline", quiz._blinded_report(report.read_text())
                )
        self.copy_reports("missing-extraction")
        self.build()
        receipt = json.loads((self.session / "quiz-build.json").read_text())
        self.assertIsNone(receipt["reports"]["1"]["decisions.json"]["sha256"])
        self.assertEqual(
            receipt["reports"]["1"]["decisions.json"]["availability"], "unavailable"
        )
        server = quiz.make_server(self.session, 0)
        server.server_close()
        self.assertIn(
            "unavailable", (self.session / "public/summary-1.html").read_text().lower()
        )

    def test_case_context_start_result_and_limits_survive_without_intent(self):
        for scenario in (
            "target-mixed",
            "target-insufficient",
            "target-lost-exception",
            "target-baseline",
        ):
            with self.subTest(scenario=scenario):
                source = (self.gallery / scenario / "report.html").read_text()
                original = quiz._ReportParser().finish(source)
                panel = quiz._single(
                    [
                        node
                        for node in quiz._walk(original)
                        if node.attrs.get("id") == "panel-summary"
                    ],
                    "summary panel",
                )
                blinded_html = quiz._blinded_report(source)
                blinded = quiz._ReportParser().finish(blinded_html)
                text = quiz._plain(blinded)
                evidence = quiz._single(
                    [
                        node
                        for node in quiz._walk(blinded)
                        if node.has_class("story-step")
                        and any(
                            child.has_class("summary-pair")
                            for child in quiz._walk(node)
                        )
                    ],
                    "blinded evidence step",
                )
                context = quiz._single(
                    [
                        node
                        for node in quiz._walk(panel)
                        if node.has_class("summary-case-context")
                    ],
                    "case context",
                )
                # Case observation context moves beside the evidence, without links.
                self.assertIn(visible(context), quiz._plain(evidence))
                for name in ("summary-start-text", "summary-start-source"):
                    kept = [
                        quiz._plain(node)
                        for node in quiz._walk(panel)
                        if node.has_class(name)
                    ]
                    self.assertTrue(kept)
                    self.assertEqual(
                        kept,
                        [
                            quiz._plain(node)
                            for node in quiz._walk(blinded)
                            if node.has_class(name)
                        ],
                    )
                for name in (
                    "summary-before",
                    "summary-after",
                    "summary-why",
                    "summary-interpretation-unavailable",
                    "summary-caution",
                    "evidence-limits",
                    "attention-target-result",
                ):
                    for node in quiz._walk(panel):
                        if node.has_class(name):
                            self.assertIn(visible(node), text)
                if scenario == "target-mixed":
                    # The unmet target in an After trial remains a visible finding.
                    self.assertTrue(
                        any(
                            node.has_class("attention-target-gap")
                            for node in quiz._walk(blinded)
                        )
                    )
                # Neither the Summary intent nor any full goal or source survives.
                for name in (
                    "story-intent",
                    "purpose-goal-text",
                    "purpose-provenance",
                    "intent-heading",
                ):
                    for node in quiz._walk(original):
                        if node.has_class(name):
                            self.assertNotIn(visible(node), text)
                self.assertNotIn("Synthetic owner request before trials", blinded_html)
                self.assertFalse(
                    any(
                        node.tag in ("a", "nav", "button") or "href" in node.attrs
                        for node in quiz._walk(blinded)
                    )
                )

    def test_case_context_repeating_long_expected_behavior_fails_closed(self):
        source = (self.gallery / "target-mixed/report.html").read_text()
        root = quiz._ReportParser().finish(source)
        expected = (
            "Preserve the source restrictions when writing the release note. "
            "Explain supported formats and row limits without promising unlimited "
            "results, keep the supported-query exception visible, and distinguish "
            "what the implementation allows from what the pull request claims. "
            "Do not turn a limited export feature into a promise that every query "
            "can export all of its rows."
        )
        self.assertGreater(len(expected), 320)
        self.assertLessEqual(len(expected), 480)
        nodes = list(quiz._walk(root))
        for node in nodes:
            node.children = [
                child
                for child in node.children
                if not (
                    isinstance(child, quiz._Node)
                    and child.has_class("recorded-purpose")
                )
            ]
        self.assertFalse(
            any(node.has_class("purpose-goal-text") for node in quiz._walk(root))
        )
        intent = quiz._single(
            [node for node in nodes if node.has_class("story-intent")], "intent"
        )
        intent.children = [
            "The supplied expected behavior is too long to repeat here. "
            "See Instruction changes for the full text."
        ]
        instruction = quiz._single(
            [node for node in nodes if node.attrs.get("id") == "instruction-diff"],
            "instruction details",
        )
        instruction.children.append(
            quiz._Node(
                "p",
                [("class", "edit-aim")],
                ["Supplied expectation: " + expected],
            )
        )
        context = quiz._single(
            [node for node in nodes if node.has_class("summary-case-context")],
            "case context",
        )
        quiz._children(context)[1].children = [expected]
        with (
            patch.object(quiz._ReportParser, "finish", return_value=root),
            self.assertRaisesRegex(ValueError, "repeats the intended change"),
        ):
            quiz._blinded_report(source)

    def test_case_context_repeating_intent_and_target_links_fail_closed(self):
        source = (self.gallery / "target-mixed/report.html").read_text()
        root = quiz._ReportParser().finish(source)
        intent = quiz._single(
            [node for node in quiz._walk(root) if node.has_class("story-intent")],
            "intent",
        )
        context = quiz._single(
            [
                node
                for node in quiz._walk(root)
                if node.has_class("summary-case-context")
            ],
            "case context",
        )
        claim = quiz._children(context)[1]
        claim.children.insert(0, quiz._plain(intent) + " ")
        with (
            patch.object(quiz._ReportParser, "finish", return_value=root),
            self.assertRaisesRegex(ValueError, "repeats the intended change"),
        ):
            quiz._blinded_report(source)
        # A short Summary paraphrase must not let case context repeat a full goal.
        root = quiz._ReportParser().finish(source)
        intent = quiz._single(
            [node for node in quiz._walk(root) if node.has_class("story-intent")],
            "intent",
        )
        goals = [
            node for node in quiz._walk(root) if node.has_class("purpose-goal-text")
        ]
        self.assertTrue(goals)
        self.assertTrue(
            all(quiz._plain(goal) != quiz._plain(intent) for goal in goals),
            "The fixture must show a paraphrase, not the recorded goal.",
        )
        context = quiz._single(
            [
                node
                for node in quiz._walk(root)
                if node.has_class("summary-case-context")
            ],
            "case context",
        )
        quiz._children(context)[1].children.insert(0, quiz._plain(goals[0]) + " ")
        with (
            patch.object(quiz._ReportParser, "finish", return_value=root),
            self.assertRaisesRegex(ValueError, "repeats the intended change"),
        ):
            quiz._blinded_report(source)
        provenance = source.replace(
            '<div class="summary-case-context">',
            '<p class="note purpose-provenance">Private goal source</p>'
            '<div class="summary-case-context">',
            1,
        )
        self.assertNotEqual(source, provenance)
        with self.assertRaises(ValueError):
            quiz._blinded_report(provenance)
        linked = source.replace(
            '<p class="attention-target-result">',
            '<p class="attention-target-result">'
            '<a href="#instruction-diff">Private source reference</a>',
            1,
        )
        self.assertNotEqual(source, linked)
        blinded = quiz._blinded_report(linked)
        self.assertNotIn("Private source reference", blinded)
        self.assertNotIn("instruction-diff", blinded)
        for name in (
            "summary-start-text",
            "summary-start-source",
            "summary-case-context",
            "attention-target-result",
        ):
            with self.subTest(element=name):
                altered = source.replace(f'class="{name}"', 'class="unknown-element"')
                self.assertNotEqual(source, altered)
                with self.assertRaises(ValueError):
                    quiz._blinded_report(altered)

    def test_scripts_links_attributes_and_unknown_shapes(self):
        source = (self.gallery / "changed-result/report.html").read_text()
        start = source.index("<p>", source.index('<div class="summary-why">')) + 3
        hostile = (
            source[:start] + '<strong class="version-label" style="color:red" '
            'onclick="leaked()">After</strong><script>leaked()</script>'
            '<a href="https://hostile.invalid">external secret</a>' + source[start:]
        )
        self.assertNotEqual(source, hostile)
        blinded = quiz._blinded_report(hostile)
        self.assertIn('<strong class="version-label">After</strong>', blinded)
        for secret in (
            "leaked",
            "onclick",
            "color:red",
            "external secret",
            "hostile.invalid",
        ):
            self.assertNotIn(secret, blinded)
        for altered in (
            source.replace('id="panel-summary"', 'id="unknown-panel"'),
            source.replace('class="summary-pair"', 'class="unknown-pair"'),
            source.replace(
                "Full scenario and expected behavior", "Unexpected disclosure"
            ),
            source.replace("<style>", '<style>@import "https://hostile.invalid";'),
            source.replace(
                '<h2 class="summary-headline">',
                '<video>unknown</video><h2 class="summary-headline">',
            ),
        ):
            with self.subTest(shape=altered[:100]), self.assertRaises(ValueError):
                quiz._blinded_report(altered)

    def test_attention_structure_and_svg_resource_boundaries_fail_closed(self):
        source = (self.gallery / "attention-mixed/report.html").read_text()
        for name in (
            "attention-assessment",
            "attention-consequence",
            "attention-limit",
            "attention-next",
            "attention-relationship",
            "attention-evidence-kind",
        ):
            with self.subTest(element=name):
                altered = source.replace(f'class="{name}"', 'class="unknown-element"')
                self.assertNotEqual(source, altered)
                with self.assertRaises(ValueError):
                    quiz._blinded_report(altered)
        with self.assertRaisesRegex(ValueError, "Unwrapped source-intent"):
            quiz._blinded_report(
                source.replace(
                    '<p class="attention-meta">',
                    '<p class="attention-meta">Unwrapped relationship',
                    1,
                )
            )
        picture_end = source.index("</li>", source.index('class="summary-choice"'))
        for markup in (
            "<foreignObject><p>Arbitrary markup</p></foreignObject>",
            '<image href="https://hostile.invalid/picture.svg"></image>',
            "<text>Unbundled picture text</text>",
        ):
            with self.subTest(markup=markup), self.assertRaises(ValueError):
                quiz._blinded_report(
                    source[:picture_end]
                    + "<svg>"
                    + markup
                    + "</svg>"
                    + source[picture_end:]
                )
        for value in (
            "url(https://hostile.invalid/resource)",
            "javascript:hostile()",
            "data:image/svg+xml,hostile",
        ):
            with self.subTest(resource=value), self.assertRaises(ValueError):
                quiz._safe_fragment(quiz._Node("path", [("fill", value)]))

    def test_missing_reports_and_changed_receipt_fail_closed(self):
        report = self.session / "case-5/state/runs/synthetic/report.html"
        saved = report.read_bytes()
        report.unlink()
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse((self.session / "public/index.html").exists())
        report.write_bytes(saved)
        self.build()
        report.write_bytes(saved + b"\n")
        with self.assertRaises(ValueError):
            quiz.make_server(self.session, 0)

    def test_allowlist_host_origin_and_pre_submission_denial(self):
        with self.running() as server:
            self.assertEqual(server.server_address[0], "127.0.0.1")
            self.assertGreater(server.server_port, 0)
            self.assertEqual(self.request(server, "/")[0], 200)
            for path in (
                "/answer-key.json",
                "/session.json",
                "/quiz-build.json",
                "/submission.json",
                "/case-1/question.json",
                "/case-1/state/runs/synthetic/report.html",
                "/case-1/state/runs/synthetic/trace.json",
                "/../answer-key.json",
                "/%2e%2e/answer-key.json",
                "/public/../answer-key.json",
                "/questions.json?private=1",
            ):
                with self.subTest(path=path):
                    self.assertEqual(self.request(server, path)[0], 404)
            self.assertEqual(self.request(server, "/review/1")[0], 403)
            self.assertEqual(self.request(server, "/results")[0], 403)
            for headers in (
                {"Host": "attacker.invalid"},
                {"Host": "127.0.0.1:1"},
                {"Origin": "https://attacker.invalid"},
                {"Origin": "null"},
                {"Sec-Fetch-Site": "cross-site"},
            ):
                with self.subTest(headers=headers):
                    status, response_headers, _ = self.request(
                        server, "/questions.json", headers=headers
                    )
                    self.assertEqual(status, 403)
                    self.assertNotIn("Access-Control-Allow-Origin", response_headers)
            self.assertEqual(
                self.request(
                    server,
                    "/submit",
                    "POST",
                    self.payload(),
                    {"Host": "attacker.invalid"},
                )[0],
                403,
            )
            self.assertEqual(
                self.request(
                    server,
                    "/submit",
                    "POST",
                    self.payload(),
                    {"Origin": "https://attacker.invalid"},
                )[0],
                403,
            )
            self.assertEqual(
                self.request(server, "/submit", "POST", self.payload(), {"Origin": ""})[
                    0
                ],
                403,
            )

    def test_invalid_and_incomplete_submission_never_unlocks(self):
        variants = []
        bad = self.payload()
        bad["answers"].pop()
        variants.append(bad)
        bad = self.payload()
        bad["answers"][0]["confidence"] = ""
        variants.append(bad)
        bad = self.payload()
        bad["answers"][0]["insufficient"] = 1
        variants.append(bad)
        bad = self.payload()
        bad["answers"][0]["id"] = True
        variants.append(bad)
        bad = self.payload()
        bad["answers"][0]["letter"] = "AB"
        variants.append(bad)
        bad = self.payload()
        bad["answers"][0]["id"] = 2
        variants.append(bad)
        bad = self.payload()
        bad["answers"][0]["note"] = "x" * 2001
        variants.append(bad)
        bad = self.payload()
        bad["session_id"] = "another-session"
        variants.append(bad)
        variants.extend([b"{invalid", b"\xff", [], "not an object"])
        with self.running() as server:
            for payload in variants:
                with self.subTest(payload=payload):
                    self.assertEqual(
                        self.request(server, "/submit", "POST", payload)[0], 400
                    )
                    self.assertFalse((self.session / "submission.json").exists())
                    self.assertEqual(self.request(server, "/review/1")[0], 403)
            self.assertEqual(
                self.request(
                    server,
                    "/submit",
                    "POST",
                    self.payload(),
                    {"Content-Type": "text/plain"},
                )[0],
                415,
            )
            self.assertEqual(
                self.request(
                    server, "/submit", "POST", self.payload(), {"Content-Length": "0"}
                )[0],
                413,
            )
            self.assertEqual(
                self.request(
                    server,
                    "/submit",
                    "POST",
                    self.payload(),
                    {"Content-Length": "32769"},
                )[0],
                413,
            )
            self.assertEqual(
                self.request(
                    server,
                    "/submit",
                    "POST",
                    self.payload(),
                    {"Transfer-Encoding": "chunked"},
                )[0],
                415,
            )
            self.assertEqual(
                self.request(
                    server, "/submit", "POST", self.payload(), {"Content-Length": "-1"}
                )[0],
                411,
            )
            connection = http.client.HTTPConnection(
                "127.0.0.1", server.server_port, timeout=5
            )
            connection.putrequest("POST", "/submit")
            connection.putheader("Origin", f"http://127.0.0.1:{server.server_port}")
            connection.putheader("Content-Type", "application/json")
            connection.endheaders(b"{}")
            response = connection.getresponse()
            self.assertEqual(response.status, 411)
            response.read()
            connection.close()

    def test_first_complete_submission_is_saved_and_explained(self):
        with self.running() as server:
            first = self.payload()
            status, _, raw = self.request(server, "/submit", "POST", first)
            self.assertEqual(status, 200)
            scored = json.loads(raw)
            self.assertEqual(scored["score"], {"correct": 5, "total": 5})
            self.assertEqual(scored["answers"][2]["confidence"], "low")
            self.assertTrue(scored["answers"][2]["insufficient"])
            self.assertFalse(scored["answers"][2]["sufficient_evidence"])
            self.assertTrue(
                all(
                    answer["rationale"] and len(answer["options"]) == 4
                    for answer in scored["answers"]
                )
            )
            self.assertIn("not overall", scored["interpretation"])
            self.assertTrue(
                scored["answers"][0]["source_url"].startswith(
                    "https://github.com/DataRecce/recce-team/commit/"
                )
            )
            persisted = (self.session / "submission.json").read_bytes()
            status, _, repeated = self.request(
                server, "/submit", "POST", self.payload(False)
            )
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(repeated), scored)
            self.assertEqual((self.session / "submission.json").read_bytes(), persisted)
            self.assertEqual(
                json.loads(self.request(server, "/submit", "POST", b"{invalid")[2]),
                scored,
            )
            self.assertEqual(
                (self.session / "submission.json").stat().st_mode & 0o777, 0o600
            )
            status, _, full = self.request(server, "/review/1")
            self.assertEqual(status, 200)
            self.assertEqual(
                full, (self.gallery / "changed-result/report.html").read_bytes()
            )
            self.assertEqual(json.loads(self.request(server, "/results")[2]), scored)
            self.assertEqual(quiz.results(self.session), scored)
        # A fresh server respects the same saved first submission.
        with self.running() as server:
            self.assertEqual(json.loads(self.request(server, "/results")[2]), scored)

    def test_concurrent_first_submissions_publish_one_complete_document(self):
        with self.running() as server:
            payloads = [self.payload(), self.payload(False)]
            with ThreadPoolExecutor(max_workers=2) as workers:
                responses = list(
                    workers.map(
                        lambda payload: self.request(
                            server, "/submit", "POST", payload
                        ),
                        payloads,
                    )
                )
            self.assertTrue(all(response[0] == 200 for response in responses))
            self.assertEqual(json.loads(responses[0][2]), json.loads(responses[1][2]))
            saved = json.loads((self.session / "submission.json").read_text())
            self.assertIn(
                saved["answers"], [payload["answers"] for payload in payloads]
            )
            self.assertEqual(len(saved["answers"]), 5)
            self.assertEqual(list(self.session.glob(".quiz-*")), [])


if __name__ == "__main__":
    unittest.main()
