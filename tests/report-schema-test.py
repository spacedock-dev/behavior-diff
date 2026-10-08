#!/usr/bin/env python3
import contextlib
import copy
import importlib.util
import html
import io
import json
import os
import re
import sys
import tempfile
from dataclasses import asdict, replace
from html.parser import HTMLParser
from pathlib import Path

scripts = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(scripts))

from reporting import content  # noqa: E402
from reporting.schema import (  # noqa: E402
    CommandFlowData,
    DecisionChoiceData,
    DecisionRowData,
    FlowBranchData,
    FlowPathData,
    ReportData,
    TrialData,
)
from reporting.trial_summary import (  # noqa: E402
    TrialSummaryData,
    parse_trial_summaries,
    trial_group_names,
)
from report_fixtures import SCENARIOS, build_reports  # noqa: E402
from explanation_contract import assert_change_explanations  # noqa: E402
from attention_contract import assert_attention_reports  # noqa: E402
from target_contract import assert_target_reports  # noqa: E402


def synthetic_raw():
    raw = {
        "schema_version": 12,
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
            "task": "Compare the synthetic files. Report differences without modifying them.",
            "expected_heading": "Expected behavior",
            "expected": "Test the changed behavior.",
            "diff_heading": "Diff of AGENTS.md",
            "decision_heading": "Decision diff: what each side chose to do",
            "decision_blurb": "Synthetic decision explanation.",
            "tag_legend": [
                ["changed", "Changed", "the extracted choice proportions differ"]
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
                    "edit_hunks": [],
                    "before": [
                        {"choice": "read only", "count": 1, "trials": ["before-1"]},
                        {"choice": "search", "count": 1, "trials": ["before-2"]},
                    ],
                    "after": [
                        {
                            "choice": "read and test",
                            "count": 2,
                            "trials": ["after-1", "after-2"],
                        }
                    ],
                },
                {
                    "decision": "State result",
                    "topic": "Delivery",
                    "anchor": "answer",
                    "diverges": False,
                    "note": "",
                    "edit_hunks": [],
                    "before": [
                        {
                            "choice": "explain",
                            "count": 2,
                            "trials": ["before-1", "before-2"],
                        }
                    ],
                    "after": [
                        {
                            "choice": "explain",
                            "count": 2,
                            "trials": ["after-1", "after-2"],
                        }
                    ],
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
            "narrative": None,
            "intent": None,
            "explanation": None,
            "attention": None,
            "trial_summaries": [
                {
                    "before_trial": "before-1",
                    "after_trial": "after-1",
                    "takeaway": "The after record adds testing to the file review.",
                    "before": "The before record shows a file read.",
                    "after": "The after record shows a file read and a test command.",
                    "caveat": "The recorded test command alone does not establish success.",
                },
                {
                    "before_trial": "before-2",
                    "after_trial": "after-2",
                    "takeaway": "Both records show the same search activity.",
                    "before": "The before record shows a file search.",
                    "after": "The after record shows a file search.",
                    "caveat": "",
                },
            ],
        },
    }
    raw["decisions"].update(
        purpose=[], recorded_evidence=[], target_assessment=None, evidence_limits=None
    )
    from reporting.schema import _decisions, _metadata, _variants
    from reporting.summary import build_intent, build_summary

    decisions = _decisions(
        raw["decisions"],
        "decisions",
        0,
        final_answers={
            side: {trial["name"]: trial["final"] for trial in variant["trials"]}
            for side, variant in raw["variants"].items()
        },
    )
    raw["summary"] = json.loads(
        json.dumps(
            asdict(
                build_summary(
                    _metadata(raw["metadata"], "metadata"),
                    _variants(raw["variants"], "variants"),
                    decisions,
                )
            )
        )
    )
    raw["intent"] = json.loads(
        json.dumps(
            asdict(
                build_intent(
                    raw["content"]["expected"],
                    decisions,
                )
            )
        )
    )
    return raw


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


def assert_branch_membership_validation(raw):
    """Canonical branch attribution is exact or explicitly unavailable."""
    for side in ("before", "after"):
        malformed = (
            None,
            "not a list",
            [False],
            [""],
            [f"{side}-unknown"],
            [f"{'after' if side == 'before' else 'before'}-1"],
            [f"{side}-1", f"{side}-1"],
            [],
        )
        for members in malformed:
            invalid = copy.deepcopy(raw)
            invalid["decisions"]["rows"][0][side][0]["trials"] = members
            # Emptying a unanimous side is a valid legacy aggregate, not partial attribution.
            if members == [] and len(invalid["decisions"]["rows"][0][side]) == 1:
                continue
            try:
                ReportData.from_dict(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "Invalid canonical branch membership was accepted."
                )
    duplicate = copy.deepcopy(raw)
    duplicate["decisions"]["rows"][0]["before"][1]["trials"] = ["before-1"]
    try:
        ReportData.from_dict(duplicate)
    except ValueError:
        pass
    else:
        raise AssertionError("One trial was attributed to multiple choices.")
    partial = copy.deepcopy(raw)
    del partial["decisions"]["rows"][0]["before"][0]["trials"]
    try:
        ReportData.from_dict(partial)
    except ValueError:
        pass
    else:
        raise AssertionError("Partial canonical branch attribution was accepted.")
    for omit in (False, True):
        legacy = copy.deepcopy(raw)
        for row in legacy["decisions"]["rows"]:
            for side in ("before", "after"):
                for choice in row[side]:
                    if omit:
                        del choice["trials"]
                    else:
                        choice["trials"] = []
        report = ReportData.from_dict(legacy)
        assert all(
            choice.trials == ()
            for row in report.decisions.rows
            for side in ("before", "after")
            for choice in getattr(row, side)
        )


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


def assert_unchanged_scripts(baseline, rendered):
    class Scripts(HTMLParser):
        def __init__(self):
            super().__init__()
            self.scripts = []
            self.parts = None

        def handle_starttag(self, tag, attrs):
            if tag == "script":
                self.parts = []
                self.scripts.append((attrs, self.parts))

        def handle_data(self, text):
            if self.parts is not None:
                self.parts.append(text)

        def handle_endtag(self, tag):
            if tag == "script":
                self.parts = None

    expected = Scripts()
    expected.feed(baseline)
    expected.close()
    actual = Scripts()
    actual.feed(rendered)
    actual.close()
    assert actual.scripts == expected.scripts, (
        "Report evidence added or altered an executable script."
    )


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

    page = render_artifact(report, "")
    links = Links()
    links.feed(page)
    assert set(links.targets) <= links.ids, "An evidence link has no target."
    markdown = render_markdown(report)
    markdown_links = Links()
    markdown_links.feed(markdown)
    markdown_links.targets.extend(re.findall(r"\]\(#([^)]+)\)", markdown))
    assert set(markdown_links.targets) <= markdown_links.ids, (
        "A Markdown evidence link has no target."
    )
    for index in range(1, len(report.decisions.rows) + 1):
        target = f"decision-{index}"
        assert target in links.ids, "A comparison has no stable evidence target."
        assert target in markdown_links.ids
    if report.metadata.trace_source == "captured":
        for side, variant in (
            ("before", report.variants.before),
            ("after", report.variants.after),
        ):
            for trial in variant.trials:
                target = content.trial_anchor(side, trial.name)
                assert target in links.targets and target in links.ids
                assert f"](#{target})" in markdown
                assert f'id="{target}"' in markdown


