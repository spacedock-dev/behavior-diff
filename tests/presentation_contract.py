"""Consumer contracts for Summary navigation and version-name emphasis in HTML prose."""

import html
import json
import re
from dataclasses import replace
from unittest.mock import patch

from attention_contract import _ReportMarkup, _plain

LABEL = '<strong class="version-label">{0}</strong>'
WRAPPED = re.compile(r'<strong class="version-label">(Before|After)</strong>')
SUMMARY_LINKS = [
    ["#instruction-diff"],
    ["#panel-explanation"],
    ["#attention-explanation"],
    [],
]
# {B} and {A} mark the only words that name a compared version.
VERSION_NAME_CASES = (
    ("Both Before and After trials stop.", "Both {B} and {A} trials stop."),
    ("Unlike Before, the edit asks first.", "Unlike {B}, the edit asks first."),
    ("Before: asks first.", "{B}: asks first."),
    ("Before, it asked first.", "{B}, it asked first."),
    ("Before and After both stop.", "{B} and {A} both stop."),
    ("Before was cautious; After is direct.", "{B} was cautious; {A} is direct."),
    (
        "After explicitly requires that explanation.",
        "{A} explicitly requires that explanation.",
    ),
    ("After adds a rollback prerequisite.", "{A} adds a rollback prerequisite."),
    ("After cannot complete it, so stop.", "{A} cannot complete it, so stop."),
    (
        "After adds a rollback prerequisite, but Before does not.",
        "{A} adds a rollback prerequisite, but {B} does not.",
    ),
    (
        "Before deleted it in two attempts, though it moved the rules first.",
        "{B} deleted it in two attempts, though it moved the rules first.",
    ),
    (
        "Before wrote the new plan under different filenames.",
        "{B} wrote the new plan under different filenames.",
    ),
    ("After kept the old plan.", "{A} kept the old plan."),
    ("After ran the checks.", "{A} ran the checks."),
    (
        "Before running the checks, After wrote the plan.",
        "Before running the checks, {A} wrote the plan.",
    ),
    (
        "Both plans wait; After extends the interval.",
        "Both plans wait; {A} extends the interval.",
    ),
    (
        "Compare After's answer with After’s answer.",
        "Compare {A}'s answer with {A}’s answer.",
    ),
    ("After's answer stops.", "{A}'s answer stops."),
    # Ordinary temporal uses, including at sentence openings.
    ("Before deleting files, read them.", None),
    ("After checking the log, stop.", None),
    ("After tests pass, the agent stops.", None),
    ("After tests pass we deploy.", None),
    ("In this workflow, After tests pass we deploy.", None),
    ("In this workflow, After tests pass, we deploy.", None),
    ("After noted issues were fixed, stop.", None),
    ("After failed checks were retried.", None),
    ("After the review, stop. Before that, read.", None),
    ("After Emma signs off, stop.", None),
    ("After signoff, poll every 5 minutes.", None),
    ("After only two trials, stop.", None),
    ("before and after the edit; BEFORE and AFTER.", None),
    # Quoted, code, URL, identifier and path forms stay verbatim.
    ("Use the `After` flag and the `Before run` step.", None),
    ("Keep ``After`` unchanged.", None),
    ("Keep `` `Before` and After `` literal.", None),
    ("Keep ```Before `x` and After``` literal.", None),
    ('The "Before" label and the “After” label stay.', None),
    ("The ‘Before’ label stays.", None),
    ("Keep the 'Before you go' note.", None),
    ("See https://example.invalid/After and www.example.invalid/Before now.", None),
    ("Trial After-1 and Before-run use After_1 and After.md.", None),
    ("Open docs/After, @After, #Before, and x=After here.", None),
    ("Both Before and `After` differ.", "Both {B} and `After` differ."),
    (
        'Compare Before & After <b>"x"</b> <script>',
        'Compare {B} & {A} <b>"x"</b> <script>',
    ),
)
# Recorded evidence, frozen intent and headings keep their original markup.
UNLABELLED_TAGS = {"pre", "code", "a", "button", "h1", "h2", "h3", "h4", "h5", "h6"}
UNLABELLED_CLASSES = {
    "summary-side-label",
    "purpose-goal-text",
    "edit-aim",
    "scenario-context",
    "scenario-prompt",
}


