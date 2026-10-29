#!/usr/bin/env python3
"""Synthetic CLI contracts; no model, network client, or real credentials are used."""

import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HELPER = (
    Path(__file__).resolve().parents[1]
    / "plugin/skills/behavior-diff/scripts/codex_isolated.py"
)
SANDBOX = Path("/usr/bin/sandbox-exec")
MODEL = "synthetic-exact-model-2099"

# This executable only runs authored shell instructions. It cannot call a model.
CODEX_STUB = r"""#!/bin/sh
if [ "$1" = "--version" ]; then
    if [ -e "$CODEX_HOME/auth.json" ]; then
        printf 'Credentials reached non-model preflight\n' >&2
        exit 87
    fi
    printf 'codex-cli 0.165.0\n'
    exit 0
fi
printf '%s\n' "$@" > "$PWD/invocation-args"
printf '%s\n' "$HOME" > "$PWD/isolated-home"
printf '%s\n' "$CODEX_HOME" > "$PWD/isolated-codex-home"
if [ -n "${OPENAI_API_KEY+x}" ] || [ -n "${SYNTHETIC_PRIVATE_ENV+x}" ]; then
    printf 'Inherited private environment\n' >&2
    exit 88
fi
if [ -f "$CODEX_HOME/auth.json" ]; then
    printf 'present\n' > "$PWD/auth-observation"
else
    printf 'absent\n' > "$PWD/auth-observation"
fi
/bin/sh -s
status=$?
if [ "$status" -ne 0 ]; then
    printf 'Synthetic child failure\n' >&2
    exit "$status"
fi
printf '%s\n' '{"type":"item.completed","item":{"id":"synthetic-command","type":"command_execution","command":"synthetic sandbox file checks","aggregated_output":"file checks passed","exit_code":0,"status":"completed"}}'
"""


def quote(path):
    return shlex.quote(str(path))


class IsolationHarness(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-isolation-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.home = self.base / "original-home"
        self.home.mkdir()
        self.auth_home = self.home / "configured-codex"
        self.auth_home.mkdir()
        self.auth = self.auth_home / "auth.json"
        self.auth.write_text('{"synthetic_auth":"not-a-real-credential"}\n')
        self.root = self.base / "private"
        self.root.mkdir(mode=0o700)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.source = self.base / "protected-source"
        self.source.mkdir()
        self.source_canary = self.source / "source-canary"
        self.source_canary.write_text("synthetic source canary\n")
        self.home_canary = self.home / "home-canary"
        self.home_canary.write_text("synthetic home canary\n")
        self.sibling = self.root / "other-trial"
        self.sibling.mkdir()
        self.sibling_canary = self.sibling / "private-canary"
        self.sibling_canary.write_text("synthetic private canary\n")
        self.purpose_canary = self.root / "purpose"
        self.purpose_canary.write_text("synthetic private purpose\n")
        self.bin = self.base / "synthetic-runtime" / "bin"
        self.bin.mkdir(parents=True)
        self.codex = self.bin / "codex"
        self.codex.write_text(CODEX_STUB)
        self.codex.chmod(0o755)
        self.env = {
            "HOME": str(self.home),
            "CODEX_HOME": str(self.auth_home),
            "PATH": f"{self.bin}:/usr/bin:/bin:/usr/sbin:/sbin",
            "TMPDIR": str(self.base),
            "OPENAI_API_KEY": "synthetic-never-use",
            "SYNTHETIC_PRIVATE_ENV": "must-not-reach-child",
        }

    def cli(self, mode="exec", *, prompt="", changes=None, prefix=(), extra=()):
        options = {
            "--workspace": str(self.workspace),
            "--root": str(self.root),
            "--deny-read": str(self.source),
            "--codex": str(self.codex),
        }
        options.update(changes or {})
        arguments = [sys.executable, str(HELPER), mode]
        for flag, value in options.items():
            arguments.extend((flag, value))
        if mode == "exec":
            arguments.extend(("--model", MODEL))
        arguments.extend(extra)
        return subprocess.run(
            [*prefix, *arguments],
            input=prompt,
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.workspace,
            timeout=30,
            check=False,
        )

    def assert_not_invoked(self):
        self.assertFalse((self.workspace / "invocation-args").exists())

    def assert_cleaned(self):
        self.assertEqual(list(self.root.glob(".codex-runtime-*")), [])
        self.assertEqual(list(self.root.glob(".codex-canary-*")), [])
        self.assertEqual(list(self.root.rglob("auth.json")), [])
        self.assertEqual(
            self.auth.read_text(), '{"synthetic_auth":"not-a-real-credential"}\n'
        )

    def assert_rejected(self, changes, diagnostic):
        result = self.cli(changes=changes)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, "")
        self.assertIn(diagnostic, result.stderr.lower())
        self.assert_not_invoked()
        self.assert_cleaned()