def assert_guided_report_structure(report):
    """Navigation and paired records retain evidence without inventing pairing."""
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown

    diff = (
        "--- a/WORKFLOW.md\n+++ b/WORKFLOW.md\n"
        "@@ -20,2 +20,2 @@ Questions\n-old questions\n+new questions\n context\n"
        "@@ -26 +26 @@ Transition\n-old gate\n+new gate\n"
    )
    labels = [content.instruction_hunk_label(diff, number) for number in (1, 2)]
    assert labels[0] != labels[1], "Neighboring edit blocks need distinct locations."
    assert "Questions" in labels[0] and "Transition" in labels[1]
    assert "20" in labels[0] and "21" in labels[0] and "26" in labels[1]
    raw_lines = tuple(content.instruction_diff_lines(diff))
    assert tuple(line for line, _ in raw_lines) == tuple(diff.splitlines())
    assert tuple(number for _, number in raw_lines if number) == (1, 2)

    class Evidence(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_trials = False
            self.details = 0
            self.pre = None
            self.visible_answers = []
            self.ids = []
            self.primary_targets = []
            self.missing_cells = 0

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            anchor = attrs.get("id", "")
            if anchor:
                self.ids.append(anchor)
            if anchor == "panel-trials":
                self.in_trials = True
            if tag == "details":
                self.details += 1
            if tag == "pre" and self.in_trials and self.details == 0:
                self.pre = []
            if (
                tag == "a"
                and "summary-evidence-button" in attrs.get("class", "").split()
            ):
                self.primary_targets.append(attrs["href"])
            if "trial-missing" in attrs.get("class", "").split():
                self.missing_cells += 1

        def handle_data(self, text):
            if self.pre is not None:
                self.pre.append(text)

        def handle_endtag(self, tag):
            if tag == "pre" and self.pre is not None:
                self.visible_answers.append("".join(self.pre))
                self.pre = None
            if tag == "details":
                self.details -= 1

    first = replace(
        report.variants.before.trials[0],
        final="Before evidence | workflow feedback run 1",
        commands=("printf 'before|one'\nprintf 'before-two'",),
    )
    second = replace(
        report.variants.after.trials[0],
        final="After evidence | workflow feedback run 1",
        verdict="BLOCKED",
        commands=(),
    )
    missing = replace(second, name="after-missing", final="")
    specimen = replace(
        report,
        variants=replace(
            report.variants,
            before=replace(report.variants.before, trials=(first,), total=1, valid=1),
            after=replace(
                report.variants.after,
                trials=(second, missing),
                total=2,
                valid=1,
                blocked=1,
            ),
        ),
    )
    assert_evidence_links(specimen)
    for rendered, is_html in (
        (render_artifact(specimen, ""), True),
        (render_markdown(specimen), False),
    ):
        evidence = Evidence()
        evidence.feed(rendered)
        for panel in (
            "summary",
            "explanation",
            "instruction",
            "decision",
            "flow",
            "trials",
        ):
            assert f"panel-{panel}" in evidence.ids
        assert [
            anchor
            for anchor in evidence.ids
            if re.fullmatch(r"trial-group-\d+", anchor)
        ] == [content.trial_group_anchor(1), content.trial_group_anchor(2)], (
            "Unequal sides lost a shared trial group."
        )
        before_anchor = content.trial_anchor("before", first.name)
        after_anchor = content.trial_anchor("after", second.name)
        assert evidence.ids.index(before_anchor) < evidence.ids.index(after_anchor)
        assert first.final in evidence.visible_answers
        assert second.final in evidence.visible_answers
        assert content.NO_FINAL_ANSWER in rendered
        assert "BLOCKED" in rendered
        assert evidence.missing_cells, (
            "An unequal side needs an explicit missing-record cell."
        )
        assert "workflow feedback run 1" in rendered, (
            "Domain run terminology was rewritten."
        )
        if is_html:
            assert evidence.primary_targets == ["#panel-explanation"], (
                "The Summary must open the dedicated explanation."
            )

    # Independently retained records remain navigable without an extraction.
    unavailable = replace(
        report,
        decisions=replace(report.decisions, rows=(), outcome=None, narrative=None),
    )
    from reporting.summary import build_summary

    unavailable = replace(
        unavailable,
        summary=build_summary(
            unavailable.metadata, unavailable.variants, unavailable.decisions
        ),
    )
    assert_evidence_links(unavailable)
    assert unavailable.summary.status == "unavailable"
    assert unavailable.summary.before.choices == unavailable.summary.after.choices == ()
    assert unavailable.summary.why is None and unavailable.summary.caution is None
    for render in (lambda value: render_artifact(value, ""), render_markdown):
        rendered = render(unavailable)
        for variant in (report.variants.before, report.variants.after):
            for trial in variant.trials:
                assert html.escape(trial.final) in rendered


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


def assert_tab_comparison_boundaries(report):
    """Different row roles and incomplete evidence must not imply causal links."""
    action, result = report.decisions.rows
    detail = replace(result, topic="Answer wording")
    assert content.decision_role(1, action, 2) == "Action"
    assert content.decision_role(2, result, 2) == "Final result"
    assert content.decision_role(3, detail, 2) == "Answer detail"
    assert content.decision_role(1, action, 1) == "Final result"
    assert (
        content.decision_role(1, replace(action, anchor="unknown"), None)
        == "Comparison"
    )
    # Status follows proportions, not a stale extractor flag or absolute totals.
    assert content.decision_status(replace(action, diverges=False)) == "Changed"
    assert (
        content.decision_status(
            replace(result, after=(DecisionChoiceData("explain", 4),), diverges=True)
        )
        == "Unchanged"
    )
    assert content.decision_status(replace(result, after=())) == "Unavailable"
    assert (
        content.decision_status(replace(result, after=(DecisionChoiceData(" ", 2),)))
        == "Unavailable"
    )

    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown

    independent = replace(
        report,
        decisions=replace(
            report.decisions,
            rows=(action, replace(result, after=(DecisionChoiceData("hold", 2),))),
            fork_note="",
            implications=(),
        ),
        result=replace(report.result, implications=()),
    )
    for rendered in (
        render_artifact(independent, ""),
        render_markdown(independent),
    ):
        assert "possible link" not in rendered.lower(), (
            "A later difference acquired a causal label without an explanation."
        )


def assert_flow_pattern_boundaries():
    """Expand compressed groups without losing empty suffixes or counting grades."""
    flow = CommandFlowData(
        enabled=True,
        same=False,
        kinds=("Read files", "Run tests"),
        shared=("Read files",),
        before=FlowBranchData(
            prefix=(),
            paths=(FlowPathData((), 1), FlowPathData(("Run tests", "PASS"), 1)),
            total=2,
        ),
        after=FlowBranchData(
            prefix=(),
            paths=(
                FlowPathData((), 2),
                FlowPathData(("Run tests", "FAIL"), 1),
                FlowPathData(("Run tests", "PASS"), 1),
            ),
            total=4,
        ),
    )
    patterns = content.flow_patterns(flow)
    assert patterns == ((("Read files",), 1, 2), (("Read files", "Run tests"), 1, 2))
    assert content.flow_overview(flow, patterns).endswith("— unchanged")
    changed = replace(flow, after=FlowBranchData(("Run tests", "PASS"), (), 4))
    assert content.flow_patterns(changed) == (
        (("Read files",), 1, 0),
        (("Read files", "Run tests"), 1, 4),
    )
    assert content.flow_overview(changed, content.flow_patterns(changed)).endswith(
        "— changed"
    )
    absent = replace(flow, after=FlowBranchData((), (), 0))
    assert content.flow_patterns(absent) == (
        (("Read files",), 1, 0),
        (("Read files", "Run tests"), 1, 0),
    )
    assert content.flow_overview(absent, content.flow_patterns(absent)).endswith(
        "— unavailable"
    )
    uncategorized = replace(
        flow,
        shared=(),
        before=FlowBranchData((), (), 2),
        after=FlowBranchData((), (), 4),
    )
    assert content.flow_patterns(uncategorized) == (((), 2, 4),)
    assert content.flow_overview(
        uncategorized, content.flow_patterns(uncategorized)
    ).endswith("— unavailable"), (
        "No categorized evidence became an unchanged-process claim."
    )
    assert content.flow_patterns(replace(flow, enabled=False)) == ()


def assert_command_progression_boundaries(report):
    """Grouping must preserve repeats, order, empty traces, and blocked members."""
    first = replace(
        report.variants.before.trials[0],
        name="before-α<&>",
        commands=(
            "cat alpha.py",
            "cat alpha.py",
            "printf 'a  b'\n\tprintf '<script>x</script>'",
        ),
    )
    repeated = replace(first, name="before-blocked", verdict="BLOCKED")
    reordered = replace(
        first,
        name="before-reordered",
        commands=(first.commands[-1], "cat alpha.py", "cat alpha.py"),
    )
    empty = replace(first, name="before-empty", commands=())
    before = replace(
        report.variants.before,
        trials=(first, repeated, reordered, empty),
        total=4,
        blocked=1,
        valid=3,
    )
    groups = content.command_progressions(before)
    assert tuple(commands for commands, _ in groups) == (
        first.commands,
        reordered.commands,
        (),
    ), "Command order, repetition, or empty evidence was lost."
    assert tuple(trial.name for trial in groups[0][1]) == (
        "before-α<&>",
        "before-blocked",
    ), "Identical recorded paths were not grouped with their original trials."
    assert groups[0][1][1].verdict == "BLOCKED"
    assert content.command_progressions(replace(before, trials=(), total=0)) == ()

    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown

    specimen = replace(report, variants=replace(report.variants, before=before))
    assert_evidence_links(specimen)

    class ProgressionCommands(HTMLParser):
        def __init__(self):
            super().__init__()
            self.active = False
            self.parts = None
            self.commands = []

        def handle_starttag(self, tag, attrs):
            anchor = dict(attrs).get("id")
            if anchor in ("flow-progression", "panel-trials"):
                self.active = anchor == "flow-progression"
            if tag == "pre" and self.active:
                self.parts = []

        def handle_data(self, text):
            if self.parts is not None:
                self.parts.append(text)

        def handle_endtag(self, tag):
            if tag == "pre" and self.parts is not None:
                self.commands.append("".join(self.parts))
                self.parts = None

    for baseline, rendered in (
        (
            render_artifact(report, ""),
            render_artifact(specimen, ""),
        ),
        (render_markdown(report), render_markdown(specimen)),
    ):
        assert_unchanged_scripts(baseline, rendered)
        assert "&lt;script&gt;" in rendered, (
            "Escaping removed recorded command evidence."
        )
        commands = ProgressionCommands()
        commands.feed(rendered)
        assert commands.commands == list(
            first.commands
            + reordered.commands
            + report.variants.after.trials[0].commands
            + report.variants.after.trials[1].commands
        ), "Progression lost command order, repetition, or verbatim whitespace."


def assert_intent_reports(reports, root):
    """Signal ranking must not change identity or invent edit-related evidence."""
    from reporting.load import load_report

    flip = reports["intent-flip"]
    assert flip.decisions.outcome == 3
    assert content.consistent_changes(flip.decisions) == (2,)
    assert flip.decisions.rows[1].edit_hunks == (1,)

    changed_row = flip.decisions.rows[1]
    for before_count, after_count, before_n, after_n, expected in (
        (1, 1, 1, 1, ()),
        (3, 3, 2, 3, ()),
        (3, 3, 3, 2, ()),
        (2, 5, 2, 5, (1,)),
    ):
        decisions = replace(
            flip.decisions,
            rows=(
                replace(
                    changed_row,
                    before=(DecisionChoiceData("query-old", before_n),),
                    after=(DecisionChoiceData("query-new", after_n),),
                ),
            ),
            before_count=before_count,
            after_count=after_count,
            outcome=None,
        )
        assert content.consistent_changes(decisions) == expected

    for invalid in ([True], [0], [2], [1, 1], "1"):
        raw = flip.to_dict()
        raw["decisions"]["rows"][1]["edit_hunks"] = invalid
        try:
            ReportData.from_dict(raw)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Invalid edit evidence reference accepted: {invalid!r}"
            )

    run = root / "intent-flip"
    extraction = json.loads((run / "decisions.json").read_text())
    for provenance in ("different instruction diff", None):
        stale = dict(extraction)
        if provenance is None:
            stale.pop("instruction_diff", None)
        else:
            stale["instruction_diff"] = provenance
        (run / "decisions.json").write_text(json.dumps(stale))
        loaded = load_report(run, run, "synthetic/authored", run / "config.json")
        assert len(loaded.decisions.rows) == len(flip.decisions.rows)
        assert all(not row.edit_hunks for row in loaded.decisions.rows)
        assert content.consistent_changes(loaded.decisions) == (2,), (
            "Stale edit interpretation must not discard observed choices."
        )


