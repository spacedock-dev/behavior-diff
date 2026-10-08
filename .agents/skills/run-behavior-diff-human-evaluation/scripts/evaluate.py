#!/usr/bin/env python3
"""Private, manual, fixed-source Behavior Diff human-evaluation lifecycle."""

import argparse
import datetime
import hashlib
import io
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import random
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tarfile
import uuid

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugin/skills/behavior-diff/scripts"))
from purpose import read_purpose

SOURCE_REPO = "DataRecce/recce-team"
SOURCE_URL = "https://github.com/DataRecce/recce-team.git"
CASE_COUNT = 5
RECEIPT = "freeze-receipt.json"
SHA = re.compile(r"[0-9a-f]{40}\Z")
CI_MARKERS = (
    "CI",
    "GITHUB_ACTIONS",
    "GITLAB_CI",
    "BUILDKITE",
    "CIRCLECI",
    "TRAVIS",
    "TF_BUILD",
    "JENKINS_URL",
    "TEAMCITY_VERSION",
)


class EvaluationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvaluationError(message)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save_json(path, value, exclusive=False):
    path = Path(path)
    with path.open("x" if exclusive else "w", encoding="utf-8") as stream:
        os.chmod(path, 0o600)
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EvaluationError("Cannot read {}: {}".format(path, exc)) from exc


def within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def no_symlinks(path):
    path = Path(os.path.abspath(str(path.expanduser())))
    for component in (path,) + tuple(path.parents):
        require(
            not component.is_symlink(), "Symlink path is unsafe: {}".format(component)
        )
    return path


def relative_file(value):
    require(
        isinstance(value, str) and value and "\x00" not in value and "\\" not in value,
        "Expected a safe relative file path",
    )
    path = PurePosixPath(value)
    require(
        not path.is_absolute()
        and all(part not in (".", "..", ".git") for part in value.split("/")),
        "Unsafe relative path: {}".format(value),
    )
    require(str(path) == value, "Noncanonical relative path: {}".format(value))
    return path


def private_root(session, must_exist=True):
    session = no_symlinks(Path(session))
    require(
        not within(session, REPO_ROOT.resolve())
        and not within(REPO_ROOT.resolve(), session),
        "Evaluation state must be outside the code repository",
    )
    if must_exist:
        require(
            session.is_dir(), "Session directory does not exist: {}".format(session)
        )
        mode = session.stat().st_mode
        require(mode & 0o077 == 0, "Session root must be private (chmod 700)")
        require(
            session.stat().st_uid == os.getuid(),
            "Session root must belong to this user",
        )
        files(session, include_git=True)
    return session


def files(root, include_git=False, skip_caches=False):
    """Return regular files, rejecting links and special files, including empty dirs' safety."""
    result = []
    root = Path(root)
    require(
        root.is_dir() and not root.is_symlink(), "Unsafe directory: {}".format(root)
    )
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in list(dirs):
            child = Path(directory) / name
            require(not child.is_symlink(), "Symlink is unsafe: {}".format(child))
            if (not include_git and name == ".git") or (
                skip_caches and name == "__pycache__"
            ):
                dirs.remove(name)
        for name in names:
            path = Path(directory) / name
            require(
                not path.is_symlink() and stat.S_ISREG(path.stat().st_mode),
                "Nonregular file is unsafe: {}".format(path),
            )
            if skip_caches and path.suffix in (".pyc", ".pyo"):
                continue
            result.append(path)
    return sorted(result)


def git_environment():
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("GIT_"):
            env.pop(key)
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "core.hooksPath",
            "GIT_CONFIG_VALUE_0": os.devnull,
            "GIT_CONFIG_KEY_1": "commit.gpgSign",
            "GIT_CONFIG_VALUE_1": "false",
        }
    )
    return env


def git(repo, *arguments, allow_failure=False):
    proc = subprocess.run(
        ["git", "-C", str(repo), *arguments], capture_output=True, env=git_environment()
    )
    if not allow_failure and proc.returncode:
        raise EvaluationError(
            "git {} failed: {}".format(
                " ".join(arguments), proc.stderr.decode("utf-8", "replace").strip()
            )
        )
    return proc


def git_text(repo, *arguments):
    return git(repo, *arguments).stdout.decode("utf-8").strip()


def code_fingerprint(root=None):
    root = Path(root or REPO_ROOT).resolve()
    inventory = {}
    targets = (
        root / "plugin",
        root / "bin/behavior-diff",
        root / ".agents/skills/run-behavior-diff-human-evaluation/scripts",
        root / ".agents/skills/run-behavior-diff-human-evaluation/assets",
    )
    for target in targets:
        require(not target.is_symlink(), "Code symlink is unsafe: {}".format(target))
        if target.is_dir():
            entries = files(target, skip_caches=True)
        elif target.is_file():
            entries = [target]
        else:
            continue
        for entry in entries:
            inventory[entry.relative_to(root).as_posix()] = {
                "sha256": digest(entry.read_bytes()),
                "executable": bool(entry.stat().st_mode & 0o111),
            }
    require(inventory, "No local Behavior Diff code found")
    head = git_text(root, "rev-parse", "HEAD")
    fingerprint = digest(
        json.dumps({"head": head, "files": inventory}, sort_keys=True).encode()
    )
    return {
        "root": str(root),
        "head": head,
        "fingerprint": fingerprint,
        "files": inventory,
    }


