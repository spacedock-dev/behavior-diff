#!/usr/bin/env python3
"""Synthetic saved-evidence export/analysis contracts; no trials or private reads."""

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from report_fixtures import build_reports

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


helpers = load(
    "synthetic_workflow_helpers", ROOT / "tests/human-evaluation-workflow-test.py"
)
workflow = helpers.workflow
quiz = workflow.quiz_module()
hosted = workflow.hosted_module()


def prepare_session(root, source, gallery):
    session = root / "session"
    manifest = workflow.populate_session(session, source, seed=17)
    for entry in manifest["cases"]:
        case = session / f"case-{entry['id']}"
        fixture = case / "fixture"
        helpers.repository(fixture)
        target = fixture / ".claude/skills/example/SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_bytes((case / "before.md").read_bytes())
        (fixture / "input.txt").write_text("Synthetic task input.\n")
        helpers.commit(fixture, "Synthetic Before")
        target.write_bytes((case / "after.md").read_bytes())
        workflow.save_json(
            case / "scenario.json",
            {
                "file": ".claude/skills/example/SKILL.md",
                "task": "Read the skill and explain the synthetic rule.",
            },
        )
        workflow.save_json(
            case / "question.json",
            {
                "stem": "Which synthetic contrast is observed?",
                "scope": "Only this authored synthetic fixture.",
                "options": [
                    {
                        "statement": f"Synthetic option {index}",
                        "correct": index == 2,
                        "rationale": f"Synthetic rationale {index}",
                    }
                    for index in range(4)
                ],
            },
        )
    workflow.freeze_session(session)
    for number in range(1, 6):
        run = session / f"case-{number}/state/runs/synthetic"
        run.mkdir(parents=True)
        for name in ("report.html", "report.md", "decisions.json", "report-data.json"):
            original = gallery / "changed-result" / name
            if original.exists():
                shutil.copyfile(original, run / name)
    quiz.build_quiz(session, ROOT)
    return session


def synthetic_export(root):
    """Persist a production-CLI package using existing authored synthetic fixtures."""
    root = Path(root).expanduser().resolve()
    hosted.outside_trees(root, ROOT)
    root.mkdir(mode=0o700)
    source, _, _, _ = helpers.synthetic_history(root)
    gallery = root / "gallery"
    gallery.mkdir()
    build_reports(gallery)
    session = prepare_session(root, source, gallery)
    status = workflow.main(
        [
            "export-package",
            str(session),
            "--evaluation-id",
            "synthetic-saved-evidence",
            "--title",
            "Synthetic saved evidence compatibility fixture",
            "--out",
            str(root / "package"),
        ]
    )
    if status:
        raise ValueError("Synthetic production export failed")


class HostedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory(prefix="hosted-synthetic-shared-")
        root = Path(cls.shared.name).resolve()
        cls.source, _, _, _ = helpers.synthetic_history(root)
        cls.gallery = root / "gallery"
        cls.gallery.mkdir()
        build_reports(cls.gallery)

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="hosted-synthetic-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.session = prepare_session(self.root, self.source, self.gallery)
        self.package = self.root / "package"
        self.responses = self.root / "responses.json"

    def cli(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = workflow.main([str(value) for value in arguments])
        return status, stdout.getvalue(), stderr.getvalue()

    def export(self):
        status, stdout, stderr = self.cli(
            "export-package",
            self.session,
            "--evaluation-id",
            "synthetic-cohort",
            "--title",
            "Synthetic cohort",
            "--out",
            self.package,
        )
        self.assertEqual(status, 0, stderr)
        return json.loads(stdout)

    def response_export(self):
        manifest = hosted.read_json(self.package / "manifest.json")
        questions = hosted.read_json(self.package / "questions.json")
        content_hash = hosted.digest(hosted.canonical(manifest))
        records = []
        for index, name in enumerate(("Synthetic Person", "synthetic person")):
            submission = {
                "schemaVersion": 1,
                "evaluationId": manifest["evaluationId"],
                "respondent": name,
                "contentHash": content_hash,
                "siteBuild": f"synthetic-build-{index}",
                "answers": {q["id"]: q["correctOption"] for q in questions},
                "confidence": {case: "high" for case in hosted.CASE_IDS},
                "insufficientEvidence": {
                    case: case == "case-3" for case in hosted.CASE_IDS
                },
                "notes": {case: "Synthetic note" for case in hosted.CASE_IDS},
                "clientScore": 0,
                "submittedAt": "2026-10-06T12:00:00.000Z",
            }
            records.append(
                {
                    "uid": f"synthetic-uid-{index}",
                    "submission": submission,
                    "recomputedScore": 1,
                }
            )
        return {
            "schemaVersion": 1,
            "evaluationId": manifest["evaluationId"],
            "contentHash": content_hash,
            "manifest": manifest,
            "exportedAt": "2026-10-06T13:00:00.000Z",
            "responses": records,
        }

    def analyze(self, exported):
        self.responses.write_bytes(hosted.json_bytes(exported))
        return self.cli(
            "hosted-results",
            self.session,
            "--package",
            self.package,
            "--responses",
            self.responses,
        )

    def test_exact_saved_bytes_minimal_mapping_and_local_provenance(self):
        result = self.export()
        self.assertFalse(result["publicationAuthorized"])
        manifest = hosted.read_json(self.package / "manifest.json")
        self.assertEqual(
            set(manifest),
            {
                "schemaVersion",
                "evaluationId",
                "title",
                "caseIds",
                "producerVersion",
                "files",
            },
        )
        self.assertEqual(manifest["caseIds"], hosted.CASE_IDS)
        self.assertEqual(
            result["contentHash"], hosted.digest(hosted.canonical(manifest))
        )
        questions = hosted.read_json(self.package / "questions.json")
        key = hosted.read_json(self.session / "answer-key.json")
        for number, (question, frozen) in enumerate(
            zip(questions, key["questions"]), 1
        ):
            self.assertEqual(set(question), {"id", "stem", "options", "correctOption"})
            self.assertEqual(question["correctOption"], frozen["correct"])
            self.assertEqual(
                [option["id"] for option in question["options"]], list("ABCD")
            )
            self.assertTrue(
                all(set(option) == {"id", "text"} for option in question["options"])
            )
            data = (self.package / f"summaries/case-{number}.html").read_bytes()
            self.assertEqual(
                data, (self.session / f"public/summary-{number}.html").read_bytes()
            )
            self.assertEqual(
                manifest["files"][f"summaries/case-{number}.html"], hosted.digest(data)
            )
        self.assertEqual(
            manifest["files"]["questions.json"],
            hosted.digest(hosted.canonical(questions)),
        )
        for path in self.package.rglob("*"):
            self.assertFalse(path.is_symlink())
            if path.is_file():
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        mapping = Path(result["privateMappingPath"])
        self.assertTrue(self.session in mapping.parents)
        self.assertNotIn(self.package, mapping.parents)
        self.assertEqual(mapping.stat().st_mode & 0o777, 0o600)
        shipped = b"".join(
            path.read_bytes() for path in self.package.rglob("*") if path.is_file()
        )
        self.assertNotIn(str(self.session).encode(), shipped)
        self.assertNotIn(b"Synthetic rationale", shipped)

    def test_immutable_destination_and_export_identity(self):
        self.export()
        before = (self.package / "manifest.json").read_bytes()
        status, _, _ = self.cli(
            "export-package",
            self.session,
            "--evaluation-id",
            "other-id",
            "--title",
            "Other",
            "--out",
            self.package,
        )
        self.assertEqual(status, 2)
        self.assertEqual((self.package / "manifest.json").read_bytes(), before)
        another = self.root / "another"
        status, _, _ = self.cli(
            "export-package",
            self.session,
            "--evaluation-id",
            "synthetic-cohort",
            "--title",
            "Other",
            "--out",
            another,
        )
        self.assertEqual(status, 2)
        self.assertFalse(another.exists())

    def test_reject_tree_destinations_symlinks_and_invalid_ids(self):
        link = self.root / "link"
        link.symlink_to(self.root, target_is_directory=True)
        for destination in (
            ROOT / "synthetic-package",
            ROOT.parent / "behavior-diff-evaluation/synthetic-package",
            link / "package",
            self.session / "package",
        ):
            with self.subTest(destination=destination):
                status, _, _ = self.cli(
                    "export-package",
                    self.session,
                    "--evaluation-id",
                    "synthetic-cohort",
                    "--title",
                    "Synthetic",
                    "--out",
                    destination,
                )
                self.assertEqual(status, 2)
        status, _, _ = self.cli(
            "export-package",
            self.session,
            "--evaluation-id",
            "../escape",
            "--title",
            "Synthetic",
            "--out",
            self.package,
        )
        self.assertEqual(status, 2)
        self.assertFalse(self.package.exists())

    def test_frozen_inputs_and_saved_build_drift_fail_before_writes(self):
        frozen = self.session / "answer-key.json"
        original = frozen.read_bytes()
        frozen.write_bytes(original + b" ")
        status, _, _ = self.cli(
            "export-package",
            self.session,
            "--evaluation-id",
            "synthetic-cohort",
            "--title",
            "Synthetic",
            "--out",
            self.package,
        )
        self.assertEqual(status, 2)
        self.assertFalse(self.package.exists())
        frozen.write_bytes(original)
        (self.session / "public/summary-1.html").write_text("Changed saved summary")
        status, _, _ = self.cli(
            "export-package",
            self.session,
            "--evaluation-id",
            "synthetic-cohort",
            "--title",
            "Synthetic",
            "--out",
            self.package,
        )
        self.assertEqual(status, 2)
        self.assertFalse(self.package.exists())

    def test_forged_projection_receipt_and_oversize_fail_closed(self):
        summary = self.session / "public/summary-1.html"
        receipt_path = self.session / "quiz-build.json"
        receipt = hosted.read_json(receipt_path)
        summary.write_bytes(
            summary.read_bytes().replace(b"<body>", b"<body><p>Forged prose</p>", 1)
        )
        receipt["public"]["summary-1.html"] = hosted.digest(summary.read_bytes())
        receipt_path.write_bytes(hosted.json_bytes(receipt))
        status, _, _ = self.cli(
            "export-package",
            self.session,
            "--evaluation-id",
            "synthetic-cohort",
            "--title",
            "Synthetic",
            "--out",
            self.package,
        )
        self.assertEqual(status, 2)
        self.assertFalse(self.package.exists())
        quiz.build_quiz(self.session, ROOT)
        with patch.object(hosted, "SUMMARY_LIMIT", 1):
            with self.assertRaisesRegex(ValueError, "too large"):
                hosted.export_package(
                    self.session,
                    quiz,
                    ROOT,
                    "synthetic-cohort",
                    "Synthetic",
                    self.package,
                )
        self.assertFalse(self.package.exists())

    def test_failed_write_cleans_only_new_destination(self):
        with patch.object(
            hosted, "exclusive_file", side_effect=OSError("Synthetic write failure")
        ):
            with self.assertRaises(OSError):
                hosted.export_package(
                    self.session,
                    quiz,
                    ROOT,
                    "synthetic-cohort",
                    "Synthetic",
                    self.package,
                )
        self.assertFalse(self.package.exists())
        self.assertTrue((self.session / "answer-key.json").is_file())
        self.assertFalse(
            (self.session / "hosted-exports/synthetic-cohort.json").exists()
        )

    def test_recomputes_all_responses_keeps_originals_and_advises_duplicates(self):
        self.export()
        exported = self.response_export()
        before = hosted.json_bytes(exported)
        status, stdout, stderr = self.analyze(exported)
        self.assertEqual(status, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result["responseCount"], 2)
        self.assertEqual(len(result["duplicateRespondents"]), 1)
        self.assertEqual(
            result["duplicateRespondents"][0]["uids"],
            ["synthetic-uid-0", "synthetic-uid-1"],
        )
        self.assertEqual(
            [item["id"] for item in result["questionValidity"]], hosted.CASE_IDS
        )
        self.assertTrue(
            all(item["status"] == "not-assessed" for item in result["questionValidity"])
        )
        for original, analyzed in zip(exported["responses"], result["responses"]):
            self.assertEqual(analyzed["original"], original)
            self.assertEqual(
                analyzed["keyedResult"]["score"], {"correct": 5, "total": 5}
            )
            self.assertFalse(analyzed["clientScoreMatches"])
            self.assertFalse(analyzed["exportedScoreMatches"])
            self.assertEqual(analyzed["insufficientEvidenceCount"], 1)
            self.assertEqual(len(analyzed["keyedResult"]["answers"]), 5)
        self.assertEqual(self.responses.read_bytes(), before)
        self.assertFalse((self.session / "submission.json").exists())

    def test_invalid_identity_maps_types_and_duplicate_uid_rejected(self):
        self.export()
        original = self.response_export()
        variants = []
        for field, value in (
            ("schemaVersion", True),
            ("evaluationId", "another"),
            ("contentHash", "0" * 64),
        ):
            bad = copy.deepcopy(original)
            bad[field] = value
            variants.append(bad)
        for field, value in (
            ("schemaVersion", True),
            ("clientScore", True),
            ("respondent", " "),
            ("submittedAt", "2026-10-06T12:00:00"),
            ("answers", {"case-1": "A"}),
            ("notes", {case: 1 for case in hosted.CASE_IDS}),
        ):
            bad = copy.deepcopy(original)
            bad["responses"][0]["submission"][field] = value
            variants.append(bad)
        bad = copy.deepcopy(original)
        bad["responses"][1]["uid"] = bad["responses"][0]["uid"]
        variants.append(bad)
        for bad in variants:
            with self.subTest(export=bad):
                status, stdout, _ = self.analyze(bad)
                self.assertEqual(status, 2)
                self.assertEqual(stdout, "")

    def test_package_allowlist_drift_symlink_and_provenance_rejected(self):
        self.export()
        exported = self.response_export()
        extra = self.package / "private-provenance.json"
        extra.write_text("{}")
        self.assertEqual(self.analyze(exported)[0], 2)
        extra.unlink()
        summary = self.package / "summaries/case-1.html"
        original = summary.read_bytes()
        summary.unlink()
        summary.symlink_to(self.session / "public/summary-1.html")
        self.assertEqual(self.analyze(exported)[0], 2)
        summary.unlink()
        summary.write_bytes(original + b" ")
        self.assertEqual(self.analyze(exported)[0], 2)
        summary.write_bytes(original)
        mapping = self.session / "hosted-exports/synthetic-cohort.json"
        local = hosted.read_json(mapping)
        local["contentHash"] = "0" * 64
        mapping.write_bytes(hosted.json_bytes(local))
        self.assertEqual(self.analyze(exported)[0], 2)

    def test_semantic_json_formatting_and_empty_response_export(self):
        self.export()
        exported = self.response_export()
        exported["responses"] = []
        for name in ("manifest.json", "questions.json"):
            path = self.package / name
            path.write_bytes(hosted.canonical(hosted.read_json(path)))
        status, stdout, stderr = self.analyze(exported)
        self.assertEqual(status, 0, stderr)
        self.assertEqual(json.loads(stdout)["responseCount"], 0)
        self.assertEqual(len(json.loads(stdout)["questionValidity"]), 5)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--export-synthetic":
        synthetic_export(sys.argv[2])
    else:
        unittest.main()
