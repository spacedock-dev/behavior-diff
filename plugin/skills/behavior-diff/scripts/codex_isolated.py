#!/usr/bin/env python3
"""Run Codex under one macOS filesystem sandbox, without a nested seatbelt.

This is filesystem containment, not network or complete adversarial isolation.
Only exec reads credentials or starts a model; probe performs local access checks.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile


class IsolationError(Exception):
    """A prerequisite for isolated execution could not be established."""


def contains(parent, child):
    return child == parent or parent in child.parents


def canonical(value, label):
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise IsolationError(f"{label} must be an absolute path")
    # macOS's system /tmp and /var aliases are legitimate; caller-controlled
    # symlinks are not, including symlinked ancestors of a missing root.
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if current.is_symlink() and current not in (Path("/tmp"), Path("/var")):
            raise IsolationError(f"{label} must not contain symlinks")
    return path.resolve()


def validate_paths(workspace, root, deny_read, codex):
    workspace = canonical(workspace, "workspace")
    root = canonical(root, "root")
    home = Path.home().resolve()
    denied = [canonical(value, "deny-read") for value in deny_read]
    if not workspace.is_dir():
        raise IsolationError("workspace must be an existing directory")
    if contains(workspace, home):
        raise IsolationError("workspace must not expose the original home directory")
    if root == Path("/") or root == home or contains(workspace, root):
        raise IsolationError(
            "root must be outside workspace and must not be home or filesystem root"
        )
    for path in denied:
        if not path.exists():
            raise IsolationError("deny-read paths must exist")
        if contains(path, workspace) or contains(workspace, path):
            raise IsolationError("deny-read paths must not overlap workspace")
        if contains(path, root) or contains(root, path):
            raise IsolationError("deny-read paths must not overlap private root")
    if not contains(root, workspace):
        raise IsolationError("workspace must be inside the private root")
    executable = shutil.which(codex)
    if executable is None:
        raise IsolationError(
            "Codex executable is unavailable; install Codex or pass --codex"
        )
    executable = Path(executable).resolve()
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise IsolationError("Codex executable must be an executable file")
    runtime_parent = executable.parent
    if runtime_parent == home or contains(runtime_parent, home):
        raise IsolationError("Codex runtime parent would expose the original home")
    configured_home = (
        Path(os.environ.get("CODEX_HOME", str(home / ".codex"))).expanduser().resolve()
    )
    if contains(workspace, configured_home) or contains(configured_home, workspace):
        raise IsolationError("workspace must not expose original authentication data")
    if contains(runtime_parent, configured_home):
        raise IsolationError(
            "Codex runtime parent would expose original authentication data"
        )
    if contains(runtime_parent, root) or contains(root, runtime_parent):
        raise IsolationError("Codex runtime must be outside private root")
    if contains(runtime_parent, workspace) or contains(workspace, runtime_parent):
        raise IsolationError("Codex runtime must be outside workspace")
    if any(contains(runtime_parent, p) or contains(p, runtime_parent) for p in denied):
        raise IsolationError("Codex runtime parent overlaps protected source data")
    denied.append(configured_home)
    if not root.exists():
        # Do not create an uncontrolled chain of parents or chmod existing data.
        root.mkdir(mode=0o700)
    info = root.stat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise IsolationError(
            "root permissions must be 0700 and ownership must match this user"
        )
    return workspace, root, home, denied, executable


def sandbox_profile(workspace, root, runtime, home, denied, codex_parent):
    def subpath(path):
        return "(subpath " + json.dumps(str(path)) + ")"

    protected = [home, root, *denied]
    reads = [workspace, runtime, codex_parent]
    # Canonicalization needs ancestor metadata, not directory contents. Keep
    # sibling files and directory listings denied by using exact literals only.
    ancestors = sorted({str(parent) for path in reads for parent in path.parents})
    return "\n".join(
        [
            "(version 1)",
            "(allow default)",
            "(deny file-read* " + " ".join(map(subpath, protected)) + ")",
            "(allow file-read* " + " ".join(map(subpath, reads)) + ")",
            "(allow file-read-metadata "
            + " ".join("(literal " + json.dumps(path) + ")" for path in ancestors)
            + ")",
            "(deny file-write*)",
            "(allow file-write* "
            + subpath(workspace)
            + " "
            + subpath(runtime)
            + ' (literal "/dev/null") (literal "/dev/tty"))',
            "",
        ]
    )


def isolated_environment(runtime):
    # Deliberately omit API keys, inherited Codex settings, shell startup files,
    # dynamic loader overrides, package-manager hooks, and plugin configuration.
    env = {
        key: os.environ[key] for key in ("LANG", "LC_ALL", "TERM") if key in os.environ
    }
    env.update(
        {
            "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "HOME": str(runtime / "home"),
            "CODEX_HOME": str(runtime / "codex-home"),
            "TMPDIR": str(runtime / "tmp"),
            "SHELL": "/bin/sh",
            "BEHAVIOR_DIFF_TRIAL": "1",
            "BEHAVIOR_DIFF_HOME": str(runtime / "behavior-diff-home"),
        }
    )
    return env


def sandbox_command(profile, command):
    return ["/usr/bin/sandbox-exec", "-f", str(profile), *command]


def preflight(workspace, root, runtime, home, denied, executable, profile, env):
    canary_dir = Path(tempfile.mkdtemp(prefix=".codex-canary-", dir=root))
    link = workspace / (canary_dir.name + "-link")
    checks = []
    try:
        canary = canary_dir / "private"
        canary.write_text("synthetic isolation canary\n")
        link.symlink_to(canary)
        # All operations run under the exact profile used for the model process.
        script = """set -eu