def assert_visual_summaries(reports):
    """A visual lead must retain distributions, provenance, and evidence limits."""
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown
    from reporting.summary import build_summary

    changed = reports["changed-result"]
    assert changed.summary.decision == changed.decisions.outcome
    planned = reports["planned-actions"]
    assert planned.decisions.narrative.evidence_kind == "plans"
    assert "plan" in planned.summary.evidence_label.lower()
    assert "captured" not in reports["self-reported"].summary.evidence_label.lower()
    target = reports["target-baseline"].decisions.target_assessment
    for name in ("planned-actions", "self-reported", "same-result"):
        report = reports[name]
        decisions = replace(report.decisions, target_assessment=target)
        assessed = replace(
            report,
            decisions=decisions,
            summary=build_summary(report.metadata, report.variants, decisions),
        )
        for rendered in (render_artifact(assessed, ""), render_markdown(assessed)):
            plain = html.unescape(rendered).replace("\\", "")
            assert report.summary.evidence_label in plain
            for side in (report.summary.before, report.summary.after):
                assert all(choice.label in plain for choice in side.choices)
    for report in reports.values():
        summary = report.summary
        if summary.decision is not None:
            row = report.decisions.rows[summary.decision - 1]
            for side in ("before", "after"):
                visual = getattr(summary, side)
                assert [(item.choice, item.count) for item in visual.choices] == [
                    (item.choice, item.count) for item in getattr(row, side)
                ]
                assert visual.total == getattr(report.variants, side).total
    mixed = reports["mixed"]
    assert mixed.summary.status == "mixed"
    assert sorted(choice.count for choice in mixed.summary.after.choices) == [1, 2]
    for name in ("blocked", "missing-extraction"):
        assert reports[name].summary.status == "unavailable"
        assert reports[name].summary.why is None
    assert reports["unchanged"].summary.status == "unchanged"

    non_outcome = reports["non-outcome-narrative"]
    assert non_outcome.decisions.outcome == 4
    assert non_outcome.decisions.narrative.decision == 5
    assert non_outcome.decisions.rows[4].edit_hunks == (1,)
    assert non_outcome.summary.decision == 5, (
        "A changed outcome must not displace a validated changed non-outcome narrative."
    )
    assert non_outcome.summary.headline == non_outcome.decisions.narrative.headline
    assert non_outcome.summary.status == "changed"
    selected = non_outcome.decisions.rows[4]
    narrative = non_outcome.decisions.narrative
    mixed_selected = replace(
        selected,
        before=(
            replace(selected.before[0], count=2),
            replace(selected.after[0], count=1),
        ),
    )
    mixed_narrative = replace(
        narrative,
        before=replace(
            narrative.before, choices=narrative.before.choices + narrative.after.choices
        ),
    )
    mixed_decisions = replace(
        non_outcome.decisions,
        rows=non_outcome.decisions.rows[:4] + (mixed_selected,),
        narrative=mixed_narrative,
    )
    mixed_lead = build_summary(
        non_outcome.metadata, non_outcome.variants, mixed_decisions
    )
    assert mixed_lead.decision == 5
    assert mixed_lead.headline == narrative.headline
    assert mixed_lead.status == "mixed"
    assert [choice.count for choice in mixed_lead.before.choices] == [2, 1]
    assert [choice.count for choice in mixed_lead.after.choices] == [3]
    for decisions, status in (
        (replace(non_outcome.decisions, narrative=None), "changed"),
        (replace(non_outcome.decisions, dropped=1), "unavailable"),
    ):
        fallback = build_summary(non_outcome.metadata, non_outcome.variants, decisions)
        assert fallback.decision == non_outcome.decisions.outcome
        assert fallback.status == status
        assert fallback.headline != narrative.headline
        assert fallback.why is None

    mixed_primary = reports["mixed-primary"]
    assert mixed_primary.decisions.narrative is not None
    assert mixed_primary.summary.decision == mixed_primary.decisions.outcome, (
        "A unanimous secondary action must not displace a mixed primary-result narrative."
    )
    assert mixed_primary.summary.headline == mixed_primary.decisions.narrative.headline
    assert mixed_primary.summary.status == "mixed"
    assert [
        (choice.choice, choice.count) for choice in mixed_primary.summary.before.choices
    ] == [
        ("HOLD", 2),
        ("APPROVE", 1),
    ]
    assert [
        (choice.choice, choice.count) for choice in mixed_primary.summary.after.choices
    ] == [
        ("APPROVE", 3),
    ]
    primary_decisions = mixed_primary.decisions
    fallback = build_summary(
        mixed_primary.metadata,
        mixed_primary.variants,
        replace(primary_decisions, narrative=None),
    )
    assert fallback.decision == 2, (
        "Without a supported changed primary narrative, retain the action fallback."
    )
    assert fallback.headline != primary_decisions.narrative.headline
    incomplete = build_summary(
        mixed_primary.metadata,
        mixed_primary.variants,
        replace(primary_decisions, dropped=1),
    )
    assert incomplete.status == "unavailable"
    assert incomplete.headline != primary_decisions.narrative.headline
    assert incomplete.why is None
    missing_primary = build_summary(
        mixed_primary.metadata,
        mixed_primary.variants,
        replace(primary_decisions, outcome=None),
    )
    assert missing_primary.decision == primary_decisions.narrative.decision
    assert missing_primary.headline == primary_decisions.narrative.headline
    assert missing_primary.status == "mixed"

    def summarize(variants=changed.variants, decisions=changed.decisions):
        return build_summary(changed.metadata, variants, decisions)

    for decisions in (
        replace(changed.decisions, dropped=1),
        replace(changed.decisions, after_count=4),
        replace(
            changed.decisions,
            narrative=None,
            rows=tuple(
                replace(row, after=(DecisionChoiceData(" ", 3),))
                for row in changed.decisions.rows
            ),
        ),
    ):
        assert summarize(decisions=decisions).status == "unavailable"
    single_variants = replace(
        changed.variants,
        before=replace(
            changed.variants.before,
            total=1,
            valid=1,
            trials=changed.variants.before.trials[:1],
        ),
        after=replace(
            changed.variants.after,
            total=1,
            valid=1,
            trials=changed.variants.after.trials[:1],
        ),
    )
    single_decisions = replace(
        changed.decisions,
        before_count=1,
        after_count=1,
        rows=tuple(
            replace(
                row,
                before=tuple(replace(choice, count=1) for choice in row.before),
                after=tuple(replace(choice, count=1) for choice in row.after),
            )
            for row in changed.decisions.rows
        ),
    )
    single = summarize(single_variants, single_decisions)
    assert single.before.total == single.after.total == 1
    assert any(
        "one" in note.lower() or "single" in note.lower() for note in single.notices
    )
    for field, value in (("count", 99), ("choice", "unsupported choice")):
        raw = changed.to_dict()
        raw["summary"]["after"]["choices"][0][field] = value
        try:
            ReportData.from_dict(raw)
        except ValueError:
            pass
        else:
            raise AssertionError("Visual summary accepted invented choice evidence.")

    payload = '<script>alert("x")</script>|[link](javascript:alert(1))'
    unsafe_decisions = replace(
        changed.decisions,
        narrative=replace(changed.decisions.narrative, headline=payload),
    )
    unsafe = replace(
        changed,
        decisions=unsafe_decisions,
        summary=summarize(decisions=unsafe_decisions),
    )
    for render in (lambda report: render_artifact(report, ""), render_markdown):
        rendered = render(unsafe)
        assert_unchanged_scripts(render(changed), rendered)
        assert "&lt;script&gt;" in rendered
    assert "](javascript:" not in render_markdown(unsafe)
    assert_primary_result_context(reports)