def changed_files(repo, before, after):
    raw = git(
        repo,
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "-r",
        "-z",
        "--no-renames",
        before,
        after,
    ).stdout.split(b"\0")
    require(raw[-1] == b"", "Malformed git diff-tree output")
    raw.pop()
    require(len(raw) % 2 == 0, "Malformed git name/status pairs")
    return [
        {"status": raw[i].decode("ascii"), "path": raw[i + 1].decode("utf-8")}
        for i in range(0, len(raw), 2)
    ]


def regular_blob(repo, commit, path):
    entry = git(repo, "ls-tree", "-z", commit, "--", path).stdout
    require(
        entry.endswith(b"\0") and entry.count(b"\0") == 1,
        "Missing or ambiguous source file: {}".format(path),
    )
    metadata, found = entry[:-1].split(b"\t", 1)
    mode, kind, blob = metadata.decode("ascii").split()
    require(
        found.decode("utf-8") == path
        and mode in ("100644", "100755")
        and kind == "blob",
        "Source skill must be an existing regular file: {}".format(path),
    )
    return blob


def substantive_change(repo, before, after, path):
    statistics = git(
        repo,
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--ignore-all-space",
        "--ignore-blank-lines",
        "--numstat",
        "-z",
        before,
        after,
        "--",
        path,
    ).stdout
    return bool(statistics) and statistics.split(b"\t", 2)[:2] != [b"0", b"0"]


def enumerate_candidates(repo, tip):
    candidates, excluded = [], []
    rows = git_text(repo, "rev-list", "--parents", tip).splitlines()
    for row in rows:
        sha, *parents = row.split()
        item = {"sha": sha, "parents": parents}
        if len(parents) != 1:
            item["reason"] = "root" if not parents else "merge"
            excluded.append(item)
            continue
        before = parents[0]
        changes = changed_files(repo, before, sha)
        item.update({"before_sha": before, "changes": changes})
        skills = [
            change
            for change in changes
            if PurePosixPath(change["path"]).name == "SKILL.md"
        ]
        reason = None
        if len(skills) != 1 or skills[0]["status"] != "M":
            reason = "not-exactly-one-existing-modified-skill"
        else:
            path = skills[0]["path"]
            try:
                relative_file(path)
                before_blob = regular_blob(repo, before, path)
                after_blob = regular_blob(repo, sha, path)
            except EvaluationError:
                reason = "unsafe-or-nonregular-skill"
            directory = str(PurePosixPath(path).parent)
            prefix = "" if directory == "." else directory + "/"
            if reason is None and any(
                change["path"] != path and change["path"].startswith(prefix)
                for change in changes
            ):
                reason = "companion-change-in-skill-directory"
            if reason is None and not substantive_change(repo, before, sha, path):
                reason = "whitespace-only"
            if reason is None:
                item.update(
                    {
                        "skill_path": path,
                        "before_blob": before_blob,
                        "after_blob": after_blob,
                    }
                )
                candidates.append(item)
        if reason:
            item["reason"] = reason
            excluded.append(item)
    return {
        "reachable_commits": len(rows),
        "candidates": candidates,
        "excluded": excluded,
    }


def case_entry(candidate, case_id):
    return {
        "id": case_id,
        "sha": candidate["sha"],
        "before_sha": candidate["before_sha"],
        "skill_path": candidate["skill_path"],
    }


def snapshot_case(session, entry):
    case = session / "case-{}".format(entry["id"])
    case.mkdir(mode=0o700)
    source = session / "source"
    for filename, commit in (
        ("before.md", entry["before_sha"]),
        ("after.md", entry["sha"]),
    ):
        path = case / filename
        path.write_bytes(
            git(source, "show", "{}:{}".format(commit, entry["skill_path"])).stdout
        )
        path.chmod(0o600)
    patch = case / "patch.diff"
    patch.write_bytes(
        git(
            source,
            "diff",
            "--binary",
            "--no-ext-diff",
            "--no-textconv",
            entry["before_sha"],
            entry["sha"],
            "--",
            entry["skill_path"],
        ).stdout
    )
    patch.chmod(0o600)


