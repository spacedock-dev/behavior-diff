#!/usr/bin/env python3
"""Private skill helper: freeze shared files into an isolated runner project.

This does not generate scenarios, launch models, or infer source provenance.
The caller reviews trial-visible files and names private paths to exclude.
"""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tarfile
import unicodedata


class PreparationError(ValueError):
    pass


def check_git_environment():
    # The existing runner inherits this environment. Do not verify one world
    # and then let Git redirect the runner's repository, index, or attributes.
    redirects = {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_NAMESPACE",
        "GIT_SHALLOW",
        "GIT_REPLACE_REF_BASE",
        "GIT_CEILING_DIRECTORIES",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_ATTR_SOURCE",
    }
    if any(
        key in redirects or key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))
        for key in os.environ
    ):
        raise PreparationError(
            "unset Git repository, index, and config overrides before preparation and launch"
        )


def git(project, *args, check=True, launch=False):
    # Isolate construction; read-only handoff checks must match the runner.
    env = None
    if not launch:
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    result = subprocess.run(
        ["git", "--literal-pathspecs", "-C", str(project), *args],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        raise PreparationError(
            "Git could not construct or inspect the isolated snapshot"
        )
    return result


def relative(value):
    path = PurePosixPath(value)
    if (
        not value
        or value == "."
        or path.is_absolute()
        or str(path) != value
        or any(part in (".", "..") or part.lower() == ".git" for part in path.parts)
        or "\\" in value
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise PreparationError("expected a safe project-relative path")
    return value


def within(path, root):
    key, root_key = path_key(str(path)), path_key(str(root))
    return key == root_key or key.startswith(root_key.rstrip("/") + "/")


def path_key(name):
    return unicodedata.normalize("NFC", name).casefold()


def excluded(name, exclusions):
    key = path_key(name)
    return any(
        key == path_key(item) or key.startswith(path_key(item) + "/")
        for item in exclusions
    )


def regular_file(path):
    if not stat.S_ISREG(path.lstat().st_mode):
        raise PreparationError(
            "inputs must be regular files, not links or special files"
        )
    return path.read_bytes(), bool(path.stat().st_mode & 0o111)


def safe_file(root, name):
    path = root
    for part in PurePosixPath(name).parts:
        path = path / part
        if path.is_symlink():
            raise PreparationError("input paths must not traverse symlinks")
    return regular_file(path)


def tree(root, exclusions=(), skip_git=False):
    files = {}

    def visit(folder):
        for path in sorted(folder.iterdir()):
            name = path.relative_to(root).as_posix()
            if (skip_git and name == ".git") or excluded(name, exclusions):
                continue
            relative(name)
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode):
                visit(path)
            elif stat.S_ISREG(mode):
                files[name] = regular_file(path)
            else:
                raise PreparationError(
                    "shared projects cannot contain links or special files"
                )

    visit(root)
    return files


def archive(project, commit, launch=False):
    entries = git(project, "ls-tree", "-r", commit, launch=launch).stdout.splitlines()
    if any(entry.startswith(b"160000 ") for entry in entries):
        raise PreparationError("submodules require an unsupported project setup")
    raw = git(project, "archive", "--format=tar", commit, launch=launch).stdout
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as bundle:
        for entry in bundle:
            name = relative(entry.name.rstrip("/"))
            if entry.isdir():
                continue
            if not entry.isfile():
                raise PreparationError(
                    "Git snapshots cannot contain links or special files"
                )
            if name in files:
                raise PreparationError("duplicate archive path")
            with bundle.extractfile(entry) as stream:
                files[name] = stream.read(), bool(entry.mode & 0o111)
    return files


def inventory(files):
    return {
        name: {"sha256": hashlib.sha256(data).hexdigest(), "executable": executable}
        for name, (data, executable) in sorted(files.items())
    }


def encode(path):
    return str(path).replace("%", "%25").replace("/", "%2F")


def baseline(project, target, commit, before_file, home):
    if before_file is not None:
        return "file", regular_file(before_file)
    if commit is not None:
        found = git(project, "cat-file", "-e", f"{commit}:{target}", check=False)
        if found.returncode == 0:
            entry = git(project, "ls-tree", commit, "--", target).stdout
            if not entry.startswith((b"100644 ", b"100755 ")):
                raise PreparationError("Before instruction must be a regular file")
            return "head", (
                git(project, "show", f"{commit}:{target}").stdout,
                entry.startswith(b"100755 "),
            )
    store = home / "baselines" / encode(project / target)
    if store.is_symlink():
        raise PreparationError("baseline store must not be a symlink")
    candidates = (
        [entry for entry in store.iterdir() if not entry.name.startswith(".")]
        if store.is_dir()
        else []
    )
    if not candidates:
        raise PreparationError(
            "no Before source; supply --before-file or capture a hook baseline"
        )
    selected = max(
        candidates, key=lambda entry: (entry.lstat().st_mtime_ns, entry.name)
    )
    content = regular_file(selected)
    return ("absent", None) if selected.name.endswith("-ABSENT") else ("file", content)


def validate_files(files):
    aliases = {}
    file_keys = {path_key(name) for name in files}
    for name in files:
        relative(name)
        path = PurePosixPath(name)
        for part in (path, *path.parents):
            text = str(part)
            key = path_key(text)
            if key in aliases and aliases[key] != text:
                raise PreparationError(
                    "case-colliding paths are not portable trial inputs"
                )
            aliases[key] = text
        if any(path_key(str(parent)) in file_keys for parent in path.parents):
            raise PreparationError("file and directory paths collide")


def write_files(root, files):
    for name, (data, executable) in sorted(files.items()):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # Also catches filesystem-specific aliases, e.g. Unicode normalization.
        with path.open("xb") as stream:
            stream.write(data)
        path.chmod(0o755 if executable else 0o644)


def prepare(args):
    check_git_environment()
    project = Path(args.project).resolve(strict=True)
    data_path = Path(args.data)
    if data_path.is_symlink():
        raise PreparationError("shared-data directory must not be a symlink")
    data_path = data_path.resolve(strict=True)
    output_arg = Path(args.output).absolute()
    if output_arg.exists() or output_arg.is_symlink():
        raise PreparationError("output must be a new private directory")
    output = output_arg.parent.resolve(strict=True) / output_arg.name
    if not project.is_dir() or not data_path.is_dir():
        raise PreparationError("project and shared-data inputs must be directories")
    if within(data_path, project) or within(project, data_path):
        raise PreparationError("shared data must be outside the original project")
    if any(
        within(output, root) or within(root, output) for root in (project, data_path)
    ):
        raise PreparationError("output must be outside the project and shared data")
    target = relative(args.file)
    exclusions = {relative(name) for name in args.exclude}
    if excluded(target, exclusions):
        raise PreparationError("the selected instruction cannot be excluded")
    after = safe_file(project, target)
    home = Path(
        os.environ.get("BEHAVIOR_DIFF_HOME", str(Path.home() / ".behavior-diff"))
    ).resolve()
    before_file = None
    if args.before_file:
        supplied = Path(args.before_file).absolute()
        before_file = supplied.parent.resolve(strict=True) / supplied.name
        if before_file == project / target:
            raise PreparationError("Before and After must be separate files")
        if within(before_file, project):
            exclusions.add(before_file.relative_to(project).as_posix())
    head = git(project, "rev-parse", "--verify", "HEAD", check=False)
    commit = head.stdout.decode().strip() if head.returncode == 0 else None
    if commit is not None:
        top = git(project, "rev-parse", "--show-toplevel").stdout.decode().strip()
        if Path(top).resolve() != project:
            raise PreparationError("--project must name the repository root")
        base = archive(project, commit)
        base = {
            name: content
            for name, content in base.items()
            if not excluded(name, exclusions)
        }
    else:
        copy_exclusions = set(exclusions)
        if within(home, project):
            if home == project:
                raise PreparationError(
                    "project cannot be the Behavior Diff state directory"
                )
            copy_exclusions.add(home.relative_to(project).as_posix())
        base = tree(project, copy_exclusions, skip_git=True)
    mode, before = baseline(project, target, commit, before_file, home)
    if before is not None and before[0] == after[0]:
        raise PreparationError(
            "Before and After instructions match; nothing to compare"
        )
    if before is not None and before[1] != after[1]:
        raise PreparationError("instruction executable-mode changes are not supported")
    shared = tree(data_path)
    if not shared:
        raise PreparationError("shared-data directory contains no files")
    for name in shared:
        if (
            excluded(name, (target,))
            or excluded(target, (name,))
            or excluded(name, exclusions)
            or any(excluded(item, (name,)) for item in exclusions)
        ):
            raise PreparationError(
                "shared data collides with instructions or excluded context"
            )
    base.update(shared)
    if before is None:
        base.pop(target, None)
    else:
        base[target] = before
    working = {**base, target: after}
    validate_files(working)
    cap = int(os.environ.get("BEHAVIOR_DIFF_COPY_CAP_KB", "204800")) * 1024
    if (
        cap <= 0
        or sum(len(content[0]) for content in working.values())
        + (len(before[0]) if before else 0)
        > cap
    ):
        raise PreparationError("prepared project exceeds BEHAVIOR_DIFF_COPY_CAP_KB")
    output.mkdir(mode=0o700)
    try:
        scratch = output / "project"
        scratch.mkdir(mode=0o700)
        (output / "home").mkdir(mode=0o700)
        write_files(scratch, base)
        git(scratch, "init", "-q", "--template=")
        for key, value in (
            ("user.name", "Behavior Diff"),
            ("user.email", "behavior-diff@example.invalid"),
            ("core.hooksPath", os.devnull),
            ("commit.gpgSign", "false"),
            ("core.autocrlf", "false"),
            ("core.attributesFile", os.devnull),
        ):
            git(scratch, "config", key, value)
        git(scratch, "add", "--force", "--all")
        git(
            scratch,
            "commit",
            "--quiet",
            "--allow-empty",
            "--signoff",
            "-m",
            "Shared scenario baseline",
        )
        scratch_commit = git(scratch, "rev-parse", "HEAD").stdout.decode().strip()
        expected_archive = inventory(base)
        if inventory(archive(scratch, scratch_commit)) != expected_archive:
            raise PreparationError(
                "Git attributes alter prepared files; this setup cannot be delivered faithfully"
            )
        target_path = scratch / target
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(after[0])
        target_path.chmod(0o755 if after[1] else 0o644)
        marker = None
        if mode == "absent":
            marker = "home/baselines/" + encode(scratch / target) + "/frozen-ABSENT"
            marker_path = output / marker
            marker_path.parent.mkdir(parents=True, mode=0o700)
            marker_path.touch(mode=0o600)
        else:
            before_path = output / "before"
            before_path.write_bytes(before[0])
            before_path.chmod(0o700 if before[1] else 0o600)
        frozen = {
            "original_project": str(project),
            "original_commit": commit,
            "target": target,
            "before_mode": mode,
            "scratch_commit": scratch_commit,
            "exclusions": sorted(exclusions),
            "archive": expected_archive,
            "working": inventory(working),
            "absent_marker": marker,
            "before": inventory({"before": before}) if before is not None else None,
        }
        record = output / "freeze.json"
        with record.open("x") as stream:
            record.chmod(0o600)
            json.dump(frozen, stream, indent=2, sort_keys=True)
            stream.write("\n")
        verify(output)
    except BaseException:
        shutil.rmtree(output)
        raise
    return output


def verify(root):
    check_git_environment()
    root = Path(root).resolve(strict=True)
    record = root / "freeze.json"
    regular_file(record)
    frozen = json.loads(record.read_text())
    scratch = root / "project"
    if scratch.is_symlink() or (scratch / ".git").is_symlink():
        raise PreparationError("frozen project must not be redirected")
    top = (
        git(scratch, "rev-parse", "--show-toplevel", launch=True)
        .stdout.decode()
        .strip()
    )
    if Path(top).resolve() != scratch:
        raise PreparationError("frozen project must not be redirected")
    current = git(scratch, "rev-parse", "HEAD", launch=True).stdout.decode().strip()
    if current != frozen["scratch_commit"]:
        raise PreparationError("prepared baseline changed after freeze")
    if inventory(tree(scratch, skip_git=True)) != frozen["working"]:
        raise PreparationError("prepared files changed after freeze")
    if inventory(archive(scratch, current, launch=True)) != frozen["archive"]:
        raise PreparationError("launch Git configuration or prepared archive changed")
    if frozen["before_mode"] == "absent":
        if (root / "before").exists() or (root / "before").is_symlink():
            raise PreparationError("absent Before must not have a frozen content file")
        marker = root / frozen["absent_marker"]
        if marker.parent.is_symlink() or marker.is_symlink() or not marker.is_file():
            raise PreparationError("frozen absent-file baseline is unavailable")
        if sorted(path.name for path in marker.parent.iterdir()) != [marker.name]:
            raise PreparationError("frozen absent-file baseline changed")
    elif inventory({"before": regular_file(root / "before")}) != frozen["before"]:
        raise PreparationError("frozen Before instruction changed")
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    stage = commands.add_parser(
        "prepare", help="freeze reviewed shared files; never launch trials"
    )
    for name in ("project", "file", "data", "output"):
        stage.add_argument("--" + name, required=True)
    stage.add_argument("--before-file")
    stage.add_argument("--exclude", action="append", default=[])
    check = commands.add_parser(
        "verify", help="reject changed inputs before using the existing runner"
    )
    check.add_argument("root")
    args = parser.parse_args()
    try:
        result = prepare(args) if args.command == "prepare" else verify(args.root)
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as exc:
        message = (
            str(exc)
            if isinstance(exc, PreparationError)
            else "invalid or unreadable preparation inputs"
        )
        print("prepare-shared: " + message, file=sys.stderr)
        return 2
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
