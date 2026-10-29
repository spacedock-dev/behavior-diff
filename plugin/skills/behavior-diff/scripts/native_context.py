#!/usr/bin/env python3
"""Native Codex filesystem policy construction and model-free preflight.

This is not an agent launcher. The existing shell runner owns model execution.
Only macOS native local-command enforcement is supported here. Other context
surfaces and undetected/obfuscated access attempts are not isolation evidence.
"""

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from purpose import unique_object


PROFILE = "behavior-diff-context"


def load_requirements(path):
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("context requirements must be a regular non-symlink file")
    data = json.loads(source.read_text(), object_pairs_hook=unique_object)
    if not isinstance(data, dict) or set(data) != {"version", "scope", "deny_read"}:
        raise ValueError("invalid context requirements fields")
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("unsupported context requirements version")
    if data["scope"] != "codex-local-filesystem":
        raise ValueError("required context scope is unavailable")
    paths = data["deny_read"]
    if not isinstance(paths, list) or not paths or len(paths) > 64:
        raise ValueError("deny_read requires 1 to 64 exact absolute paths")
    for item in paths:
        if not isinstance(item, str) or not item.startswith("/") or item == "/":
            raise ValueError("deny_read requires exact absolute paths")
        if any(c in item for c in "\x00\n\r*?[]") or ".." in Path(item).parts:
            raise ValueError("deny_read does not accept globs or parent traversal")
        if str(Path(item).resolve()) != item:
            raise ValueError("deny_read paths must be canonical")
    return data


def policy_args(workspace, denied):
    # Whole-table override prevents additive profile roots/allow rules.
    entries = [
        '":minimal"="read"',
        '":workspace_roots"={"."="write",".git"="read",".agents"="read",".codex"="read",".aws"="read"}',
    ]
    entries.extend(f'{json.dumps(path)}="deny"' for path in denied)
    profile = (
        "{"
        + json.dumps(PROFILE)
        + "={filesystem={"
        + ",".join(entries)
        + "},network={enabled=false}}}"
    )
    args = [
        "-c",
        f'default_permissions="{PROFILE}"',
        "-c",
        "permissions=" + profile,
        "-c",
        'approval_policy="never"',
        "-c",
        'web_search="disabled"',
        "-c",
        "mcp_servers={}",
    ]
    for feature in (
        "memories",
        "apps",
        "plugins",
        "hooks",
        "multi_agent",
        "multi_agent_v2",
    ):
        args.extend(["-c", f"features.{feature}=false"])
    return args


def check_route(agent, workspace):
    if agent != "codex" or platform.system() != "Darwin":
        raise ValueError("required native filesystem route unavailable on this host")
    if os.environ.get("BEHAVIOR_DIFF_CODEX_ISOLATION_ROOT") or os.environ.get(
        "BEHAVIOR_DIFF_CODEX_DENY_READ"
    ):
        raise ValueError("native requirements cannot use the custom isolation helper")
    # A loaded legacy sandbox setting overrides default_permissions. Do not
    # modify any config or assume CLI precedence can remove that setting.
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    configs = [
        home / "config.toml",
        Path("/etc/codex/config.toml"),
        Path("/etc/codex/managed_config.toml"),
    ]
    configs.extend(
        parent / ".codex/config.toml" for parent in [workspace, *workspace.parents]
    )
    for config in configs:
        if config.exists():
            try:
                import tomllib
            except ImportError as error:
                raise ValueError(
                    "native policy inspection requires Python 3.11 or later"
                ) from error
            data = tomllib.loads(config.read_text())
            if config != home / "config.toml":
                raise ValueError(
                    "project or system config makes native route unavailable"
                )
            if "sandbox_mode" in data or "sandbox_workspace_write" in data:
                raise ValueError(
                    "legacy sandbox config conflicts with required permission profile"
                )
            selected = data.get("profiles", {}).get(data.get("profile"), {})
            if "sandbox_mode" in selected or "sandbox_workspace_write" in selected:
                raise ValueError(
                    "selected legacy sandbox profile conflicts with native permissions"
                )
    help_text = subprocess.run(
        ["codex", "exec", "--help"], capture_output=True, text=True, check=True
    ).stdout
    if "--strict-config" not in help_text:
        raise ValueError(
            "native Codex permission route unavailable in this CLI version"
        )