def populate_session(session, source_repo=None, seed=None):
    """Populate a new private session. Local source/seed injection is test-only API, not CLI."""
    session = private_root(session, must_exist=False)
    session.mkdir(mode=0o700, parents=True, exist_ok=False)
    try:
        command = [
            "git",
            "clone",
            "--no-checkout",
            "--no-local",
            str(source_repo) if source_repo is not None else SOURCE_URL,
            str(session / "source"),
        ]
        clone_environment = git_environment()
        if source_repo is None:
            require(shutil.which("gh"), "Authenticated GitHub CLI (gh) is required")
            # Local Git configuration stays isolated, but private upstream access
            # still needs an explicit credential provider. Never capture its token.
            clone_environment.update(
                {
                    "GIT_CONFIG_COUNT": "3",
                    "GIT_CONFIG_KEY_2": "credential.helper",
                    "GIT_CONFIG_VALUE_2": "!gh auth git-credential",
                }
            )
        proc = subprocess.run(command, capture_output=True, env=clone_environment)
        (session / "clone.log").write_bytes(proc.stdout + proc.stderr)
        (session / "clone.log").chmod(0o600)
        require(
            proc.returncode == 0,
            "Fixed upstream clone failed; see {}".format(session / "clone.log"),
        )
        source = session / "source"
        tip = git_text(source, "rev-parse", "refs/remotes/origin/main")
        require(SHA.fullmatch(tip), "Upstream main must resolve to a full SHA")
        git(source, "update-ref", "refs/heads/human-evaluation-source", tip)
        sampling = enumerate_candidates(source, tip)
        seed = secrets.randbits(128) if seed is None else seed
        require(
            type(seed) is int and seed >= 0,
            "Sampling seed must be a nonnegative integer",
        )
        order = list(sampling["candidates"])
        random.Random(seed).shuffle(order)
        require(
            len(order) >= CASE_COUNT,
            "Fewer than five eligible commits; no substitutions allowed",
        )
        sampling.update(
            {
                "source_repo": SOURCE_REPO,
                "source_tip": tip,
                "seed": seed,
                "algorithm": "uniform-random.Random-shuffle-v1",
                "order": [item["sha"] for item in order],
            }
        )
        manifest = {
            "schema_version": 1,
            "id": session.name,
            "created_at": now(),
            "source_repo": SOURCE_REPO,
            "source_tip": tip,
            "seed": seed,
            "code": code_fingerprint(),
            "trials": 3,
            "trial_model": "opus",
            "extract_model": "sonnet",
            "cases": [
                case_entry(candidate, index + 1)
                for index, candidate in enumerate(order[:CASE_COUNT])
            ],
            "next_candidate": CASE_COUNT,
            "rejections": [],
        }
        save_json(session / "sampling.json", sampling, exclusive=True)
        for entry in manifest["cases"]:
            snapshot_case(session, entry)
        save_json(session / "session.json", manifest, exclusive=True)
        return manifest
    except Exception:
        # Keep the failed clone/sampling evidence in its private unique directory.
        raise


def init_session():
    base = private_root(
        Path.home() / ".behavior-diff/human-evaluations", must_exist=False
    )
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    identifier = (
        datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
        + uuid.uuid4().hex
    )
    session = base / identifier
    populate_session(session)
    return session


def load_session(session):
    session = private_root(session)
    manifest = read_json(session / "session.json")
    require(
        isinstance(manifest, dict) and manifest.get("schema_version") == 1,
        "Unsupported session manifest",
    )
    require(
        manifest.get("id") == session.name
        and manifest.get("source_repo") == SOURCE_REPO,
        "Manifest must name this session and fixed DataRecce/recce-team source",
    )
    require(
        isinstance(manifest.get("source_tip"), str)
        and SHA.fullmatch(manifest["source_tip"]),
        "Invalid pinned source tip",
    )
    require(
        type(manifest.get("seed")) is int and manifest["seed"] >= 0,
        "Invalid sampling seed",
    )
    require(
        manifest.get("trials") == 3
        and manifest.get("trial_model") == "opus"
        and manifest.get("extract_model") == "sonnet",
        "This protocol fixes three trials and Claude Opus/Sonnet",
    )
    code = manifest.get("code")
    require(
        isinstance(code, dict)
        and code.get("root") == str(REPO_ROOT.resolve())
        and isinstance(code.get("head"), str)
        and isinstance(code.get("fingerprint"), str),
        "Manifest must identify this local code checkout",
    )
    cases = manifest.get("cases")
    require(
        isinstance(cases, list) and len(cases) == CASE_COUNT,
        "Exactly five cases are required",
    )
    seen = set()
    for index, entry in enumerate(cases, 1):
        require(
            isinstance(entry, dict)
            and type(entry.get("id")) is int
            and entry["id"] == index,
            "Case ids must be 1 through 5 in order",
        )
        require(
            all(
                isinstance(entry.get(key), str) and SHA.fullmatch(entry[key])
                for key in ("sha", "before_sha")
            ),
            "Cases must pin full source SHAs",
        )
        require(entry["sha"] not in seen, "Cases must be unique")
        seen.add(entry["sha"])
        relative_file(entry.get("skill_path"))
        require(
            PurePosixPath(entry["skill_path"]).name == "SKILL.md",
            "Only existing SKILL.md edits are eligible",
        )
        require((session / "case-{}".format(index)).is_dir(), "Missing case directory")
    source = session / "source"
    require(
        source.is_dir() and (source / ".git").is_dir(), "Missing private source clone"
    )
    require(
        git_text(source, "rev-parse", "refs/remotes/origin/main")
        == manifest["source_tip"],
        "Pinned upstream main changed",
    )
    sampling = read_json(session / "sampling.json")
    require(
        isinstance(sampling, dict)
        and sampling.get("source_repo") == SOURCE_REPO
        and sampling.get("source_tip") == manifest["source_tip"]
        and sampling.get("seed") == manifest["seed"],
        "Sampling provenance does not match manifest",
    )
    entries = sampling.get("candidates")
    require(
        isinstance(entries, list)
        and all(
            isinstance(item, dict)
            and all(
                isinstance(item.get(key), str)
                for key in ("sha", "before_sha", "skill_path")
            )
            for item in entries
        ),
        "Invalid sampling candidates",
    )
    candidates = {candidate["sha"]: candidate for candidate in entries}
    require(len(candidates) == len(entries), "Duplicate sampled candidates")
    order = sampling.get("order")
    require(
        isinstance(order, list)
        and all(isinstance(item, str) for item in order)
        and len(order) == len(candidates)
        and set(order) == set(candidates),
        "Sampling order must cover every eligible candidate once",
    )
    expected = list(candidates.values())
    random.Random(manifest["seed"]).shuffle(expected)
    require(order == [item["sha"] for item in expected], "Sampling shuffle changed")
    require(
        type(manifest.get("next_candidate")) is int
        and CASE_COUNT <= manifest["next_candidate"] <= len(order),
        "Invalid replacement cursor",
    )
    require(
        isinstance(manifest.get("rejections"), list), "Invalid rejection provenance"
    )
    selected = [
        case_entry(candidates[sha], index + 1)
        for index, sha in enumerate(order[:CASE_COUNT])
    ]
    for cursor, rejection in enumerate(manifest["rejections"], CASE_COUNT):
        require(
            isinstance(rejection, dict)
            and type(rejection.get("case")) is int
            and 1 <= rejection["case"] <= CASE_COUNT
            and isinstance(rejection.get("reason"), str)
            and rejection["reason"].strip()
            and cursor < len(order),
            "Invalid replacement record",
        )
        index = rejection["case"] - 1
        replacement = case_entry(candidates[order[cursor]], index + 1)
        require(
            rejection.get("rejected") == selected[index]
            and rejection.get("replacement") == replacement,
            "Replacement must use the next unused random candidate",
        )
        selected[index] = replacement
    require(
        manifest["next_candidate"] == CASE_COUNT + len(manifest["rejections"])
        and cases == selected,
        "Case selection no longer follows the recorded random order",
    )
    return manifest