def assert_primary_result_context(reports):
    """A secondary lead cannot conceal canonical primary outcomes or uncertainty."""
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown
    from reporting.summary import build_summary

    base = reports["non-outcome-narrative"]
    primary = base.decisions.outcome
    original = base.decisions.rows[primary - 1]

    def with_primary(row=original, **changes):
        rows = tuple(
            row if index == primary else value
            for index, value in enumerate(base.decisions.rows, 1)
        )
        decisions = replace(base.decisions, rows=rows, **changes)
        return replace(
            base,
            decisions=decisions,
            summary=build_summary(base.metadata, base.variants, decisions),
        )

    same = with_primary(replace(original, after=original.before))
    assert same.summary.decision != primary
    assert same.decisions.rows[same.summary.decision - 1].anchor == "answer"
    mixed = with_primary(
        replace(
            original,
            before=(
                replace(original.before[0], count=2),
                replace(original.after[0], count=1),
            ),
        )
    )
    no_primary = with_primary(outcome=None)
    cases = (
        (same, "unchanged"),
        (base, "changed"),
        (mixed, "mixed"),
        (with_primary(dropped=1), "unavailable"),
        (no_primary, "unavailable"),
    )
    for report, expected_status in cases:
        # Incomplete evidence may select the primary fallback; force the existing
        # secondary lead here to exercise the context's independent safety gate.
        if report.summary.decision == report.decisions.outcome:
            report = replace(
                report,
                summary=replace(report.summary, decision=base.summary.decision),
            )
        context = content.primary_result_context(report)
        assert context is not None and context.status == expected_status
        assert context.decision == report.decisions.outcome
        rendered = render_artifact(report, "")
        block = rendered.split('class="primary-result-context"', 1)[1].split(
            "</section>", 1
        )[0]
        markdown = render_markdown(report)
        md_block = markdown.split(f"#### {context.heading}", 1)[1].split("### 3.", 1)[0]
        assert expected_status in block and expected_status in md_block
        assert "<a " not in block, (
            "Primary-result context must not add a competing link."
        )
        assert re.findall(r"\]\(#panel-explanation\)", md_block) == [
            "](#panel-explanation)"
        ], "The observed comparison opens the shared explanation destination."
        if context.decision is None:
            assert not context.sides
        else:
            row = report.decisions.rows[context.decision - 1]
            for side in ("before", "after"):
                for choice in getattr(row, side):
                    assert html.escape(choice.choice) in block
                    assert choice.choice in md_block
                    count = content.trial_count(
                        choice.count, getattr(report.decisions, side + "_count")
                    )
                    assert count in block and count in md_block
            if row.anchor == "answer":
                assert "reported" in context.heading.lower()
                assert "execution" in context.note.lower()
    assert content.primary_result_context(reports["changed-result"]) is None

    for field, value in (("blocked", 1), ("valid", 2)):
        variants = replace(
            base.variants,
            after=replace(base.variants.after, **{field: value}),
        )
        report = replace(base, variants=variants)
        assert content.primary_result_context(report).status == "unavailable"


