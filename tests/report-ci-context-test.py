#!/usr/bin/env python3
"""CI run context: config -> report JSON -> HTML/Markdown header."""

import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

scripts = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(scripts))

from reporting.load import load_report  # noqa: E402
from reporting.render_html import render_artifact  # noqa: E402
from reporting.render_markdown import render_markdown  # noqa: E402
from reporting.schema import ReportData  # noqa: E402

GITHUB = "https://github.com/synthetic-owner/synthetic-repo"
GITLAB = "https://gitlab.com/synthetic-group/synthetic-project"
BEFORE = "37d302b4c2b379d1f7b63031dab1c84e6046e952"
AFTER = "3a216abc72dfc7a898a72a123dd6217868f760d1"


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


def _config(**extra):
    config = {
        "mode": "review",
        "vocab": "generic",
        "target_file": "AGENTS.md",
        "before_label": "../base-AGENTS.md",
        "after_label": "/tmp/synthetic/fixture/AGENTS.md",
    }
    config.update(extra)
    return config


def _roundtrip(report):
    raw = report.to_dict()
    assert ReportData.from_dict(json.loads(report.to_json())).to_dict() == raw
    return raw


def _render_offline(report):
    """Rendering must not consult CI environment variables."""
    with patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_SERVER_URL": "https://github.com",
            "GITHUB_REPOSITORY": "env-owner/env-repo",
            "GITLAB_CI": "",
        },
    ):
        page = render_artifact(report, "")
        markdown = render_markdown(report)
    assert "env-owner" not in page and "env-owner" not in markdown
    return page, markdown


def _header(page):
    return page[
        page.index('<div class="source-line">') : page.index('<p class="meta">')
    ]


def assert_no_context_unchanged():
    report = _load(_config())
    raw = _roundtrip(report)
    assert raw["schema_version"] == 17
    assert raw["metadata"]["ci_context"] is None
    page, markdown = _render_offline(report)
    for absent in ("source-line", "revision-pair", "local-paths", "Workflow"):
        assert absent not in page, absent
    assert "Repository:" not in markdown and "Workflow" not in markdown


def assert_github_pull_request():
    title = "Tighten the “exactly one” rule"
    context = {
        "forge": "github",
        "repository_url": GITHUB,
        "pull_request": {"number": 42, "title": title, "url": GITHUB + "/pull/42"},
    }
    report = _load(_config(ci_context=context))
    raw = _roundtrip(report)
    assert raw["metadata"]["ci_context"] == context
    assert raw["metadata"]["source"] is None
    page, markdown = _render_offline(report)
    header = _header(page)
    assert f'<a href="{GITHUB}">synthetic-owner/synthetic-repo</a>' in header
    assert "Workflow PR" in header and "Related PR" not in header
    assert f'<a href="{GITHUB}/pull/42">#42 — {title}</a>' in header
    # CI context carries no commit pair: ordinary labels stay visible.
    for absent in ("revision-pair", "local-paths", "/commit/"):
        assert absent not in page, absent
    assert "<span><b>before</b>../base-AGENTS.md</span>" in page
    assert "<span><b>after</b>/tmp/synthetic/fixture/AGENTS.md</span>" in page
    assert f"[synthetic\\-owner/synthetic\\-repo](<{GITHUB}>)" in markdown
    assert f"Workflow PR: [\\#42 — {title}](<{GITHUB}/pull/42>)" in markdown
    assert "/commit/" not in markdown


def assert_gitlab_merge_request_fork_target():
    # A fork MR links the owning target project, which is the persisted repository.
    context = {
        "forge": "gitlab",
        "repository_url": GITLAB,
        "pull_request": {
            "number": 7,
            "title": "From a fork",
            "url": GITLAB + "/-/merge_requests/7",
        },
    }
    report = _load(_config(ci_context=context))
    assert _roundtrip(report)["metadata"]["ci_context"] == context
    page, markdown = _render_offline(report)
    header = _header(page)
    assert "Workflow MR" in header and "Workflow PR" not in header
    assert f'<a href="{GITLAB}/-/merge_requests/7">!7 — From a fork</a>' in header
    assert f'<a href="{GITLAB}">synthetic-group/synthetic-project</a>' in header
    assert f"(<{GITLAB}/-/merge_requests/7>)" in markdown


