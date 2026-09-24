#!/usr/bin/env python3
import contextlib
import copy
import importlib.util
import io
import json
import os
import sys
import tempfile
from dataclasses import replace
from html.parser import HTMLParser
from pathlib import Path

scripts = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(scripts))

from reporting import content  # noqa: E402
from reporting.schema import (  # noqa: E402
    CommandFlowData,
    DecisionChoiceData,
    DecisionRowData,
    FlowPathData,
    ReportData,
    TrialData,
)
from report_fixtures import SCENARIOS, build_reports  # noqa: E402


def synthetic_raw():
    return {
        "schema_version": 3,
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
            "subtitle": "before: current file · after: your change applied",
            "meta": [["before", "current file"], ["after", "your change applied"]],
            "note": "",
            "limits_heading": "Evidence limits",
            "scenario_heading": "Scenario",
            "scenario": "Compare two synthetic files.",
            "expected_heading": "Expected behavior",
            "expected": "Test the changed behavior.",
            "diff_heading": "Diff of AGENTS.md",
            "decision_heading": "Decision diff: what each side chose to do",
            "decision_blurb": "Synthetic decision explanation.",
            "tag_legend": [
                ["root", "first difference", "where before and after split"]
            ],
            "flow_heading": "Flow diff: what kinds of commands each side ran",
            "flow_purpose": "Synthetic flow explanation.",
            "result_heading": "Result",
            "boundary": "Synthetic evidence only.",
        },
        "rule_diff": "--- before\n+++ after\n",
        "result": {
            "text": "Same result, different process",
            "kind": "neutral",
            "summary": "The reported result stayed the same.",
            "outcome_heading": "Final result — unchanged",
            "behavior_heading": "Behavior — changed",
            "outcomes": [2],
            "behavior": [1],
            "implications": [
                {"text": "The evidence method changed.", "decisions": [1, 2]}
            ],
            "limits": ["Synthetic evidence only."],
        },
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
            "kinds": ["Inspect git history and status", "Read files"],
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
                        {"choice": "read only", "count": 1},
                        {"choice": "search", "count": 1},
                    ],
                    "after": [{"choice": "read and test", "count": 2}],
                },
                {
                    "decision": "State result",
                    "topic": "Delivery",
                    "anchor": "answer",
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
            "outcome": 2,
            "implications": [
                {"text": "The evidence method changed.", "decisions": [1, 2]}
            ],
        },
    }


def assert_round_trip(raw):
    report = ReportData.from_dict(raw)
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


def assert_summary_evidence(report):
    """Incomplete evidence takes precedence over an apparent result change."""

    def summarize(variants=report.variants, decisions=report.decisions):
        return content.result_data(report.metadata, variants, decisions, None)

    complete = summarize()
    assert complete.outcomes == (2,)
    assert complete.behavior == (1,)
    assert complete.outcome_heading.endswith("— unchanged")
    assert complete.behavior_heading.endswith("— changed")
    for after in (
        replace(report.variants.after, valid=1, blocked=1),
        replace(report.variants.after, valid=0, blocked=2),
        replace(
            report.variants.after,
            trials=(
                replace(report.variants.after.trials[0], final=""),
                report.variants.after.trials[1],
            ),
        ),
    ):
        result = summarize(replace(report.variants, after=after))
        assert result.outcome_heading.endswith("— unavailable"), result
        assert result.behavior_heading.endswith("— unavailable"), result
        assert result.limits[0] in result.summary
        assert result.kind == "neutral"
    for decisions in (
        replace(report.decisions, after_count=3),
        replace(report.decisions, dropped=1),
        replace(report.decisions, rows=(), outcome=None, implications=()),
    ):
        result = summarize(decisions=decisions)
        assert result.outcome_heading.endswith("— unavailable"), result
        assert result.limits[0] in result.summary
    blank_result = replace(
        report.decisions.rows[1], after=(DecisionChoiceData(" ", 2),)
    )
    blank = summarize(
        decisions=replace(
            report.decisions, rows=(report.decisions.rows[0], blank_result)
        )
    )
    assert blank.outcome_heading.endswith("— unavailable")
    assert blank.behavior_heading.endswith("— changed")
    mixed_row = replace(
        report.decisions.rows[1],
        after=(DecisionChoiceData("explain", 1), DecisionChoiceData("withhold", 1)),
    )
    mixed = summarize(
        decisions=replace(report.decisions, rows=(report.decisions.rows[0], mixed_row))
    )
    assert mixed.outcome_heading == "Final result — varies", mixed
    unselected = summarize(
        decisions=replace(
            report.decisions, rows=(report.decisions.rows[0], mixed_row), outcome=None
        )
    )
    assert unselected.outcome_heading == "Reported answers — varies"
    assert unselected.outcomes == (2,)
    assert content.choices_changed(
        (DecisionChoiceData("PASS", 2),), (DecisionChoiceData("pass", 2),)
    ), "Case-sensitive result labels must not be merged."
    assert not content.choices_changed(
        (DecisionChoiceData("A", 1), DecisionChoiceData("B", 1)),
        (DecisionChoiceData("B", 2), DecisionChoiceData("A", 2)),
    ), "Proportional distributions must not change when trial totals differ."


