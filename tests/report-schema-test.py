#!/usr/bin/env python3
import contextlib
import copy
import importlib.util
import io
import json
import os
import sys
import tempfile
from pathlib import Path

scripts = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(scripts))

from reporting.schema import (  # noqa: E402
    CommandFlowData,
    DecisionChoiceData,
    DecisionRowData,
    FlowPathData,
    ReportData,
    TrialData,
)


def synthetic_raw():
    return {
        "schema_version": 1,
        "metadata": {
            "model": "synthetic/model",
            "mode": "review",
            "vocab": "generic",
            "trace_source": "captured",
            "target_file": "AGENTS.md",
            "before_label": "current file",
            "after_label": "your change applied",
        },
        "content": {
            "title": "Synthetic report",
            "subtitle": "Synthetic subtitle.",
            "observation": "Synthetic observation.",
            "scenario_heading": "Scenario",
            "scenario": "Compare two synthetic files.",
            "expected_heading": "Expected behavior",
            "expected": "Test the changed behavior.",
            "diff_heading": "Diff of AGENTS.md — the only difference between the variants",
            "decision_heading": "Decision diff — top divergences",
            "decision_blurb": "Synthetic decision explanation.",
            "flow_heading": "Flow diff — where the variants diverge",
            "result_heading": "Result",
            "boundary": "Synthetic evidence only.",
        },
        "rule_diff": "--- before\n+++ after\n",
        "result": {"text": "No automatic verdict", "kind": "neutral"},
        "variants": {
            "before": {
                "label": "Before",
                "note": "current file",
                "passed": 0,
                "blocked": 0,
                "valid": 2,
                "total": 2,
                "count_text": "2 valid trials",
                "count_suffix": "",
                "count_emphasized": False,
                "trials": [
                    {
                        "name": "before-1",
                        "verdict": "REVIEW",
                        "actions": "-",
                        "commands": ["read AGENTS.md"],
                        "final": "Before first answer",
                        "outcome": None,
                    },
                    {
                        "name": "before-2",
                        "verdict": "REVIEW",
                        "actions": "-",
                        "commands": ["search AGENTS.md"],
                        "final": "Before second answer",
                        "outcome": "Reviewed file",
                    },
                ],
            },
            "after": {
                "label": "After",
                "note": "your change applied",
                "passed": 1,
                "blocked": 0,
                "valid": 2,
                "total": 2,
                "count_text": "1 of 2 valid trials passed",
                "count_suffix": " (blocked: 0)",
                "count_emphasized": True,
                "trials": [
                    {
                        "name": "after-1",
                        "verdict": "PASS",
                        "actions": "-",
                        "commands": ["read AGENTS.md", "run tests"],
                        "final": "After first answer",
                        "outcome": "Tested behavior",
                    },
                    {
                        "name": "after-2",
                        "verdict": "REVIEW",
                        "actions": "-",
                        "commands": ["search AGENTS.md"],
                        "final": "After second answer",
                        "outcome": None,
                    },
                ],
            },
        },
        "command_flow": {
            "enabled": True,
            "same": False,
            "shared": ["Read files", "Compare output"],
            "before": {
                "prefix": ["Review result"],
                "paths": [
                    {"steps": ["Stop"], "count": 1},
                    {"steps": ["Explain"], "count": 1},
                ],
                "total": 2,
            },
            "after": {
                "prefix": ["Run tests"],
                "paths": [{"steps": ["Explain"], "count": 2}],
                "total": 2,
            },
        },
        "decisions": {
            "rows": [
                {
                    "decision": "Use evidence",
                    "topic": "Evidence",
                    "anchor": 2,
                    "diverges": True,
                    "note": "Synthetic divergence.",
                    "before": [
                        {"choice": "read only", "count": 2},
                        {"choice": "search", "count": 1},
                    ],
                    "after": [{"choice": "read and test", "count": 2}],
                },
                {
                    "decision": "State result",
                    "topic": "Delivery",
                    "anchor": "final answer",
                    "diverges": False,
                    "note": "",
                    "before": [{"choice": "explain", "count": 2}],
                    "after": [{"choice": "explain", "count": 2}],
                },
            ],
            "fork": 1,
            "fork_note": "Synthetic fork.",
            "dropped": 0,
            "extractor": "synthetic extractor",
            "before_count": 2,
            "after_count": 2,
        },
    }


def assert_round_trip(raw):
    report = ReportData.from_dict(raw)
    assert report.schema_version == 1
    assert report.to_dict() == raw
    assert report.to_json() == json.dumps(raw, indent=2, sort_keys=True) + "\n"
    return report


def assert_rejected(raw, message):
    try:
        ReportData.from_dict(raw)
    except ValueError as error:
        assert str(error) == message
    else:
        raise AssertionError("invalid report data was accepted")


