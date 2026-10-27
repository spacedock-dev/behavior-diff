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

from purpose import read_purpose, unique_object
from scenario import read_scenario
from source import read_source


def private_file(path):
    path = Path(path).absolute()
    if ".." in path.parts:
        raise PreparationError("private paths must not contain parent traversal")
    safe_file(Path(path.anchor), path.relative_to(path.anchor).as_posix())
    if path.stat().st_mode & 0o077 or path.parent.stat().st_mode & 0o077:
        raise PreparationError(
            "handoff files need private files and parent directories"
        )
    return path


def handoff(path, project, working, root, data=None):
    path = private_file(path)
    trial_roots = [p for p in (project, root, data) if p is not None]
    if any(within(path, p) for p in trial_roots):
        raise PreparationError(
            "private descriptor must be outside trial projects and data"
        )
    record = json.loads(path.read_text(), object_pairs_hook=unique_object)
    required = {
        "task_file",
        "purpose_file",
        "notes_file",
        "references",
        "tools",
        "settings",
    }
    if type(record) is not dict or not required <= record.keys() <= required | {
        "scenario_file",
        "source_file",
    }:
        raise PreparationError("invalid handoff fields")
    files = {str(path): regular_file(path)}
    for key in (
        "task_file",
        "purpose_file",
        "notes_file",
        "scenario_file",
        "source_file",
    ):
        if key not in record:
            continue
        value = private_file(record[key])
        if any(within(value, p) for p in trial_roots):
            raise PreparationError(
                "private handoff context must be outside trial projects"
            )
        record[key] = str(value)
        files[str(value)] = regular_file(value)
    private_paths = list(files)
    purpose = read_purpose(record["purpose_file"])
    if purpose is not None and "scenario_file" not in record:
        raise PreparationError("a non-null purpose needs its reviewed scenario")
    if "scenario_file" in record:
        read_scenario(record["scenario_file"], record["purpose_file"])
    if "source_file" in record:
        read_source(record["source_file"])
    task = Path(record["task_file"]).read_text().rstrip("\n")
    if not task.strip() or "\0" in task:
        raise PreparationError("task must be nonempty text without NUL")
    for key in ("references", "tools"):
        if type(record[key]) is not list or any(
            type(x) is not str for x in record[key]
        ):
            raise PreparationError("references and tools must be path lists")
    for name in record["references"]:
        if relative(name) not in working:
            raise PreparationError("required reference is absent from the trial base")
    for name in record["tools"]:
        tool = Path(name)
        if not tool.is_absolute():
            if relative(name) not in working:
                raise PreparationError(
                    "tool implementation is absent from the trial base"
                )
            continue
        safe_file(Path(tool.anchor), tool.relative_to(tool.anchor).as_posix())
        files[str(tool)] = regular_file(tool)
    settings = record["settings"]
    flags = ("agent", "model", "extract_agent", "extract_model", "vocab")
    if type(settings) is not dict or not {"agent"} <= settings.keys() <= set(flags) | {
        "fast",
        "reasoning",
        "preparation_model",
    }:
        raise PreparationError("invalid handoff settings")
    if settings["agent"] not in ("claude", "codex", "pi", "omp"):
        raise PreparationError("invalid trial host")
    if settings["agent"] in ("pi", "omp") and not settings.get("model"):
        raise PreparationError("Pi and OMP require an exact model")
    argv = ["--task", task]
    for key in flags:
        if key in settings:
            if (
                type(settings[key]) is not str
                or not settings[key]
                or "\0" in settings[key]
            ):
                raise PreparationError("runner settings must be nonempty strings")
            argv += ["--" + key.replace("_", "-"), settings[key]]
    if "fast" in settings and type(settings["fast"]) is not bool:
        raise PreparationError("fast must be a boolean")
    if settings.get("fast"):
        argv.append("--fast")
    for key in ("purpose_file", "scenario_file", "source_file"):
        if key in record:
            argv += ["--" + key.replace("_", "-"), record[key]]
    # Freeze shipped mechanics as well as custom tools, without caches or data.
    for tool in sorted(Path(__file__).parent.rglob("*")):
        if tool.is_file() and tool.suffix in (".py", ".sh"):
            files[str(tool)] = regular_file(tool)
    return {
        "files": inventory(files),
        "private": private_paths,
        "settings": settings,
        "argv": argv,
    }


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
    direct = args.command == "freeze"
    data_path = None
    if not direct:
        data_path = Path(args.data)
        if data_path.is_symlink():
            raise PreparationError("shared-data directory must not be a symlink")
        data_path = data_path.resolve(strict=True)
    output_arg = Path(args.output).absolute()
    if output_arg.exists() or output_arg.is_symlink():
        raise PreparationError("output must be a new private directory")
    output = output_arg.parent.resolve(strict=True) / output_arg.name
    if not project.is_dir() or (data_path is not None and not data_path.is_dir()):
        raise PreparationError("project and shared-data inputs must be directories")
    if data_path is not None and (
        within(data_path, project) or within(project, data_path)
    ):
        raise PreparationError("shared data must be outside the original project")
    if any(
        within(output, root) or within(root, output)
        for root in (project, data_path)
        if root is not None
    ):
        raise PreparationError("output must be outside the project and shared data")
    target = relative(args.file)
    exclusions = {relative(name) for name in args.exclude}
    if excluded(target, exclusions):
        raise PreparationError("the selected instruction cannot be excluded")
    after = safe_file(project, target)
    home = Path(
        os.environ.get("BEHAVIOR_DIFF_HOME") or str(Path.home() / ".behavior-diff")
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
    shared = tree(data_path) if data_path is not None else {}
    if data_path is not None and not shared:
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
    context = (
        handoff(args.handoff, project, working, output, data_path)
        if args.handoff
        else None
    )
    if direct and exclusions:
        raise PreparationError("direct freeze cannot exclude files; use prepare")
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
        scratch = project if direct else output / "project"
        if not direct:
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
        scratch_commit = (
            git(scratch, "rev-parse", "HEAD").stdout.decode().strip()
            if not direct
            else commit
        )
        expected_archive = inventory(
            base
            if not direct
            else {name: content for name, content in base.items() if name != target}
        )
        if (
            not direct
            and inventory(archive(scratch, scratch_commit)) != expected_archive
        ):
            raise PreparationError(
                "Git attributes alter prepared files; this setup cannot be delivered faithfully"
            )
        target_path = scratch / target
        if not direct:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(after[0])
            target_path.chmod(0o755 if after[1] else 0o644)
        marker = None
        if mode == "absent" and not direct:
            marker = "home/baselines/" + encode(scratch / target) + "/frozen-ABSENT"
            marker_path = output / marker
            marker_path.parent.mkdir(parents=True, mode=0o700)
            marker_path.touch(mode=0o600)
        elif before is not None:
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
            "direct": direct,
            "home": str(home if direct else output / "home"),
            "context": context,
            "before_source": str(before_file) if before_file else None,
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


def verify(root, as_json=False):
    check_git_environment()
    root = Path(root).resolve(strict=True)
    record = root / "freeze.json"
    regular_file(record)
    frozen = json.loads(record.read_text())
    direct = frozen.get("direct", False)
    scratch = Path(frozen["original_project"]) if direct else root / "project"
    if scratch.is_symlink() or (scratch / ".git").is_symlink():
        raise PreparationError("frozen project must not be redirected")
    head = git(scratch, "rev-parse", "--verify", "HEAD", check=False, launch=True)
    current = head.stdout.decode().strip() if head.returncode == 0 else None
    if current is not None:
        top = (
            git(scratch, "rev-parse", "--show-toplevel", launch=True)
            .stdout.decode()
            .strip()
        )
        if Path(top).resolve() != scratch:
            raise PreparationError("frozen project must not be redirected")
    if current != frozen["scratch_commit"]:
        raise PreparationError("prepared baseline changed after freeze")
    if direct:
        files = (
            archive(scratch, current, launch=True)
            if current
            else tree(
                scratch,
                [str(Path(frozen["home"]).relative_to(scratch))]
                if within(Path(frozen["home"]), scratch)
                else (),
                skip_git=True,
            )
        )
        files.pop(frozen["target"], None)
        if inventory(files) != frozen["archive"]:
            raise PreparationError("direct project base changed after freeze")
        files[frozen["target"]] = safe_file(scratch, frozen["target"])
        mode, before = baseline(
            scratch,
            frozen["target"],
            current,
            Path(frozen["before_source"]) if frozen["before_source"] else None,
            Path(frozen["home"]),
        )
        if (
            mode != frozen["before_mode"]
            or (inventory({"before": before}) if before is not None else None)
            != frozen["before"]
        ):
            raise PreparationError("direct Before source changed after freeze")
    else:
        files = tree(scratch, skip_git=True)
        if inventory(archive(scratch, current, launch=True)) != frozen["archive"]:
            raise PreparationError(
                "launch Git configuration or prepared archive changed"
            )
    if inventory(files) != frozen["working"]:
        raise PreparationError("prepared files changed after freeze")
    context = frozen.get("context")
    if context:
        for name in context["private"]:
            private_file(name)
        for name, expected in context["files"].items():
            path = Path(name)
            safe_file(Path(path.anchor), path.relative_to(path.anchor).as_posix())
            if inventory({name: regular_file(path)})[name] != expected:
                raise PreparationError(
                    "handoff context, settings or tools changed after freeze"
                )
    if frozen["before_mode"] == "absent":
        if (root / "before").exists() or (root / "before").is_symlink():
            raise PreparationError("absent Before must not have a frozen content file")
        if not direct:
            marker = root / frozen["absent_marker"]
            safe_file(root, frozen["absent_marker"])
            if sorted(path.name for path in marker.parent.iterdir()) != [marker.name]:
                raise PreparationError("frozen absent-file baseline changed")
    elif inventory({"before": regular_file(root / "before")}) != frozen["before"]:
        raise PreparationError("frozen Before instruction changed")
    if as_json:
        if not context:
            raise PreparationError(
                "a complete handoff is required for JSON runner arguments"
            )
        argv = ["--file", frozen["target"], *context["argv"]]
        if frozen["before"] is not None:
            argv += ["--before-file", str(root / "before")]
        return {
            "project": str(scratch),
            "home": frozen["home"],
            "argv": argv,
            "inventory": frozen,
        }
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "freeze"):
        stage = commands.add_parser(
            command, help="freeze reviewed inputs; never launch trials"
        )
        for name in ("project", "file", "output"):
            stage.add_argument("--" + name, required=True)
        if command == "prepare":
            stage.add_argument("--data", required=True)
        stage.add_argument("--handoff", required=command == "freeze")
        stage.add_argument("--before-file")
        stage.add_argument("--exclude", action="append", default=[])
    check = commands.add_parser(
        "verify", help="reject changed inputs before using the existing runner"
    )
    check.add_argument("root")
    check.add_argument(
        "--json", action="store_true", help="return verified runner arguments"
    )
    args = parser.parse_args()
    try:
        result = (
            prepare(args) if args.command != "verify" else verify(args.root, args.json)
        )
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as exc:
        message = (
            str(exc)
            if isinstance(exc, PreparationError)
            else "invalid or unreadable preparation inputs"
        )
        print("prepare-shared: " + message, file=sys.stderr)
        return 2
    print(
        json.dumps(result, indent=2, sort_keys=True)
        if isinstance(result, dict)
        else result
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
