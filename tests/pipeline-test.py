#!/usr/bin/env python3
"""Synthetic, model-free dependency, persistence, and partial-result contracts."""

from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(SCRIPTS))
from pipeline import Pipeline, Stage  # noqa: E402
from stage_contract import StageResult, content_hash  # noqa: E402


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.records = self.root / "stages"
        self.calls = []

    def callback(self, name, state="completed"):
        def run(dependencies):
            self.calls.append((name, dict(dependencies)))
            return StageResult(state, output={"synthetic": name})

        return run

    def pipeline(self, stages, **kwargs):
        return Pipeline(
            stages, self.records, producer="synthetic-implementation", **kwargs
        )

    def test_preexisting_dangling_output_symlink_rejected_before_effects(self):
        output = self.root / "output.json"
        target = self.root / "outside.json"
        output.symlink_to(target)

        def write_output(dependencies):
            self.calls.append("write")
            output.write_text("{}")
            return StageResult("completed")

        pipeline = self.pipeline(
            [Stage("analysis", run=write_output)],
            outputs={"analysis": (output,)},
        )
        with self.assertRaises(FileExistsError):
            pipeline.run()
        self.assertEqual(self.calls, [])
        self.assertFalse(target.exists())

    def test_contracts_are_frozen_and_states_are_terminal(self):
        stage = Stage("synthetic", run=self.callback("synthetic"))
        with self.assertRaises(FrozenInstanceError):
            stage.name = "changed"
        with self.assertRaises(ValueError):
            StageResult("running")
        with self.assertRaises(ValueError):
            StageResult("completed", error="not completed")
        with self.assertRaises(TypeError):
            StageResult("completed", output=object())

    def test_unknown_cycle_and_duplicate_dependencies_have_no_effects(self):
        invalid = (
            [Stage("a", required=("unknown",), run=self.callback("a"))],
            [
                Stage("a", required=("b",), run=self.callback("a")),
                Stage("b", optional=("a",), run=self.callback("b")),
            ],
            [
                Stage("a", run=self.callback("a")),
                Stage("b", required=("a",), optional=("a",), run=self.callback("b")),
            ],
            [Stage("a", run=self.callback("a")), Stage("a", run=self.callback("a"))],
        )
        for stages in invalid:
            with self.subTest(stages=stages), self.assertRaises(ValueError):
                self.pipeline(stages)
            self.assertFalse(self.records.exists())
            self.assertEqual(self.calls, [])

    def test_output_ownership_is_validated_before_effects(self):
        stages = [
            Stage("a", run=self.callback("a")),
            Stage("b", run=self.callback("b")),
        ]
        output = self.root / "synthetic.json"
        for outputs in (
            {"a": (output,), "b": (output.parent / "." / output.name,)},
            {"unknown": (output,)},
            {"a": (self.records / "b.json",)},
        ):
            with self.subTest(outputs=outputs), self.assertRaises(ValueError):
                self.pipeline(stages, outputs=outputs)
        self.assertEqual(self.calls, [])
        self.assertFalse(self.records.exists())

    def test_only_declared_dependencies_are_passed_in_dependency_order(self):
        stages = [
            Stage(
                "render",
                required=("evidence",),
                optional=("analysis",),
                run=self.callback("render"),
            ),
            Stage("unrelated", run=self.callback("unrelated")),
            Stage("analysis", required=("evidence",), run=self.callback("analysis")),
            Stage("evidence", run=self.callback("evidence")),
        ]
        results = self.pipeline(stages).run()
        self.assertEqual(
            [name for name, _ in self.calls],
            ["evidence", "analysis", "render", "unrelated"],
        )
        render = dict(self.calls)["render"]
        self.assertEqual(set(render), {"evidence", "analysis"})
        self.assertEqual(render["analysis"], results["analysis"])

    def test_failure_blocks_required_but_optional_and_independent_continue(self):
        def crash(dependencies):
            raise RuntimeError("synthetic failure")

        results = self.pipeline(
            [
                Stage("observer", run=crash),
                Stage(
                    "assessor", required=("observer",), run=self.callback("assessor")
                ),
                Stage(
                    "render",
                    optional=("observer", "assessor"),
                    run=self.callback("render"),
                ),
                Stage("independent", run=self.callback("independent")),
            ]
        ).run()
        self.assertEqual(results["observer"].state, "failed")
        self.assertIn("synthetic failure", results["observer"].error)
        self.assertEqual(results["assessor"].state, "blocked")
        self.assertEqual(results["render"].state, "completed")
        self.assertEqual(results["independent"].state, "completed")
        self.assertNotIn("assessor", dict(self.calls))
        self.assertEqual(dict(self.calls)["render"]["assessor"].state, "blocked")

    def test_skipped_input_is_terminal_and_blocks_required_consumer(self):
        results = self.pipeline(
            [
                Stage("trials", run=self.callback("trials", "skipped")),
                Stage("analysis", required=("trials",), run=self.callback("analysis")),
                Stage("render", optional=("analysis",), run=self.callback("render")),
            ]
        ).run()
        self.assertEqual(results["analysis"].state, "blocked")
        self.assertEqual(results["render"].state, "completed")

    def test_invalid_handler_return_becomes_failed_result(self):
        results = self.pipeline([Stage("invalid", run=lambda dependencies: None)]).run()
        self.assertEqual(results["invalid"].state, "failed")
        self.assertIn("StageResult", results["invalid"].error)

    def test_records_capture_identity_input_hashes_and_original_output_bytes(self):
        artifact = self.root / "synthetic.txt"

        def save(dependencies):
            artifact.write_bytes(b"synthetic original bytes\n")
            return StageResult("completed", output={"path": str(artifact)})

        self.pipeline(
            [
                Stage("prepare", run=self.callback("prepare")),
                Stage("save", required=("prepare",), run=save),
            ],
            outputs={"save": (artifact,)},
        ).run()
        record = json.loads((self.records / "save.json").read_text())
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["producer"], "synthetic-implementation")
        self.assertEqual(record["stage"], "save")
        prepare_record = json.loads((self.records / "prepare.json").read_text())
        self.assertEqual(
            record["input_hashes"], {"prepare": content_hash(prepare_record)}
        )
        self.assertEqual(
            record["outputs"][0]["sha256"],
            hashlib.sha256(artifact.read_bytes()).hexdigest(),
        )
        self.assertEqual(record["state"], "completed")
        self.assertFalse(list(self.records.glob(".*")))

    def test_existing_output_is_never_overwritten_even_without_record(self):
        artifact = self.root / "synthetic.json"
        artifact.write_text("original")
        pipeline = self.pipeline(
            [Stage("analysis", run=self.callback("analysis"))],
            outputs={"analysis": (artifact,)},
        )
        with self.assertRaises(FileExistsError):
            pipeline.run()
        self.assertEqual(artifact.read_text(), "original")
        self.assertEqual(self.calls, [])
        self.assertFalse(self.records.exists())

    def test_completed_record_refuses_rerun_before_any_callbacks(self):
        pipeline = self.pipeline([Stage("analysis", run=self.callback("analysis"))])
        pipeline.run()
        original = (self.records / "analysis.json").read_bytes()
        with self.assertRaises(FileExistsError):
            pipeline.run()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual((self.records / "analysis.json").read_bytes(), original)

    def test_failed_stage_record_also_refuses_reexecution(self):
        pipeline = self.pipeline(
            [Stage("analysis", run=self.callback("analysis", "failed"))]
        )
        pipeline.run()
        with self.assertRaises(FileExistsError):
            pipeline.run()
        self.assertEqual([name for name, _ in self.calls], ["analysis"])

    def test_failed_stage_with_partial_output_cannot_rerun_over_it(self):
        artifact = self.root / "synthetic-partial.json"

        def fail(dependencies):
            artifact.write_text("retained synthetic partial output")
            return StageResult("failed", error="synthetic failure")

        pipeline = self.pipeline(
            [Stage("analysis", run=fail)], outputs={"analysis": (artifact,)}
        )
        pipeline.run()
        with self.assertRaises(FileExistsError):
            pipeline.run()
        self.assertEqual(artifact.read_text(), "retained synthetic partial output")

    def test_completed_stage_requires_declared_regular_files(self):
        for invalid_kind in ("missing", "directory", "symlink"):
            with self.subTest(invalid_kind=invalid_kind):
                artifact = self.root / f"synthetic-{invalid_kind}"
                records = self.root / invalid_kind

                def invalid_output(dependencies):
                    if invalid_kind == "directory":
                        artifact.mkdir()
                    elif invalid_kind == "symlink":
                        artifact.symlink_to(self.root / "absent")
                    return StageResult("completed")

                results = Pipeline(
                    [
                        Stage("analysis", run=invalid_output),
                        Stage(
                            "render",
                            optional=("analysis",),
                            run=self.callback("render"),
                        ),
                    ],
                    records,
                    outputs={"analysis": (artifact,)},
                ).run()
                self.assertEqual(results["analysis"].state, "failed")
                self.assertEqual(results["render"].state, "completed")
                record = json.loads((records / "analysis.json").read_text())
                self.assertEqual(record["state"], "failed")

    def test_second_writer_cannot_execute_stage_or_change_record(self):
        self.records.mkdir()
        writer = self.records / ".analysis.writer"
        writer.write_text("synthetic active writer")
        pipeline = self.pipeline([Stage("analysis", run=self.callback("analysis"))])
        with self.assertRaises(FileExistsError):
            pipeline.run()
        self.assertEqual(self.calls, [])
        self.assertEqual(writer.read_text(), "synthetic active writer")
        self.assertFalse((self.records / "analysis.json").exists())


if __name__ == "__main__":
    unittest.main()
