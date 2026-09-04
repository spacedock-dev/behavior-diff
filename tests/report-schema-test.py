#!/usr/bin/env python3
import copy
import json
import sys
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


def main():
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

def assert_file_round_trip(path):
    """Validate any renderer-produced report without fixture assumptions."""
    raw = json.loads(Path(path).read_text())
    report = ReportData.from_dict(raw)
    assert report.to_dict() == raw
    assert json.loads(report.to_json()) == raw


if len(sys.argv) == 2:
    assert_file_round_trip(sys.argv[1])


if __name__ == "__main__":
    main()