def assert_summary_boundaries(report):
    """Answer details never become action rows or establish a primary result."""
    action, outcome = report.decisions.rows
    unchanged_action = replace(
        action,
        before=(DecisionChoiceData("read", 2),),
        after=(DecisionChoiceData("read", 2),),
        diverges=False,
    )
    answer_detail = replace(
        outcome,
        decision="How did the agent describe its work?",
        topic="Process details",
        before=(DecisionChoiceData("concise", 2),),
        after=(DecisionChoiceData("expanded", 2),),
        diverges=True,
    )

    def summarize(rows, primary=2, variants=report.variants, **changes):
        decisions = replace(report.decisions, rows=rows, outcome=primary, **changes)
        return content.result_data(report.metadata, variants, decisions, None)

    answer_change = summarize((unchanged_action, outcome, answer_detail), fork=3)
    unchanged = summarize((unchanged_action, outcome))
    assert answer_change.behavior == (1,), "Answer details entered the action table."
    assert answer_change.behavior_heading.endswith("— unchanged")
    assert answer_change.outcome_heading.endswith("— unchanged")
    assert answer_change.text != unchanged.text, (
        "Answer-detail differences disappeared."
    )
    assert (
        answer_change.text
        != content.result_data(
            report.metadata, report.variants, report.decisions, None
        ).text
    ), "Answer-detail changes implied an observed action change."
    actions_only = summarize((unchanged_action,), primary=None, implications=())
    assert actions_only.outcomes == (), "A topic label invented a primary result."
    assert actions_only.outcome_heading == "Reported answers — unavailable"
    assert actions_only.behavior == (1,)
    no_actions = summarize((outcome, answer_detail), primary=1, fork=2)
    assert no_actions.behavior == ()
    assert no_actions.behavior_heading.endswith("— unavailable")
    assert no_actions.text != unchanged.text
    no_primary = summarize((action, outcome, answer_detail), primary=None)
    assert no_primary.outcomes == (2, 3)
    assert no_primary.behavior == (1,)
    assert no_primary.outcome_heading == "Reported answers — changed"
    # A selected result can have an action anchor, but cannot appear twice.
    selected_action = summarize((action, outcome), primary=1)
    assert selected_action.outcomes == (1,)
    assert selected_action.behavior == ()
    prioritized = summarize((unchanged_action, outcome, action, answer_detail))
    assert prioritized.behavior == (3,), "Unchanged actions obscured changed actions."
    varied_action = replace(action, after=action.before, diverges=False)
    varied = summarize((varied_action, outcome))
    assert varied.behavior_heading.endswith("— varies")
    changed_result = replace(outcome, after=(DecisionChoiceData("withhold", 2),))
    changed = summarize((unchanged_action, changed_result))
    assert changed.outcome_heading == "Final result — changed"
    assert "explain" in changed.text and "withhold" in changed.text
    assert changed.kind == "neutral"
    # Unequal totals with equal proportions do not imply a change.
    after = report.variants.after
    extra_trials = tuple(
        replace(after.trials[0], name="after-" + str(index)) for index in range(1, 5)
    )
    uneven = summarize(
        (
            replace(unchanged_action, after=(DecisionChoiceData("read", 4),)),
            replace(outcome, after=(DecisionChoiceData("explain", 4),)),
        ),
        variants=replace(
            report.variants, after=replace(after, total=4, valid=4, trials=extra_trials)
        ),
        after_count=4,
    )
    assert uneven.outcome_heading.endswith("— unchanged")
    assert uneven.behavior_heading.endswith("— unchanged")


