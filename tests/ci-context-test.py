#!/usr/bin/env python3
"""Synthetic CI-context detection; no CI runner, models, forges, or network."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(SCRIPTS))
import ci_context
from ci_context import detect_ci_context, parse_ci_context

GITHUB = "https://github.com/synthetic-owner/synthetic-repo"
GITLAB = "https://gitlab.example.invalid/synthetic-group/synthetic-project"
FORK = "https://gitlab.example.invalid/synthetic-fork/synthetic-project"
SECRET = "synthetic-job-token-secret"
COMMIT = "c" * 40


def github_env(**changes):
    value = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REPOSITORY": "synthetic-owner/synthetic-repo",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_SHA": COMMIT,
        "GITHUB_REF": "refs/heads/synthetic-branch",
    }
    value.update(changes)
    return value


def gitlab_env(**changes):
    value = {
        "GITLAB_CI": "true",
        "CI_PROJECT_URL": GITLAB,
        "CI_PROJECT_PATH": "synthetic-group/synthetic-project",
        "CI_COMMIT_SHA": COMMIT,
        "CI_COMMIT_REF_NAME": "synthetic-branch",
        "CI_REPOSITORY_URL": (
            f"https://gitlab-ci-token:{SECRET}@gitlab.example.invalid/"
            "synthetic-group/synthetic-project.git"
        ),
    }
    value.update(changes)
    return value


def merge_request_env(project=GITLAB, **changes):
    path = project.split("/", 3)[3]
    value = gitlab_env(
        CI_MERGE_REQUEST_IID="7",
        CI_MERGE_REQUEST_TITLE="Synthetic merge request",
        CI_MERGE_REQUEST_PROJECT_URL=GITLAB,
        CI_MERGE_REQUEST_PROJECT_PATH="synthetic-group/synthetic-project",
        CI_PROJECT_URL=project,
        CI_PROJECT_PATH=path,
    )
    value.update(changes)
    return value


def pull_request_payload(**changes):
    request = {
        "number": 12,
        "title": "Synthetic pull request",
        "html_url": f"{GITHUB}/pull/12",
        "head": {"sha": COMMIT, "ref": "synthetic-branch"},
    }
    request.update(changes)
    return {
        "action": "opened",
        "number": 12,
        "repository": {"full_name": "synthetic-owner/synthetic-repo"},
        "pull_request": request,
    }


def comment_payload(**changes):
    issue = {
        "number": 12,
        "title": "Synthetic pull request",
        "html_url": f"{GITHUB}/pull/12",
        "pull_request": {"url": "https://api.github.com/synthetic"},
    }
    issue.update(changes)
    return {
        "action": "created",
        "repository": {"full_name": "synthetic-owner/synthetic-repo"},
        "issue": issue,
        "comment": {"body": f"synthetic comment {SECRET}"},
    }


def context(repository_url=GITHUB, pull_request=None, forge="github"):
    return {
        "forge": forge,
        "repository_url": repository_url,
        "pull_request": pull_request,
    }


def request(number=12, title="Synthetic pull request", url=f"{GITHUB}/pull/12"):
    return {"number": number, "title": title, "url": url}


class EventFileTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ci-context-")
        self.addCleanup(self.temp.cleanup)
        self.event = Path(self.temp.name) / "event.json"

    def detect_event(self, payload, event="pull_request", **changes):
        text = payload if type(payload) is str else json.dumps(payload)
        self.event.write_text(text, encoding="utf-8")
        return detect_ci_context(
            github_env(
                GITHUB_EVENT_NAME=event, GITHUB_EVENT_PATH=str(self.event), **changes
            )
        )


class NoContextTests(unittest.TestCase):
    def test_no_ci_and_non_true_markers_return_none(self):
        self.assertIsNone(detect_ci_context({}))
        for marker in ("false", "1", "TRUE", ""):
            with self.subTest(marker=marker):
                self.assertIsNone(detect_ci_context(github_env(GITHUB_ACTIONS=marker)))
                self.assertIsNone(detect_ci_context(gitlab_env(GITLAB_CI=marker)))

    def test_conflicting_markers_return_none(self):
        both = {**gitlab_env(), **github_env()}
        self.assertIsNone(detect_ci_context(both))

    def test_missing_repository_variables_return_none(self):
        for name in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY"):
            env = github_env()
            del env[name]
            with self.subTest(name=name):
                self.assertIsNone(detect_ci_context(env))
        for name in ("CI_PROJECT_URL", "CI_PROJECT_PATH"):
            env = gitlab_env()
            del env[name]
            with self.subTest(name=name):
                self.assertIsNone(detect_ci_context(env))

    def test_reads_process_environment_only_when_not_given(self):
        with mock.patch.dict(os.environ, github_env(), clear=True):
            self.assertEqual(detect_ci_context(), context())
            self.assertIsNone(detect_ci_context({}))


class GitHubTests(EventFileTest):
    def test_push_is_repository_only_without_commits_or_branches(self):
        detected = detect_ci_context(github_env())
        self.assertEqual(detected, context())
        self.assertNotIn(COMMIT, json.dumps(detected))
        self.assertNotIn("synthetic-branch", json.dumps(detected))
        # A push event never reads a payload, even one naming a pull request.
        self.assertEqual(self.detect_event(pull_request_payload(), "push"), context())
        for event in ("workflow_dispatch", "merge_group", "schedule", None):
            env = github_env(GITHUB_EVENT_PATH=str(self.event))
            if event is None:
                del env["GITHUB_EVENT_NAME"]
            else:
                env["GITHUB_EVENT_NAME"] = event
            with self.subTest(event=event):
                self.assertEqual(detect_ci_context(env), context())

    def test_pull_request_events_link_the_named_request(self):
        for event in ci_context.GITHUB_REQUEST_EVENTS:
            with self.subTest(event=event):
                self.assertEqual(
                    self.detect_event(pull_request_payload(), event),
                    context(pull_request=request()),
                )

    def test_pull_request_url_and_title_are_normalized(self):
        payload = pull_request_payload(
            title="  Synthetic pull request \n",
            html_url=f"{GITHUB.replace('synthetic-owner', 'Synthetic-Owner')}/pull/12/",
        )
        self.assertEqual(self.detect_event(payload), context(pull_request=request()))

    def test_issue_comment_links_only_pull_request_issues(self):
        self.assertEqual(
            self.detect_event(comment_payload(), "issue_comment"),
            context(pull_request=request()),
        )
        plain = comment_payload(html_url=f"{GITHUB}/issues/12")
        del plain["issue"]["pull_request"]
        self.assertEqual(self.detect_event(plain, "issue_comment"), context())
        self.assertNotIn(
            SECRET, json.dumps(self.detect_event(comment_payload(), "issue_comment"))
        )

    def test_enterprise_server_uses_its_own_host(self):
        server = "https://github.example.invalid"
        url = f"{server}/synthetic-owner/synthetic-repo"
        payload = pull_request_payload(html_url=f"{url}/pull/12")
        self.assertEqual(
            self.detect_event(payload, GITHUB_SERVER_URL=server + "/"),
            context(url, request(url=f"{url}/pull/12")),
        )

    def test_unassociated_or_mismatched_requests_keep_repository_only(self):
        for payload in (
            {**pull_request_payload(), "repository": None},
            {**pull_request_payload(), "repository": {"full_name": "other/repo"}},
            {**pull_request_payload(), "repository": {"full_name": 7}},
            {**pull_request_payload(), "pull_request": None},
            {**pull_request_payload(), "pull_request": [12]},
            pull_request_payload(html_url=f"{GITHUB}/pull/13"),
            pull_request_payload(html_url=f"{GITHUB}/issues/12"),
            pull_request_payload(
                html_url="https://github.com/other-owner/synthetic-repo/pull/12"
            ),
            pull_request_payload(
                html_url="https://github.example.invalid/synthetic-owner/"
                "synthetic-repo/pull/12"
            ),
            pull_request_payload(html_url=None),
            pull_request_payload(number=True),
            pull_request_payload(number="12"),
            pull_request_payload(number=0),
            pull_request_payload(number=-12),
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.detect_event(payload), context())

    def test_unsafe_titles_are_omitted_but_request_kept(self):
        for title in ("", "   ", None, 12, "x" * 301, "line\u2028break", "a\x00b"):
            with self.subTest(title=title):
                self.assertEqual(
                    self.detect_event(pull_request_payload(title=title)),
                    context(pull_request=request(title=None)),
                )

    def test_malformed_or_unsafe_event_files_keep_repository_only(self):
        for text in (
            "not json",
            "null",
            "[]",
            "\xff",
            "[" * 100000 + "]" * 100000,
            json.dumps(pull_request_payload())[:-1] + ',"number":12}',
        ):
            with self.subTest(text=text[:20]):
                self.assertEqual(self.detect_event(text), context())
        self.event.write_bytes(b"\xff\xfe\x00")
        self.assertEqual(
            detect_ci_context(
                github_env(
                    GITHUB_EVENT_NAME="pull_request", GITHUB_EVENT_PATH=str(self.event)
                )
            ),
            context(),
        )
        self.event.write_text(json.dumps(pull_request_payload()), encoding="utf-8")
        linked = self.event.parent / "linked.json"
        linked.symlink_to(self.event)
        fifo = self.event.parent / "event.fifo"
        os.mkfifo(fifo)
        for path in ("", str(linked), str(self.event.parent), str(fifo), "missing"):
            env = github_env(GITHUB_EVENT_NAME="pull_request", GITHUB_EVENT_PATH=path)
            with self.subTest(path=path):
                self.assertEqual(detect_ci_context(env), context())

    def test_oversized_event_file_is_not_read(self):
        payload = pull_request_payload()
        with mock.patch.object(ci_context, "MAX_EVENT_BYTES", 64):
            self.assertEqual(self.detect_event(payload), context())
        self.assertEqual(self.detect_event(payload), context(pull_request=request()))

    def test_unsafe_server_or_repository_returns_none(self):
        for changes in (
            {"GITHUB_SERVER_URL": f"https://x-access-token:{SECRET}@github.com"},
            {"GITHUB_SERVER_URL": "http://github.com"},
            {"GITHUB_SERVER_URL": "https://github.com:8443"},
            {"GITHUB_SERVER_URL": "https://github.com/prefix"},
            {"GITHUB_SERVER_URL": "https://gitlab.com"},
            {"GITHUB_REPOSITORY": "synthetic-owner"},
            {"GITHUB_REPOSITORY": "synthetic-owner/synthetic-repo.git"},
            {"GITHUB_REPOSITORY": "synthetic-owner/../synthetic-repo"},
            {"GITHUB_REPOSITORY": "synthetic-owner/synthetic-repo?x=1"},
        ):
            with self.subTest(changes=changes):
                self.assertIsNone(detect_ci_context(github_env(**changes)))


class GitLabTests(unittest.TestCase):
    def test_branch_pipeline_is_repository_only_without_credentials(self):
        detected = detect_ci_context(
            gitlab_env(CI_OPEN_MERGE_REQUESTS="synthetic-group/synthetic-project!7")
        )
        self.assertEqual(detected, context(GITLAB, forge="gitlab"))
        text = json.dumps(detected)
        for hidden in (SECRET, COMMIT, "synthetic-branch", ".git"):
            self.assertNotIn(hidden, text)

    def test_merge_request_pipeline_links_the_request(self):
        url = f"{GITLAB}/-/merge_requests/7"
        self.assertEqual(
            detect_ci_context(merge_request_env()),
            context(GITLAB, request(7, "Synthetic merge request", url), "gitlab"),
        )
        self.assertEqual(
            detect_ci_context(merge_request_env(CI_MERGE_REQUEST_TITLE="\x1b[31mred")),
            context(GITLAB, request(7, None, url), "gitlab"),
        )
        missing_title = merge_request_env()
        del missing_title["CI_MERGE_REQUEST_TITLE"]
        self.assertEqual(
            detect_ci_context(missing_title),
            context(GITLAB, request(7, None, url), "gitlab"),
        )

    def test_fork_merge_request_links_the_owning_target_project(self):
        detected = detect_ci_context(merge_request_env(FORK))
        url = f"{GITLAB}/-/merge_requests/7"
        self.assertEqual(
            detected,
            context(GITLAB, request(7, "Synthetic merge request", url), "gitlab"),
        )
        self.assertNotIn("synthetic-fork", json.dumps(detected))

    def test_unverifiable_merge_requests_keep_the_running_project_only(self):
        other_host = "https://gitlab.other.invalid/synthetic-group/synthetic-project"
        leaked = f"https://u:{SECRET}@gitlab.example.invalid/g/p"
        for changes in (
            {"CI_MERGE_REQUEST_IID": "0"},
            {"CI_MERGE_REQUEST_IID": "07"},
            {"CI_MERGE_REQUEST_IID": "7a"},
            {"CI_MERGE_REQUEST_IID": ""},
            {"CI_MERGE_REQUEST_PROJECT_URL": ""},
            {"CI_MERGE_REQUEST_PROJECT_PATH": "synthetic-group/other-project"},
            {"CI_MERGE_REQUEST_PROJECT_URL": other_host},
            {"CI_MERGE_REQUEST_PROJECT_URL": leaked},
        ):
            with self.subTest(changes=changes):
                detected = detect_ci_context(merge_request_env(FORK, **changes))
                self.assertEqual(detected, context(FORK, forge="gitlab"))
                self.assertNotIn(SECRET, json.dumps(detected))
        no_target = merge_request_env(FORK)
        del no_target["CI_MERGE_REQUEST_PROJECT_URL"]
        self.assertEqual(detect_ci_context(no_target), context(FORK, forge="gitlab"))

    def test_unsafe_or_inconsistent_project_returns_none(self):
        for changes in (
            {"CI_PROJECT_URL": f"https://gitlab-ci-token:{SECRET}@gitlab.com/g/p"},
            {
                "CI_PROJECT_URL": "http://gitlab.example.invalid/g/p",
                "CI_PROJECT_PATH": "g/p",
            },
            {"CI_PROJECT_URL": "https://github.com/g/p", "CI_PROJECT_PATH": "g/p"},
            {"CI_PROJECT_PATH": "synthetic-group/other-project"},
            {"CI_PROJECT_URL": GITLAB + ".git"},
        ):
            with self.subTest(changes=changes):
                self.assertIsNone(detect_ci_context(gitlab_env(**changes)))

    def test_nested_groups_are_preserved(self):
        nested = "https://gitlab.com/synthetic-group/sub-group/synthetic-project"
        detected = detect_ci_context(
            gitlab_env(
                CI_PROJECT_URL=nested,
                CI_PROJECT_PATH="synthetic-group/sub-group/synthetic-project",
            )
        )
        self.assertEqual(detected, context(nested, forge="gitlab"))


class ParseTests(unittest.TestCase):
    def test_accepts_normalized_context_and_is_idempotent(self):
        self.assertIsNone(parse_ci_context(None))
        for value in (
            context(),
            context(pull_request=request()),
            context(pull_request=request(title=None)),
            context(
                GITLAB,
                request(7, "Synthetic", f"{GITLAB}/-/merge_requests/7"),
                "gitlab",
            ),
        ):
            with self.subTest(value=value):
                self.assertEqual(parse_ci_context(value), value)
        loose = context(
            "https://GitHub.com/synthetic-owner/synthetic-repo/",
            request(url="https://GITHUB.COM/synthetic-owner/synthetic-repo/pull/12/"),
        )
        self.assertEqual(parse_ci_context(loose), context(pull_request=request()))

    def test_rejects_shape_commits_and_unsafe_values(self):
        for value in (
            "null",
            [],
            {},
            {"forge": "github", "repository_url": GITHUB},
            {**context(), "before_commit": COMMIT},
            {**context(), "commit": COMMIT},
            context(forge=None),
            context(forge="bitbucket"),
            context(forge="gitlab"),
            context(f"https://user:{SECRET}@github.com/synthetic-owner/synthetic-repo"),
            context(GITHUB + ".git"),
            context(pull_request=[]),
            context(pull_request={**request(), "applies_to": "after"}),
            context(pull_request={"number": 12, "url": f"{GITHUB}/pull/12"}),
            context(pull_request=request(number=True)),
            context(pull_request=request(number=0)),
            context(pull_request=request(number="12")),
            context(pull_request=request(title="")),
            context(pull_request=request(title=" padded")),
            context(pull_request=request(title="a\u202eb")),
            context(pull_request=request(title="x" * 301)),
            context(pull_request=request(url=f"{GITHUB}/pull/13")),
            context(pull_request=request(url="https://github.com/other/repo/pull/12")),
            context(pull_request=request(url=f"{GITHUB}/-/merge_requests/12")),
            context(pull_request=request(url=f"http://{GITHUB[8:]}/pull/12")),
            context(pull_request=request(url=f"{GITHUB}/pull/12?x=1")),
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_ci_context(value)

    def test_parsing_a_frozen_value_ignores_the_environment(self):
        frozen = context(pull_request=request())
        hostile = {**gitlab_env(), **github_env(GITHUB_REPOSITORY="other/repo")}
        with mock.patch.dict(os.environ, hostile, clear=True):
            self.assertEqual(parse_ci_context(frozen), frozen)
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(parse_ci_context(frozen), frozen)


class CommandTests(EventFileTest):
    def run_cli(self, env, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "ci_context.py"), *args],
            capture_output=True,
            text=True,
            env=env,
        )

    def test_prints_normalized_json_or_null(self):
        result = self.run_cli({})
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr), (0, "null\n", "")
        )
        self.event.write_text(json.dumps(comment_payload()), encoding="utf-8")
        result = self.run_cli(
            github_env(
                GITHUB_EVENT_NAME="issue_comment", GITHUB_EVENT_PATH=str(self.event)
            )
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), context(pull_request=request()))
        self.assertNotIn(SECRET, result.stdout + result.stderr)

    def test_hides_credentials_and_rejects_arguments(self):
        result = self.run_cli(merge_request_env(FORK))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(SECRET, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["repository_url"], GITLAB)
        result = self.run_cli(
            gitlab_env(CI_PROJECT_URL=f"https://t:{SECRET}@gitlab.com/g/p")
        )
        self.assertEqual((result.returncode, result.stdout), (0, "null\n"))
        self.assertNotIn(SECRET, result.stderr)
        result = self.run_cli({}, "surplus")
        self.assertEqual((result.returncode, result.stdout), (2, ""))


if __name__ == "__main__":
    unittest.main()
