#!/usr/bin/env python3
"""Git history provenance: config -> report JSON -> HTML/Markdown header."""

import copy
import json
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

scripts = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(scripts))

from reporting.load import load_report  # noqa: E402
from reporting.render_html import render_artifact  # noqa: E402
from reporting.render_markdown import render_markdown  # noqa: E402
from reporting.schema import ReportData  # noqa: E402

BEFORE = "37d302b4c2b379d1f7b63031dab1c84e6046e952"
AFTER = "3a216abc72dfc7a898a72a123dd6217868f760d1"
REPO = "https://github.com/synthetic-owner/synthetic-repo"


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.append(dict(attrs)["href"])
        if tag == "script":
            self.scripts += 1


def _links(page):
    parser = _Links()
    parser.feed(page)
    return parser


def _load(config):
    with tempfile.TemporaryDirectory() as directory:
        run = Path(directory)
        (run / "task.md").write_text("Compare the synthetic outputs.")
        (run / "grades.tsv").write_text("before-1\tREVIEW\t-\nafter-1\tREVIEW\t-\n")
        (run / "config.json").write_text(json.dumps(config))
        for side in ("before", "after"):
            (run / (side + "-1")).mkdir()
            (run / (side + "-1") / "trace.jsonl").write_text(
                json.dumps({"type": "result", "result": side + " synthetic answer"})
            )
        return load_report(run, run, "synthetic/model", run / "config.json")


def _config(source=None):
    config = {
        "mode": "review",
        "vocab": "generic",
        "target_file": "AGENTS.md",
        "before_label": "../base-AGENTS.md",
        "after_label": "/tmp/synthetic/fixture/AGENTS.md",
    }
    if source is not None:
        config["source"] = source
    return config


def _github_source(requests):
    return {
        "repository_url": REPO,
        "before_commit": BEFORE,
        "after_commit": AFTER,
        "pull_requests": requests,
    }


def assert_source_free_unchanged():
    report = _load(_config())
    assert report.metadata.source is None
    assert report.to_dict()["metadata"]["source"] is None
    page = render_artifact(report, "")
    for absent in ("source-line", "revision-pair", "local-paths", "Repository"):
        assert absent not in page, absent
    assert "<span><b>before</b>../base-AGENTS.md</span>" in page
    markdown = render_markdown(report)
    assert "Repository:" not in markdown and "/commit/" not in markdown
    return report


def assert_github_header():
    title = "Fix the “exactly one” instruction"
    report = _load(
        _config(
            _github_source(
                [
                    {
                        "number": 123,
                        "title": title,
                        "url": REPO + "/pull/123",
                        "applies_to": "both",
                    }
                ]
            )
        )
    )
    raw = report.to_dict()
    assert ReportData.from_dict(json.loads(report.to_json())).to_dict() == raw
    assert raw["metadata"]["source"]["forge"] == "github"
    page = render_artifact(report, "")
    line = page.index('<div class="source-line">')
    pair = page.index('<p class="revision-pair">')
    meta = page.index('<p class="meta">')
    paths = page.index('<details class="local-paths">')
    assert line < pair < meta < paths
    assert f'<a href="{REPO}">synthetic-owner/synthetic-repo</a>' in page[line:pair]
    assert "Related PR" in page[line:pair]
    assert f"#123 — {title}" in page[line:pair], "PR title must stay verbatim."
    for commit in (BEFORE, AFTER):
        assert (
            f'<a class="commit" href="{REPO}/commit/{commit}" title="{commit}">'
            f"{commit[:8]}</a>"
        ) in page[pair:meta]
    assert "<b>before</b>" not in page[meta:paths]
    assert "../base-AGENTS.md" in page[paths:] and "<b>model</b>" in page[meta:paths]
    markdown = render_markdown(report)
    assert f"[synthetic\\-owner/synthetic\\-repo](<{REPO}>)" in markdown
    assert f"(<{REPO}/pull/123>)" in markdown
    assert f"[{BEFORE[:8]}](<{REPO}/commit/{BEFORE}>)" in markdown


