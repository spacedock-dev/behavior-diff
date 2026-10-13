#!/usr/bin/env python3
"""Validate caller-supplied historical source provenance for a Git history report.

The caller owns provenance: this module checks shape and URL safety only. It
never infers a repository, commit, or pull request and never contacts a forge.
"""

import argparse
import json
from pathlib import Path
import re
import sys

FORGES = ("github", "gitlab")
KNOWN_HOSTS = {"github.com": "github", "gitlab.com": "gitlab"}
APPLIES_TO = ("before", "after", "both")
SOURCE_FIELDS = {
    "forge",
    "repository_url",
    "before_commit",
    "after_commit",
    "pull_requests",
}
REQUIRED_FIELDS = {"repository_url", "before_commit", "after_commit"}
PULL_REQUEST_FIELDS = {"number", "title", "url", "applies_to"}
MAX_PULL_REQUESTS = 20
MAX_TITLE = 300
MAX_URL = 512
HOST = re.compile(
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?"
)
SEGMENT = re.compile(r"(?!\.{1,2}\Z)[A-Za-z0-9._-]{1,100}")
COMMIT = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")
# C0/C1 controls, line separators, and bidirectional overrides.
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202e\u2066-\u2069]")


def _repository(raw, forge):
    if type(raw) is not str or len(raw) > MAX_URL or not raw.startswith("https://"):
        raise ValueError("repository_url must be an https URL")
    host, _, path = raw[len("https://") :].partition("/")
    host = host.lower()
    # Rejecting ':' and '@' in the host excludes ports and embedded credentials.
    if not HOST.fullmatch(host):
        raise ValueError("repository_url needs a plain host name")
    if path.endswith("/"):
        path = path[:-1]
    segments = path.split("/")
    if not all(SEGMENT.fullmatch(segment) for segment in segments):
        raise ValueError("repository_url path must be repository segments only")
    if segments[-1].lower().endswith(".git"):
        raise ValueError("repository_url must be the web URL, not a clone URL")
    inferred = KNOWN_HOSTS.get(host)
    if forge is None:
        if inferred is None:
            raise ValueError("forge is required for a self-hosted repository")
        forge = inferred
    elif type(forge) is not str or forge not in FORGES:
        raise ValueError("forge must be github or gitlab")
    elif inferred is not None and inferred != forge:
        raise ValueError("forge does not match the repository host")
    if forge == "github" and len(segments) != 2:
        raise ValueError("GitHub repository_url must be https://host/owner/repo")
    if forge == "gitlab" and (len(segments) < 2 or "-" in segments):
        raise ValueError("GitLab repository_url must be https://host/group/project")
    return forge, f"https://{host}/{'/'.join(segments)}"


def _commit(raw, field):
    if type(raw) is not str or not COMMIT.fullmatch(raw.lower()):
        raise ValueError(f"{field} must be a full 40- or 64-character hex commit")
    return raw.lower()


def _pull_request(raw, forge, repository_url):
    if type(raw) is not dict or set(raw) != PULL_REQUEST_FIELDS:
        raise ValueError("pull request needs number, title, url, and applies_to")
    number = raw["number"]
    if type(number) is not int or number < 1:
        raise ValueError("pull request number must be a positive integer")
    title = raw["title"]
    if (
        type(title) is not str
        or not 1 <= len(title) <= MAX_TITLE
        or title != title.strip()
        or CONTROL.search(title)
    ):
        raise ValueError("pull request title must be short plain text")
    if type(raw["applies_to"]) is not str or raw["applies_to"] not in APPLIES_TO:
        raise ValueError("pull request applies_to must be before, after, or both")
    kind = "pull" if forge == "github" else "-/merge_requests"
    expected = f"{repository_url}/{kind}/{number}"
    url = raw["url"]
    if type(url) is not str or not url.startswith("https://"):
        raise ValueError("pull request url must match the repository and number")
    host, _, path = url[len("https://") :].partition("/")
    if f"https://{host.lower()}/{path.removesuffix('/')}" != expected:
        raise ValueError("pull request url must match the repository and number")
    return {
        "number": number,
        "title": title,
        "url": expected,
        "applies_to": raw["applies_to"],
    }


def parse_source(value):
    """Return normalized source provenance, None for None, or raise ValueError."""
    if value is None:
        return None
    if type(value) is not dict or not REQUIRED_FIELDS <= set(value) <= SOURCE_FIELDS:
        raise ValueError(
            "source needs repository_url, before_commit, and after_commit only"
        )
    if "forge" in value and value["forge"] is None:
        raise ValueError("forge must be github or gitlab")
    forge, repository_url = _repository(value["repository_url"], value.get("forge"))
    before = _commit(value["before_commit"], "before_commit")
    after = _commit(value["after_commit"], "after_commit")
    if len(before) != len(after):
        raise ValueError("before_commit and after_commit must use one hash format")
    if before == after:
        raise ValueError("before_commit and after_commit must differ")
    raw_pull_requests = value.get("pull_requests", [])
    if (
        type(raw_pull_requests) is not list
        or len(raw_pull_requests) > MAX_PULL_REQUESTS
    ):
        raise ValueError(f"pull_requests must be a list of at most {MAX_PULL_REQUESTS}")
    pull_requests = [
        _pull_request(item, forge, repository_url) for item in raw_pull_requests
    ]
    if len({item["number"] for item in pull_requests}) != len(pull_requests):
        raise ValueError("pull_requests must not repeat a number")
    return {
        "forge": forge,
        "repository_url": repository_url,
        "before_commit": before,
        "after_commit": after,
        "pull_requests": pull_requests,
    }


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate source JSON field")
        result[key] = value
    return result


def read_source(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Source must be a regular JSON file")
    with path.open(encoding="utf-8") as stream:
        raw = json.load(stream, object_pairs_hook=unique_object)
    if raw is None:
        raise ValueError("Source file must contain an object")
    return parse_source(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        source = read_source(args.file)
    except (OSError, ValueError, TypeError):
        # Do not echo rejected content: a malformed URL can carry credentials.
        print(
            "behavior-diff: invalid --source-file JSON; use {repository_url,"
            "before_commit,after_commit[,forge][,pull_requests]} with an https "
            "GitHub/GitLab web URL (no credentials, port, query, or fragment), "
            "full 40- or 64-hex distinct commits, forge github|gitlab (required "
            "for self-hosted), and at most 20 pull_requests "
            "{number,title,url,applies_to} whose url matches the repository and "
            "number; applies_to before|after|both",
            file=sys.stderr,
        )
        return 2
    print(json.dumps(source, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