def _expected(text, template):
    escaped = html.escape(template if template is not None else text, quote=True)
    return escaped.replace("{B}", LABEL.format("Before")).replace(
        "{A}", LABEL.format("After")
    )


def _unwrap(markup):
    return WRAPPED.sub(r"\1", markup)


def visible_text(rendered):
    """Reader-visible HTML or Markdown text; version-name emphasis adds no words."""
    return html.unescape(_unwrap(rendered)).replace("\\", "")


def _assert_helper():
    from reporting.version_names import version_name_html

    for text, template in VERSION_NAME_CASES:
        rendered = version_name_html(text)
        assert rendered == _expected(text, template), (text, rendered)
        assert _unwrap(rendered) == html.escape(text, quote=True), text
        assert html.unescape(_unwrap(rendered)) == text, text


def _labels(node, ancestors=()):
    """Yield every version label with the elements that enclose it."""
    if "version-label" in node["attrs"].get("class", "").split():
        yield node, ancestors
    for child in node["children"]:
        yield from _labels(child, (*ancestors, node))


def _assert_label_placement(name, page, report):
    # Only a model-written purpose summary is prose; goals, expectations and
    # inferred intent stay exact.
    unlabelled = set(UNLABELLED_CLASSES)
    if not (
        report.intent.source == "purpose"
        and report.decisions.purpose_summary is not None
    ):
        unlabelled.add("story-intent")
    markup = _ReportMarkup(page)
    labels = list(_labels(markup.root))
    for label, ancestors in labels:
        assert label["tag"] == "strong" and not label["children"], name
        assert _plain(label) in ("Before", "After"), (name, _plain(label))
        for ancestor in ancestors:
            classes = set(ancestor["attrs"].get("class", "").split())
            assert ancestor["tag"] not in UNLABELLED_TAGS, (name, ancestor["tag"])
            assert not classes & unlabelled, (name, classes)
    return len(labels)


def _assert_rendered_reports(reports):
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown

    labelled = 0
    for name, report in reports.items():
        stored = report.to_dict()
        page = render_artifact(report, "")
        with patch("reporting.render_html.version_name_html", html.escape):
            plain_page = render_artifact(report, "")
        # Emphasis is additive markup only: wording and escaping stay identical.
        assert _unwrap(page) == plain_page, name
        labelled += _assert_label_placement(name, page, report)
        assert "version-label" not in render_markdown(report), name
        assert report.to_dict() == stored, name
        assert "version-label" not in json.dumps(stored), name
        for variant in (report.variants.before, report.variants.after):
            for trial in variant.trials:
                if trial.final:
                    assert f"<pre>{html.escape(trial.final)}</pre>" in page, name
        assert "version-label" not in "".join(
            re.findall(r"<pre[^>]*>.*?</pre>", page, re.S)
        ), name
        # Temporal openings in saved fixture prose stay ordinary words.
        for word, rest in (
            ("After", " signoff"),
            ("After", " the edit"),
            ("Before", " returning"),
        ):
            assert LABEL.format(word) + rest not in page, (name, word + rest)
    assert labelled, "No saved report prose named a compared version."
    page = render_artifact(reports["target-additional"], "")
    markup = _ReportMarkup(page)
    summary = markup.select(anchor="panel-summary")[0]
    attention = markup.select(summary, class_name="story-attention")[0]
    consequences = [
        node
        for node in markup.select(attention, class_name="attention-consequence")
        if _plain(node)
        == "The After draft does not contain the required publishing metadata."
    ]
    assert len(consequences) == 1 and [
        _plain(child)
        for child in consequences[0]["children"]
        if "version-label" in child["attrs"].get("class", "").split()
    ] == ["After"], "A Summary concern lost its version-name emphasis."
    assert "<h4>Required publishing tag is omitted After</h4>" in page
    timing = render_artifact(reports["timing-rule"], "")
    assert (
        "; " + LABEL.format("After") + " extends the interval and deadline." in timing
    )