def verify_sampling(session, manifest):
    sampling = read_json(session / "sampling.json")
    actual = enumerate_candidates(session / "source", manifest["source_tip"])
    require(
        all(sampling.get(key) == value for key, value in actual.items()),
        "Complete sampling candidates/exclusions no longer match pinned upstream history",
    )


def replace_case(session, case_id, reason):
    session = private_root(session)
    manifest = load_session(session)
    require(
        not (session / RECEIPT).exists() and not (session / "answer-key.json").exists(),
        "Replacement is forbidden after freeze",
    )
    require(
        not any(
            (session / "case-{}".format(index) / "attempt.json").exists()
            for index in range(1, 6)
        ),
        "Replacement is forbidden after any live attempt",
    )
    require(
        type(case_id) is int
        and 1 <= case_id <= CASE_COUNT
        and isinstance(reason, str)
        and reason.strip(),
        "Replacement requires a case 1..5 and a nonempty reason",
    )
    case = session / "case-{}".format(case_id)
    require(
        {path.name for path in case.iterdir()}
        == {"before.md", "after.md", "patch.diff"},
        "Case has authored artifacts; preserve them rather than replacing",
    )
    verify_sampling(session, manifest)
    old = manifest["cases"][case_id - 1]
    verify_source_case(session, old)
    sampling = read_json(session / "sampling.json")
    cursor = manifest["next_candidate"]
    require(cursor < len(sampling["order"]), "No unused eligible candidate remains")
    candidates = {item["sha"]: item for item in sampling["candidates"]}
    replacement = case_entry(candidates[sampling["order"][cursor]], case_id)
    archive = session / "rejected"
    archive.mkdir(mode=0o700, exist_ok=True)
    case.rename(archive / "case-{}-{}".format(case_id, old["sha"]))
    snapshot_case(session, replacement)
    manifest["cases"][case_id - 1] = replacement
    manifest["next_candidate"] = cursor + 1
    manifest["rejections"].append(
        {
            "case": case_id,
            "rejected": old,
            "replacement": replacement,
            "reason": reason.strip(),
            "at": now(),
        }
    )
    save_json(session / "session.json", manifest)
    return replacement


def verify_source_case(session, entry):
    source = session / "source"
    tip = read_json(session / "session.json")["source_tip"]
    require(
        git(
            source, "merge-base", "--is-ancestor", entry["sha"], tip, allow_failure=True
        ).returncode
        == 0,
        "Source case is not reachable from pinned main",
    )
    require(
        git_text(source, "rev-list", "--parents", "-n", "1", entry["sha"]).split()
        == [entry["sha"], entry["before_sha"]],
        "Source case is not a nonmerge parent-child pair",
    )
    changes = changed_files(source, entry["before_sha"], entry["sha"])
    path = entry["skill_path"]
    skill_changes = [
        item for item in changes if PurePosixPath(item["path"]).name == "SKILL.md"
    ]
    require(
        skill_changes == [{"status": "M", "path": path}],
        "Source case is not one existing SKILL.md edit",
    )
    prefix = (
        ""
        if str(PurePosixPath(path).parent) == "."
        else str(PurePosixPath(path).parent) + "/"
    )
    require(
        not any(
            item["path"] != path and item["path"].startswith(prefix) for item in changes
        ),
        "Source case includes companion changes in the skill directory",
    )
    case = session / "case-{}".format(entry["id"])
    for filename, commit in (
        ("before.md", entry["before_sha"]),
        ("after.md", entry["sha"]),
    ):
        regular_blob(source, commit, path)
        require(
            (case / filename).read_bytes()
            == git(source, "show", "{}:{}".format(commit, path)).stdout,
            "Source snapshot bytes changed: {}".format(case / filename),
        )
    expected = git(
        source,
        "diff",
        "--binary",
        "--no-ext-diff",
        "--no-textconv",
        entry["before_sha"],
        entry["sha"],
        "--",
        path,
    ).stdout
    require(
        (case / "patch.diff").read_bytes() == expected, "Source patch bytes changed"
    )
    require(
        substantive_change(source, entry["before_sha"], entry["sha"], path),
        "Source change is whitespace-only or unreadable",
    )


