"""Deterministic contracts for authored target assessments and observed behavior."""

import copy
import html
import json
from dataclasses import asdict, replace
from html.parser import HTMLParser

from reporting.attention import parse_attention
from reporting.explanation import parse_explanation
from reporting.load import load_report
from reporting.render_html import render_artifact
from reporting.render_markdown import render_markdown
from reporting.schema import ReportData
from reporting.summary import (
    EditIntentData,
    build_intent,
    build_summary,
    parse_narrative,
)
from reporting.target import (
    UNAVAILABLE,
    effective_purpose,
    parse_purpose,
    parse_target,
)


def _answers(report):
    return {
        side: {
            trial.name: trial.final for trial in getattr(report.variants, side).trials
        }
        for side in ("before", "after")
    }


def _assert_presentation(reports):
    for name in (
        "target-baseline",
        "target-persists",
        "target-mixed",
        "target-insufficient",
        "target-preservation",
        "target-additional",
        "target-lost-exception",
    ):
        report = reports[name]
        for rendered in (render_artifact(report, ""), render_markdown(report)):
            plain = html.unescape(rendered).replace("\\", "")
            assert report.decisions.narrative.headline in plain
            assert report.summary.why.text in plain
            for side in (report.summary.before, report.summary.after):
                assert all(choice.label in plain for choice in side.choices)
            assert "Based on final answers" in plain
        artifact = render_artifact(report, "")
        table = artifact.split('<div class="target-checks">', 1)[1].split(
            "</table>", 1
        )[0]
        assert "<a " not in table and "<svg" not in table
        assert artifact.count('class="summary-card ') == 2
        assert ("target-result-changed" in table) == (name == "target-mixed")
        markdown = render_markdown(report)
        row = next(
            line
            for line in markdown.splitlines()
            if line.startswith("| Customer claims")
        )
        assert ("**" in row) == (name == "target-mixed")
        if name == "target-mixed":
            assert "No (3/3) → Yes (2/3); No (1/3)" in html.unescape(table)
        if name == "target-insufficient":
            assert "Not enough evidence (3/3)" in html.unescape(table)
            assert "Yes (" not in table and "No (" not in table

    baseline = reports["target-baseline"]
    criterion = baseline.decisions.target_assessment.criteria[0]
    uncertain = replace(
        criterion,
        after=(replace(criterion.after[0], outcome="uncertain"),) + criterion.after[1:],
    )
    report = replace(
        baseline,
        decisions=replace(
            baseline.decisions,
            target_assessment=replace(
                baseline.decisions.target_assessment, criteria=(uncertain,)
            ),
        ),
    )
    for rendered in (render_artifact(report, ""), render_markdown(report)):
        plain = html.unescape(rendered).replace("\\", "")
        assert "Yes (2/3); Unclear (1/3)" in plain
    table = render_artifact(report, "").split('<div class="target-checks">', 1)[1]
    table = table.split("</table>", 1)[0]
    assert "<strong" not in table

    lost = reports["target-lost-exception"]
    for rendered in (render_artifact(lost, ""), render_markdown(lost)):
        plain = html.unescape(rendered).replace("\\", "")
        finding = lost.decisions.attention.findings[0]
        assert finding.title in plain
        assert finding.consequence in plain
        assert finding.next_step in plain
        assert "No (3/3) → No (3/3)" in plain


