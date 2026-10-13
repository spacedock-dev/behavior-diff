#!/usr/bin/env python3
"""Detect report-only CI repository and PR/MR links for a Behavior Diff run.

The context names where a GitHub Actions or GitLab CI comparison ran. It never
describes what Before or After contain: it carries no commits, and workflow
SHAs or branches are never read. Detection reads only whitelisted variables
and event fields, never CI_REPOSITORY_URL (it embeds a job token), and drops a
field or the whole context instead of guessing. `parse_ci_context` strictly
validates a frozen value so reports render without the CI environment.
"""

import argparse
import json
import os
import re
import stat

from source import CONTROL, FORGES, MAX_TITLE, _repository, unique_object

FIELDS = {"forge", "repository_url", "pull_request"}
PULL_REQUEST_FIELDS = {"number", "title", "url"}
# GitHub caps webhook payloads at 25 MB; a request event needs far less.
MAX_EVENT_BYTES = 4 * 1024 * 1024
# Events whose payload names exactly one pull request in `pull_request`.
GITHUB_REQUEST_EVENTS = (
    "pull_request",
    "pull_request_target",
    "pull_request_review",
    "pull_request_review_comment",
)
IID = re.compile(r"[1-9][0-9]{0,17}")


def request_url(forge, repository_url, number):
    kind = "pull" if forge == "github" else "-/merge_requests"
    return f"{repository_url}/{kind}/{number}"


def _title(raw):
    if raw is None:
        return None
    if (
        type(raw) is not str
        or not 1 <= len(raw) <= MAX_TITLE
        or raw != raw.strip()
        or CONTROL.search(raw)
    ):
        raise ValueError("pull request title must be short plain text or null")
    return raw


def _pull_request(raw, forge, repository_url):
    if raw is None:
        return None
    if type(raw) is not dict or set(raw) != PULL_REQUEST_FIELDS:
        raise ValueError("pull_request needs number, title, and url only")
    number = raw["number"]
    if type(number) is not int or number < 1:
        raise ValueError("pull request number must be a positive integer")
    title = _title(raw["title"])
    expected = request_url(forge, repository_url, number)
    url = raw["url"]
    if type(url) is not str or not url.startswith("https://"):
        raise ValueError("pull request url must match the repository and number")
    host, _, path = url[len("https://") :].partition("/")
    if f"https://{host.lower()}/{path.removesuffix('/')}" != expected:
        raise ValueError("pull request url must match the repository and number")
    return {"number": number, "title": title, "url": expected}


def parse_ci_context(value):
    """Return normalized CI context, None for None, or raise ValueError."""
    if value is None:
        return None
    if type(value) is not dict or set(value) != FIELDS:
        raise ValueError(
            "ci_context needs forge, repository_url, and pull_request only"
        )
    if type(value["forge"]) is not str or value["forge"] not in FORGES:
        raise ValueError("ci_context forge must be github or gitlab")
    forge, repository_url = _repository(value["repository_url"], value["forge"])
    return {
        "forge": forge,
        "repository_url": repository_url,
        "pull_request": _pull_request(value["pull_request"], forge, repository_url),
    }


def _detected_title(raw):
    """Keep a detected title only when it is already safe plain text."""
    try:
        return _title(raw.strip() if type(raw) is str else raw)
    except ValueError:
        return None


def _read_event(path):
    """Return a bounded GitHub event object from a regular file, else None."""
    if type(path) is not str or not path:
        return None
    # O_NONBLOCK keeps a FIFO swapped in for the event file from blocking open.
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_EVENT_BYTES:
                return None
            data = stream.read(MAX_EVENT_BYTES + 1)
        if len(data) > MAX_EVENT_BYTES:
            return None
        payload = json.loads(data, object_pairs_hook=unique_object)
    except (OSError, ValueError, RecursionError):
        return None
    return payload if type(payload) is dict else None


def _github_request(env, repository, repository_url):
    event = env.get("GITHUB_EVENT_NAME")
    if event in GITHUB_REQUEST_EVENTS:
        field = "pull_request"
    elif event == "issue_comment":
        field = "issue"
    else:
        return None
    payload = _read_event(env.get("GITHUB_EVENT_PATH"))
    if payload is None:
        return None
    owner = payload.get("repository")
    if (
        type(owner) is not dict
        or type(owner.get("full_name")) is not str
        or owner["full_name"].lower() != repository.lower()
    ):
        return None
    request = payload.get(field)
    if type(request) is not dict:
        return None
    # An issue comment names a PR only when its issue carries a PR object.
    if field == "issue" and type(request.get("pull_request")) is not dict:
        return None
    number = request.get("number")
    if type(number) is not int or number < 1:
        return None
    url = request_url("github", repository_url, number)
    html_url = request.get("html_url")
    # GitHub owner and repository names are case-insensitive.
    if type(html_url) is not str or html_url.removesuffix("/").lower() != url.lower():
        return None
    return {
        "number": number,
        "title": _detected_title(request.get("title")),
        "url": url,
    }


def _github(env):
    server = env.get("GITHUB_SERVER_URL")
    repository = env.get("GITHUB_REPOSITORY")
    if type(server) is not str or type(repository) is not str:
        return None
    if not server or not repository:
        return None
    try:
        _, repository_url = _repository(
            f"{server.removesuffix('/')}/{repository}", "github"
        )
    except ValueError:
        return None
    return {
        "forge": "github",
        "repository_url": repository_url,
        "pull_request": _github_request(env, repository, repository_url),
    }


def _gitlab_project(url, path):
    """Return a project web URL whose path matches its declared project path."""
    if type(url) is not str or type(path) is not str or not url or not path:
        return None
    try:
        _, normalized = _repository(url, "gitlab")
    except ValueError:
        return None
    if normalized.split("/", 3)[3].lower() != path.lower():
        return None
    return normalized


def _host(url):
    return url.split("/", 3)[2]


def _gitlab(env):
    project = _gitlab_project(env.get("CI_PROJECT_URL"), env.get("CI_PROJECT_PATH"))
    if project is None:
        return None
    iid = env.get("CI_MERGE_REQUEST_IID")
    # A fork MR lives in its target project, so link that owning project.
    target = _gitlab_project(
        env.get("CI_MERGE_REQUEST_PROJECT_URL"),
        env.get("CI_MERGE_REQUEST_PROJECT_PATH"),
    )
    if (
        type(iid) is not str
        or not IID.fullmatch(iid)
        or target is None
        or _host(target) != _host(project)
    ):
        return {"forge": "gitlab", "repository_url": project, "pull_request": None}
    number = int(iid)
    return {
        "forge": "gitlab",
        "repository_url": target,
        "pull_request": {
            "number": number,
            "title": _detected_title(env.get("CI_MERGE_REQUEST_TITLE")),
            "url": request_url("gitlab", target, number),
        },
    }


def detect_ci_context(environ=None):
    """Return normalized GitHub Actions or GitLab CI context, else None."""
    env = os.environ if environ is None else environ
    github = env.get("GITHUB_ACTIONS") == "true"
    gitlab = env.get("GITLAB_CI") == "true"
    if github == gitlab:  # Neither CI, or conflicting markers.
        return None
    detected = _github(env) if github else _gitlab(env)
    return parse_ci_context(detected)


def main():
    parser = argparse.ArgumentParser(
        description="Print detected CI context as normalized JSON, or null."
    )
    parser.parse_args()
    print(json.dumps(detect_ci_context(), ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