def validate_case(session, entry):
    verify_source_case(session, entry)
    case = session / "case-{}".format(entry["id"])
    scenario = read_json(case / "scenario.json")
    require(isinstance(scenario, dict), "Scenario must be an object")
    target = str(relative_file(scenario.get("file")))
    require(
        PurePosixPath(target).name == "SKILL.md", "Fixture target must remain SKILL.md"
    )
    require(
        isinstance(scenario.get("task"), str) and scenario["task"].strip(),
        "Scenario task must be nonempty",
    )
    try:
        purpose = read_purpose(case / "purpose.json")
    except (OSError, ValueError, TypeError) as exc:
        raise EvaluationError("Missing or invalid reviewed case purpose") from exc
    require(
        purpose is None
        or all(goal["source"] in ("commit", "diff") for goal in purpose["goals"]),
        "Historical purpose must come from the selected commit or diff, not this session",
    )
    fixture = case / "fixture"
    files(fixture)
    require(
        (fixture / ".git").is_dir() and not (fixture / ".git").is_symlink(),
        "Fixture must have its own committed Before git repository",
    )
    require(
        git_text(fixture, "rev-parse", "--show-toplevel") == str(fixture),
        "Fixture git root escaped its directory",
    )
    alternates = fixture / ".git/objects/info/alternates"
    require(
        not alternates.exists() or not alternates.read_bytes().strip(),
        "Fixture may not use external object alternates",
    )
    require(
        all(
            not row.startswith(b"160000 ")
            for row in git(fixture, "ls-files", "--stage").stdout.splitlines()
        ),
        "Fixture submodules are not supported",
    )
    regular_blob(fixture, "HEAD", target)
    before = git(fixture, "show", "HEAD:" + target).stdout
    require(
        before == (case / "before.md").read_bytes(),
        "Fixture HEAD target must contain exact Before bytes",
    )
    with tarfile.open(
        fileobj=io.BytesIO(git(fixture, "archive", "--format=tar", "HEAD").stdout)
    ) as archive:
        try:
            member = archive.getmember(target)
        except KeyError as exc:
            raise EvaluationError(
                "Fixture archive omits target (export-ignore is unsafe)"
            ) from exc
        require(
            member.isfile() and archive.extractfile(member).read() == before,
            "Fixture archive must retain exact Before bytes (no export-subst)",
        )
    require(
        (fixture / target).is_file()
        and (fixture / target).read_bytes() == (case / "after.md").read_bytes(),
        "Fixture working target must contain exact After bytes",
    )
    changes = git(fixture, "diff", "--name-status", "-z", "--no-renames", "HEAD").stdout
    require(
        changes == b"M\0" + target.encode("utf-8") + b"\0",
        "After must be the sole working change",
    )
    status = git(
        fixture, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored"
    ).stdout
    require(
        status
        in (
            b" M " + target.encode() + b"\0",
            b"M  " + target.encode() + b"\0",
            b"MM " + target.encode() + b"\0",
        ),
        "Fixture contains untracked, ignored, or extra changes",
    )
    return {
        "file": target,
        "task": scenario["task"],
        "head": git_text(fixture, "rev-parse", "HEAD"),
    }


def frozen_inputs(session, manifest):
    inventory = {}
    fixed = [
        session / name
        for name in (
            "session.json",
            "sampling.json",
            "answer-key.json",
            "public/questions.json",
        )
    ]
    heads = {}
    for entry in manifest["cases"]:
        case = session / "case-{}".format(entry["id"])
        fixed.extend(
            case / name
            for name in (
                "before.md",
                "after.md",
                "patch.diff",
                "scenario.json",
                "question.json",
                "purpose.json",
            )
        )
        fixed.extend(files(case / "fixture"))
        heads[str(entry["id"])] = git_text(case / "fixture", "rev-parse", "HEAD")
    for path in fixed:
        require(
            path.is_file() and not path.is_symlink(),
            "Missing frozen input: {}".format(path),
        )
        inventory[path.relative_to(session).as_posix()] = {
            "sha256": digest(path.read_bytes()),
            "executable": bool(path.stat().st_mode & 0o111),
        }
    return {"files": inventory, "fixture_heads": heads}