def assert_timing_rule_cards(report):
    """Rule cards retain timing and their own counts beside a mixed primary result."""
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown
    from reporting.summary import build_summary

    assert report.summary.decision == 1 and report.decisions.outcome == 2
    assert report.summary.status == "mixed"
    assert report.summary.evidence_label == (
        "Plans stated in final answers; not executed actions."
    )
    primary = report.decisions.rows[1]
    changed_primary = replace(
        primary,
        after=(
            DecisionChoiceData("Recommend proceeding", 1),
            DecisionChoiceData("Recommend deferring", 2),
        ),
    )
    decisions = replace(
        report.decisions, rows=(report.decisions.rows[0], changed_primary)
    )
    changed = replace(
        report,
        decisions=decisions,
        summary=build_summary(report.metadata, report.variants, decisions),
    )
    assert changed.summary.before == report.summary.before
    assert changed.summary.after == report.summary.after
    rendered = render_artifact(report, "")
    changed_html = render_artifact(changed, "")
    markdown = render_markdown(report)
    cards = {}
    md_cards = {}
    for side, timing in (
        ("before", ("every 5 minutes", "15-minute deadline")),
        ("after", ("every 10 minutes", "30-minute deadline", "check once")),
    ):
        marker = f'class="summary-card summary-{side}"'
        cards[side] = html.unescape(
            rendered.split(marker, 1)[1].split("</section>", 1)[0]
        )
        assert cards[side] == html.unescape(
            changed_html.split(marker, 1)[1].split("</section>", 1)[0]
        ), "Primary-result counts must not rewrite operative-rule cards."
        md_cards[side] = (
            markdown.split(f"#### {side.capitalize()}\n", 1)[1]
            .split("#### ", 1)[0]
            .replace(r"\-", "-")
        )
        for text in ("wait for signoff", *timing):
            assert text in cards[side] and text in md_cards[side]
        assert "Recommend" not in cards[side] and "Recommend" not in md_cards[side]
    for text in ("2 of 3 trials", "1 of 3 trials"):
        assert text in cards["after"] and text in md_cards["after"]
    context = content.primary_result_context(report)
    changed_context = content.primary_result_context(changed)
    assert context.status == changed_context.status == "mixed"
    assert context.sides != changed_context.sides
    assert all(
        "Recommend proceeding" in text and "Recommend deferring" in text
        for _, text in context.sides
    )
    assert "primary result varies across trials" in rendered
    assert "primary result varies across trials" in markdown


def assert_instruction_intent(reports, root):
    """The edit's inferred aim is distinct from both supplied expectations and results."""
    from reporting.load import load_report
    from reporting.summary import build_intent

    planned = reports["planned-actions"]
    assert planned.intent.source == "inferred"
    assert planned.intent.edit_hunks == (1,)
    assert reports["missing-extraction"].intent.source == "unavailable"
    supplied = "Return a repair plan; do not execute it."
    intent = build_intent(supplied, planned.decisions)
    assert intent.source == "expected" and intent.text == supplied
    assert intent.edit_hunks == ()
    assert build_intent("  ", planned.decisions) == planned.intent
    for field, value in (
        ("source", "expected"),
        ("text", "The trials prove the author wanted this result."),
        ("edit_hunks", [2]),
    ):
        raw = planned.to_dict()
        raw["intent"][field] = value
        try:
            ReportData.from_dict(raw)
        except ValueError:
            pass
        else:
            raise AssertionError("Report accepted unsupported instruction intent.")

    run = root / "planned-actions"
    path = run / "decisions.json"
    original = path.read_text()
    try:
        raw = json.loads(original)
        for provenance in ("different diff", None):
            stale = dict(raw)
            if provenance is None:
                stale.pop("instruction_diff")
            else:
                stale["instruction_diff"] = provenance
            path.write_text(json.dumps(stale))
            loaded = load_report(run, run, "synthetic/authored", run / "config.json")
            assert loaded.intent.source == "unavailable"
            assert loaded.decisions.rows == planned.decisions.rows
        legacy = dict(raw)
        legacy.pop("intent")
        path.write_text(json.dumps(legacy))
        loaded = load_report(run, run, "synthetic/authored", run / "config.json")
        assert loaded.intent.source == "unavailable"
        assert loaded.summary == planned.summary
    finally:
        path.write_text(original)

    grades = run / "grades.tsv"
    original_grades = grades.read_text()
    try:
        grades.write_text(
            original_grades.replace("after-1\tREVIEW", "after-1\tBLOCKED")
        )
        blocked = load_report(run, run, "synthetic/authored", run / "config.json")
        assert blocked.summary.status == "unavailable"
        assert blocked.intent == planned.intent, (
            "Incomplete trials must not erase independently supported edit interpretation."
        )
    finally:
        grades.write_text(original_grades)

    config_path = run / "config.json"
    original_config = config_path.read_text()
    try:
        config = json.loads(original_config)
        config["expected"] = supplied
        config_path.write_text(json.dumps(config))
        loaded = load_report(run, run, "synthetic/authored", config_path)
        assert loaded.intent == intent
        assert loaded.decisions.intent == planned.decisions.intent
    finally:
        config_path.write_text(original_config)