def assert_evidence_links(report):
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown

    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids = set()
            self.targets = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if "id" in attrs:
                assert attrs["id"] not in self.ids, "Duplicate evidence anchor"
                self.ids.add(attrs["id"])
            if tag == "a" and attrs.get("href", "").startswith("#"):
                self.targets.append(attrs["href"][1:])

    page = render_artifact(report, ".result { background:__RESULT_BG__; }")
    links = Links()
    links.feed(page)
    assert set(links.targets) <= links.ids, "An evidence link has no target."
    markdown = render_markdown(report)
    for index in report.result.outcomes + report.result.behavior:
        target = f"decision-{index}"
        assert target in links.targets, "A comparison does not link to its evidence."
        assert f"](#{target})" in markdown
        assert f'id="{target}"' in markdown


def assert_no_invented_causality():
    from reporting.load import load_report

    with tempfile.TemporaryDirectory() as directory:
        run = Path(directory)
        (run / "task.md").write_text("Compare the synthetic outputs.")
        (run / "grades.tsv").write_text("before-1\tREVIEW\t-\nafter-1\tREVIEW\t-\n")
        (run / "config.json").write_text('{"mode":"review","vocab":"generic"}')
        for side in ("before", "after"):
            (run / (side + "-1")).mkdir()
            (run / (side + "-1") / "trace.jsonl").write_text(
                json.dumps({"type": "result", "result": side + " synthetic answer"})
            )
        chain = [
            {
                "decision": question,
                "anchor": anchor,
                "before": [{"choice": "before", "n": 1}],
                "after": [{"choice": "after", "n": 1}],
                "diverges": True,
            }
            for question, anchor in (
                ("Which method?", 1),
                ("Which outcome?", "answer"),
            )
        ]
        (run / "decisions.json").write_text(
            json.dumps({"chain": chain, "fork": None, "outcome": 2})
        )
        report = load_report(run, run, "synthetic/model", run / "config.json")
        assert report.decisions.fork is None, "The loader invented a causal fork."


def assert_gallery_reports():
    """Exercise the same authored cases used by the local gallery through the CLI."""
    expected = {
        "same-result": ("unchanged", "changed"),
        "changed-result": ("changed", "changed"),
        "unchanged": ("unchanged", "unchanged"),
        "answer-details": ("unchanged", "unchanged"),
        "mixed": ("varies", "changed"),
        "missing-primary": ("changed", "changed"),
        "blocked": ("unavailable", "unavailable"),
        "missing-extraction": ("unavailable", "unavailable"),
        "self-reported": ("changed", "changed"),
    }
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        build_reports(root)
        assert {scenario.name for scenario in SCENARIOS} == set(expected)
        reports = {}
        for name, (result_state, action_state) in expected.items():
            report = assert_file_round_trip(root / name / "report-data.json")
            reports[name] = report
            assert report.result.outcome_heading.endswith("— " + result_state), name
            assert report.result.behavior_heading.endswith("— " + action_state), name
            assert report.result.kind == "neutral", (
                "A demo inferred automatic correctness."
            )
            assert_evidence_links(report)
            for variant in (report.variants.before, report.variants.after):
                assert variant.total == len(variant.trials) == 3, name
                assert all(trial.final.strip() for trial in variant.trials), name
                for row in report.decisions.rows:
                    choices = (
                        row.before if variant is report.variants.before else row.after
                    )
                    assert sum(choice.count for choice in choices) == len(
                        variant.trials
                    ), name
            assert all(
                type(report.decisions.rows[index - 1].anchor) is int
                and index != report.decisions.outcome
                for index in report.result.behavior
            ), "An answer detail appeared as an action change."

        answer_details = reports["answer-details"]
        assert any(
            row.anchor == "answer"
            and index != answer_details.decisions.outcome
            and row.before != row.after
            for index, row in enumerate(answer_details.decisions.rows, 1)
        ), "The answer-only case no longer exercises an answer change."
        missing_primary = reports["missing-primary"]
        assert missing_primary.decisions.outcome is None
        assert missing_primary.result.outcomes
        assert missing_primary.result.outcome_heading.startswith("Reported answers")
        blocked = reports["blocked"]
        assert blocked.variants.after.valid == 2
        assert blocked.variants.after.blocked == 1
        missing_extraction = reports["missing-extraction"]
        assert missing_extraction.decisions.rows == ()
        assert all(
            trial.commands and trial.final
            for variant in (
                missing_extraction.variants.before,
                missing_extraction.variants.after,
            )
            for trial in variant.trials
        ), "Missing extraction removed raw evidence."
        self_reported = reports["self-reported"]
        assert self_reported.metadata.trace_source == "self-reported"
        assert not self_reported.command_flow.enabled
        assert self_reported.command_flow.shared == ()
        for branch in (
            self_reported.command_flow.before,
            self_reported.command_flow.after,
        ):
            assert branch.prefix == branch.paths == ()

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        sentinel = root / "keep.txt"
        sentinel.write_text("Existing user content.")
        try:
            build_reports(root)
        except (ValueError, FileExistsError):
            pass
        else:
            raise AssertionError("The gallery wrote into an occupied output directory.")
        assert sentinel.read_text() == "Existing user content."
        assert list(root.iterdir()) == [sentinel], "Refusal left partial gallery files."