def assert_sided_requests():
    report = _load(
        _config(
            _github_source(
                [
                    {
                        "number": 8,
                        "title": "After change",
                        "url": REPO + "/pull/8",
                        "applies_to": "after",
                    },
                    {
                        "number": 7,
                        "title": "Before change",
                        "url": REPO + "/pull/7",
                        "applies_to": "before",
                    },
                ]
            )
        )
    )
    page = render_artifact(report, "")
    assert page.index("Before PR") < page.index("After PR")
    assert "Related PR" not in page
    only_after = _load(
        _config(
            _github_source(
                [
                    {
                        "number": 8,
                        "title": "After change",
                        "url": REPO + "/pull/8",
                        "applies_to": "after",
                    }
                ]
            )
        )
    )
    page = render_artifact(only_after, "")
    assert "After PR" in page and "Before PR" not in page
    no_request = _load(_config(_github_source([])))
    assert "PR" not in render_artifact(no_request, "").split('<p class="meta">')[0]


def assert_gitlab_header():
    repo = "https://gitlab.example.com/group/subgroup/project"
    source = {
        "forge": "gitlab",
        "repository_url": repo,
        "before_commit": BEFORE,
        "after_commit": AFTER,
        "pull_requests": [
            {
                "number": 42,
                "title": "Tighten rules",
                "url": repo + "/-/merge_requests/42",
                "applies_to": "both",
            }
        ],
    }
    report = _load(_config(source))
    page = render_artifact(report, "")
    assert ">group/subgroup/project</a>" in page
    assert "Related MR" in page and "Related PR" not in page
    assert "!42 — Tighten rules" in page
    assert f'href="{repo}/-/commit/{AFTER}"' in page
    assert "Related MR" in render_markdown(report)


def assert_injection_safety():
    payload = '"><script>alert(1)</script>[x](javascript:alert(1))'
    report = _load(
        _config(
            _github_source(
                [
                    {
                        "number": 9,
                        "title": payload,
                        "url": REPO + "/pull/9",
                        "applies_to": "both",
                    }
                ]
            )
        )
    )
    page = render_artifact(report, "")
    links = _links(page)
    baseline = _links(render_artifact(_load(_config()), "")).scripts
    assert links.scripts == baseline and "&lt;script&gt;" in page
    assert all(href.startswith(("https://", "#")) for href in links.hrefs)
    assert "](javascript:" not in render_markdown(report)
    for unsafe in (
        "javascript:alert(1)",
        "http://github.com/synthetic-owner/synthetic-repo",
        "https://user:pw@github.com/synthetic-owner/synthetic-repo",
        "https://github.com/synthetic-owner/synthetic-repo?x=1",
    ):
        try:
            _load(_config(dict(_github_source([]), repository_url=unsafe)))
        except SystemExit as error:
            assert "invalid config source" in str(error)
        else:
            raise AssertionError("Unsafe repository URL was accepted: " + unsafe)
    raw = report.to_dict()
    for field, value in (
        ("repository_url", "javascript:alert(1)"),
        ("before_commit", BEFORE.upper()),
        ("unknown", "value"),
    ):
        tampered = copy.deepcopy(raw)
        tampered["metadata"]["source"][field] = value
        try:
            ReportData.from_dict(tampered)
        except ValueError as error:
            assert "metadata.source" in str(error), error
        else:
            raise AssertionError("Serialized source was not validated: " + field)
    tampered = copy.deepcopy(raw)
    tampered["metadata"]["source"]["pull_requests"][0]["url"] = (
        "https://github.com/other/repo/pull/9"
    )
    try:
        ReportData.from_dict(tampered)
    except ValueError:
        pass
    else:
        raise AssertionError("Mismatched PR URL was accepted.")


def main():
    assert_source_free_unchanged()
    assert_github_header()
    assert_sided_requests()
    assert_gitlab_header()
    assert_injection_safety()


if __name__ == "__main__":
    main()