class IsolationCLI(IsolationHarness):
    def test_reject_root_equal_to_or_inside_workspace(self):
        for root in (self.workspace, self.workspace / "nested-private"):
            with self.subTest(root=root):
                self.assert_rejected({"--root": str(root)}, "workspace")

    def test_reject_workspace_inside_denied_source(self):
        self.assert_rejected({"--workspace": str(self.source)}, "deny")

    def test_reject_nonprivate_root(self):
        self.root.chmod(0o755)
        self.assert_rejected({}, "permission")

    def test_reject_relative_denied_path(self):
        self.assert_rejected({"--deny-read": "relative-source"}, "absolute")

    def test_reject_symlink_root_and_workspace(self):
        for flag, destination in (
            ("--root", self.root),
            ("--workspace", self.workspace),
        ):
            link = self.base / (flag.removeprefix("--") + "-link")
            link.symlink_to(destination, target_is_directory=True)
            with self.subTest(flag=flag):
                self.assert_rejected({flag: str(link)}, "symlink")

    def test_reject_runtime_parent_overlapping_protected_source(self):
        executable = self.source / "codex"
        executable.write_text(CODEX_STUB)
        executable.chmod(0o755)
        self.assert_rejected({"--codex": str(executable)}, "runtime")

    def test_exec_requires_exact_model_argument(self):
        result = subprocess.run(
            [
                sys.executable,
                str(HELPER),
                "exec",
                "--workspace",
                str(self.workspace),
                "--root",
                str(self.root),
                "--codex",
                str(self.codex),
            ],
            capture_output=True,
            text=True,
            env=self.env,
            timeout=30,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--model", result.stderr)
        self.assert_not_invoked()

    @unittest.skipIf(sys.platform == "darwin", "non-macOS failure contract")
    def test_unsupported_platform_fails_without_child(self):
        result = self.cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("macos", result.stderr.lower())
        self.assert_not_invoked()
        self.assert_cleaned()


@unittest.skipUnless(sys.platform == "darwin", "requires macOS sandbox-exec")
class MacOSIsolationCLI(IsolationHarness):
    def test_probe_is_non_model_and_credential_free(self):
        result = self.cli("probe")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["checks"])
        self.assertLess(len(result.stdout), 8192)
        self.assert_not_invoked()
        self.assert_cleaned()

    def test_runtime_and_workspace_can_be_canonicalized(self):
        script = (
            "import os, pathlib; "
            "paths = [os.environ['CODEX_HOME'], os.getcwd()]; "
            "assert all(os.path.realpath(p, strict=True) == p for p in paths); "
            "pathlib.Path('canonicalized').write_text('runtime and workspace')"
        )
        result = self.cli(
            prompt=f"set -eu\n{quote(sys.executable)} -c {quote(script)}\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (self.workspace / "canonicalized").read_text(), "runtime and workspace"
        )
        self.assert_cleaned()

    def file_checks_prompt(self):
        lines = [
            "set -eu",
            "printf 'workspace-write\\n' > allowed-file",
            'test "$(/bin/cat allowed-file)" = workspace-write',
            'printf "runtime-write\\n" > "$HOME/runtime-file"',
            'test "$(/bin/cat "$HOME/runtime-file")" = runtime-write',
            'printf "codex-write\\n" > "$CODEX_HOME/runtime-file"',
            'test "$(/bin/cat "$CODEX_HOME/runtime-file")" = codex-write',
        ]
        for label, path in (
            ("home", self.home_canary),
            ("source", self.source_canary),
            ("sibling", self.sibling_canary),
            ("purpose", self.purpose_canary),
        ):
            link = self.workspace / f"{label}-escape"
            link.symlink_to(path)
            for candidate in (path, link):
                lines.extend(
                    (
                        f"if /bin/cat {quote(candidate)} >/dev/null 2>&1; then exit 81; fi",
                        f"if (printf changed > {quote(candidate)}) 2>/dev/null; then exit 82; fi",
                    )
                )
        return "\n".join(lines) + "\n"

    def test_real_profile_allows_workspace_and_denies_private_reads_and_writes(self):
        result = self.cli(prompt=self.file_checks_prompt())
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"]["type"], "command_execution")
        self.assertEqual(events[0]["item"]["exit_code"], 0)
        self.assertEqual(
            (self.workspace / "allowed-file").read_text(), "workspace-write\n"
        )
        self.assertEqual(self.source_canary.read_text(), "synthetic source canary\n")
        self.assertEqual(self.home_canary.read_text(), "synthetic home canary\n")
        self.assertEqual(self.sibling_canary.read_text(), "synthetic private canary\n")
        arguments = (self.workspace / "invocation-args").read_text().splitlines()
        self.assertEqual(arguments[arguments.index("--model") + 1], MODEL)
        for flag in (
            "--ignore-user-config",
            "--ignore-rules",
            "--ephemeral",
            "--skip-git-repo-check",
            "--json",
        ):
            self.assertIn(flag, arguments)
        self.assertIn("exec", arguments)
        self.assertEqual((self.workspace / "auth-observation").read_text(), "present\n")
        self.assertNotEqual(
            (self.workspace / "isolated-home").read_text().strip(), str(self.home)
        )
        self.assert_cleaned()

    def test_repeated_denied_paths_remain_protected(self):
        additional = self.base / "additional-source"
        additional.mkdir()
        canary = additional / "canary"
        canary.write_text("synthetic additional source\n")
        prompt = (
            "set -eu\n"
            f"if /bin/cat {quote(canary)} >/dev/null 2>&1; then exit 83; fi\n"
            f"if (printf changed > {quote(canary)}) 2>/dev/null; then exit 84; fi\n"
        )
        result = self.cli(prompt=prompt, extra=("--deny-read", str(additional)))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(canary.read_text(), "synthetic additional source\n")
        self.assert_cleaned()

    def test_root_reuse_creates_fresh_runtime_for_every_exec(self):
        homes = []
        for _ in range(2):
            result = self.cli(prompt="exit 0\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            homes.append((self.workspace / "isolated-codex-home").read_text().strip())
            self.assert_cleaned()
        self.assertNotEqual(*homes)

    def test_auth_and_runtime_removed_after_child_failure(self):
        result = self.cli(prompt="exit 17\n")
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("Synthetic child failure", result.stderr)
        self.assertEqual((self.workspace / "auth-observation").read_text(), "present\n")
        runtime_home = Path(
            (self.workspace / "isolated-codex-home").read_text().strip()
        )
        self.assertFalse(runtime_home.exists())
        self.assert_cleaned()

    def test_failed_same_profile_preflight_never_invokes_model_command(self):
        profile = '(version 1)(allow default)(deny process-exec (literal "/bin/sh"))'
        result = self.cli(
            prompt="printf should-not-run > forbidden-invocation\n",
            prefix=(str(SANDBOX), "-p", profile),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr)
        self.assert_not_invoked()
        self.assertFalse((self.workspace / "forbidden-invocation").exists())
        self.assert_cleaned()


if __name__ == "__main__":
    unittest.main(verbosity=2)