def _assert_authored_prose(report):
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown
    from reporting.schema import EvidenceClaimData
    from reporting.version_names import version_name_html

    why = "Both Before and After stop; the `After` flag stays, and After-1 is an ID."
    caution = "Before deleting files, read them. After checking the log, stop."
    step = "Before: asks first."
    evidence = "\nBoth Before and After stop in this recorded answer."
    # A supplied expectation is literal; its unbalanced quote must not shift spans.
    expected = 'Reply "Before review and After merge, then stop.'
    limits = (
        f"Expected behavior: {expected}",
        "Both Before and After trials are independent.",
    )
    assert report.decisions.explanation is not None
    explanation = report.decisions.explanation
    before = report.variants.before
    first = replace(before.trials[0], final=before.trials[0].final + evidence)
    authored = replace(
        report,
        summary=replace(
            report.summary,
            why=EvidenceClaimData(why, (1,)),
            caution=EvidenceClaimData(caution, (1,)),
        ),
        decisions=replace(
            report.decisions,
            explanation=replace(
                explanation,
                steps=(
                    replace(explanation.steps[0], before=step),
                    *explanation.steps[1:],
                ),
            ),
        ),
        variants=replace(
            report.variants,
            before=replace(before, trials=(first, *before.trials[1:])),
        ),
        content=replace(report.content, expected=expected),
        result=replace(report.result, limits=limits),
    )
    stored = authored.to_dict()
    page = render_artifact(authored, "")
    assert f"<p>{version_name_html(why)}</p>" in page
    assert LABEL.format("Before") + " and " + LABEL.format("After") + " stop;" in page
    assert "the `After` flag stays, and After-1 is an ID." in page
    assert f"<p>{html.escape(caution)}</p>" in page, "A temporal opening was labelled."
    assert version_name_html(step) == LABEL.format("Before") + ": asks first."
    assert version_name_html(step) in page
    assert f"<pre>{html.escape(first.final)}</pre>" in page, "Raw evidence changed."
    assert f"<li>{html.escape(limits[0])}</li>" in page, (
        "An expectation was reformatted."
    )
    assert (
        "<li>Both "
        + LABEL.format("Before")
        + " and "
        + LABEL.format("After")
        + " trials are independent.</li>"
    ) in page
    assert authored.to_dict() == stored and "version-label" not in json.dumps(stored)
    markdown = render_markdown(authored)
    assert "version-label" not in markdown
    for text in (why, caution, step):
        assert text in html.unescape(markdown).replace("\\", "")
    _assert_label_placement("authored", page, authored)


def assert_version_labels(reports):
    _assert_helper()
    _assert_rendered_reports(reports)
    _assert_authored_prose(reports["formula-writing"])


def assert_summary_detail_links(reports):
    """The Summary keeps one detail link per section; detailed views keep evidence."""
    from reporting import content
    from reporting.render_html import render_artifact

    for name, report in reports.items():
        markup = _ReportMarkup(render_artifact(report, ""))
        summary = markup.select(anchor="panel-summary")[0]
        steps = markup.select(summary, class_name="story-step")
        assert [
            [link["attrs"].get("href") for link in markup.select(step, tag="a")]
            for step in steps
        ] == SUMMARY_LINKS, name
        assert {
            link["attrs"].get("href") for link in markup.select(summary, tag="a")
        } == {href for links in SUMMARY_LINKS for href in links}, name
        for removed in ("evidence-links", "attention-finding-nav"):
            assert not markup.select(summary, class_name=removed), (name, removed)
        for item in content.attention_items(report):
            if item.finding is None:
                anchor = content.target_criterion_anchor(item.criterion_number)
                assert markup.select(anchor=anchor), (name, anchor)
                continue
            detail = markup.select(
                anchor=content.attention_finding_anchor(item.finding.decision)
            )
            assert len(detail) == 1, name
            assert f"#decision-{item.finding.decision}" in [
                link["attrs"].get("href") for link in markup.select(detail[0], tag="a")
            ], name
        explanation = report.decisions.explanation
        if explanation is not None and content.complete_trial_evidence(report):
            panel = markup.select(anchor="panel-explanation")[0]
            targets = {
                link["attrs"].get("href") for link in markup.select(panel, tag="a")
            }
            claims = (*explanation.steps, *explanation.unchanged, *explanation.limits)
            for item in claims:
                for index in item.decisions:
                    assert f"#decision-{index}" in targets, (name, index)
