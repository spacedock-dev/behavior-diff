"""Consumer contracts for authored synthetic attention assessments."""

import copy
import html
import json
from dataclasses import replace
from html.parser import HTMLParser


class _ReportMarkup(HTMLParser):
    """Collect rendered subtrees so contracts inspect presentation, not source."""

    def __init__(self, markup):
        super().__init__()
        self.root = {"tag": "root", "attrs": {}, "children": [], "text": []}
        self.stack = [self.root]
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "children": [], "text": []}
        self.stack[-1]["children"].append(node)
        if tag not in ("br", "hr", "img", "input", "meta", "link", "wbr"):
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack[-1]["tag"] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break

    def handle_data(self, text):
        for node in self.stack:
            node["text"].append(text)

    @staticmethod
    def nodes(node):
        yield node
        for child in node["children"]:
            yield from _ReportMarkup.nodes(child)

    def select(self, node=None, *, class_name=None, anchor=None, tag=None):
        return [
            item
            for item in self.nodes(self.root if node is None else node)
            if (
                class_name is None
                or class_name in item["attrs"].get("class", "").split()
            )
            and (anchor is None or item["attrs"].get("id") == anchor)
            and (tag is None or item["tag"] == tag)
        ]


def _plain(node):
    return "".join(node["text"])


def _rejected_report(raw):
    from reporting.schema import ReportData

    try:
        ReportData.from_dict(raw)
    except ValueError:
        pass
    else:
        raise AssertionError("Canonical report accepted malformed attention data.")


def _assert_rendered_attention(report):
    from reporting import content
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown

    markup = _ReportMarkup(render_artifact(report, ""))
    summary = markup.select(anchor="panel-summary")[0]
    attention = markup.select(summary, class_name="story-attention")[0]
    explanation = markup.select(anchor="panel-explanation")[0]
    detail = markup.select(explanation, anchor="attention-explanation")[0]
    assert not markup.select(attention, tag="pre")
    for link in markup.select(attention, tag="a"):
        href = link["attrs"].get("href", "")
        assert href.startswith("#") and markup.select(anchor=href[1:])
    md_plain = html.unescape(render_markdown(report)).replace("\\", "")
    summary_text, detail_text = _plain(attention), _plain(detail)
    data = report.decisions.attention
    findings = () if data is None else data.findings
    assert bool(markup.select(attention, class_name="attention-unavailable")) == (
        data is None
    )
    original = report.decisions.explanation
    if original is not None:
        for text in (
            original.headline,
            original.overview,
            *(
                text
                for step in original.steps
                for text in (step.title, step.before, step.after, step.meaning)
            ),
            *(claim.text for claim in (*original.unchanged, *original.limits)),
        ):
            assert text in _plain(explanation)
    for finding in findings:
        for text in (
            finding.title,
            finding.consequence,
            finding.next_step,
            finding.limit,
        ):
            assert text in summary_text and text in md_plain
        assert finding.matters_if in summary_text + detail_text
        assert finding.explanation in detail_text and finding.explanation in md_plain
        for claim in finding.context:
            assert claim.text in detail_text and claim.text in md_plain
        if finding.evidence_kind == "actions":
            evidence = (
                "Self-reported actions, not independently captured command evidence"
                if report.metadata.trace_source == "self-reported"
                else "Recorded actions, not proof of successful execution"
            )
        elif finding.evidence_kind == "plans":
            evidence = "Plans in the answers, not observed execution"
        else:
            evidence = "Final answers, not proof of execution"
        assert evidence in summary_text
        row = report.decisions.rows[finding.decision - 1]
        deeper = next(
            node
            for node in markup.select(
                detail, class_name="attention-explanation-finding"
            )
            if finding.title in _plain(node)
        )
        for side in ("before", "after"):
            evidence_side = markup.select(
                deeper, class_name=f"attention-evidence-{side}"
            )[0]
            branches = markup.select(
                evidence_side, class_name="attention-evidence-branch"
            )
            choices = getattr(row, side)
            assert len(branches) == len(choices)
            total = getattr(report.decisions, f"{side}_count")
            for branch, choice in zip(branches, choices):
                assert choice.choice in _plain(branch)
                count_text = content.trial_count(choice.count, total)
                assert count_text in _plain(branch) and count_text in md_plain
                links = markup.select(branch, tag="a")
                if choice.trials:
                    assert [_plain(link) for link in links] == list(choice.trials)
                    for name in choice.trials:
                        target = content.trial_anchor(side, name)
                        assert any(
                            link["attrs"].get("href") == f"#{target}" for link in links
                        )
                        assert markup.select(anchor=target)
                else:
                    assert not links
                    assert content.ATTENTION_MEMBERSHIP_UNAVAILABLE in _plain(branch)
        for side in (finding.before, finding.after):
            for choice in side:
                for step in choice.steps:
                    assert step.label in summary_text + detail_text
                    assert step.label in md_plain
        for disclosure in markup.select(deeper, tag="details"):
            assert "open" not in disclosure["attrs"]
    return summary_text, detail_text