def assert_repository_only():
    for forge, url in (("github", GITHUB), ("gitlab", GITLAB)):
        context = {"forge": forge, "repository_url": url, "pull_request": None}
        report = _load(_config(ci_context=context))
        assert _roundtrip(report)["metadata"]["ci_context"] == context
        page, markdown = _render_offline(report)
        header = _header(page)
        assert "Repository" in header and "Workflow" not in header
        assert "<b>before</b>" in page and "revision-pair" not in page
        assert f"(<{url}>)" in markdown and "Workflow" not in markdown


def assert_title_less_request():
    context = {
        "forge": "github",
        "repository_url": GITHUB,
        "pull_request": {"number": 9, "title": None, "url": GITHUB + "/pull/9"},
    }
    report = _load(_config(ci_context=context))
    assert _roundtrip(report)["metadata"]["ci_context"] == context
    page, markdown = _render_offline(report)
    assert f'<a href="{GITHUB}/pull/9">#9</a>' in _header(page)
    assert "None" not in _header(page)
    assert f"Workflow PR: [\\#9](<{GITHUB}/pull/9>)" in markdown


def assert_explicit_source_wins():
    source = {
        "repository_url": GITHUB,
        "before_commit": BEFORE,
        "after_commit": AFTER,
        "pull_requests": [],
    }
    context = {
        "forge": "gitlab",
        "repository_url": GITLAB,
        "pull_request": {
            "number": 3,
            "title": "CI",
            "url": GITLAB + "/-/merge_requests/3",
        },
    }
    report = _load(_config(source=source, ci_context=context))
    raw = _roundtrip(report)
    assert raw["metadata"]["ci_context"] is None
    assert raw["metadata"]["source"]["repository_url"] == GITHUB
    ignored = _load(_config(source=source, ci_context={"invalid": "context"}))
    assert ignored.to_dict()["metadata"] == raw["metadata"]
    page, markdown = _render_offline(report)
    for absent in ("Workflow", GITLAB, "merge_requests"):
        assert absent not in page and absent not in markdown, absent
    assert '<p class="revision-pair">' in page

    tampered = copy.deepcopy(raw)
    tampered["metadata"]["ci_context"] = context
    _assert_rejected(tampered, "metadata.ci_context")


def _assert_rejected(raw, needle):
    try:
        ReportData.from_dict(raw)
    except ValueError as error:
        assert needle in str(error), error
    else:
        raise AssertionError("Serialized ci_context was accepted: " + needle)


def assert_strict_ingestion():
    context = {
        "forge": "github",
        "repository_url": GITHUB,
        "pull_request": {"number": 4, "title": "Ok", "url": GITHUB + "/pull/4"},
    }
    raw = _load(_config(ci_context=context)).to_dict()
    missing = copy.deepcopy(raw)
    del missing["metadata"]["ci_context"]
    _assert_rejected(missing, "metadata")
    for mutate in (
        lambda c: c.update(forge="bitbucket"),
        lambda c: c.update(repository_url="http://github.com/a/b"),
        lambda c: c.update(unknown="value"),
        lambda c: c.update(before_commit=BEFORE),
        lambda c: c["pull_request"].update(number=0),
        lambda c: c["pull_request"].update(url="https://github.com/other/repo/pull/4"),
        lambda c: c["pull_request"].update(url=GITHUB + "/pull/4?x=1"),
    ):
        tampered = copy.deepcopy(raw)
        mutate(tampered["metadata"]["ci_context"])
        _assert_rejected(tampered, "metadata.ci_context")


def main():
    assert_no_context_unchanged()
    assert_github_pull_request()
    assert_gitlab_merge_request_fork_target()
    assert_repository_only()
    assert_title_less_request()
    assert_explicit_source_wins()
    assert_strict_ingestion()


if __name__ == "__main__":
    main()