def quiz_module():
    path = Path(__file__).with_name("quiz.py")
    spec = importlib.util.spec_from_file_location("behavior_diff_human_quiz", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def hosted_module():
    path = Path(__file__).with_name("hosted.py")
    spec = importlib.util.spec_from_file_location(
        "behavior_diff_hosted_evaluation", path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def freeze_session(session):
    session = private_root(session)
    manifest = load_session(session)
    require(
        not (session / RECEIPT).exists()
        and not (session / "answer-key.json").exists()
        and not (session / "public/questions.json").exists(),
        "Freeze is one-time and cannot overwrite questions/key",
    )
    require(
        not any(
            (session / "case-{}".format(i) / "attempt.json").exists()
            for i in range(1, 6)
        ),
        "Cannot freeze after a live attempt",
    )
    current = code_fingerprint()
    require(
        current == manifest["code"],
        "Local code changed since init; create a fresh session",
    )
    verify_sampling(session, manifest)
    for entry in manifest["cases"]:
        validate_case(session, entry)
    quiz_module().freeze_questions(session, manifest)
    receipt = {
        "schema_version": 1,
        "session_id": manifest["id"],
        "frozen_at": now(),
        "code": current,
        "inputs": frozen_inputs(session, manifest),
    }
    save_json(session / RECEIPT, receipt, exclusive=True)
    return receipt


def verify_frozen(session, manifest=None, check_code=True):
    session = private_root(session)
    manifest = load_session(session) if manifest is None else manifest
    receipt = read_json(session / RECEIPT)
    require(
        isinstance(receipt, dict)
        and receipt.get("schema_version") == 1
        and receipt.get("session_id") == manifest["id"]
        and receipt.get("code") == manifest["code"],
        "Invalid frozen receipt",
    )
    require(
        receipt.get("inputs") == frozen_inputs(session, manifest),
        "Frozen inputs drifted; never run edited cases",
    )
    for entry in manifest["cases"]:
        validate_case(session, entry)
    if check_code:
        require(
            code_fingerprint() == receipt["code"],
            "Local code/HEAD changed after freeze; create a fresh session",
        )


LAUNCHER = """#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys, threading, uuid
REAL = __REAL__
LOGS = pathlib.Path(__LOGS__)
SAFETY = ['--safe-mode', '--restricted', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
          '--setting-sources', '', '--settings', '{"disableAllHooks":true}', '--no-chrome',
          '--disable-slash-commands', '--tools', 'Read,Grep,Glob', '--permission-mode', 'dontAsk',
          '--no-session-persistence']
os.umask(0o077)
call = LOGS / uuid.uuid4().hex
call.mkdir(mode=0o700)
command = [REAL] + sys.argv[1:] + SAFETY
(call / 'invocation.json').write_text(json.dumps({'command': command, 'cwd': os.getcwd(),
                                               'effective_tools': ['Read', 'Grep', 'Glob']}))
proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
def copy(source, destination, filename):
    with (call / filename).open('wb') as log:
        while True:
            data = source.read1(65536)
            if not data:
                break
            log.write(data)
            log.flush()
            destination.write(data)
            destination.flush()
threads = [threading.Thread(target=copy, args=(proc.stdout, sys.stdout.buffer, 'stdout.log')),
           threading.Thread(target=copy, args=(proc.stderr, sys.stderr.buffer, 'stderr.log'))]
for thread in threads:
    thread.start()
status = proc.wait()
for thread in threads:
    thread.join()
(call / 'exit.json').write_text(json.dumps({'returncode': status}))
sys.exit(status)
"""


def prepare_launcher(session):
    # Resolve before adding the private bin to PATH: never recursively invoke our wrapper.
    real = shutil.which("claude")
    require(
        real is not None, "Real Claude executable is required for approved live runs"
    )
    real = Path(real).resolve()
    require(
        real.is_file() and os.access(real, os.X_OK) and not within(real, session),
        "Claude must resolve to a real executable outside this session",
    )
    require(
        shutil.which("jq") is not None, "jq is required by the unchanged local runner"
    )
    binary = session / "bin"
    binary.mkdir(mode=0o700, exist_ok=True)
    logs = session / "launcher-logs"
    logs.mkdir(mode=0o700, exist_ok=True)
    content = LAUNCHER.replace("__REAL__", repr(str(real))).replace(
        "__LOGS__", repr(str(logs))
    )
    deny_open = "#!/bin/sh\nprintf '%s\\n' 'Full reports are gated until quiz submission.' >&2\nexit 1\n"
    for name, body in (("claude", content), ("open", deny_open)):
        launcher = binary / name
        if launcher.exists():
            require(
                launcher.read_text() == body,
                "Existing {} launcher differs from the enforced guard".format(name),
            )
        else:
            with launcher.open("x") as stream:
                stream.write(body)
            launcher.chmod(0o700)
    return {
        "real_executable": str(real),
        "launcher": str(binary / "claude"),
        "sha256": digest(content.encode()),
        "open_denial_sha256": digest(deny_open.encode()),
        "tools": ["Read", "Grep", "Glob"],
        "trials": 3,
        "trial_model": "opus",
        "extract_model": "sonnet",
    }


def trace_evidence(trace, project, target):
    events, malformed = [], 0
    if trace.is_file():
        for line in trace.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    events.append(value)
                else:
                    malformed += 1
            except ValueError:
                malformed += 1
    models, advertised_tools, used_tools, reads, responses, costs = (
        set(),
        set(),
        [],
        [],
        {},
        [],
    )
    final = []
    for event in events:
        if isinstance(event.get("model"), str):
            models.add(event["model"])
        for tool in (
            event.get("tools", []) if isinstance(event.get("tools"), list) else []
        ):
            if isinstance(tool, str):
                advertised_tools.add(tool)
        message = event.get("message", {})
        if not isinstance(message, dict):
            continue
        if isinstance(message.get("model"), str):
            models.add(message["model"])
        content = message.get("content", [])
        if not isinstance(content, list):
            content = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                used_tools.append(block.get("name"))
                if block.get("name") == "Read":
                    arguments = block.get("input", {})
                    path = (
                        arguments.get("file_path", "")
                        if isinstance(arguments, dict)
                        else ""
                    )
                    reads.append({"id": block.get("id"), "path": path})
            elif block.get("type") == "tool_result":
                responses[block.get("tool_use_id")] = block
        if event.get("type") == "result":
            final.append(event)
            if isinstance(event.get("total_cost_usd"), (int, float)):
                costs.append(event["total_cost_usd"])
    successful, missing, failed, unmatched, target_success = 0, 0, 0, 0, 0
    for read in reads:
        response = responses.get(read["id"])
        if response is None:
            read["outcome"] = "unmatched"
            unmatched += 1
        elif response.get("is_error"):
            text = json.dumps(response.get("content", "")).lower()
            absent = any(
                term in text for term in ("does not exist", "no such file", "not found")
            )
            read["outcome"] = "missing" if absent else "failed"
            missing += int(absent)
            failed += int(not absent)
        else:
            read["outcome"] = "success"
            successful += 1
            if isinstance(read["path"], str):
                path = Path(read["path"])
                if not path.is_absolute():
                    path = project / path
                if os.path.normpath(str(path)) == str(project / target):
                    target_success += 1
    success = any(
        event.get("result")
        and not event.get("is_error")
        and event.get("subtype", "success") == "success"
        for event in final
    )
    return {
        "actual_models": sorted(models),
        "advertised_tools": sorted(advertised_tools),
        "used_tools": used_tools,
        "success": bool(success),
        "malformed_events": malformed,
        "source_reads": {
            "successful": successful,
            "missing": missing,
            "failed": failed,
            "unmatched": unmatched,
            "successful_target": target_success,
            "calls": reads,
        },
        "cost_usd": sum(costs) if costs else None,
        "usage": [event.get("usage") for event in final if "usage" in event],
    }


def launcher_evidence(session, case):
    logs = session / "launcher-logs"
    calls = []
    if not logs.is_dir():
        return calls
    for call in sorted(logs.iterdir()):
        invocation = read_json(call / "invocation.json")
        cwd = Path(invocation["cwd"])
        if not within(cwd, case):
            continue
        command = invocation["command"]
        model = command[command.index("--model") + 1] if "--model" in command else None
        exit_path = call / "exit.json"
        calls.append(
            {
                "path": str(call.relative_to(session)),
                "cwd": str(cwd.relative_to(session)),
                "requested_model": model,
                "enforced_tools": invocation["effective_tools"],
                "exit_code": read_json(exit_path)["returncode"]
                if exit_path.exists()
                else None,
                "logs": {
                    name: digest((call / name).read_bytes())
                    if (call / name).is_file()
                    else None
                    for name in (
                        "invocation.json",
                        "stdout.log",
                        "stderr.log",
                        "exit.json",
                    )
                },
            }
        )
    return calls


def collect_evidence(session, entry, scenario, exit_code, settings):
    case = session / "case-{}".format(entry["id"])
    runs_root = case / "state/runs"
    runs = (
        sorted(path for path in runs_root.iterdir() if path.is_dir())
        if runs_root.is_dir()
        else []
    )
    evidence = {
        "session_id": session.name,
        "case": entry["id"],
        "finished_at": now(),
        "runner_exit_code": exit_code,
        "settings": settings,
        "runs": [path.name for path in runs],
        "trials": [],
        "artifacts": {},
        "blocked_reasons": [],
        "launcher_calls": launcher_evidence(session, case),
    }
    if len(runs) != 1:
        evidence["blocked_reasons"].append(
            "expected exactly one report run, found {}".format(len(runs))
        )
    else:
        run = runs[0]
        targets = case / "trial-targets"
        targets.mkdir(mode=0o700)
        for variant in ("before", "after"):
            expected = (case / (variant + ".md")).read_bytes()
            for index in range(1, 4):
                trial_id = "{}-{}".format(variant, index)
                trial = run / trial_id
                project = trial / "project"
                item = trace_evidence(trial / "trace.jsonl", project, scenario["file"])
                item["id"] = trial_id
                target = project / scenario["file"]
                item["target_present"] = target.is_file() and not target.is_symlink()
                if item["target_present"]:
                    data = target.read_bytes()
                    saved = targets / (trial_id + ".md")
                    saved.write_bytes(data)
                    saved.chmod(0o600)
                    item.update(
                        {
                            "target_sha256": digest(data),
                            "target_matches_frozen": data == expected,
                        }
                    )
                else:
                    item["target_matches_frozen"] = False
                if (
                    not item["success"]
                    or not item["target_matches_frozen"]
                    or item["malformed_events"]
                    or not item["source_reads"]["successful_target"]
                    or any(
                        tool not in ("Read", "Grep", "Glob")
                        for tool in item["used_tools"]
                    )
                ):
                    evidence["blocked_reasons"].append(
                        "{}: missing/invalid result, target bytes/read, or unsafe tools".format(
                            trial_id
                        )
                    )
                evidence["trials"].append(item)
        for filename in (
            "report.html",
            "report.md",
            "report-data.json",
            "decisions.json",
        ):
            path = run / filename
            evidence["artifacts"][filename] = (
                {
                    "path": str(path.relative_to(session)),
                    "sha256": digest(path.read_bytes()),
                }
                if path.is_file()
                else None
            )
    evidence["blocked"] = bool(evidence["blocked_reasons"])
    costs = [
        item["cost_usd"] for item in evidence["trials"] if item["cost_usd"] is not None
    ]
    evidence["cost_usd"] = sum(costs) if costs else None
    evidence["cost_scope"] = (
        "Retained trial result events only; extraction cost unavailable unless retained in launcher logs."
    )
    save_json(case / "run-evidence.json", evidence, exclusive=True)
    return evidence


def run_session(session, approve_live=False, case_id=None):
    session = private_root(session)
    manifest = load_session(session)
    require(approve_live is True, "Live model calls require explicit --approve-live")
    require(
        not any(marker in os.environ for marker in CI_MARKERS),
        "Live human evaluations are forbidden in CI",
    )
    verify_frozen(session, manifest)
    require(
        case_id is None or type(case_id) is int and 1 <= case_id <= CASE_COUNT,
        "Case must be 1..5",
    )
    cases = manifest["cases"] if case_id is None else [manifest["cases"][case_id - 1]]
    # Refuse the whole requested batch before any calls if one case already has an attempt.
    for entry in cases:
        case = session / "case-{}".format(entry["id"])
        require(
            not (case / "attempt.json").exists(),
            "Case {} was already attempted; never retry".format(entry["id"]),
        )
        require(
            not (case / "state").exists() and not (case / "trial-targets").exists(),
            "Case contains prior live state; never overwrite it",
        )
    settings = prepare_launcher(session)
    env = git_environment()
    env["PATH"] = str(session / "bin") + os.pathsep + env.get("PATH", "")
    env["BEHAVIOR_DIFF_TRIAL"] = "1"
    env.pop("CLAUDECODE", None)
    runner = REPO_ROOT / "plugin/skills/behavior-diff/scripts/behavior-diff.sh"
    failures = []
    completed = []
    for entry in cases:
        verify_frozen(session, manifest)
        case = session / "case-{}".format(entry["id"])
        scenario = validate_case(session, entry)
        command = [
            "bash",
            str(runner),
            "--agent",
            "claude",
            "--trials",
            "3",
            "--model",
            "opus",
            "--extract-agent",
            "claude",
            "--extract-model",
            "sonnet",
            "--file",
            scenario["file"],
            "--task",
            scenario["task"],
            "--purpose-file",
            str(case / "purpose.json"),
        ]
        save_json(
            case / "attempt.json",
            {
                "started_at": now(),
                "command": command,
                "settings": settings,
                "approved_live": True,
                "frozen_receipt_sha256": digest((session / RECEIPT).read_bytes()),
            },
            exclusive=True,
        )
        (case / "state").mkdir(mode=0o700)
        env["BEHAVIOR_DIFF_HOME"] = str(case / "state")
        try:
            with (case / "runner.log").open("xb") as log:
                os.chmod(case / "runner.log", 0o600)
                proc = subprocess.run(
                    command,
                    cwd=case / "fixture",
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
            status = proc.returncode
        except OSError as exc:
            status = None
            save_json(case / "launch-error.json", {"error": str(exc)}, exclusive=True)
        evidence = collect_evidence(session, entry, scenario, status, settings)
        completed.append(evidence)
        if any(
            evidence["artifacts"].get(name) is None
            for name in ("report.html", "report.md", "report-data.json")
        ):
            failures.append(
                "case {} has no complete report; retained evidence at {}".format(
                    entry["id"], case
                )
            )
    require(not failures, "; ".join(failures))
    return completed


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "init", help="Create a fresh private session from fixed upstream main"
    )
    for name in (
        "replace",
        "freeze",
        "run",
        "build",
        "serve",
        "results",
        "export-package",
        "hosted-results",
    ):
        command = commands.add_parser(name)
        command.add_argument("session", type=Path)
        if name == "replace":
            command.add_argument("--case", type=int, required=True, choices=range(1, 6))
            command.add_argument("--reason", required=True)
        elif name == "run":
            command.add_argument("--approve-live", action="store_true")
            command.add_argument("--case", type=int, choices=range(1, 6))
        elif name == "serve":
            command.add_argument("--port", type=int, default=0)
        elif name == "export-package":
            command.add_argument("--evaluation-id", required=True)
            command.add_argument("--title", required=True)
            command.add_argument("--out", required=True, type=Path)
        elif name == "hosted-results":
            command.add_argument("--package", required=True, type=Path)
            command.add_argument("--responses", required=True, type=Path)
    return cli


def main(arguments=None):
    args = parser().parse_args(arguments)
    try:
        if args.command == "init":
            print(init_session())
            return 0
        session = private_root(args.session)
        manifest = load_session(session)
        if args.command == "replace":
            print(json.dumps(replace_case(session, args.case, args.reason), indent=2))
        elif args.command == "freeze":
            freeze_session(session)
            print(str(session / RECEIPT))
        elif args.command == "run":
            evidence = run_session(session, args.approve_live, args.case)
            print(
                json.dumps(
                    [
                        {
                            "case": item["case"],
                            "blocked": item["blocked"],
                            "artifacts": item["artifacts"],
                        }
                        for item in evidence
                    ],
                    indent=2,
                )
            )
        else:
            verify_frozen(session, manifest, check_code=False)
            quiz = quiz_module()
            if args.command == "build":
                quiz.build_quiz(session, REPO_ROOT)
                print(str(session / "public/index.html"))
            elif args.command == "serve":
                require(0 <= args.port <= 65535, "Port must be 0..65535")
                quiz.serve(session, args.port)
            elif args.command == "results":
                print(json.dumps(quiz.results(session), indent=2, ensure_ascii=False))
            elif args.command == "export-package":
                result = hosted_module().export_package(
                    session, quiz, REPO_ROOT, args.evaluation_id, args.title, args.out
                )
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif args.command == "hosted-results":
                result = hosted_module().analyze_responses(
                    session, quiz, REPO_ROOT, args.package, args.responses
                )
                print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (EvaluationError, OSError, ValueError) as exc:
        print("human evaluation: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