def _assert_validation(report, assert_round_trip):
    from reporting.attention import ATTENTION_ICONS, parse_attention

    rows = report.decisions.rows
    valid = report.to_dict()["decisions"]["attention"]
    assert parse_attention(valid, rows) == report.decisions.attention
    assert parse_attention(None, rows) is None
    assert parse_attention({}, rows) is None
    empty = {
        "assessment": "Synthetic assessment completed without a finding.",
        "findings": [],
    }
    assert parse_attention(empty, rows).findings == ()
    empty_report = report.to_dict()
    empty_report["decisions"]["attention"] = empty
    assert assert_round_trip(empty_report).decisions.attention.findings == ()
    null_report = report.to_dict()
    null_report["decisions"]["attention"] = None
    assert assert_round_trip(null_report).decisions.attention is None
    missing = report.to_dict()
    del missing["decisions"]["attention"]
    _rejected_report(missing)

    malformed = [
        None,
        False,
        [],
        {},
        {"assessment": "", "findings": []},
        dict(empty, extra=True),
    ]
    for field, value in (
        ("assessment", "x" * 601),
        ("assessment", "<script>synthetic</script>"),
        ("findings", "not findings"),
        ("findings", [False]),
        ("findings", [valid["findings"][0]] * 2),
    ):
        malformed.append(dict(valid, **{field: value}))
    for field, values in (
        ("decision", (True, 0, -1, 99, 3)),
        (
            "title",
            (
                "",
                "x" * 121,
                "<img src=x onerror=alert(1)>",
                "bad\x00text",
                "bad\x85text",
            ),
        ),
        ("evidence_kind", ("future", "plans")),
        ("relationship", ("future",)),
        ("status", ("future", None)),
        ("criterion", ("foreign-target", True)),
        ("explanation", ("x" * 601,)),
        ("matters_if", ("x" * 481,)),
        ("next_step", ("https://invalid.example/execute",)),
        (
            "context",
            (
                [{"text": "Synthetic context.", "decisions": [99]}],
                [{"text": "Synthetic context.", "decisions": [True]}],
                [{"text": "Synthetic context.", "decisions": [1, 1]}],
            ),
        ),
    ):
        for value in values:
            bad = copy.deepcopy(valid)
            bad["findings"][0][field] = value
            malformed.append(bad)
    for side in ("before", "after"):
        for branches in (
            [],
            valid["findings"][0][side][:1],
            valid["findings"][0][side] + valid["findings"][0][side][:1],
        ):
            bad = copy.deepcopy(valid)
            bad["findings"][0][side] = branches
            malformed.append(bad)
        bad = copy.deepcopy(valid)
        bad["findings"][0][side][0]["choice"] = "Invented branch"
        malformed.append(bad)
        for field, value in (("count", 99), ("trials", ["after-invented"])):
            bad = copy.deepcopy(valid)
            bad["findings"][0][side][0][field] = value
            malformed.append(bad)
        for field, value in (
            ("icon", "<svg onload=alert(1)>"),
            ("icon", "https://invalid.example/icon"),
            ("label", "<script>synthetic</script>"),
            ("label", "x" * 81),
        ):
            bad = copy.deepcopy(valid)
            bad["findings"][0][side][0]["steps"][0][field] = value
            malformed.append(bad)
        for length in (0, 1, 3):
            bad = copy.deepcopy(valid)
            step = bad["findings"][0][side][0]["steps"][0]
            bad["findings"][0][side][0]["steps"] = [step] * length
            malformed.append(bad)
    for raw in malformed:
        assert parse_attention(raw, rows) is None, raw
        if raw is not None:
            canonical = report.to_dict()
            canonical["decisions"]["attention"] = raw
            _rejected_report(canonical)

    # Distribution evidence, not the extractor's changed flag, governs eligibility.
    changed = replace(rows[0], diverges=False)
    assert parse_attention(valid, (changed, *rows[1:])) is not None
    unchanged = replace(rows[0], after=rows[0].before)
    matching = copy.deepcopy(valid)
    matching["findings"][0]["after"] = matching["findings"][0]["before"]
    assert parse_attention(matching, (unchanged, *rows[1:])) is None
    proportional = replace(
        rows[0],
        after=tuple(
            replace(choice, count=choice.count * 2) for choice in rows[0].before
        ),
    )
    assert parse_attention(matching, (proportional, *rows[1:])) is None
    for side in ("before", "after"):
        invalid_row = replace(rows[0], **{side: ()})
        assert parse_attention(valid, (invalid_row, *rows[1:])) is None
        invalid_row = replace(
            rows[0], **{side: (replace(getattr(rows[0], side)[0], count=0),)}
        )
        assert parse_attention(valid, (invalid_row, *rows[1:])) is None
    for icon in ATTENTION_ICONS:
        supported = copy.deepcopy(valid)
        supported["findings"][0]["before"][0]["steps"][0]["icon"] = icon
        assert parse_attention(supported, rows) is not None

    plan = copy.deepcopy(valid)
    plan["findings"] = [plan["findings"][1]]
    assert parse_attention(plan, rows).findings[0].evidence_kind == "plans"
    plan["findings"][0]["evidence_kind"] = "actions"
    assert parse_attention(plan, rows) is None
    # No fixed finding cap may hide otherwise valid distinct comparisons.
    many_rows, many_findings = [], []
    for index in range(1, 9):
        many_rows.append(rows[0])
        finding = copy.deepcopy(valid["findings"][0])
        finding["decision"] = index
        finding["context"] = []
        many_findings.append(finding)
    many = parse_attention(dict(valid, findings=many_findings), tuple(many_rows))
    assert many is not None and len(many.findings) == 8