def preflight(workspace, denied):
    # Synthetic canary checks the native effective sandbox, not a Python
    # approximation. Never read prohibited real files or emit their contents.
    with (
        tempfile.TemporaryDirectory(prefix="bd-outside-") as outside,
        tempfile.TemporaryDirectory(prefix=".bd-policy-", dir=workspace) as root,
    ):
        root = Path(root).resolve()
        forbidden = root / "denied"
        forbidden.write_text("synthetic canary\n")
        writable = root / "writable"
        args = policy_args(workspace, [*denied, str(forbidden)])
        config = subprocess.run(
            ["codex", "app-server", *args, "--print-startup-config", "--strict-config"],
            cwd=workspace,
            capture_output=True,
            timeout=30,
        )
        if config.returncode != 0:
            failure = ValueError(
                "native strict configuration check failed; trial unavailable"
            )
            failure.native_stderr = config.stderr
            failure.native_stdout = config.stdout
            raise failure
        outside_file = Path(outside).resolve() / "outside"
        outside_file.write_text("synthetic outside canary\n")
        code = 'printf "synthetic write\\n" >"$2" || exit 20; /bin/cat "$2" >/dev/null || exit 21; if /bin/cat "$1" >/dev/null 2>&1; then exit 19; fi; if /bin/cat "$3" >/dev/null 2>&1; then exit 19; fi'
        result = subprocess.run(
            [
                "codex",
                "sandbox",
                *args,
                "--permission-profile",
                PROFILE,
                "--include-managed-config",
                "-C",
                str(workspace),
                "--",
                "/bin/sh",
                "-c",
                code,
                "bd-native-canary",
                str(forbidden),
                str(writable),
                str(outside_file),
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0 or not writable.is_file():
            failure = ValueError(
                "native filesystem policy canary failed; trial unavailable"
            )
            failure.native_stderr = result.stderr
            failure.native_stdout = result.stdout
            raise failure
    return policy_args(workspace, denied)


def observe(trace, denied):
    attempted = False
    unattributed_denial = False
    for line in Path(trace).read_text().splitlines():
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError("invalid trace event")
        message = event.get("message", {})
        if not isinstance(message, dict) or not isinstance(
            message.get("content", []), list
        ):
            raise ValueError("invalid trace message")
        for block in message.get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                value = json.dumps(block.get("input", {}), ensure_ascii=False)
                if any(path in value for path in denied):
                    attempted = True
            elif (
                isinstance(block, dict)
                and block.get("type") == "tool_result"
                and block.get("is_error")
            ):
                content = json.dumps(block.get("content", ""))
                if (
                    "Operation not permitted" in content
                    or "Permission denied" in content
                ):
                    unattributed_denial = True
    status = (
        "violation"
        if attempted
        else "unavailable"
        if unattributed_denial
        else "enforced"
    )
    reasons = (
        ["recorded_prohibited_path_reference"]
        if attempted
        else ["unattributed_permission_denial"]
        if unattributed_denial
        else []
    )
    return {
        "version": 1,
        "required": True,
        "scope": "codex-local-filesystem",
        "status": status,
        "observation": "attempted_or_successful"
        if attempted
        else "unknown"
        if unattributed_denial
        else "not_observed",
        "clean_context_proven": False,
        "reason_codes": reasons,
        "limits": [
            "sandboxed_local_commands_only",
            "non_filesystem_context_unverified",
            "attempt_detection_incomplete",
        ],
    }


def private_json(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=["validate", "freeze", "prepare", "observe"]
    )
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--agent", default="codex")
    parser.add_argument("--workspace")
    parser.add_argument("--output")
    parser.add_argument("--policy-workspace")
    parser.add_argument("--trace")
    args = parser.parse_args()
    try:
        requirements = load_requirements(args.requirements)
        if args.operation == "freeze":
            private_json(args.output, requirements)
        elif args.operation == "validate":
            check_route(args.agent, Path(args.workspace or os.getcwd()).resolve())
            if args.policy_workspace:
                preflight(
                    Path(args.policy_workspace).resolve(), requirements["deny_read"]
                )
            else:
                with tempfile.TemporaryDirectory(prefix="bd-native-preflight-") as root:
                    preflight(Path(root).resolve(), requirements["deny_read"])
        elif args.operation == "prepare":
            workspace = Path(args.workspace).resolve()
            check_route(args.agent, workspace)
            native_args = preflight(workspace, requirements["deny_read"])
            private_json(
                args.output,
                {
                    "version": 1,
                    "required": True,
                    "status": "unavailable",
                    "scope": requirements["scope"],
                    "observation": "unknown",
                    "clean_context_proven": False,
                    "reason_codes": ["observation_pending"],
                },
            )
            for arg in native_args:
                sys.stdout.buffer.write(arg.encode() + b"\0")
        else:
            private_json(args.output, observe(args.trace, requirements["deny_read"]))
        return 0
    except (
        ValueError,
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as error:
        # Never expose config values, forbidden paths or tool output.
        if args.output:
            private_json(
                args.output,
                {
                    "version": 1,
                    "required": True,
                    "status": "unavailable",
                    "observation": "unknown",
                    "clean_context_proven": False,
                    "reason_codes": ["native_context_unavailable"],
                },
            )
        print(
            "native context boundary unavailable: requirements, policy, or native capability check failed",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