def _assert_human_first_explanation(report):
    raw = json.loads(json.dumps(asdict(report.decisions.explanation)))
    raw["examples"] = [
        {
            "side": "before",
            "trial": "before-1",
            "text": report.variants.before.trials[0].final.strip(),
        }
    ]
    explanation = parse_explanation(raw, report.decisions.rows, _answers(report))
    assert explanation is not None
    explained = replace(
        report, decisions=replace(report.decisions, explanation=explanation)
    )
    for rendered in (render_artifact(explained, ""), render_markdown(explained)):
        plain = html.unescape(rendered).replace("\\", "")
        explanation_view = plain.split('id="panel-explanation"', 1)[1]
        assessment_position = explanation_view.index("What we checked")
        assert explanation_view.index(explanation.headline) < assessment_position
        for step in explanation.steps:
            assert explanation_view.index(step.title) < assessment_position

    class RawEvidence(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.in_explanation = False

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if attrs.get("id", "").startswith("panel-"):
                self.in_explanation = attrs["id"] == "panel-explanation"
            if tag == "pre" and self.in_explanation:
                assert any(
                    name == "details" and "open" not in entry
                    for name, entry in self.stack
                ), "Raw explanation evidence must be hidden by default."
            if tag not in ("input", "br", "hr", "meta", "link", "img", "path", "use"):
                self.stack.append((tag, attrs))

        def handle_endtag(self, tag):
            for index in range(len(self.stack) - 1, -1, -1):
                if self.stack[index][0] == tag:
                    del self.stack[index:]
                    break

    RawEvidence().feed(render_artifact(explained, ""))
    RawEvidence().feed(render_markdown(explained))


def assert_target_reports(reports, root, assert_round_trip):
    expected = {
        "target-baseline": ("met", "met"),
        "target-persists": ("not_met", "not_met"),
        "target-mixed": ("not_met", "mixed"),
        "target-insufficient": ("unassessable", "unassessable"),
        "target-preservation": ("met", "met"),
        "target-additional": ("met", "met"),
    }
    for name, (before, after) in expected.items():
        report = reports[name]
        assert_round_trip(report.to_dict())
        target = report.decisions.target_assessment
        assert target is not None
        criterion = target.criteria[0]
        assert all(value.outcome == before for value in criterion.before)
        if after == "mixed":
            assert [value.outcome for value in criterion.after] == [
                "met",
                "met",
                "not_met",
            ]
        else:
            assert all(value.outcome == after for value in criterion.after)
        assert len(report.decisions.recorded_evidence) == 12
        assert report.decisions.evidence_limits.per_excerpt_characters == 4096
    persistent = reports["target-persists"]
    finding = persistent.decisions.attention.findings[0]
    assert (
        finding.status == "pre_existing_problem" and finding.relationship == "expected"
    )
    assert finding.criterion == "export-qualification"
    assert not persistent.decisions.rows[finding.decision - 1].diverges
    assert reports["target-baseline"].decisions.attention.findings == ()
    additional = reports["target-additional"].decisions.attention.findings[0]
    assert (
        additional.status == "observed_difference"
        and additional.relationship == "unclear"
    )
    assert additional.criterion is None
    assert "publication" in additional.limit
    additional_report = reports["target-additional"]
    hypothetical = replace(
        additional_report.decisions.attention,
        findings=(replace(additional, status="hypothetical_consequence"),),
    )
    parsed = parse_attention(
        json.loads(json.dumps(asdict(hypothetical))),
        additional_report.decisions.rows,
        target=additional_report.decisions.target_assessment,
    )
    assert parsed is not None and parsed.findings[0].relationship == "unclear"
    _assert_purpose_conclusion(reports["target-baseline"], assert_round_trip)
    _assert_presentation(reports)
    _assert_human_first_explanation(reports["target-baseline"])
    _assert_invalid_assessments(reports["target-baseline"])
    _assert_attention_gate(persistent)
    _assert_goal_modes(reports["target-baseline"])
    _assert_missing_records(reports["target-baseline"])
    _assert_legacy(reports["target-baseline"])
    _assert_saved_provenance(reports["target-baseline"], root / "target-baseline")
    _assert_legacy_attention(reports["attention-mixed"])
    _assert_normalization(persistent, root / "target-persists")


def _assert_purpose_conclusion(report, assert_round_trip):
    text = (
        "Both versions already qualify the export limits, so these trials show no "
        "additional accuracy benefit from requiring verification. After changes the "
        "description of scope, but that wording change does not establish better "
        "handling of misleading summaries on other tasks."
    )
    raw = json.loads(json.dumps(asdict(report.decisions.narrative)))
    raw["decision"] = 2
    raw["headline"] = "Both versions qualify the export limits."
    for side in ("before", "after"):
        raw[side]["choices"] = [
            {
                "choice": choice.choice,
                "label": "Qualified export claim",
                "detail": choice.choice,
            }
            for choice in getattr(report.decisions.rows[1], side)
        ]
    raw["why"] = {"text": text, "decisions": [2, 5]}
    narrative = parse_narrative(raw, report.decisions.rows)
    assert narrative is not None
    decisions = replace(report.decisions, narrative=narrative)
    summary = build_summary(report.metadata, report.variants, decisions)
    concluded = replace(report, decisions=decisions, summary=summary)
    assert_round_trip(concluded.to_dict())
    without_assessment = replace(decisions, target_assessment=None)
    observed = replace(
        concluded,
        decisions=without_assessment,
        summary=build_summary(report.metadata, report.variants, without_assessment),
    )
    for specimen in (concluded, observed):
        for rendered in (render_artifact(specimen, ""), render_markdown(specimen)):
            plain = html.unescape(rendered).replace("\\", "")
            assert text in plain, (
                "An unchanged observation must retain its supported conclusion."
            )
            assert raw["headline"] in plain
    incomplete = build_summary(
        report.metadata, report.variants, replace(decisions, dropped=1)
    )
    assert incomplete.why is None, (
        "Incomplete evidence must not present the full conclusion."
    )
    raw["why"]["text"] = text + "x" * 481
    assert parse_narrative(raw, report.decisions.rows) is None


def _assert_invalid_assessments(report):
    raw = json.loads(json.dumps(asdict(report.decisions.target_assessment)))
    goals = report.decisions.purpose
    answers = _answers(report)
    evidence = report.decisions.recorded_evidence

    def parse(value, records=evidence):
        return parse_target(value, goals, answers, records, report.decisions.rows)

    assert parse(raw) == report.decisions.target_assessment
    invalid = [False, [], {}, {"criteria": []}, {**raw, "extra": True}]
    for field, values in (
        ("goal", (True, 0, 2)),
        ("mode", ("future",)),
        ("evidence_kind", ("truth",)),
        ("decisions", ([True], [99], [2, 2])),
        ("text", ("", "x" * 601, "<script>bad</script>")),
        ("required_evidence", ("",)),
    ):
        for value in values:
            changed = copy.deepcopy(raw)
            changed["criteria"][0][field] = value
            invalid.append(changed)
    for field, values in (
        ("trial", ("after-1", "before-foreign", "before-1 ")),
        ("outcome", ("failed", "", False)),
        (
            "refs",
            (
                ["after-1:answer"],
                ["before-1:tool-999"],
                ["before-1:answer"] * 2,
                [],
                ["before-1:answer"],
            ),
        ),
        ("explanation", ("", "bad\x00text")),
        ("output_excerpt", ("Invented output text.", "", "x" * 1201)),
    ):
        for value in values:
            changed = copy.deepcopy(raw)
            changed["criteria"][0]["before"][0][field] = value
            invalid.append(changed)
    changed = copy.deepcopy(raw)
    changed["criteria"][0]["before"][1] = changed["criteria"][0]["before"][0]
    invalid.append(changed)
    changed = copy.deepcopy(raw)
    changed["criteria"][0]["after"].pop()
    invalid.append(changed)
    changed = copy.deepcopy(raw)
    changed["criteria"].append(changed["criteria"][0])
    invalid.append(changed)
    for changed in invalid:
        assert parse(changed) is None, (
            "Invalid target membership or refs became assessed evidence."
        )
    omitted = tuple(
        replace(entry, status="omitted", text="", reason="Synthetic content omitted")
        for entry in evidence
    )
    assert parse(raw, omitted) is None, "Unavailable source cannot prove consistency."
    unavailable = copy.deepcopy(raw)
    for side in ("before", "after"):
        for trial in unavailable["criteria"][0][side]:
            trial["outcome"] = "unassessable"
            trial["explanation"] = (
                "The draft is observed, but the required source content is unavailable."
            )
    assert parse(unavailable, omitted) is not None
    output = copy.deepcopy(raw["criteria"][0])
    output.update(
        id="written-qualification",
        text="Does the draft state the export limit?",
        required_evidence="The final draft's exact wording.",
        evidence_kind="output",
    )
    for side in ("before", "after"):
        for trial in output[side]:
            trial["refs"] = [trial["trial"] + ":answer"]
    separate = parse({"criteria": [output, unavailable["criteria"][0]]}, omitted)
    assert separate is not None
    for side in ("before", "after"):
        assert all(t.outcome == "met" for t in getattr(separate.criteria[0], side))
        assert all(
            t.outcome == "unassessable" for t in getattr(separate.criteria[1], side)
        )
    conflicting = copy.deepcopy(raw)
    conflicting["criteria"][0]["after"][0]["outcome"] = "uncertain"
    conflicting["criteria"][0]["after"][0]["explanation"] = (
        "Two recorded sources disagree; the output is observed but consistency remains uncertain."
    )
    assessed = parse(conflicting)
    assert assessed is not None and assessed.criteria[0].after[0].outcome == "uncertain"
    assert assessed.criteria[0].after[1].outcome == "met", (
        "One uncertain claim must not erase supported trials."
    )


def _assert_attention_gate(report):
    raw = json.loads(json.dumps(asdict(report.decisions.attention)))
    rows = report.decisions.rows
    target = report.decisions.target_assessment
    assert parse_attention(raw, rows, target=target) == report.decisions.attention
    assert parse_attention(raw, rows) is None, (
        "Unchanged attention needs assessed target outcomes."
    )
    for field, value in (
        ("criterion", None),
        ("criterion", "foreign"),
        ("status", "observed_difference"),
        ("relationship", "additional"),
    ):
        changed = copy.deepcopy(raw)
        changed["findings"][0][field] = value
        assert parse_attention(changed, rows, target=target) is None
    criterion = target.criteria[0]
    met = replace(
        criterion,
        after=tuple(replace(trial, outcome="met") for trial in criterion.after),
    )
    assert parse_attention(raw, rows, target=replace(target, criteria=(met,))) is None
    unrelated = replace(criterion, decisions=(1,))
    assert (
        parse_attention(raw, rows, target=replace(target, criteria=(unrelated,)))
        is None
    )


def _assert_goal_modes(report):
    raw = json.loads(json.dumps(asdict(report.decisions.target_assessment)))
    for mode in ("correction", "new", "change", "preservation"):
        raw["criteria"][0]["mode"] = mode
        assert (
            parse_target(
                raw,
                report.decisions.purpose,
                _answers(report),
                report.decisions.recorded_evidence,
                report.decisions.rows,
            )
            is not None
        )
    goals = report.decisions.purpose + (
        replace(
            report.decisions.purpose[0], text="Retain the supported query exception."
        ),
    )
    assert (
        parse_target(
            raw,
            goals,
            _answers(report),
            report.decisions.recorded_evidence,
            report.decisions.rows,
        )
        is None
    )
    other = copy.deepcopy(raw["criteria"][0])
    other.update(
        id="query-exception", goal=2, text="Retain the supported query exception."
    )
    raw["criteria"].append(other)
    assert (
        parse_target(
            raw,
            goals,
            _answers(report),
            report.decisions.recorded_evidence,
            report.decisions.rows,
        )
        is not None
    )
    diff_goals = effective_purpose((), EditIntentData("Qualify claims.", (1,)))
    assert diff_goals[0].source == "diff" and diff_goals[0].basis == "inferred"
    assert effective_purpose((), None) == (), (
        "Observed outputs must not manufacture a fallback purpose."
    )
    fallback = replace(
        report.decisions, purpose=(), intent=EditIntentData("Qualify claims.", (1,))
    )
    assert (
        build_intent("An unrelated legacy expectation.", fallback).source == "inferred"
    )
    purpose = {"goals": [asdict(report.decisions.purpose[0])]}
    for changed in (
        {"goals": [dict(purpose["goals"][0], source="diff", basis="explicit")]},
        {"goals": [dict(purpose["goals"][0], text="bad\x00text")]},
        {
            "goals": [
                purpose["goals"][0],
                dict(purpose["goals"][0], text=purpose["goals"][0]["text"].upper()),
            ]
        },
    ):
        try:
            parse_purpose(changed)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid immutable purpose accepted.")


def _assert_missing_records(report):
    extra = replace(
        report.variants.after.trials[0],
        name="after-missing",
        final="",
        verdict="BLOCKED",
    )
    after = replace(
        report.variants.after,
        total=4,
        blocked=1,
        trials=report.variants.after.trials + (extra,),
    )
    variants = replace(report.variants, after=after)
    summary = build_summary(report.metadata, variants, report.decisions)
    assert summary.after.total == 4
    incomplete = replace(report, variants=variants, summary=summary)
    for rendered in (render_artifact(incomplete, ""), render_markdown(incomplete)):
        plain = html.unescape(rendered).replace("\\", "")
        assert "Yes (3/4); Not assessed (1/4)" in plain
        assert "No (1/4)" not in plain
    assert summary.why is None
    assert summary.status == "unavailable"


def _assert_legacy(report):
    raw = report.to_dict()
    raw["schema_version"] = 11
    for name in (
        "purpose",
        "target_assessment",
        "recorded_evidence",
        "evidence_limits",
    ):
        raw["decisions"].pop(name)
    raw["intent"] = asdict(
        build_intent(
            raw["content"]["expected"],
            replace(report.decisions, purpose=(), target_assessment=None),
        )
    )
    legacy = ReportData.from_dict(json.loads(json.dumps(raw)))
    assert legacy.schema_version == 12
    assert legacy.decisions.target_assessment is None
    assert legacy.variants == report.variants
    assert UNAVAILABLE in legacy.summary.notices


def _assert_saved_provenance(report, run):
    config_path = run / "config.json"
    config_text = config_path.read_text()
    source_path = run / "before-1/project/implementation.txt"
    source_text = source_path.read_text()
    try:
        config = json.loads(config_text)
        config["purpose"]["goals"][0]["text"] = (
            "An unrelated goal supplied after seeing outcomes."
        )
        config_path.write_text(json.dumps(config))
        source_path.write_text(
            "Current file content is NOT the content received by the trial."
        )
        loaded = load_report(run, run, "synthetic/authored", config_path)
        assert loaded.decisions.purpose == report.decisions.purpose
        assert loaded.decisions.recorded_evidence == report.decisions.recorded_evidence
        assert loaded.decisions.target_assessment == report.decisions.target_assessment
        assert "Current file content" not in render_artifact(loaded, "")
        assert html.escape(source_text) in render_artifact(loaded, "")
    finally:
        config_path.write_text(config_text)
        source_path.write_text(source_text)


def _assert_legacy_attention(report):
    raw = report.to_dict()
    raw["schema_version"] = 11
    for name in (
        "purpose",
        "target_assessment",
        "recorded_evidence",
        "evidence_limits",
    ):
        raw["decisions"].pop(name)
    for finding in raw["decisions"]["attention"]["findings"]:
        finding.pop("status")
        finding.pop("criterion")
    legacy = ReportData.from_dict(raw)
    assert legacy.decisions.attention == report.decisions.attention
    assert legacy.decisions.target_assessment is None
    assert UNAVAILABLE in legacy.summary.notices


def _assert_normalization(report, run):
    from decisions import normalize
    from reporting.evidence import collect_run_evidence

    raw = json.loads((run / "extraction.json").read_text())
    purpose = {"goals": [asdict(goal) for goal in report.decisions.purpose]}
    answers = _answers(report)
    names = {side: list(records) for side, records in answers.items()}
    evidence = collect_run_evidence(run)
    normalized = normalize(
        raw, names, final_answers=answers, purpose=purpose, recorded_evidence=evidence
    )
    assert normalized["target_assessment"] == json.loads(
        json.dumps(asdict(report.decisions.target_assessment))
    )
    remapped = copy.deepcopy(raw)
    remapped["chain"].insert(0, {"decision": "Malformed synthetic row"})
    remapped["target_assessment"]["criteria"][0]["decisions"] = [3]
    remapped["attention"]["findings"][0]["decision"] = 3
    remapped["outcome"] += 1
    remapped["summary"]["decision"] += 1
    normalized = normalize(
        remapped,
        names,
        final_answers=answers,
        purpose=purpose,
        recorded_evidence=evidence,
    )
    assert normalized["target_assessment"]["criteria"][0]["decisions"] == [2]
    assert normalized["attention"]["findings"][0]["decision"] == 2
    assert normalized["dropped"] == 1
    invalid = copy.deepcopy(raw)
    invalid["target_assessment"]["criteria"][0]["after"][0]["refs"] = [
        "before-1:answer"
    ]
    normalized = normalize(
        invalid,
        names,
        final_answers=answers,
        purpose=purpose,
        recorded_evidence=evidence,
    )
    assert normalized["target_assessment"] is None
    assert normalized["attention"] is None, (
        "Unchanged concern outlived its invalid target support."
    )
    assert normalized["chain"] and normalized["recorded_evidence"]