def assert_saved_scenario_task(root):
    """A short description must not replace the prompt actually given to the agent."""
    from reporting.load import load_report

    run = root / "planned-actions"
    config_path = run / "config.json"
    task_path = run / "task.md"
    original_config = config_path.read_text()
    original_task = task_path.read_text()
    config = json.loads(original_config)
    config["scenario"] = "A synthetic failing-check scenario."
    config_path.write_text(json.dumps(config))
    try:
        with tempfile.TemporaryDirectory() as directory:
            capsule = Path(directory)
            (capsule / "task.md").write_text("A different capsule task.")
            report = load_report(run, capsule, "synthetic/model", config_path)
            assert report.content.scenario == config["scenario"]
            assert report.content.task == original_task.strip()
            assert_round_trip(report.to_dict())
            task_path.unlink()
            report = load_report(run, capsule, "synthetic/model", config_path)
            assert report.content.task == "A different capsule task."
            (capsule / "task.md").unlink()
            report = load_report(run, capsule, "synthetic/model", config_path)
            assert report.content.task is None
            assert report.content.scenario == config["scenario"]
            assert_round_trip(report.to_dict())
    finally:
        config_path.write_text(original_config)
        task_path.write_text(original_task)


def assert_gallery_reports():
    """Exercise the same authored cases used by the local gallery through the CLI."""
    expected = {
        "same-result": ("unchanged", "changed"),
        "changed-result": ("changed", "changed"),
        "unchanged": ("unchanged", "unchanged"),
        "answer-details": ("unchanged", "unchanged"),
        "mixed": ("varies", "changed"),
        "mixed-primary": ("varies", "changed"),
        "non-outcome-narrative": ("changed", "changed"),
        "missing-primary": ("changed", "changed"),
        "blocked": ("unavailable", "unavailable"),
        "missing-extraction": ("unavailable", "unavailable"),
        "self-reported": ("changed", "changed"),
        "flow-changed": ("unchanged", "changed"),
        "flow-mixed": ("unchanged", "changed"),
        "intent-flip": ("varies", "changed"),
        "intent-unchanged": ("unchanged", "unavailable"),
        "planned-actions": ("changed", "unavailable"),
        "timing-rule": ("varies", "unavailable"),
        "formula-writing": ("unchanged", "unchanged"),
        "attention-mixed": ("unchanged", "changed"),
        "attention-self-reported": ("unchanged", "changed"),
        "attention-plans": ("unchanged", "changed"),
        "attention-quiet": ("unchanged", "unchanged"),
        "attention-unavailable": ("unchanged", "changed"),
        "attention-multiple": ("unchanged", "changed"),
    }
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        build_reports(root)
        reports = {}
        for scenario in SCENARIOS:
            name = scenario.name
            report = assert_file_round_trip(root / name / "report-data.json")
            reports[name] = report
            if name in expected:
                result_state, action_state = expected[name]
                assert report.result.outcome_heading.endswith("— " + result_state), name
                assert report.result.behavior_heading.endswith("— " + action_state), (
                    name
                )
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

        mixed_summaries = reports["mixed"].decisions.trial_summaries
        assert len(mixed_summaries) == 3
        assert "changes" in mixed_summaries[0].takeaway
        assert "changes" in mixed_summaries[1].takeaway
        assert mixed_summaries[2].takeaway.startswith("Both reviews")
        assert "changes" not in mixed_summaries[2].takeaway
        assert reports["missing-extraction"].decisions.trial_summaries == ()
        for name, report in reports.items():
            if name != "missing-extraction":
                assert len(report.decisions.trial_summaries) == 3, name
            for number, summary in enumerate(report.decisions.trial_summaries):
                assert (
                    summary.before_trial == report.variants.before.trials[number].name
                )
                assert summary.after_trial == report.variants.after.trials[number].name
        assert reports["planned-actions"].decisions.trial_summaries[0].caveat == (
            "Neither proposed step is recorded as executed."
        )
        assert_timing_rule_cards(reports["timing-rule"])

        assert content.flow_patterns(reports["same-result"].command_flow) == (
            (("Read files",), 3, 3),
        ), "Different files must not become different command categories."
        assert content.flow_patterns(reports["flow-changed"].command_flow) == (
            (("Read files",), 3, 0),
            (("Read files", "Run tests"), 0, 3),
        )
        assert content.flow_patterns(reports["flow-mixed"].command_flow) == (
            (("Read files",), 3, 1),
            (("Read files", "Run tests"), 0, 2),
        ), "The optional-test pattern lost trials or collapsed category combinations."

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
        assert_visual_summaries(reports)
        assert_instruction_intent(reports, root)
        assert_attention_reports(
            reports,
            root,
            assert_round_trip,
            assert_evidence_links,
            assert_unchanged_scripts,
        )
        assert_intent_reports(reports, root)
        assert_saved_scenario_task(root)
        assert_change_explanations(
            reports,
            root,
            assert_round_trip,
            assert_evidence_links,
            assert_unchanged_scripts,
        )
        assert_target_reports(reports, root, assert_round_trip)

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