def assert_render_import_safe():
    render_path = scripts / "render.py"
    original_cwd = Path.cwd()
    original_argv = sys.argv
    stdout = io.StringIO()
    stderr = io.StringIO()
    module_name = "_behavior_diff_render_import_test"

    try:
        with tempfile.TemporaryDirectory() as directory:
            os.chdir(directory)
            sys.argv = [str(render_path)]
            spec = importlib.util.spec_from_file_location(module_name, render_path)
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                spec.loader.exec_module(module)
            assert list(Path(".").iterdir()) == []
            assert stdout.getvalue() == ""
            assert stderr.getvalue() == ""
            assert callable(module.main)
    finally:
        sys.modules.pop(module_name, None)
        sys.argv = original_argv
        os.chdir(original_cwd)


def main():
    assert_render_import_safe()
    raw = synthetic_raw()
    report = assert_round_trip(raw)
    assert isinstance(report.variants.before.trials[0], TrialData)
    assert isinstance(report.command_flow, CommandFlowData)
    assert isinstance(report.command_flow.before.paths[0], FlowPathData)
    assert isinstance(report.decisions.rows[0], DecisionRowData)
    assert isinstance(report.decisions.rows[0].before[0], DecisionChoiceData)
    assert [trial.name for trial in report.variants.before.trials] == [
        "before-1",
        "before-2",
    ]
    assert [path.steps for path in report.command_flow.before.paths] == [
        ("Stop",),
        ("Explain",),
    ]
    assert [row.anchor for row in report.decisions.rows] == [2, "final answer"]
    assert [choice.choice for choice in report.decisions.rows[0].before] == [
        "read only",
        "search",
    ]

    assert_rejected(
        dict(raw, schema_version=2),
        "unsupported report-data schema version: 2",
    )
    assert_rejected(
        dict(raw, schema_version=True),
        "invalid report-data field schema_version: expected integer",
    )
    assert_rejected(
        dict(raw, schema_version=1.0),
        "invalid report-data field schema_version: expected integer",
    )

    invalid_commands = copy.deepcopy(raw)
    invalid_commands["variants"]["before"]["trials"][0]["commands"] = "read AGENTS.md"
    assert_rejected(
        invalid_commands,
        "invalid report-data field variants.before.trials[0].commands: expected list",
    )
    invalid_model = copy.deepcopy(raw)
    invalid_model["metadata"]["model"] = ["synthetic/model"]
    assert_rejected(
        invalid_model,
        "invalid report-data field metadata.model: expected string",
    )
    invalid_count = copy.deepcopy(raw)
    invalid_count["command_flow"]["before"]["paths"][0]["count"] = True
    assert_rejected(
        invalid_count,
        "invalid report-data field command_flow.before.paths[0].count: expected integer",
    )
    invalid_suffix = copy.deepcopy(raw)
    invalid_suffix["variants"]["after"]["count_suffix"] = True
    assert_rejected(
        invalid_suffix,
        "invalid report-data field variants.after.count_suffix: expected string",
    )

    from reporting.render_html import _resolve_css, render_artifact, render_document

    assert _resolve_css(".result { background:__RESULT_BG__; }", "good") == (
        ".result { background:var(--pass); }"
    )
    assert _resolve_css(".result { background:__RESULT_BG__; }", "bad") == (
        ".result { background:var(--fail); }"
    )
    assert _resolve_css(".result { background:__RESULT_BG__; }", "neutral") == (
        ".result { background:var(--accent); }"
    )
    for css in (".result {}", "__RESULT_BG__ __RESULT_BG__"):
        try:
            _resolve_css(css, "good")
        except ValueError as error:
            assert str(error) == "report.css must contain __RESULT_BG__ exactly once"
        else:
            raise AssertionError("invalid CSS token count was accepted")

    artifact = render_artifact(report, ".result { background:__RESULT_BG__; }")
    assert artifact == render_artifact(report, ".result { background:__RESULT_BG__; }")
    document = render_document(artifact)
    assert document == render_document(artifact)
    escaping_raw = copy.deepcopy(raw)
    escaping_raw["variants"]["before"]["trials"][0]["verdict"] = 'REVIEW"><script>&'
    escaping_artifact = render_artifact(
        ReportData.from_dict(escaping_raw),
        ".result { background:__RESULT_BG__; }",
    )
    assert "<script>" not in escaping_artifact
    assert 'class="badge review&quot;&gt;&lt;script&gt;&amp;"' in escaping_artifact
    assert "REVIEW&quot;&gt;&lt;script&gt;&amp;</span>" in escaping_artifact

    if len(sys.argv) == 2:
        assert_file_round_trip(sys.argv[1])


def assert_file_round_trip(path):
    """Validate any renderer-produced report without fixture assumptions."""
    raw = json.loads(Path(path).read_text())
    report = ReportData.from_dict(raw)
    assert report.to_dict() == raw
    assert json.loads(report.to_json()) == raw

    from reporting.render_html import render_artifact, render_document
    from reporting.render_markdown import render_markdown

    markdown_path = Path(path).with_name("report.md")
    artifact_path = Path(path).with_name("report-artifact.html")
    document_path = Path(path).with_name("report.html")
    css = (scripts / "reporting/report.css").read_text()
    assert render_markdown(report) == markdown_path.read_text()
    artifact = render_artifact(report, css)
    assert artifact == artifact_path.read_text()
    assert render_document(artifact) == document_path.read_text()


if __name__ == "__main__":
    main()
