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
        blinded = (self.session / "public/summary-1.html").read_text()
        blind_root = quiz._ReportParser().finish(blinded)
        text = quiz._plain(blind_root)
        for name in (
            "summary-headline",
            "summary-context",
            "summary-provenance",
            "summary-status",
            "summary-before",
            "summary-after",
            "summary-why",
            "summary-caution",
            "summary-notices",
            "evidence-limits",
        ):
            for node in nodes:
                if node.has_class(name):
                    expected = quiz._plain(node)
                    # Navigation is excluded; generated supported-claim text remains unchanged.
                    if name in ("summary-why", "summary-caution"):
                        expected = "".join(
                            quiz._plain(child)
                            if isinstance(child, quiz._Node)
                            else child
                            for child in node.children
                            if not isinstance(child, quiz._Node)
                            or not child.has_class("evidence-links")
                        )
                    self.assertIn(expected, text)
        for name in ("story-intent", "scenario-context", "scenario-prompt"):
            for node in nodes:
                if node.has_class(name) and quiz._plain(node).strip():
                    self.assertNotIn(quiz._plain(node), text)
        self.assertNotIn("Full scenario and expected behavior", blinded)
        self.assertNotIn('id="panel-instruction"', blinded)
        self.assertNotIn("<script", blinded)
        self.assertNotIn("<nav", blinded)
        self.assertNotIn("<a ", blinded)
        self.assertNotIn("https://", blinded)
        self.assertNotIn("Other findings", blinded)
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

    def test_attention_pictures_counts_and_states_survive_blinding(self):
        for scenario in (
            "attention-mixed",
            "attention-self-reported",
            "attention-plans",
            "attention-quiet",
            "attention-unavailable",
            "attention-multiple",
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
                if scenario == "attention-self-reported":
                    self.assertIn(
                        "Self-reported actions, not independently captured command evidence",
                        quiz._plain(retained),
                    )
                    self.assertNotIn("Recorded actions", quiz._plain(retained))
                for name in (
                    "attention-assessment",
                    "attention-branch",
                    "attention-consequence",
                    "attention-evidence-kind",
                    "attention-limit",
                    "attention-guidance",
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
                self.assertEqual(
                    [
                        quiz._plain(
                            quiz._ReportParser().finish(quiz._safe_fragment(node))
                        )
                        for node in original_nodes
                        if node.has_class("attention-meta")
                    ],
                    [
                        quiz._plain(node)
                        for node in retained_nodes
                        if node.has_class("attention-meta")
                    ],
                )
                branches = [
                    node
                    for node in retained_nodes
                    if node.has_class("attention-branch")
                ]
                self.assertEqual(
                    len(branches) * 2,
                    sum(node.tag == "svg" for node in retained_nodes),
                )
                for svg in (node for node in retained_nodes if node.tag == "svg"):
                    self.assertEqual(svg.attrs["aria-hidden"], "true")
                    self.assertEqual(svg.attrs["focusable"], "false")
                    self.assertIn("viewbox", svg.attrs)
                    self.assertTrue(quiz._children(svg))
                for forbidden in (
                    "<button",
                    "<nav",
                    "<a ",
                    "data-attention-",
                    "Not relevant here",
                    "Show again",
                ):
                    self.assertNotIn(forbidden, blinded_html)
                steps = [
                    node for node in quiz._walk(blinded) if node.has_class("story-step")
                ]
                self.assertEqual(len(steps), 3)
                self.assertEqual(
                    [
                        quiz._plain(quiz._children(quiz._children(step)[1])[0])
                        for step in steps
                    ],
                    [
                        "What the evidence shows",
                        "What needs your attention",
                        "What this means",
                    ],
                )

    def test_old_summary_shapes_and_wrapper_recovery_are_rejected(self):
        source = (self.gallery / "changed-result/report.html").read_text()
        for legacy in ("three-steps", "other-findings"):
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
                if legacy == "three-steps":
                    steps = quiz._single(
                        [
                            node
                            for node in quiz._walk(panel)
                            if node.has_class("story-steps")
                        ],
                        "story steps",
                    )
                    steps.children = [
                        child
                        for child in steps.children
                        if not isinstance(child, quiz._Node)
                        or not child.has_class("story-attention")
                    ]
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

    def test_blinding_preserves_assessment_counts_without_source_links(self):
        source = (self.gallery / "target-mixed/report.html").read_text()
        blinded = quiz._blinded_report(source)
        parsed = quiz._ReportParser().finish(blinded)
        table = quiz._single(
            [node for node in quiz._walk(parsed) if node.has_class("target-checks")],
            "blinded assessment",
        )
        self.assertIn("No (3/3) → Yes (2/3); No (1/3)", quiz._plain(table))
        emphasis = quiz._single(
            [
                node
                for node in quiz._walk(table)
                if node.has_class("target-result-changed")
            ],
            "changed assessment",
        )
        self.assertEqual(emphasis.tag, "strong")
        self.assertNotIn("Synthetic owner request before trials", blinded)
        self.assertFalse(any(node.tag == "a" for node in quiz._walk(table)))
        with self.assertRaises(ValueError):
            quiz._blinded_report(
                source.replace(
                    "<td>",
                    '<td><a href="#instruction-diff">Private source reference</a>',
                    1,
                )
            )

    def test_scripts_links_attributes_and_unknown_shapes(self):
        source = (self.gallery / "changed-result/report.html").read_text()
        hostile = source.replace(
            '<h2 class="summary-headline">',
            '<h2 class="summary-headline" onclick="leaked()"><script>leaked()</script><a href="https://hostile.invalid">external secret</a>',
        )
        blinded = quiz._blinded_report(hostile)
        for secret in ("leaked", "onclick", "external secret", "hostile.invalid"):
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
            "attention-limit",
            "attention-flow-step",
            "attention-guidance",
            "attention-relationship",
            "attention-evidence-kind",
            "summary-count",
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
        attention_svg_end = source.index(
            "</svg>", source.index('class="attention-flow-step"')
        )
        for markup in (
            "<foreignObject><p>Arbitrary markup</p></foreignObject>",
            '<image href="https://hostile.invalid/picture.svg"></image>',
            "<text>Unbundled picture text</text>",
        ):
            with self.subTest(markup=markup), self.assertRaises(ValueError):
                quiz._blinded_report(
                    source[:attention_svg_end] + markup + source[attention_svg_end:]
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
