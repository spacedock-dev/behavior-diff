#!/usr/bin/env python3
"""Synthetic source-provenance validation; no models, forges, or network calls."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(SCRIPTS))
from source import parse_source, read_source

BEFORE = "a" * 40
AFTER = "b" * 40
REPOSITORY = "https://github.com/synthetic-owner/synthetic-repo"


def pull_request(**changes):
    value = {
        "number": 7,
        "title": "Synthetic instruction change",
        "url": f"{REPOSITORY}/pull/7",
        "applies_to": "after",
    }
    value.update(changes)
    return value


def source(**changes):
    value = {
        "repository_url": REPOSITORY,
        "before_commit": BEFORE,
        "after_commit": AFTER,
    }
    value.update(changes)
    return value


class ParseSourceTests(unittest.TestCase):
    def test_absent_source_and_minimal_github_source(self):
        self.assertIsNone(parse_source(None))
        self.assertEqual(
            parse_source(source()),
            {
                "forge": "github",
                "repository_url": REPOSITORY,
                "before_commit": BEFORE,
                "after_commit": AFTER,
                "pull_requests": [],
            },
        )

    def test_normalizes_and_is_idempotent(self):
        parsed = parse_source(
            source(
                repository_url="https://GitHub.com/synthetic-owner/synthetic-repo/",
                before_commit=BEFORE.upper(),
                pull_requests=[
                    pull_request(
                        url="https://GITHUB.com/synthetic-owner/synthetic-repo/pull/7/"
                    ),
                    pull_request(
                        number=8, url=f"{REPOSITORY}/pull/8", applies_to="both"
                    ),
                ],
            )
        )
        self.assertEqual(parsed["repository_url"], REPOSITORY)
        self.assertEqual(parsed["before_commit"], BEFORE)
        self.assertEqual(
            [item["url"] for item in parsed["pull_requests"]],
            [f"{REPOSITORY}/pull/7", f"{REPOSITORY}/pull/8"],
        )
        self.assertEqual(parse_source(parsed), parsed)

    def test_gitlab_nested_groups_and_explicit_self_hosted_forge(self):
        gitlab = "https://gitlab.com/synthetic-group/sub-group/synthetic-project"
        parsed = parse_source(
            source(
                repository_url=gitlab,
                pull_requests=[pull_request(url=f"{gitlab}/-/merge_requests/7")],
            )
        )
        self.assertEqual(parsed["forge"], "gitlab")
        self.assertEqual(
            parsed["pull_requests"][0]["url"], f"{gitlab}/-/merge_requests/7"
        )
        self.assertEqual(parse_source(parsed), parsed)
        hosted = "https://code.example.invalid/synthetic-group/synthetic-project"
        parsed = parse_source(source(repository_url=hosted, forge="gitlab"))
        self.assertEqual(parsed["forge"], "gitlab")
        self.assertEqual(parse_source(parsed), parsed)
        sha256 = parse_source(source(before_commit="c" * 64, after_commit="d" * 64))
        self.assertEqual(sha256["after_commit"], "d" * 64)

    def test_rejects_unsafe_or_malformed_repository_urls(self):
        for url in (
            "http://github.com/synthetic-owner/synthetic-repo",
            "https://user:token@github.com/synthetic-owner/synthetic-repo",
            "https://github.com:443/synthetic-owner/synthetic-repo",
            "https://github.com/synthetic-owner/synthetic-repo?tab=readme",
            "https://github.com/synthetic-owner/synthetic-repo#readme",
            "https://github.com/synthetic-owner/synthetic-repo.git",
            "https://github.com/synthetic-owner",
            "https://github.com/synthetic-owner/synthetic-repo/tree/main",
            "https://github.com/synthetic-owner/../synthetic-repo",
            "https://github.com/synthetic-owner/synthetic%20repo",
            "https://github.com//synthetic-repo",
            "https://localhost/synthetic-owner/synthetic-repo",
            "https://192.0.2.1/synthetic-owner/synthetic-repo",
            "https://gitlab.com/synthetic-group/-/synthetic-project",
            "https://gitlab.com/synthetic-group",
            "git@github.com:synthetic-owner/synthetic-repo.git",
            "https://github.com/synthetic-owner/synthetic-repo\n",
            None,
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                parse_source(source(repository_url=url))

    def test_forge_is_explicit_for_unknown_hosts_and_never_contradicts_host(self):
        hosted = "https://code.example.invalid/synthetic-group/synthetic-project"
        for value in (
            source(repository_url=hosted),
            source(forge="gitlab"),
            source(
                repository_url="https://gitlab.com/synthetic-group/synthetic-project",
                forge="github",
            ),
            source(forge="bitbucket"),
            source(forge=None),
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_source(value)

    def test_rejects_shape_and_commit_errors(self):
        for value in (
            [],
            "source",
            {},
            source(extra="unexpected"),
            {"repository_url": REPOSITORY, "before_commit": BEFORE},
            source(before_commit="a" * 39),
            source(before_commit="a" * 12),
            source(before_commit="g" * 40),
            source(before_commit="HEAD"),
            source(before_commit=BEFORE, after_commit=BEFORE.upper()),
            source(after_commit="d" * 64),
            source(pull_requests=None),
            source(pull_requests={}),
            source(
                pull_requests=[
                    pull_request(number=n, url=f"{REPOSITORY}/pull/{n}")
                    for n in range(1, 22)
                ]
            ),
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_source(value)

    def test_rejects_unverifiable_or_unsafe_pull_requests(self):
        gitlab = "https://gitlab.com/synthetic-group/synthetic-project"
        for value in (
            source(pull_requests=[pull_request(url=f"{REPOSITORY}/pull/8")]),
            source(
                pull_requests=[pull_request(url="https://github.com/other/repo/pull/7")]
            ),
            source(pull_requests=[pull_request(url=f"{REPOSITORY}/issues/7")]),
            source(pull_requests=[pull_request(url=f"{REPOSITORY}/pull/7?diff=split")]),
            source(pull_requests=[pull_request(url=f"{REPOSITORY}/pull/7#discussion")]),
            source(
                pull_requests=[
                    pull_request(
                        url="http://github.com/synthetic-owner/synthetic-repo/pull/7"
                    )
                ]
            ),
            source(
                pull_requests=[
                    pull_request(
                        url="https://user@github.com/synthetic-owner/synthetic-repo/pull/7"
                    )
                ]
            ),
            source(
                repository_url=gitlab,
                pull_requests=[pull_request(url=f"{gitlab}/pull/7")],
            ),
            source(pull_requests=[pull_request(number=0, url=f"{REPOSITORY}/pull/0")]),
            source(pull_requests=[pull_request(number=True)]),
            source(pull_requests=[pull_request(number="7")]),
            source(pull_requests=[pull_request(title="")]),
            source(pull_requests=[pull_request(title=" padded")]),
            source(pull_requests=[pull_request(title="x" * 301)]),
            source(pull_requests=[pull_request(title="Line\nbreak")]),
            source(pull_requests=[pull_request(title="Bidi\u202eoverride")]),
            source(pull_requests=[pull_request(applies_to="neither")]),
            source(pull_requests=[pull_request(extra="unexpected")]),
            source(pull_requests=[{"number": 7, "url": f"{REPOSITORY}/pull/7"}]),
            source(pull_requests=[pull_request(), pull_request(applies_to="before")]),
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_source(value)
        maximum = pull_request(title="x" * 300)
        self.assertEqual(
            parse_source(source(pull_requests=[maximum]))["pull_requests"], [maximum]
        )


class ReadSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="source-contract-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "source.json"

    def test_rejects_invalid_json_null_duplicates_and_non_regular_files(self):
        for text in (
            "not json",
            "null",
            "{} {}",
            json.dumps(source())[:-1] + ',"forge":"github","forge":"github"}',
        ):
            self.path.write_text(text, encoding="utf-8")
            with self.subTest(text=text), self.assertRaises(ValueError):
                read_source(self.path)
        with self.assertRaises(ValueError):
            read_source(self.path.parent / "missing.json")
        self.path.write_text(json.dumps(source()), encoding="utf-8")
        linked = self.path.parent / "linked.json"
        linked.symlink_to(self.path)
        with self.assertRaises(ValueError):
            read_source(linked)
        with self.assertRaises(ValueError):
            read_source(self.path.parent)

    def test_cli_prints_normalized_json_and_hides_rejected_content(self):
        self.path.write_text(
            json.dumps(source(before_commit=BEFORE.upper())), encoding="utf-8"
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "source.py"), str(self.path)],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(json.loads(result.stdout), parse_source(source()))
        secret = (
            "https://user:synthetic-secret@github.com/synthetic-owner/synthetic-repo"
        )
        self.path.write_text(
            json.dumps(source(repository_url=secret)), encoding="utf-8"
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "source.py"), str(self.path)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("--source-file", result.stderr)
        self.assertNotIn("synthetic-secret", result.stderr)
        self.assertNotIn(str(self.path), result.stderr)


if __name__ == "__main__":
    unittest.main()