def assert_trial_summary_rendering(report):
    """Every group leads with its own short summary while retaining complete evidence."""
    from unittest.mock import patch

    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown

    def rendered_groups(specimen):
        with patch(
            "subprocess.run", side_effect=AssertionError("Rendering called a process")
        ):
            outputs = (render_artifact(specimen, ""), render_markdown(specimen))
        for rendered in outputs:
            for number in range(
                1,
                max(
                    len(specimen.variants.before.trials),
                    len(specimen.variants.after.trials),
                )
                + 1,
            ):
                group = rendered.split(f'id="trial-group-{number}"', 1)[1]
                group = group.split(f'id="trial-group-{number + 1}"', 1)[0]
                yield number, group

    for number, group in rendered_groups(report):
        summary = report.decisions.trial_summaries[number - 1]
        plain = html.unescape(group).replace("\\", "")
        assert plain.index(content.TRIAL_CHANGE_HEADING) < plain.index(summary.takeaway)
        assert plain.index(summary.takeaway) < plain.index(content.FINAL_ANSWER_HEADING)
        assert summary.before in plain and summary.after in plain
        assert summary.caveat in plain
        for variant in (report.variants.before, report.variants.after):
            trial = variant.trials[number - 1]
            assert html.escape(trial.final) in group
            for command in trial.commands:
                assert html.escape(command) in group
        if number == 2:
            assert report.decisions.trial_summaries[0].takeaway not in plain

    first, second = report.decisions.trial_summaries
    for summaries in (
        (),
        (replace(first, after_trial=second.after_trial),),
        (first, first),
        (first, replace(first, before="Different duplicate description.")),
    ):
        specimen = replace(
            report, decisions=replace(report.decisions, trial_summaries=summaries)
        )
        for _, group in rendered_groups(specimen):
            plain = html.unescape(group).replace("\\", "")
            assert content.TRIAL_SUMMARY_UNAVAILABLE in plain
            assert first.takeaway not in plain
            assert second.takeaway not in plain
            for trial in report.variants.before.trials + report.variants.after.trials:
                if html.escape(trial.name) in group:
                    assert html.escape(trial.final) in group

    one_side = replace(
        second,
        before_trial="",
        before="",
        takeaway="Only the after review is recorded in this group.",
    )
    unequal = replace(
        report,
        variants=replace(
            report.variants,
            before=replace(
                report.variants.before, trials=report.variants.before.trials[:1]
            ),
        ),
        decisions=replace(report.decisions, trial_summaries=(first, one_side)),
    )
    for number, group in rendered_groups(unequal):
        if number == 2:
            plain = html.unescape(group).replace("\\", "")
            assert one_side.takeaway in plain and one_side.after in plain
            assert "No trial record on this side." in plain
            assert html.escape(report.variants.after.trials[1].final) in group

    payload = '<script>alert("synthetic")</script> & [link](javascript:alert(1))'
    unsafe = replace(
        report,
        decisions=replace(
            report.decisions,
            trial_summaries=(
                replace(
                    first,
                    takeaway=payload,
                    before=payload,
                    after=payload,
                    caveat=payload,
                ),
                second,
            ),
        ),
    )
    for baseline, rendered in (
        (render_artifact(report, ""), render_artifact(unsafe, "")),
        (render_markdown(report), render_markdown(unsafe)),
    ):
        assert_unchanged_scripts(baseline, rendered)
        assert "&lt;script&gt;" in rendered


def assert_trial_summary_validation(raw):
    """Optional copy is bounded, canonical, and attached only to its own group."""
    groups = (("before-1", "after-1"), ("before-2", "after-2"))
    first, second = copy.deepcopy(raw["decisions"]["trial_summaries"])
    expected = tuple(TrialSummaryData(**item) for item in (first, second))
    assert parse_trial_summaries([second, first], groups) == expected
    assert parse_trial_summaries([dict(first, caveat="")], groups)[0].caveat == ""
    without_caveat = dict(first)
    del without_caveat["caveat"]
    assert parse_trial_summaries([without_caveat], groups)[0].caveat == ""
    assert (
        parse_trial_summaries([dict(first, takeaway="  Short finding.  ")], groups)[
            0
        ].takeaway
        == "Short finding."
    )
    for field in ("takeaway", "before", "after", "caveat"):
        for text in ("x" * 240, " ".join(["word"] * 40)):
            accepted = parse_trial_summaries([dict(first, **{field: text})], groups)
            assert accepted and getattr(accepted[0], field) == text
        for text in (
            "x" * 241,
            " ".join(["word"] * 41),
            "Two\nlines",
            "Two\tcolumns",
            "Control\x7f",
            "<script>unsafe</script>",
            "`command dump`",
            "**Markdown emphasis**",
            "[Markdown link](https://example.invalid)",
            False,
            None,
            [],
        ):
            assert parse_trial_summaries([dict(first, **{field: text})], groups) == ()
    for field in ("takeaway", "before", "after"):
        assert parse_trial_summaries([dict(first, **{field: " "})], groups) == ()
        missing = dict(first)
        del missing[field]
        assert parse_trial_summaries([missing], groups) == ()
    for malformed in (None, False, {}, "summary", [None], [[]]):
        assert parse_trial_summaries(malformed, groups) == ()
    for invalid in (
        dict(first, before_trial=True),
        dict(first, after_trial=None),
        dict(first, before_trial="after-1"),
        dict(first, before_trial="", after_trial=""),
        dict(first, before_trial="before-1 ", after_trial="after-1"),
        dict(first, before_trial="before-1", after_trial="after-2"),
        dict(first, before_trial="before-unknown"),
    ):
        assert parse_trial_summaries([invalid, second], groups) == (expected[1],)
    assert parse_trial_summaries([first, first, second], groups) == (expected[1],)
    assert parse_trial_summaries(
        [first, dict(first, takeaway=False), second], groups
    ) == (expected[1],), "A malformed duplicate must not leave an arbitrary winner."

    one_sided = dict(first, before_trial="", before="")
    absent_groups = (("", "after-1"),)
    assert parse_trial_summaries([one_sided], absent_groups) == (
        TrialSummaryData(**one_sided),
    )
    assert (
        parse_trial_summaries([dict(one_sided, before="No work.")], absent_groups) == ()
    )
    other_side = dict(first, after_trial="", after="")
    assert parse_trial_summaries([other_side], (("before-1", ""),)) == (
        TrialSummaryData(**other_side),
    )
    assert trial_group_names(("before-10", "before-2"), ("after-alpha",)) == (
        ("before-10", "after-alpha"),
        ("before-2", ""),
    )

    canonical_error = (
        "invalid report-data field decisions.trial_summaries: "
        "expected valid canonical trial group summaries"
    )
    for invalid in (
        None,
        {},
        [dict(first, takeaway=" padded ")],
        [dict(first, after_trial="after-2")],
        [first, first],
        [second, first],
        [dict(first, extra="not part of the contract")],
        [dict(first, before=False)],
    ):
        specimen = copy.deepcopy(raw)
        specimen["decisions"]["trial_summaries"] = invalid
        assert_rejected(specimen, canonical_error)
    empty = copy.deepcopy(raw)
    empty["decisions"]["trial_summaries"] = []
    assert assert_round_trip(empty).decisions.trial_summaries == ()
    missing = copy.deepcopy(raw)
    del missing["decisions"]["trial_summaries"]
    assert_rejected(
        missing,
        "invalid report-data field decisions.trial_summaries: expected present field",
    )
    assert_rejected(
        dict(raw, schema_version=7), "unsupported report-data schema version: 7"
    )