def _assert_pipeline(report, run):
    import decisions
    from reporting.load import load_report

    path = run / "decisions.json"
    original = path.read_text()
    saved = json.loads(original)
    extraction = json.loads((run / "extraction.json").read_text())
    names = {
        side: [trial.name for trial in getattr(report.variants, side).trials]
        for side in ("before", "after")
    }
    normalized = decisions.normalize(extraction, names, hunk_count=1)
    valid = saved["attention"]
    assert normalized["attention"] == valid
    remapped = copy.deepcopy(extraction)
    remapped["chain"].insert(0, {"decision": "Invalid synthetic comparison."})
    for finding in remapped["attention"]["findings"]:
        finding["decision"] += 1
        for claim in finding["context"]:
            claim["decisions"] = [index + 1 for index in claim["decisions"]]
    moved = decisions.normalize(remapped, names, hunk_count=1)
    assert moved["attention"] == valid, (
        "Attention and related context must follow surviving rows."
    )
    assert len(moved["chain"]) == len(saved["chain"])
    lost_context = copy.deepcopy(remapped)
    lost_context["attention"]["findings"][0]["context"][0]["decisions"] = [1]
    assert decisions.normalize(lost_context, names, hunk_count=1)["attention"] is None
    try:
        for malformed in (
            None,
            {},
            dict(valid, findings=[False]),
            dict(valid, assessment="<script>bad</script>"),
        ):
            normalized = decisions.normalize(
                dict(extraction, attention=malformed), names, hunk_count=1
            )
            assert normalized["attention"] is None
            assert normalized["chain"] == saved["chain"]
            saved["attention"] = malformed
            path.write_text(json.dumps(saved))
            loaded = load_report(run, run, "synthetic/authored", run / "config.json")
            assert loaded.decisions.attention is None
            assert loaded.decisions.rows == report.decisions.rows
            assert loaded.variants == report.variants
        del saved["attention"]
        path.write_text(json.dumps(saved))
        loaded = load_report(run, run, "synthetic/authored", run / "config.json")
        assert (
            loaded.decisions.attention is None
            and loaded.decisions.rows == report.decisions.rows
        )
        for malformed in (
            None,
            "not a list",
            [],
            [""],
            ["before-unknown"],
            ["after-1"],
            ["before-1", "before-1"],
            ["before-1"],
        ):
            invalid = json.loads(original)
            invalid["chain"][0]["before"][0]["trials"] = malformed
            path.write_text(json.dumps(invalid))
            loaded = load_report(run, run, "synthetic/authored", run / "config.json")
            assert loaded.decisions.rows == ()
            assert loaded.decisions.attention is None, (
                "Malformed saved attribution must fail closed, never guess support."
            )
    finally:
        path.write_text(original)