printf probe > "$4.write"
/bin/cat "$4.write" >/dev/null
/bin/rm "$4.write"
printf probe > "$2/.runtime-probe"
/bin/cat "$2/.runtime-probe" >/dev/null
/bin/rm "$2/.runtime-probe"
if /bin/cat "$3" >/dev/null 2>&1; then exit 41; fi
if printf leak > "$3" 2>/dev/null; then exit 42; fi
if /bin/cat "$4" >/dev/null 2>&1; then exit 43; fi
shift 4
for source in "$@"; do
  if [ -d "$source" ]; then
    if /bin/ls "$source" >/dev/null 2>&1; then exit 44; fi
  else
    if /bin/cat "$source" >/dev/null 2>&1; then exit 45; fi
  fi
done
"""
        result = subprocess.run(
            sandbox_command(
                profile,
                [
                    "/bin/sh",
                    "-c",
                    script,
                    "probe",
                    str(workspace),
                    str(runtime),
                    str(canary),
                    str(link),
                    *map(str, denied),
                ],
            ),
            cwd=workspace,
            env=env,
            capture_output=True,
            timeout=20,
        )
        if result.returncode:
            raise IsolationError(
                "outer sandbox access probe failed (including nested sandbox denial); no model started"
            )
        checks.extend(
            [
                "workspace-read-write",
                "runtime-read-write",
                "private-sibling-denied",
                "symlink-escape-denied",
            ]
        )
        if denied:
            checks.append("protected-source-denied")
        result = subprocess.run(
            sandbox_command(profile, [str(executable), "--version"]),
            cwd=workspace,
            env=env,
            capture_output=True,
            timeout=20,
        )
        if result.returncode or result.stdout.strip() != b"codex-cli 0.165.0":
            raise IsolationError(
                "isolated Codex must report codex-cli 0.165.0; no model started"
            )
        checks.append("codex-runtime-version")
        return checks
    finally:
        link.unlink(missing_ok=True)
        Path(str(link) + ".write").unlink(missing_ok=True)
        shutil.rmtree(canary_dir)


def copy_auth(runtime):
    configured = Path(
        os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
    ).expanduser()
    auth = configured / "auth.json"
    if not auth.is_file():
        raise IsolationError(
            "Codex auth.json is unavailable in the original CODEX_HOME; authenticate before isolated exec"
        )
    target = runtime / "codex-home" / "auth.json"
    # Credentials live only in the per-call private runtime, never in evidence.
    with auth.open("rb") as source, target.open("xb") as destination:
        os.chmod(target, 0o600)
        shutil.copyfileobj(source, destination)


def run(args):
    workspace, root, home, denied, executable = validate_paths(
        args.workspace,
        args.root,
        args.deny_read,
        args.codex,
    )
    if sys.platform != "darwin":
        raise IsolationError("isolated Codex requires macOS sandbox-exec")
    if not os.access("/usr/bin/sandbox-exec", os.X_OK):
        raise IsolationError(
            "macOS sandbox-exec is unavailable; refusing unsandboxed execution"
        )
    with tempfile.TemporaryDirectory(prefix=".codex-runtime-", dir=root) as temporary:
        runtime = Path(temporary)
        for name in ("home", "codex-home", "tmp", "behavior-diff-home"):
            (runtime / name).mkdir(mode=0o700)
        profile = runtime / "isolation.sb"
        profile.write_text(
            sandbox_profile(workspace, root, runtime, home, denied, executable.parent)
        )
        env = isolated_environment(runtime)
        checks = preflight(
            workspace, root, runtime, home, denied, executable, profile, env
        )
        if args.command == "probe":
            print(json.dumps({"status": "pass", "checks": checks}))
            return 0
        copy_auth(runtime)
        command = [
            str(executable),
            "--no-daemon",
            "exec",
            "--ignore-user-config",
            "--ignore-rules",
            "--ephemeral",
            "--skip-git-repo-check",
            "--json",
            "--sandbox",
            "danger-full-access",
            "--model",
            args.model,
        ]
        for setting in (
            "features.memories=false",
            "features.plugins=false",
            "features.apps=false",
            "features.hooks=false",
            "features.chronicle=false",
            "features.daemon_auto_start=false",
            "features.skill_search=false",
            "features.shell_snapshot=false",
            "features.multi_agent=false",
            "features.multi_agent_v2=false",
            "features.image_generation=false",
            "features.view_image=false",
            "features.computer_use=false",
            "features.browser_use=false",
            "features.browser_use_external=false",
            "features.browser_use_full_cdp_access=false",
            "features.in_app_browser=false",
            "features.skip_host_skill_discovery=true",
            'web_search="disabled"',
        ):
            command.extend(["-c", setting])
        command.append("-")
        child = subprocess.Popen(
            sandbox_command(profile, command),
            cwd=workspace,
            env=env,
            start_new_session=True,
        )
        try:
            return child.wait()
        finally:
            # Kill descendants before deleting auth, including on interruption.
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("probe", "exec"):
        command = subparsers.add_parser(name)
        command.add_argument("--workspace", required=True)
        command.add_argument("--root", required=True)
        command.add_argument("--deny-read", action="append", default=[])
        command.add_argument("--codex", default="codex")
        if name == "exec":
            command.add_argument("--model", required=True)
    args = parser.parse_args()
    if args.command == "exec" and (
        not args.model.strip() or args.model != args.model.strip()
    ):
        parser.error("--model must be an exact nonempty model ID")

    def interrupted(signum, frame):
        raise IsolationError("interrupted; private runtime is being removed")

    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, interrupted)
    try:
        return run(args)
    except (IsolationError, OSError, subprocess.SubprocessError) as error:
        # Do not include arbitrary subprocess output or credential paths.
        message = (
            str(error) if isinstance(error, IsolationError) else type(error).__name__
        )
        print("codex-isolated: " + message, file=sys.stderr)
        if args.command == "probe":
            print(json.dumps({"status": "failure", "checks": [], "error": message}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
