"""Deterministic contracts for authored synthetic change explanations."""

import copy
import html
import json
from html.parser import HTMLParser
from unittest.mock import patch


class ExplanationPanel(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.text = []
        self.targets = []
        self.tabs = set()
        self.in_tabbar = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav" and "tabbar" in attrs.get("class", "").split():
            self.in_tabbar = True
        if tag == "a" and self.in_tabbar:
            self.tabs.add(attrs.get("href", "").removeprefix("#"))
        if attrs.get("id") == "panel-explanation":
            self.depth = 1
        elif self.depth and tag not in ("br", "hr", "img", "input", "meta", "link"):
            self.depth += 1
        if self.depth and tag == "a":
            self.targets.append(attrs.get("href"))

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_tabbar = False
        if self.depth:
            self.depth -= 1

    def handle_data(self, text):
        if self.depth:
            self.text.append(text)


def assert_change_explanations(
    reports, root, assert_round_trip, assert_evidence_links, assert_unchanged_scripts
):
    from reporting import content
    import decisions
    from reporting.load import load_report
    from reporting.render_html import render_artifact
    from reporting.render_markdown import render_markdown
    from reporting.schema import ReportData

    for name in ("timing-rule", "formula-writing"):
        report = reports[name]
        explanation = report.decisions.explanation
        assert explanation is not None, name
        assert assert_round_trip(report.to_dict()) == report
        assert isinstance(explanation.steps, tuple)
        assert isinstance(explanation.unchanged, tuple)
        assert isinstance(explanation.examples, tuple)
        page = render_artifact(report, "")
        markdown = render_markdown(report)
        panel = ExplanationPanel()
        panel.feed(page)
        assert set(panel.tabs) == {
            "panel-summary",
            "panel-explanation",
            "panel-decision",
            "panel-flow",
            "panel-instruction",
            "panel-trials",
        }, "Explanation must not replace or nest another top-level tab."
        plain = "".join(panel.text)
        md_plain = html.unescape(markdown).replace("\\", "")
        for text in (
            explanation.headline,
            explanation.overview,
            *(
                value
                for step in explanation.steps
                for value in (
                    step.title,
                    step.before,
                    step.after,
                    step.meaning,
                )
            ),
            *(claim.text for claim in (*explanation.unchanged, *explanation.limits)),
            *(example.text for example in explanation.examples),
        ):
            assert text in plain, (name, text)
            assert text in md_plain, (name, text)
        references = {
            index
            for item in (
                *explanation.steps,
                *explanation.unchanged,
                *explanation.limits,
            )
            for index in item.decisions
        }
        for index in references:
            assert f"#decision-{index}" in panel.targets
            assert f"](#decision-{index})" in markdown
        for example in explanation.examples:
            variant = getattr(report.variants, example.side)
            final = next(
                trial.final for trial in variant.trials if trial.name == example.trial
            )
            assert example.text in final
            assert (
                f"#{content.trial_anchor(example.side, example.trial)}" in panel.targets
            )
        assert_evidence_links(report)

    formula = reports["formula-writing"]
    assert formula.decisions.rows[0].diverges is False
    assert formula.decisions.rows[3].diverges is False
    assert [choice.count for choice in formula.decisions.rows[1].after] == [2, 1]
    assert formula.summary.status == "mixed"
    timing = reports["timing-rule"]
    assert timing.summary.status == "mixed"
    assert [choice.count for choice in timing.decisions.rows[0].after] == [2, 1]
    assert [choice.count for choice in timing.decisions.rows[1].after] == [2, 1]

    run = root / "formula-writing"
    path = run / "decisions.json"
    original = path.read_text()
    saved = json.loads(original)
    valid = saved["explanation"]
    extraction = json.loads((run / "extraction.json").read_text())
    finals = {
        side: {
            trial.name: trial.final for trial in getattr(formula.variants, side).trials
        }
        for side in ("before", "after")
    }
    names = {side: list(answers) for side, answers in finals.items()}
    normalized = decisions.normalize(
        extraction, names, hunk_count=1, final_answers=finals
    )
    assert normalized["explanation"] == valid
    canonical_missing = formula.to_dict()
    del canonical_missing["decisions"]["explanation"]
    try:
        ReportData.from_dict(canonical_missing)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Canonical report omitted its explanation availability field."
        )
    malformed = []
    for field, value in (
        ("steps", []),
        ("headline", ""),
        ("steps", "not steps"),
        ("headline", "<script>synthetic</script>"),
        ("overview", "x" * 601),
        (
            "examples",
            [{"side": "after", "trial": "after-1", "text": "bad\u0000excerpt"}],
        ),
        (
            "examples",
            [{"side": "after", "trial": "after-1", "text": "Invented formula"}],
        ),
        (
            "examples",
            [
                {
                    "side": "before",
                    "trial": "after-1",
                    "text": valid["examples"][1]["text"],
                }
            ],
        ),
        (
            "examples",
            [
                {
                    "side": "after",
                    "trial": "after-missing",
                    "text": valid["examples"][1]["text"],
                }
            ],
        ),
        (
            "examples",
            [
                {
                    "side": "after",
                    "trial": "after-3",
                    "text": valid["examples"][1]["text"],
                }
            ],
        ),
    ):
        malformed.append(dict(valid, **{field: value}))
    for field, refs in (
        ("steps", [99]),
        ("steps", [True]),
        ("steps", []),
        ("steps", [2, 2]),
        ("unchanged", [2]),
    ):
        value = copy.deepcopy(valid)
        value[field][0]["decisions"] = refs
        malformed.append(value)
    try:
        for value in malformed:
            normalized = decisions.normalize(
                dict(extraction, explanation=value),
                names,
                hunk_count=1,
                final_answers=finals,
            )
            assert normalized["explanation"] is None
            assert len(normalized["chain"]) == len(formula.decisions.rows)
            path.write_text(json.dumps(dict(saved, explanation=value)))
            loaded = load_report(run, run, "synthetic/authored", run / "config.json")
            assert loaded.decisions.explanation is None
            assert loaded.decisions.rows == formula.decisions.rows
            assert loaded.variants == formula.variants
            assert loaded.summary == formula.summary
            canonical = formula.to_dict()
            canonical["decisions"]["explanation"] = value
            try:
                ReportData.from_dict(canonical)
            except ValueError:
                pass
            else:
                raise AssertionError("Malformed stored explanation was accepted.")
        path.write_text(
            json.dumps(
                {key: value for key, value in saved.items() if key != "explanation"}
            )
        )
        missing = load_report(run, run, "synthetic/authored", run / "config.json")
        assert missing.decisions.explanation is None
        assert missing.decisions.rows == formula.decisions.rows
        with patch(
            "subprocess.run",
            side_effect=AssertionError("Offline rendering invoked a process"),
        ):
            for render in (lambda report: render_artifact(report, ""), render_markdown):
                rendered = render(missing)
                assert content.CHANGE_EXPLANATION_UNAVAILABLE in html.unescape(
                    rendered
                ).replace("\\", "")
                assert "decision-2" in rendered
        assert reports["blocked"].summary.status == "unavailable"
        assert reports["blocked"].decisions.explanation is None
        assert reports["missing-extraction"].decisions.explanation is None
    finally:
        path.write_text(original)

    grades = run / "grades.tsv"
    original_grades = grades.read_text()
    try:
        grades.write_text(
            original_grades + "after-4\tBLOCKED\tSynthetic unavailable trial\n"
        )
        incomplete = load_report(run, run, "synthetic/authored", run / "config.json")
        assert incomplete.decisions.explanation is not None
        assert not content.complete_trial_evidence(incomplete)
        for render in (lambda report: render_artifact(report, ""), render_markdown):
            rendered = render(incomplete)
            plain = html.unescape(rendered).replace("\\", "")
            assert incomplete.decisions.explanation.headline not in plain
            assert "Trial evidence is incomplete" in plain
            assert "panel-trials" in rendered
    finally:
        grades.write_text(original_grades)

    unsafe = formula.to_dict()
    payload = (
        '<script>alert("synthetic")</script>|[link](javascript:alert(1)) & value < 3'
    )
    unsafe["variants"]["before"]["trials"][0]["final"] += "\n" + payload
    unsafe["decisions"]["explanation"]["examples"] = [
        {"side": "before", "trial": "before-1", "text": payload}
    ]
    escaped = ReportData.from_dict(unsafe)
    for render in (lambda report: render_artifact(report, ""), render_markdown):
        baseline = render(formula)
        rendered = render(escaped)
        assert_unchanged_scripts(baseline, rendered)
        assert "&lt;script&gt;" in rendered
        assert "&lt; 3" in rendered
        panel = ExplanationPanel()
        panel.feed(rendered)
        assert not any(
            target and target.lower().startswith("javascript:")
            for target in panel.targets
        )