def assert_attention_reports(
    reports, root, assert_round_trip, assert_evidence_links, assert_unchanged_scripts
):
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown

    expected = {
        "attention-mixed": 1,
        "attention-self-reported": 1,
        "attention-plans": 1,
        "attention-quiet": 0,
        "attention-unavailable": None,
        "attention-multiple": 2,
    }
    displays = {}
    for name, count in expected.items():
        report = reports[name]
        attention = report.decisions.attention
        assert (None if attention is None else len(attention.findings)) == count, name
        assert assert_round_trip(report.to_dict()) == report
        assert_evidence_links(report)
        for row in report.decisions.rows:
            for side in ("before", "after"):
                choices = getattr(row, side)
                assert all(len(choice.trials) == choice.count for choice in choices)
                members = [name for choice in choices for name in choice.trials]
                assert len(members) == len(set(members))
                assert set(members) == {
                    trial.name for trial in getattr(report.variants, side).trials
                }, "Fresh fixtures must retain exact named branch attribution."
        displays[name] = _assert_rendered_attention(report)
        if count is not None:
            assert attention.assessment in displays[name][0]
            assert attention.assessment in displays[name][1]
    qualifier = "Self-reported actions, not independently captured command evidence"
    for section in displays["attention-self-reported"]:
        assert qualifier in section
        assert "Recorded actions" not in section
    reported_md = html.unescape(
        render_markdown(reports["attention-self-reported"])
    ).replace("\\", "")
    assert reported_md.count(qualifier) == 2
    assert "Recorded actions, not proof of successful execution" not in reported_md
    assert displays["attention-quiet"] != displays["attention-unavailable"], (
        "An unavailable assessment must not reassure readers as an assessed-empty result."
    )
    report = reports["attention-multiple"]
    assert tuple(
        finding.relationship for finding in report.decisions.attention.findings
    ) == ("expected", "additional")
    assert tuple(
        finding.evidence_kind for finding in report.decisions.attention.findings
    ) == ("actions", "plans")
    assert sorted(choice.count for choice in report.decisions.rows[0].before) == [1, 2]
    assert sorted(choice.count for choice in report.decisions.rows[0].after) == [1, 2]
    _assert_validation(report, assert_round_trip)
    _assert_pipeline(report, root / "attention-multiple")
    reordered = report.to_dict()
    for finding in reordered["decisions"]["attention"]["findings"]:
        finding["before"].reverse()
        finding["after"].reverse()
    _assert_rendered_attention(assert_round_trip(reordered))
    legacy = report.to_dict()
    for row in legacy["decisions"]["rows"]:
        for side in ("before", "after"):
            for choice in row[side]:
                choice["trials"] = []
    legacy_report = assert_round_trip(legacy)
    legacy_summary, legacy_detail = _assert_rendered_attention(legacy_report)
    assert legacy_summary == displays["attention-multiple"][0], (
        "Unavailable trial attribution must not alter concise Summary pictures/counts."
    )
    from reporting import content

    assert content.ATTENTION_MEMBERSHIP_UNAVAILABLE in legacy_detail
    without_interpretation = replace(
        report, decisions=replace(report.decisions, explanation=None)
    )
    _assert_rendered_attention(without_interpretation)

    # Renderers must escape even a manually constructed internal object.
    payload = '<script>alert("synthetic")</script>|[link](javascript:alert(1))'
    attention = report.decisions.attention
    first = attention.findings[0]
    choice = first.before[0]
    unsafe = replace(
        report,
        decisions=replace(
            report.decisions,
            attention=replace(
                attention,
                assessment=payload,
                findings=(
                    replace(
                        first,
                        title=payload,
                        consequence=payload,
                        matters_if=payload,
                        next_step=payload,
                        explanation=payload,
                        limit=payload,
                        before=(
                            replace(
                                choice,
                                steps=(
                                    replace(choice.steps[0], label=payload),
                                    choice.steps[1],
                                ),
                            ),
                            *first.before[1:],
                        ),
                        context=tuple(
                            replace(claim, text=payload) for claim in first.context
                        ),
                    ),
                    *attention.findings[1:],
                ),
            ),
        ),
    )
    for renderer in (lambda value: render_artifact(value, ""), render_markdown):
        rendered = renderer(unsafe)
        assert_unchanged_scripts(renderer(report), rendered)
        assert "&lt;script&gt;" in rendered
    assert "](javascript:" not in render_markdown(unsafe)