def assert_trial_summary_pipeline():
    """Production prompt, ingestion, loading, and offline rendering share identities."""
    import decisions
    from reporting.load import load_report

    with tempfile.TemporaryDirectory() as directory:
        run = Path(directory)
        (run / "task.md").write_text("Review the synthetic widget without changing it.")
        (run / "config.json").write_text(
            json.dumps(
                {"mode": "review", "vocab": "generic", "target_file": "AGENTS.md"}
            )
        )
        names = (
            "before-review-extra",
            "after-alpha",
            "before-02",
            "after-10",
            "after-z-missing",
        )
        (run / "grades.tsv").write_text(
            "".join(
                f"{name}\t{'BLOCKED' if name == 'after-z-missing' else 'REVIEW'}\t-\n"
                for name in names
            )
        )
        for name in names[:-1]:
            trial = run / name
            trial.mkdir()
            (trial / "trace.jsonl").write_text(
                "\n".join(
                    json.dumps(event)
                    for event in (
                        False,
                        {"type": "assistant", "message": {"content": [False]}},
                        {
                            "type": "assistant",
                            "message": {
                                "content": [
                                    {
                                        "type": "tool_use",
                                        "input": {
                                            "command": "read synthetic-widget.txt"
                                        },
                                    }
                                ]
                            },
                        },
                        {
                            "type": "result",
                            "result": f"Complete synthetic answer for {name}.",
                        },
                    )
                )
            )
        # Unlisted directories cannot shift the report's persisted groups.
        (run / "before-00-ungraded").mkdir()
        all_trials = decisions.trials_of(run, finished_only=False)
        groups = decisions.summary_groups(all_trials)
        assert groups == (
            ("before-02", "after-10"),
            ("before-review-extra", "after-alpha"),
            ("", "after-z-missing"),
        )
        prompt, completed_names, instruction_diff = decisions.build_prompt(run)
        assert completed_names == {
            "before": ["before-02", "before-review-extra"],
            "after": ["after-10", "after-alpha"],
        }
        assert "NOT paired executions" in prompt
        assert "before-00-ungraded" not in prompt
        assert "(not recorded)" in prompt and "after-z-missing" in prompt
        encoded_groups = json.dumps(
            [
                {"before_trial": before, "after_trial": after}
                for before, after in groups
            ],
            ensure_ascii=False,
            indent=2,
        )
        assert encoded_groups in prompt
        summaries = [
            {
                "before_trial": before,
                "after_trial": after,
                "takeaway": (
                    "Both records show a file read."
                    if before
                    else "Only an incomplete after record is available."
                ),
                "before": "The before record shows a file read." if before else "",
                "after": (
                    "The after record shows a file read."
                    if before
                    else "The after record has no recorded final answer."
                ),
                "caveat": ""
                if before
                else "No before record is available in this group.",
            }
            for before, after in groups
        ]
        extraction = {
            "chain": [
                {
                    "decision": "Which evidence was recorded?",
                    "topic": "File review",
                    "anchor": 1,
                    "before": [{"choice": "read", "trials": completed_names["before"]}],
                    "after": [{"choice": "read", "trials": completed_names["after"]}],
                }
            ],
            "trial_summaries": summaries,
        }
        with contextlib.redirect_stdout(io.StringIO()):
            assert decisions.write_decisions(
                run,
                json.dumps(extraction),
                completed_names,
                "synthetic/no-model",
                instruction_diff,
            )
        saved = json.loads((run / "decisions.json").read_text())
        assert saved["trial_summaries"] == summaries
        report = load_report(run, run, "synthetic/no-model", run / "config.json")
        assert [
            (item.before_trial, item.after_trial)
            for item in report.decisions.trial_summaries
        ] == list(groups)
        assert report.variants.after.trials[-1].final == ""
        assert report.variants.after.trials[-1].verdict == "BLOCKED"
        assert assert_round_trip(report.to_dict()) == report
        baseline_trials = report.variants
        baseline_rows = report.decisions.rows
        for malformed in (
            None,
            "not a list",
            [dict(summaries[0], after_trial="after-alpha")],
            [dict(summaries[0], takeaway="x" * 241)],
            [summaries[0], summaries[0]],
        ):
            normalized = decisions.normalize(
                dict(extraction, trial_summaries=malformed),
                completed_names,
                groups=groups,
            )
            assert normalized["trial_summaries"] == []
            assert len(normalized["chain"]) == 1
            saved["trial_summaries"] = malformed
            (run / "decisions.json").write_text(json.dumps(saved))
            loaded = load_report(run, run, "synthetic/no-model", run / "config.json")
            assert loaded.decisions.trial_summaries == ()
            assert loaded.decisions.rows == baseline_rows
            assert loaded.variants == baseline_trials
        del saved["trial_summaries"]
        (run / "decisions.json").write_text(json.dumps(saved))
        loaded = load_report(run, run, "synthetic/no-model", run / "config.json")
        assert loaded.decisions.rows == baseline_rows
        # A valid local summary is independent of invalid aggregate observations.
        summary_only = dict(extraction, chain=[{"decision": "Bad row."}])
        with contextlib.redirect_stdout(io.StringIO()):
            assert decisions.write_decisions(
                run,
                json.dumps(summary_only),
                completed_names,
                "synthetic/no-model",
                instruction_diff,
            )
        loaded = load_report(run, run, "synthetic/no-model", run / "config.json")
        assert loaded.decisions.rows == ()
        assert len(loaded.decisions.trial_summaries) == 3
        assert loaded.variants == baseline_trials
        from reporting.render_html import render_artifact
        from reporting.render_markdown import render_markdown

        for rendered in (render_artifact(loaded, ""), render_markdown(loaded)):
            plain = html.unescape(rendered).replace("\\", "")
            assert summaries[0]["takeaway"] in plain
            assert summaries[-1]["takeaway"] in plain
            assert content.TRIAL_SUMMARY_UNAVAILABLE not in plain
            assert content.NO_FINAL_ANSWER in plain
            for variant in (loaded.variants.before, loaded.variants.after):
                for trial in variant.trials:
                    if trial.final:
                        assert html.escape(trial.final) in rendered


def main():
    assert_render_import_safe()
    raw = synthetic_raw()
    report = assert_round_trip(raw)
    assert_trial_summary_validation(raw)
    assert_branch_membership_validation(raw)
    assert_trial_summary_pipeline()
    assert_trial_summary_rendering(report)
    assert_summary_evidence(report)
    assert_summary_boundaries(report)
    assert_evidence_links(report)
    assert_guided_report_structure(report)
    assert_no_invented_causality()
    assert_tab_comparison_boundaries(report)
    assert_flow_pattern_boundaries()
    assert_command_progression_boundaries(report)
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
        dict(raw, schema_version=3),
        "unsupported report-data schema version: 3",
    )
    assert_rejected(
        dict(raw, schema_version=9),
        "unsupported report-data schema version: 9",
    )
    assert_rejected(
        dict(raw, schema_version=10),
        "unsupported report-data schema version: 10",
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

    from reporting.render_html import render_artifact, render_document

    artifact = render_artifact(report, "")
    assert artifact == render_artifact(report, "")
    document = render_document(artifact)
    assert document == render_document(artifact)
    escaping_raw = copy.deepcopy(raw)
    escaping_raw["variants"]["before"]["trials"][0]["verdict"] = 'REVIEW"><script>&'
    escaping_report = ReportData.from_dict(escaping_raw)
    escaping_artifact = render_artifact(escaping_report, "")
    from reporting.render_markdown import render_markdown

    for baseline, rendered in (
        (artifact, escaping_artifact),
        (render_markdown(report), render_markdown(escaping_report)),
    ):
        assert_unchanged_scripts(baseline, rendered)
    unsafe_summary = copy.deepcopy(raw)
    payload = '<script>alert("x")</script>|[link](javascript:alert(1))'
    unsafe_summary["result"]["text"] = payload
    unsafe_summary["result"]["implications"][0]["text"] = payload
    unsafe_report = ReportData.from_dict(unsafe_summary)
    for baseline, rendered in (
        (
            artifact,
            render_artifact(unsafe_report, ""),
        ),
        (render_markdown(report), render_markdown(unsafe_report)),
    ):
        assert_unchanged_scripts(baseline, rendered)
        assert "&lt;script&gt;" in rendered, (
            "Escaping removed summary or choice evidence."
        )
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
