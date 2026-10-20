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
from presentation_contract import (  # noqa: E402
    assert_summary_detail_links,
    assert_version_labels,
)


def synthetic_raw():
    raw = {
        "schema_version": 19,
        "metadata": {
            "model": "synthetic/model",
            "mode": "review",
            "vocab": "generic",
            "trace_source": "captured",
            "target_file": "AGENTS.md",
            "before_label": "current file",
            "after_label": "your change applied",
            "source": None,
            "ci_context": None,
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
        purpose=[],
        purpose_summary=None,
        target_rejection=None,
        recorded_evidence=[],
        target_assessment=None,
        evidence_limits=None,
        scenario_record=None,
    )
    return derive_summary(raw)


def derive_summary(raw):
    """Recompute the derived Summary and intent after changing saved decisions."""
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


def assert_rejected(raw):
    try:
        ReportData.from_dict(raw)
    except ValueError:
        pass
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


SCENARIO_PURPOSE = [
    {
        "text": "Answers name the evidence they reviewed.",
        "source": "session",
        "basis": "explicit",
        "reference": "Synthetic owner request before trials",
    }
]


def scenario_record(payload=""):
    """A synthetic record frozen before trials; payload exercises escaping."""
    return {
        "summary": "Two synthetic file reviews must say what they read." + payload,
        "rationale": "The task hides the reviewed file behind a search step." + payload,
        "conditions": [
            "Both versions receive the same synthetic file." + payload,
            "No network access is available.",
        ],
        "limitations": ["One synthetic task only." + payload],
        "checks": [
            {
                "id": "names-evidence",
                "goal": 1,
                "text": "The final answer names the reviewed file." + payload,
                "mode": "new",
                "required_evidence": "The exact final answer." + payload,
                "evidence_kind": "output",
            }
        ],
        "source_requirements": [],
    }


def scenario_target(record, after_outcome="met"):
    """Outcomes for exactly the frozen checks, cited from exact final answers."""
    finals = {
        "before": ("Before first answer", "Before second answer"),
        "after": ("After first answer", "After second answer"),
    }

    def side(name, outcome):
        return [
            {
                "trial": f"{name}-{number}",
                "outcome": outcome,
                "refs": [f"{name}-{number}:answer"],
                "explanation": "Synthetic assessment of the exact answer.",
                "output_excerpt": answer,
            }
            for number, answer in enumerate(finals[name], 1)
        ]

    return {
        "criteria": [
            {
                **check,
                "decisions": [2],
                "before": side("before", "not_met"),
                "after": side("after", after_outcome),
                "rejection": None,
            }
            for check in record["checks"]
        ]
    }


def scenario_raw(raw, record, target, rejection=None):
    changed = copy.deepcopy(raw)
    changed["decisions"].update(
        purpose=copy.deepcopy(SCENARIO_PURPOSE),
        scenario_record=record,
        target_assessment=target,
        target_rejection=rejection,
    )
    return derive_summary(changed)


def assert_rejected_at(raw, field):
    try:
        ReportData.from_dict(raw)
    except ValueError as error:
        assert field in str(error), (field, str(error))
    else:
        raise AssertionError(f"invalid {field} was accepted")


def _between(page, start, end):
    return page[page.index(start) : page.index(end, page.index(start))]


def _plain_text(markup):
    return html.unescape(re.sub(r"<[^>]+>", "", markup))


def assert_scenario_record_contract(raw):
    """Frozen records round-trip strictly, bind the target, and stay visible."""
    from reporting import load
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown
    from reporting.scenario import ScenarioData
    from reporting.summary import FINDING_HEADLINES, UNMET

    record = scenario_record()
    frozen = assert_round_trip(scenario_raw(raw, record, scenario_target(record)))
    assert isinstance(frozen.decisions.scenario_record, ScenarioData)
    assert frozen.decisions.scenario_record.conditions == tuple(record["conditions"])
    assert [check.text for check in frozen.summary.checks] == [
        record["checks"][0]["text"]
    ]
    assert frozen.summary.state == "improved"
    page = render_artifact(frozen, "")
    markdown = render_markdown(frozen)
    expectation = _between(page, "story-expectation", "story-method")
    method = _between(page, "story-method", "story-evidence")
    evidence = _between(page, "story-evidence", "story-next")
    assert content.FROZEN_CHECKS_LABEL in expectation
    assert content.ASSESSOR_CHECKS_LABEL not in page
    assert content.FROZEN_UNASSESSED_MEANING not in page
    for heading, text in (
        (content.SUMMARY_SCENARIO_HEADING, record["summary"]),
        (content.SUMMARY_RATIONALE_HEADING, record["rationale"]),
        (content.SUMMARY_CONDITIONS_HEADING, record["conditions"][0]),
        (content.SUMMARY_DATA_HEADING, record["limitations"][0]),
        (content.SUMMARY_TASK_LABEL, raw["content"]["task"]),
    ):
        assert heading in method and html.escape(text) in method, heading
        assert heading in markdown, heading
        # The blinded quiz keeps Step 4; preparation text must stay outside it.
        assert html.escape(text) not in evidence, heading
    assert content.SCENARIO_UNRECORDED not in page
    assert content.FROZEN_CHECKS_LABEL in markdown

    missing = copy.deepcopy(frozen.to_dict())
    del missing["decisions"]["scenario_record"]
    assert_rejected_at(missing, "scenario_record")
    malformed = []
    for key, value in (
        ("extra", "field"),
        ("summary", "x" * 401),
        ("conditions", []),
        ("limitations", "One synthetic task only."),
        ("checks", []),
    ):
        broken = copy.deepcopy(record)
        broken[key] = value
        malformed.append(broken)
    for key, value in (
        ("goal", 2),
        ("goal", True),
        ("mode", "future"),
        ("evidence_kind", "anything"),
        ("id", " names-evidence"),
        ("text", "<b>markup</b>"),
    ):
        broken = copy.deepcopy(record)
        broken["checks"][0][key] = value
        malformed.append(broken)
    duplicate = copy.deepcopy(record)
    duplicate["checks"].append(copy.deepcopy(duplicate["checks"][0]))
    malformed.append(duplicate)
    padded = copy.deepcopy(record)
    padded["summary"] = " " + padded["summary"]
    # A saved report must hold the canonical record, not merely a parseable one.
    for broken in (*malformed, padded):
        tampered = copy.deepcopy(frozen.to_dict())
        tampered["decisions"]["scenario_record"] = broken
        assert_rejected(tampered)
    unpurposed = copy.deepcopy(frozen.to_dict())
    unpurposed["decisions"]["purpose"] = []
    assert_rejected(unpurposed)

    # A target must restate every frozen check exactly; nothing is substituted.
    for field, value in (
        ("text", "A looser restatement of the check."),
        ("required_evidence", "Any evidence."),
        ("mode", "change"),
        ("evidence_kind", "recorded_action"),
        ("id", "other-check"),
    ):
        tampered = copy.deepcopy(frozen.to_dict())
        tampered["decisions"]["target_assessment"]["criteria"][0][field] = value
        assert_rejected_at(tampered, "target_assessment")
    extra = copy.deepcopy(frozen.to_dict())
    added = copy.deepcopy(extra["decisions"]["target_assessment"]["criteria"][0])
    added["id"] = "assessor-added"
    extra["decisions"]["target_assessment"]["criteria"].append(added)
    assert_rejected_at(extra, "target_assessment")

    # Without a valid assessment, frozen checks stay visible and decide nothing.
    for rejection in (None, "target criterion must restate its frozen scenario check"):
        unassessed = assert_round_trip(scenario_raw(raw, record, None, rejection))
        assert unassessed.summary.checks == ()
        assert unassessed.summary.state == "unavailable"
        heading = content.summary_heading(unassessed)
        assert heading != UNMET
        assert unassessed.summary.headline == FINDING_HEADLINES["unavailable"]
        assert [item.kind for item in content.summary_open_items(unassessed)] == [
            "unassessed"
        ]
        page = render_artifact(unassessed, "")
        markdown = render_markdown(unassessed)
        expectation = _between(page, "story-expectation", "story-method")
        for text in (
            content.FROZEN_CHECKS_LABEL,
            content.FROZEN_UNASSESSED_MEANING,
            html.escape(record["checks"][0]["text"]),
            html.escape(
                content.required_evidence_text(
                    unassessed.decisions.scenario_record.checks[0]
                )
            ),
        ):
            assert text in expectation, text
        assert content.FROZEN_UNASSESSED_NOTE in _plain_text(expectation)
        assert 'data-state="unassessed"' in expectation
        assert expectation.count(content.FROZEN_UNASSESSED) >= 2
        assert UNMET not in page
        assert f'id="{content.target_criterion_anchor(1)}"' in page
        assert f'href="#{content.target_criterion_anchor(1)}"' in page
        assert f'<a id="{content.target_criterion_anchor(1)}"></a>' in markdown

    # Assessor-written criteria without a frozen record are labeled as such.
    legacy_raw = scenario_raw(raw, None, scenario_target(record))
    legacy = assert_round_trip(legacy_raw)
    assert legacy.decisions.scenario_record is None
    page = render_artifact(legacy, "")
    assert content.ASSESSOR_CHECKS_LABEL in _between(
        page, "story-expectation", "story-method"
    )
    assert content.FROZEN_CHECKS_LABEL not in page
    assert html.escape(content.SCENARIO_UNRECORDED) in _between(
        page, "story-method", "story-evidence"
    )
    assert content.ASSESSOR_CHECKS_LABEL in render_markdown(legacy)
    unrecorded = ReportData.from_dict(raw)
    page = render_artifact(unrecorded, "")
    assert html.escape(content.SCENARIO_UNRECORDED) in page
    assert "expected-checks" not in page

    # Every new record field is escaped in both formats.
    payload = ' Compare A & B when x < 3 > 1 "quoted" | piped.'
    unsafe_record = scenario_record(payload)
    for target in (scenario_target(unsafe_record), None):
        unsafe = assert_round_trip(scenario_raw(raw, unsafe_record, target))
        page = render_artifact(unsafe, "")
        markdown = render_markdown(unsafe)
        assert "x < 3" not in page and "A & B" not in page
        assert page.count("x &lt; 3 &gt; 1 &quot;quoted&quot; | piped") >= 6
        assert "x < 3" not in markdown and "A & B" not in markdown
        assert markdown.count('x &lt; 3 &gt; 1 "quoted" &#124; piped') >= 6
        assert_unchanged_scripts(render_artifact(frozen, ""), page)

    # Loading binds the configuration's record; persisted tampering rejects the target.
    config = {"purpose": {"goals": SCENARIO_PURPOSE}, "scenario_record": record}
    canonical = load._scenario_record(config)
    assert canonical == frozen.decisions.scenario_record
    assert load._scenario_record({"scenario_record": None}) is None
    for broken in (*malformed, None):
        try:
            load._scenario_record(
                {"purpose": config["purpose"], "scenario_record": broken}
                if broken is not None
                else {"scenario_record": record}
            )
        except ValueError:
            pass
        else:
            raise AssertionError("a malformed configured scenario was accepted")
    finals = {
        side: {trial["name"]: trial["final"] for trial in variant["trials"]}
        for side, variant in raw["variants"].items()
    }
    persisted_target = scenario_target(record)
    for criterion in persisted_target["criteria"]:
        criterion["decisions"] = []

    def convert(**changes):
        saved = {
            "chain": [],
            "purpose": copy.deepcopy(SCENARIO_PURPOSE),
            "target_assessment": copy.deepcopy(persisted_target),
            "scenario_record": copy.deepcopy(record),
            **changes,
        }
        return load._convert_decisions(
            saved,
            2,
            2,
            "",
            final_answers=finals,
            purpose=config["purpose"],
            scenario=canonical,
        )

    bound = convert()
    assert bound.target_assessment is not None and bound.target_rejection is None
    assert bound.scenario_record == canonical
    without_key = {
        "chain": [],
        "purpose": copy.deepcopy(SCENARIO_PURPOSE),
        "target_assessment": copy.deepcopy(persisted_target),
    }
    assert (
        load._convert_decisions(
            without_key,
            2,
            2,
            "",
            final_answers=finals,
            purpose=config["purpose"],
            scenario=canonical,
        ).target_assessment
        is not None
    )
    changed_record = copy.deepcopy(record)
    changed_record["checks"][0]["text"] = "A check rewritten after the trials."
    changed_goals = copy.deepcopy(SCENARIO_PURPOSE)
    changed_goals[0]["text"] = "A goal rewritten after the trials."
    for changes in (
        {"scenario_record": changed_record},
        {"scenario_record": None},
        {"purpose": changed_goals},
    ):
        rejected = convert(**changes)
        assert rejected.target_assessment is None, changes
        assert rejected.target_rejection == load.SCENARIO_MISMATCH, changes
        assert rejected.purpose == canonical_goals(config), changes
        assert rejected.scenario_record == canonical
    restated = copy.deepcopy(persisted_target)
    restated["criteria"][0]["text"] = "A looser restatement of the check."
    rejected = convert(target_assessment=restated)
    assert rejected.target_assessment is None and rejected.target_rejection
    unconfigured = load._convert_decisions(
        {
            "chain": [],
            "purpose": copy.deepcopy(SCENARIO_PURPOSE),
            "target_assessment": copy.deepcopy(persisted_target),
            "scenario_record": copy.deepcopy(record),
        },
        2,
        2,
        "",
        final_answers=finals,
        purpose=config["purpose"],
        scenario=None,
    )
    assert unconfigured.target_assessment is None
    assert unconfigured.target_rejection == load.SCENARIO_MISMATCH
    assert unconfigured.scenario_record is None


def canonical_goals(config):
    from reporting.target import parse_purpose

    return parse_purpose(config["purpose"])


def summary_narrative(context=None, before_start=None, after_start=None):
    """Synthetic Summary copy for the action row of synthetic_raw()."""
    return {
        "decision": 1,
        "headline": "After reads and tests the file in both trials.",
        "scenario": "Review a synthetic file without changing it.",
        "context": context,
        "evidence_kind": "actions",
        "before": {
            "icon": "inspect",
            "start": before_start,
            "choices": [
                {
                    "choice": "read only",
                    "label": "Reads only",
                    "detail": "The record reads the file.",
                },
                {
                    "choice": "search",
                    "label": "Searches",
                    "detail": "The record searches the file.",
                },
            ],
        },
        "after": {
            "icon": "test",
            "start": after_start,
            "choices": [
                {
                    "choice": "read and test",
                    "label": "Reads and tests",
                    "detail": "The records read the file and run tests.",
                }
            ],
        },
        "why": {
            "text": "A reviewer sees recorded tests, not only a file read.",
            "decisions": [1],
        },
        "caution": None,
    }


def assert_summary_context_and_starts(raw):
    """Optional Summary context and starts stay cited, exact, and dispensable."""
    import decisions as extractor
    from reporting.load import load_report
    from reporting.schema import EvidenceClaimData
    from reporting.summary import build_summary, parse_narrative

    report = ReportData.from_dict(raw)
    rows = report.decisions.rows
    context = {
        "text": "The task calls the file unchanged; every answer explains the review.",
        "decisions": [2],
    }
    shared = {"text": "Answers explain the review result", "decisions": [2]}
    supported = summary_narrative(context, shared, shared)
    narrative = parse_narrative(supported, rows)
    assert narrative.context.text == context["text"]
    assert narrative.context.decisions == (2,)
    for side in (narrative.before, narrative.after):
        assert side.start.text == shared["text"] and side.start.decisions == (2,)
    without_starts = replace(
        narrative,
        before=replace(narrative.before, start=None),
        after=replace(narrative.after, start=None),
    )
    plain = parse_narrative(summary_narrative(), rows)
    assert plain == replace(without_starts, context=None)

    # Unsupported optional claims are omitted; validated comparisons remain.
    for unsupported in (
        dict(context, decisions=[3]),
        dict(context, decisions=[]),
        dict(context, decisions=[True]),
        dict(context, decisions=[2, 2]),
        dict(context, decisions="2"),
        dict(context, text="x" * 481),
        dict(context, text="<b>Conflict</b>"),
        {"decisions": [2]},
        "The task conflicts with the records.",
    ):
        omitted = parse_narrative(summary_narrative(unsupported, shared, shared), rows)
        assert omitted == replace(narrative, context=None), unsupported
    # Row 1 splits Before across branches, so it cannot start every Before trial.
    split = {"text": "Reads the file", "decisions": [1]}
    partial = parse_narrative(summary_narrative(context, split, shared), rows)
    assert partial == replace(narrative, before=replace(narrative.before, start=None))
    # Coverage is checked per side: the same row is one full After branch.
    lead_after = parse_narrative(summary_narrative(context, shared, split), rows)
    assert lead_after.after.start.decisions == (1,)
    for unsupported in (
        dict(shared, decisions=[1, 2]),
        dict(shared, decisions=[]),
        dict(shared, decisions=[3]),
        dict(shared, decisions=[False]),
        dict(shared, text="x" * 81),
        "Answers explain the review result",
    ):
        omitted = parse_narrative(
            summary_narrative(context, unsupported, unsupported), rows
        )
        assert omitted == without_starts, unsupported
    # A cited branch must name exactly the attributed lead trials on that side.
    action, answer = rows
    subset = replace(answer.before[0], count=1, trials=("before-1",))
    renamed = replace(answer.before[0], trials=("before-1", "before-3"))
    unattributed = replace(action.before[0], trials=())
    for variant in (
        (action, replace(answer, before=(subset,))),
        (action, replace(answer, before=(renamed,))),
        (replace(action, before=(unattributed, action.before[1])), answer),
    ):
        changed = parse_narrative(supported, variant)
        assert changed.before.start is None
        assert changed.after.start == narrative.after.start
    aggregate = tuple(
        replace(
            row,
            before=tuple(replace(choice, trials=()) for choice in row.before),
            after=tuple(replace(choice, trials=()) for choice in row.after),
        )
        for row in rows
    )
    assert parse_narrative(supported, aggregate) == without_starts

    def narrated(value, **changes):
        decisions = replace(report.decisions, narrative=value, **changes)
        summary = build_summary(report.metadata, report.variants, decisions)
        return replace(report, decisions=decisions, summary=summary)

    full = narrated(narrative)
    assert full.summary.context == EvidenceClaimData(context["text"], (2,))
    for side in (full.summary.before, full.summary.after):
        assert side.start == EvidenceClaimData(shared["text"], (2,))
    full_raw = full.to_dict()
    assert_round_trip(full_raw)
    absent = narrated(plain)
    absent_raw = absent.to_dict()
    assert_round_trip(absent_raw)
    # Missing claims serialize as explicit nulls rather than disappearing.
    for value in (absent_raw["decisions"]["narrative"], absent_raw["summary"]):
        assert value["context"] is None
        assert value["before"]["start"] is None and value["after"]["start"] is None
    incomplete = narrated(narrative, dropped=1).summary
    assert incomplete.context is None
    assert incomplete.before.start is None and incomplete.after.start is None

    canonical = (
        "invalid report-data field decisions.narrative: "
        "expected valid canonical narrative"
    )
    derived = (
        "invalid report-data field summary: "
        "expected summary derived from the validated decision and trial evidence"
    )
    missing = object()
    for path, value, message in (
        ("decisions.narrative.before.start.decisions", [1], canonical),
        ("decisions.narrative.context.decisions", [3], canonical),
        ("decisions.narrative.context", missing, canonical),
        ("decisions.narrative.after.start", missing, canonical),
        ("summary.context", None, derived),
        ("summary.context.text", "An invented conflict.", derived),
        ("summary.before.start", None, derived),
        ("summary.after.start.decisions", [1], derived),
        (
            "summary.after.start.decisions",
            [1, 2],
            "invalid report-data field summary.after.start.decisions: "
            "expected exactly one decision row index",
        ),
        (
            "summary.context.decisions",
            [9],
            "invalid report-data field summary.context[0].decisions[0]: "
            "expected 1-based decision row index",
        ),
        (
            "summary.context",
            missing,
            "invalid report-data field summary.context: expected present field",
        ),
        (
            "summary.before.start",
            missing,
            "invalid report-data field summary.before.start: expected present field",
        ),
    ):
        changed = copy.deepcopy(full_raw)
        *parents, name = path.split(".")
        target = changed
        for key in parents:
            target = target[key]
        if value is missing:
            del target[name]
        else:
            target[name] = value
        assert_rejected(changed)
    # A Summary claim cannot appear without a validated narrative claim.
    for parents in ((), ("after",)):
        invented = copy.deepcopy(raw)
        target = invented["summary"]
        for key in parents:
            target = target[key]
        target["start" if parents else "context"] = dict(shared)
        assert_rejected(invented)

    # Extraction remaps sorted references and keeps the same canonical narrative.
    completed = {"before": ["before-1", "before-2"], "after": ["after-1", "after-2"]}
    chain = [
        {
            "decision": "State result",
            "topic": "Delivery",
            "anchor": "answer",
            "before": [{"choice": "explain", "trials": completed["before"]}],
            "after": [{"choice": "explain", "trials": completed["after"]}],
        },
        {
            "decision": "Use evidence",
            "topic": "Evidence",
            "anchor": 2,
            "before": [
                {"choice": "read only", "trials": ["before-1"]},
                {"choice": "search", "trials": ["before-2"]},
            ],
            "after": [{"choice": "read and test", "trials": completed["after"]}],
        },
    ]
    reply_summary = dict(
        summary_narrative(
            dict(context, decisions=[1]),
            dict(shared, decisions=[1]),
            dict(shared, decisions=[1]),
        ),
        decision=2,
        why=dict(summary_narrative()["why"], decisions=[2]),
    )
    reply = {"chain": chain, "outcome": 1, "summary": reply_summary}
    normalized = extractor.normalize(reply, completed)
    saved = normalized["summary"]
    assert saved == json.loads(json.dumps(asdict(narrative)))
    unattributed_row = {
        "decision": "Unattributed row",
        "anchor": 1,
        "before": [{"choice": "partial", "trials": ["before-1"]}],
        "after": [{"choice": "partial", "trials": completed["after"]}],
    }
    degraded_summary = dict(
        reply_summary,
        context=dict(context, decisions=[3]),
        before=dict(reply_summary["before"], start=dict(shared, decisions=[2])),
    )
    degraded = extractor.normalize(
        dict(reply, chain=[*chain, unattributed_row], summary=degraded_summary),
        completed,
    )
    assert degraded["dropped"] == 1
    assert degraded["chain"] == normalized["chain"]
    expected = dict(saved, context=None, before=dict(saved["before"], start=None))
    assert degraded["summary"] == expected

    # Saved decisions without the newer optional keys still load their comparison.
    legacy = copy.deepcopy(normalized)
    del legacy["summary"]["context"]
    for side in ("before", "after"):
        del legacy["summary"][side]["start"]
    with tempfile.TemporaryDirectory() as directory:
        run = Path(directory)
        names = [*completed["before"], *completed["after"]]
        (run / "task.md").write_text("Review a synthetic file without changing it.")
        (run / "config.json").write_text('{"mode":"review","vocab":"generic"}')
        (run / "grades.tsv").write_text(
            "".join(f"{name}\tREVIEW\t-\n" for name in names)
        )
        for name in names:
            (run / name).mkdir()
            (run / name / "trace.jsonl").write_text(
                json.dumps({"type": "result", "result": f"Synthetic answer {name}."})
            )
        for saved_decisions, expected in ((legacy, plain), (normalized, narrative)):
            (run / "decisions.json").write_text(json.dumps(saved_decisions))
            loaded = load_report(run, run, "synthetic/model", run / "config.json")
            assert loaded.decisions.narrative == expected
            for value, source in (
                (loaded.summary.context, expected.context),
                (loaded.summary.before.start, expected.before.start),
                (loaded.summary.after.start, expected.after.start),
            ):
                assert (value and asdict(value)) == (source and asdict(source))
            assert_round_trip(loaded.to_dict())


def assert_purpose_summary_contract(raw):
    """A plain summary of frozen goals never replaces purpose, intent, or evidence."""
    import decisions as extractor
    from reporting.load import load_report

    goals = [
        {
            "text": "Report every difference between the synthetic files.",
            "source": "session",
            "basis": "explicit",
            "reference": "Synthetic request before trials",
        },
        {
            "text": "Keep the review read-only.",
            "source": "diff",
            "basis": "inferred",
            "reference": "Synthetic instruction diff",
        },
    ]
    paraphrase = "Report every file difference and keep the review read-only."
    recorded_intent = {
        "text": " ".join(goal["text"] for goal in goals),
        "source": "purpose",
        "edit_hunks": [],
    }
    purposed = copy.deepcopy(raw)
    purposed["decisions"].update(purpose=goals, purpose_summary=paraphrase)
    purposed["intent"] = recorded_intent
    report = assert_round_trip(purposed)
    assert report.decisions.purpose_summary == paraphrase
    # The full recorded intent and each goal's provenance stay unchanged.
    assert asdict(report.intent) == {**recorded_intent, "edit_hunks": ()}
    assert [asdict(goal) for goal in report.decisions.purpose] == goals
    absent = copy.deepcopy(purposed)
    absent["decisions"]["purpose_summary"] = None
    assert assert_round_trip(absent).intent == report.intent

    invalid = (
        "invalid report-data field decisions.purpose_summary: "
        "expected plain summary of recorded purpose goals"
    )
    for value in (
        " " + paraphrase,
        "x" * 321,
        "Report differences.\nKeep it read-only.",
        "**Report** every difference.",
        "<b>Report</b> every difference.",
        "",
        1,
        False,
        [paraphrase],
    ):
        changed = copy.deepcopy(purposed)
        changed["decisions"]["purpose_summary"] = value
        assert_rejected(changed)
    # Without frozen goals a summary cannot appear, even as a paraphrase.
    unfrozen = copy.deepcopy(raw)
    unfrozen["decisions"]["purpose_summary"] = paraphrase
    assert_rejected(unfrozen)
    missing = copy.deepcopy(purposed)
    del missing["decisions"]["purpose_summary"]
    assert_rejected(missing)

    # Saved decisions keep observations whether the summary is valid, absent, or not.
    completed = {"before": ["before-1", "before-2"], "after": ["after-1", "after-2"]}
    reply = {
        "chain": [
            {
                "decision": "State result",
                "topic": "Delivery",
                "anchor": "answer",
                "before": [{"choice": "explain", "trials": completed["before"]}],
                "after": [{"choice": "explain", "trials": completed["after"]}],
            }
        ],
        "outcome": 1,
        "purpose_summary": paraphrase,
    }
    saved = extractor.normalize(reply, completed, purpose={"goals": goals})
    assert saved["purpose_summary"] == paraphrase
    assert saved["purpose"] == goals
    legacy = dict(saved)
    del legacy["purpose_summary"]
    with tempfile.TemporaryDirectory() as directory:
        run = Path(directory)
        names = [*completed["before"], *completed["after"]]
        (run / "task.md").write_text("Review a synthetic file without changing it.")
        (run / "config.json").write_text(
            json.dumps(
                {"mode": "review", "vocab": "generic", "purpose": {"goals": goals}}
            )
        )
        (run / "grades.tsv").write_text(
            "".join(f"{name}\tREVIEW\t-\n" for name in names)
        )
        for name in names:
            (run / name).mkdir()
            (run / name / "trace.jsonl").write_text(
                json.dumps({"type": "result", "result": f"Synthetic answer {name}."})
            )
        rows = None
        for saved_decisions, expected in (
            (saved, paraphrase),
            (legacy, None),
            (dict(saved, purpose_summary="<b>Report</b> differences."), None),
            (dict(saved, purpose_summary="x" * 321), None),
            # Configuration goals cannot adopt a summary saved without its goals.
            (dict(saved, purpose=[]), None),
        ):
            (run / "decisions.json").write_text(json.dumps(saved_decisions))
            loaded = load_report(run, run, "synthetic/model", run / "config.json")
            assert loaded.decisions.purpose_summary == expected
            assert [asdict(goal) for goal in loaded.decisions.purpose] == goals
            assert loaded.intent == report.intent
            rows = rows or loaded.decisions.rows
            assert rows and loaded.decisions.rows == rows
            assert loaded.decisions.outcome == 1
            assert_round_trip(loaded.to_dict())


def assert_derived_summary_claims(reports):
    """Starts cite one full lead branch; the conclusion follows validated target checks."""
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown
    from reporting import summary as finding
    from reporting.summary import build_summary

    for name, report in reports.items():
        summary = report.summary
        for side in ("before", "after"):
            start = getattr(summary, side).start
            if start is None:
                continue
            lead = getattr(report.decisions.rows[summary.decision - 1], side)
            cited = getattr(report.decisions.rows[start.decisions[0] - 1], side)
            members = {trial for branch in lead for trial in branch.trials}
            assert len(start.decisions) == len(cited) == 1, name
            assert members and set(cited[0].trials) == members, name

    report = reports["target-baseline"]
    target = report.decisions.target_assessment

    def assessed(before="met", after="met", mode=None, variants=None, drop=False):
        """Set every outcome per side; optionally change mode, health or coverage."""
        criteria = []
        for criterion in target.criteria:
            sides = {
                side: tuple(
                    replace(trial, outcome=outcome)
                    for trial in getattr(criterion, side)
                )
                for side, outcome in (("before", before), ("after", after))
            }
            if drop:
                sides["after"] = sides["after"][1:]
            criteria.append(replace(criterion, mode=mode or criterion.mode, **sides))
        decisions = replace(
            report.decisions,
            target_assessment=replace(target, criteria=tuple(criteria)),
        )
        changed = replace(
            report, decisions=decisions, variants=variants or report.variants
        )
        return replace(
            changed,
            summary=build_summary(changed.metadata, changed.variants, decisions),
        )

    from presentation_contract import visible_text as visible

    assert all(c.mode != "preservation" for c in target.criteria)
    interrupted = replace(
        report.variants,
        before=replace(
            report.variants.before,
            blocked=1,
            valid=report.variants.before.total - 1,
        ),
    )
    cases = (
        (assessed(), "already_met"),
        (assessed(before="not_met"), "improved"),
        (assessed(after="not_met"), "not_met"),
        (assessed(before="not_met", after="not_met"), "not_met"),
        (assessed(after="unassessable"), "inconclusive"),
        (assessed(after="uncertain"), "inconclusive"),
        (assessed(drop=True), "inconclusive"),
        (assessed(before="uncertain"), "baseline_incomplete"),
        # An interrupted Before never turns a met After into an improvement.
        (assessed(before="not_met", variants=interrupted), "baseline_incomplete"),
        (assessed(mode="preservation"), "preserved"),
        (assessed(after="not_met", mode="preservation"), "not_met"),
        (
            assessed(before="not_met", after="not_met", mode="preservation"),
            "not_met",
        ),
        (
            assessed(before="uncertain", after="not_met", mode="preservation"),
            "not_met",
        ),
        (
            assessed(before="unassessable", after="not_met", mode="preservation"),
            "not_met",
        ),
        (assessed(before="not_met", mode="preservation"), "improved"),
        (assessed(before="uncertain", mode="preservation"), "baseline_incomplete"),
        (assessed(before="unassessable", mode="preservation"), "baseline_incomplete"),
        (
            assessed(mode="preservation", variants=interrupted),
            "baseline_incomplete",
        ),
    )
    for value, state in cases:
        summary = value.summary
        preservation = (
            value.decisions.target_assessment.criteria[0].mode == "preservation"
        )
        assert summary.state == state, (state, summary.state)
        assert {check.state for check in summary.checks} == {state}, state
        assert summary.next_action == finding.NEXT_ACTIONS[state], state
        if preservation and state == "not_met":
            # A requested preservation does not establish a previously met baseline.
            ordinary_failure = assessed(after="not_met").summary
            assert tuple(check.meaning for check in summary.checks) == tuple(
                check.meaning for check in ordinary_failure.checks
            )
        answers_only = any(
            check.scope == finding.CHECK_SCOPES["output"] for check in summary.checks
        )
        expected = (
            finding.PRESERVATION_UNMET
            if state == "not_met" and preservation
            else finding.FINDING_HEADLINES[state]
        )
        if state in finding.MET_STATES and answers_only:
            # Met answer checks never read as proof that actions happened.
            expected += " " + finding.ANSWER_SCOPED
        assert summary.headline == expected, state
        criteria = value.decisions.target_assessment.criteria
        # A dropped assessment is invalid saved data; it is exercised in memory only.
        if all(len(c.after) == value.variants.after.total for c in criteria):
            assert_round_trip(value.to_dict())
        # Every export carries the same derived conclusion and per-check results.
        pages = (render_artifact(value, ""), render_markdown(value))
        for page in map(visible, pages):
            for text in (
                summary.headline,
                summary.meaning,
                summary.next_action,
                finding.GATE_NOTE,
                *(
                    part
                    for check in summary.checks
                    for part in (
                        check.text,
                        check.before,
                        check.after,
                        check.meaning,
                        check.scope,
                    )
                ),
            ):
                assert text in page, (state, text)
        assert value.to_dict()["summary"]["state"] == state

    # Every frozen goal needs a check; an uncovered goal blocks a met conclusion.
    extra_goal = replace(report.decisions.purpose[0], text="Synthetic extra goal.")
    uncovered = replace(
        report.decisions, purpose=report.decisions.purpose + (extra_goal,)
    )
    gap = build_summary(report.metadata, report.variants, uncovered)
    assert gap.state == "inconclusive"
    assert f"recorded goal {len(uncovered.purpose)}." in gap.meaning

    # A miss stays a miss when the extracted behavior does not diverge at all.
    same = assessed(after="not_met")
    rows = tuple(replace(row, after=row.before) for row in same.decisions.rows)
    assert report.decisions.before_count == report.decisions.after_count
    flat = replace(same.decisions, rows=rows, narrative=None)
    flat_summary = build_summary(same.metadata, same.variants, flat)
    assert flat_summary.state == "not_met" and flat_summary.headline == finding.UNMET

    # No validated target: the conclusion is unavailable, never inferred from rows.
    missing = replace(report.decisions, target_assessment=None)
    unavailable = build_summary(report.metadata, report.variants, missing)
    assert unavailable.state == "unavailable" and not unavailable.checks
    rejected = build_summary(
        report.metadata,
        report.variants,
        replace(missing, target_rejection="synthetic validation reason"),
    )
    assert rejected.meaning.endswith(": synthetic validation reason.")
    # Model narrative never sets the conclusion.
    assert unavailable.headline == finding.FINDING_HEADLINES["unavailable"]

    assert_goal_focus(report, assessed, uncovered, missing)


def _focus_markup(page):
    """Return (status, heading, finding-step plain text, open kinds) from HTML."""
    from attention_contract import _ReportMarkup, _plain

    markup = _ReportMarkup(page)
    summary = markup.select(anchor="panel-summary")[0]
    status = markup.select(summary, class_name="summary-status")[0]
    heading = markup.select(summary, class_name="summary-headline")[0]
    step = markup.select(summary, class_name="story-finding")[0]
    kinds = [
        entry["attrs"].get("data-kind")
        for listing in markup.select(step, class_name="summary-open-list")
        for entry in markup.select(listing, tag="li")
    ]
    return status, _plain(heading).strip(), _plain(step), kinds


def assert_goal_focus(report, assessed, uncovered, missing):
    """The first screen names the change, the result and the open requirement.

    The presentation heading may differ from the canonical finding headline, but
    the badge state, open items and diagnostics must follow validated state only.
    """
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown
    from reporting.summary import build_summary
    from presentation_contract import visible_text as visible

    def rebuilt(decisions):
        return replace(
            report,
            decisions=decisions,
            summary=build_summary(report.metadata, report.variants, decisions),
        )

    def check(value):
        summary = value.summary
        heading = content.summary_heading(value)
        text, diagnostic = content.summary_result(value)
        items = content.summary_open_items(value)
        html_page = render_artifact(value, "")
        status, shown, step, kinds = _focus_markup(html_page)
        assert status["attrs"].get("data-state") == summary.state
        assert content.summary_status(value) in visible(html_page)
        assert shown == heading
        # The canonical finding stays visible even when a presentation heading leads.
        for page in (visible(html_page), visible(render_markdown(value))):
            assert heading in page and summary.headline in page
            if diagnostic:
                assert diagnostic in page
        assert kinds == [item.kind for item in items]
        for item in items:
            assert item.text in step
        return summary, heading, text, diagnostic, items

    # Lead comparison changed, but no validated target: the change is shown,
    # the result stays "not checked" and never reads as a pass.
    # The fixture's lead is unchanged; rename only its After choices so the same
    # trial memberships now record a different answer.
    lead = rebuilt(replace(missing, narrative=None)).summary.decision
    assert lead is not None
    rows = list(missing.rows)
    rows[lead - 1] = replace(
        rows[lead - 1],
        after=tuple(
            replace(choice, choice="Synthetic changed answer " + str(number))
            for number, choice in enumerate(rows[lead - 1].after, 1)
        ),
    )
    # Narrative labels describe the old choices; the conclusion never uses them.
    missing = replace(missing, rows=tuple(rows), narrative=None)
    unavailable = rebuilt(missing)
    assert unavailable.summary.decision == lead
    summary, heading, text, diagnostic, items = check(unavailable)
    row = unavailable.decisions.rows[summary.decision - 1]
    assert summary.state == "unavailable" and not summary.checks
    assert content.decision_status(row) == "Changed"
    assert row.topic in heading and heading != summary.headline
    change = content.summary_change(unavailable)
    assert change is not None and row.topic in change.scope
    for (_, side_text), side in zip(change.sides, (row.before, row.after)):
        assert all(choice.choice in side_text for choice in side)
    assert diagnostic == summary.meaning and summary.meaning not in text
    assert items and {item.kind for item in items} == {"unchecked"}
    assert all(item.criterion is None for item in items)
    rejected = rebuilt(replace(missing, target_rejection="synthetic reason"))
    assert content.summary_status(rejected) == content.summary_status(unavailable)
    assert "synthetic reason" in check(rejected)[3]
    # An optional topic may be blank; the heading then names the required
    # extracted decision label, never an empty or generic subject.
    untitled_rows = list(missing.rows)
    untitled_rows[lead - 1] = replace(untitled_rows[lead - 1], topic="")
    untitled = rebuilt(replace(missing, rows=tuple(untitled_rows)))
    untitled_heading = check(untitled)[1]
    untitled_row = untitled.decisions.rows[lead - 1]
    assert untitled_row.decision.strip()
    assert untitled_heading.startswith(untitled_row.decision)
    assert untitled_heading != untitled.summary.headline

    # A process change never hides a missed goal: the finding leads verbatim and
    # every missed criterion is named and linked to its check.
    failed = assessed(after="not_met")
    summary, heading, text, diagnostic, items = check(failed)
    assert summary.state == "not_met" and heading == summary.headline
    assert summary.meaning in text and diagnostic is None
    missed = [item for item in items if item.kind == "not_met"]
    assert [item.criterion for item in missed] == [
        number
        for number, check_ in enumerate(summary.checks, 1)
        if check_.state == "not_met"
    ]
    page = render_artifact(failed, "")
    for item in missed:
        assert f'href="#{content.target_criterion_anchor(item.criterion)}"' in page

    # Met checks plus an unchecked goal: only the unchecked goal stays open.
    met = assessed().decisions
    partial = rebuilt(replace(met, purpose=uncovered.purpose))
    summary, heading, text, diagnostic, items = check(partial)
    assert summary.state == "inconclusive"
    assert any(c.state in content.MET_STATES for c in summary.checks)
    assert [item.text for item in items if item.kind == "unchecked"] == [
        uncovered.purpose[-1].text
    ]
    assert all(
        item.criterion is None
        or summary.checks[item.criterion - 1].state not in content.MET_STATES
        for item in items
    )

    # No lead comparison and no recorded purpose: an honest fallback, not a pass.
    bare = rebuilt(replace(missing, purpose=(), rows=(), narrative=None, outcome=None))
    summary, heading, text, diagnostic, items = check(bare)
    assert summary.state == "unavailable"
    assert heading == summary.headline
    assert content.summary_change(bare) is None
    assert [item.text for item in items] == [content.SUMMARY_AIM_UNCHECKED]


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
        assert fallback.why is None

    mixed_primary = reports["mixed-primary"]
    assert mixed_primary.decisions.narrative is not None
    assert mixed_primary.summary.decision == mixed_primary.decisions.outcome, (
        "A unanimous secondary action must not displace a mixed primary-result narrative."
    )
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
    incomplete = build_summary(
        mixed_primary.metadata,
        mixed_primary.variants,
        replace(primary_decisions, dropped=1),
    )
    assert incomplete.status == "unavailable"
    assert incomplete.why is None
    missing_primary = build_summary(
        mixed_primary.metadata,
        mixed_primary.variants,
        replace(primary_decisions, outcome=None),
    )
    assert missing_primary.decision == primary_decisions.narrative.decision
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
        narrative=replace(
            changed.decisions.narrative,
            why=replace(changed.decisions.narrative.why, text=payload),
        ),
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
        md_card = markdown.split(f"#### {side.capitalize()}\n", 1)[1]
        # The card ends before the next Summary section or its meaning claim.
        for boundary in (
            "#### ",
            "### ",
            f"**{content.SUMMARY_MEANING_LABEL}",
            content.SUMMARY_INTERPRETATION_UNAVAILABLE,
        ):
            md_card = md_card.split(boundary, 1)[0]
        md_cards[side] = md_card.replace(r"\-", "-")
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
        # Only the configured record is shown; no other case gains one afterward.
        for name, report in reports.items():
            record = report.decisions.scenario_record
            assert (record is not None) == (name == "target-lost-exception"), name
        frozen = reports["target-lost-exception"].decisions
        assert [criterion.id for criterion in frozen.target_assessment.criteria] == [
            check.id for check in frozen.scenario_record.checks
        ]
        frozen_page = (root / "target-lost-exception" / "report.html").read_text()
        assert content.FROZEN_CHECKS_LABEL in frozen_page
        assert content.ASSESSOR_CHECKS_LABEL not in frozen_page
        assert (
            content.ASSESSOR_CHECKS_LABEL
            in (root / "target-mixed" / "report.html").read_text()
        )
        assert_visual_summaries(reports)
        assert_derived_summary_claims(reports)
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
        assert_summary_detail_links(reports)
        assert_version_labels(reports)

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
        assert_rejected(specimen)
    empty = copy.deepcopy(raw)
    empty["decisions"]["trial_summaries"] = []
    assert assert_round_trip(empty).decisions.trial_summaries == ()
    missing = copy.deepcopy(raw)
    del missing["decisions"]["trial_summaries"]
    assert_rejected(missing)
    assert_rejected(dict(raw, schema_version=7))


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
    assert_summary_context_and_starts(raw)
    assert_purpose_summary_contract(raw)
    assert_scenario_record_contract(raw)
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

    assert_rejected(dict(raw, schema_version=1))
    assert_rejected(dict(raw, schema_version=2))
    assert_rejected(dict(raw, schema_version=3))
    assert_rejected(dict(raw, schema_version=9))
    assert_rejected(dict(raw, schema_version=10))
    # Earlier report-data shapes are rejected; saved runs regenerate from decisions.
    for version in (11, 12, 13, 14, 15, 16, 17, 18):
        assert_rejected(dict(raw, schema_version=version))
    assert_rejected(dict(raw, schema_version=True))
    assert_rejected(dict(raw, schema_version=1.0))

    invalid_commands = copy.deepcopy(raw)
    invalid_commands["variants"]["before"]["trials"][0]["commands"] = "read AGENTS.md"
    assert_rejected(invalid_commands)
    invalid_model = copy.deepcopy(raw)
    invalid_model["metadata"]["model"] = ["synthetic/model"]
    assert_rejected(invalid_model)
    invalid_count = copy.deepcopy(raw)
    invalid_count["command_flow"]["before"]["paths"][0]["count"] = True
    assert_rejected(invalid_count)
    invalid_suffix = copy.deepcopy(raw)
    invalid_suffix["variants"]["after"]["count_suffix"] = True
    assert_rejected(invalid_suffix)
    invalid_result_kind = copy.deepcopy(raw)
    invalid_result_kind["result"]["kind"] = "future"
    assert_rejected(invalid_result_kind)
    invalid_result_kind_type = copy.deepcopy(raw)
    invalid_result_kind_type["result"]["kind"] = None
    assert_rejected(invalid_result_kind_type)
    for heading in ("outcome_heading", "behavior_heading"):
        missing_heading = copy.deepcopy(raw)
        del missing_heading["result"][heading]
        assert_rejected(missing_heading)
        invalid_heading = copy.deepcopy(raw)
        invalid_heading["result"][heading] = None
        assert_rejected(invalid_heading)
    invalid_evidence = copy.deepcopy(raw)
    invalid_evidence["result"]["implications"][0]["decisions"] = [99]
    assert_rejected(invalid_evidence)

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