def main():
    assert_render_import_safe()
    raw = synthetic_raw()
    report = assert_round_trip(raw)
    assert_summary_evidence(report)
    assert_summary_boundaries(report)
    assert_evidence_links(report)
    assert_no_invented_causality()
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
    assert [row.anchor for row in report.decisions.rows] == [2, "answer"]
    assert [choice.choice for choice in report.decisions.rows[0].before] == [
        "read only",
        "search",
    ]

    assert_rejected(
        dict(raw, schema_version=1),
        "unsupported report-data schema version: 1",
    )
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
    invalid_result_kind = copy.deepcopy(raw)
    invalid_result_kind["result"]["kind"] = "future"
    assert_rejected(
        invalid_result_kind,
        "invalid report-data field result.kind: expected one of good, bad, neutral",
    )
    invalid_result_kind_type = copy.deepcopy(raw)
    invalid_result_kind_type["result"]["kind"] = None
    assert_rejected(
        invalid_result_kind_type,
        "invalid report-data field result.kind: expected string",
    )
    for heading in ("outcome_heading", "behavior_heading"):
        missing_heading = copy.deepcopy(raw)
        del missing_heading["result"][heading]
        assert_rejected(
            missing_heading,
            "invalid report-data field result." + heading + ": expected present field",
        )
        invalid_heading = copy.deepcopy(raw)
        invalid_heading["result"][heading] = None
        assert_rejected(
            invalid_heading,
            "invalid report-data field result." + heading + ": expected string",
        )
    invalid_evidence = copy.deepcopy(raw)
    invalid_evidence["result"]["implications"][0]["decisions"] = [99]
    assert_rejected(
        invalid_evidence,
        "invalid report-data field result.implications[0].decisions[0]: "
        "expected 1-based decision row index",
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
    try:
        _resolve_css(".result { background:__RESULT_BG__; }", "future")
    except ValueError as error:
        assert str(error) == "unsupported report result kind: future"
    else:
        raise AssertionError("unsupported report result kind was accepted")
    try:
        _resolve_css(".result {}", "future")
    except ValueError as error:
        assert str(error) == "report.css must contain __RESULT_BG__ exactly once"
    else:
        raise AssertionError("CSS token validation lost precedence")
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
    unsafe_summary = copy.deepcopy(raw)
    payload = '<script>alert("x")</script>|[link](javascript:alert(1))'
    unsafe_summary["result"]["text"] = payload
    unsafe_summary["result"]["implications"][0]["text"] = payload
    unsafe_summary["decisions"]["rows"][1]["after"][0]["choice"] = payload
    unsafe_report = ReportData.from_dict(unsafe_summary)
    from reporting.render_markdown import render_markdown

    for rendered in (
        render_artifact(unsafe_report, ".result { background:__RESULT_BG__; }"),
        render_markdown(unsafe_report),
    ):
        assert "<script>" not in rendered
    assert "](javascript:" not in render_markdown(unsafe_report)

    if len(sys.argv) == 2:
        assert_file_round_trip(sys.argv[1])
    else:
        assert_gallery_reports()


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
    return report


if __name__ == "__main__":
    main()
