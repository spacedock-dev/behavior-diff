#!/usr/bin/env python3
"""Synthetic catalog contracts; model executables are isolated behind local stubs."""

import contextlib
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
HELPER = SCRIPTS / "codex_model.py"

STUB = """import json
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent.parent
with (root / "calls.jsonl").open("a") as stream:
    stream.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:] != ["debug", "models"]:
    print("Model inference is forbidden in deterministic tests.", file=sys.stderr)
    sys.exit(91)
state = json.loads((root / "state.json").read_text())
sys.stdout.write(state["stdout"])
sys.stderr.write(state["stderr"])
sys.exit(state["returncode"])
"""


def model(slug, visibility="list", priority=0):
    return {
        "slug": slug,
        "visibility": visibility,
        "priority": priority,
        "supported_in_api": False,
    }


class Harness:
    def __init__(self, root, stdout, stderr, returncode):
        self.root = root
        self.bin = root / "bin"
        self.bin.mkdir()
        home = root / "home"
        home.mkdir()
        self.env = {"PATH": str(self.bin), "HOME": str(home)}
        self.set_response(stdout, stderr, returncode)
        stub = self.bin / "model-stub.py"
        stub.write_text(STUB)
        launcher = (
            "#!/bin/sh\n"
            f'exec {shlex.quote(sys.executable)} {shlex.quote(str(stub))} "$@"\n'
        )
        for name in ("codex", "claude"):
            executable = self.bin / name
            executable.write_text(launcher)
            executable.chmod(0o755)

    def set_response(self, stdout, stderr="", returncode=0):
        (self.root / "state.json").write_text(
            json.dumps({"stdout": stdout, "stderr": stderr, "returncode": returncode})
        )

    def calls(self):
        log = self.root / "calls.jsonl"
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text().splitlines()]

    def cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(HELPER), *arguments],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def load_helper(self):
        spec = importlib.util.spec_from_file_location("codex_model_under_test", HELPER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


@contextlib.contextmanager
def sandbox(stdout="", stderr="", returncode=0):
    with tempfile.TemporaryDirectory(prefix="codex-model-test-") as directory:
        harness = Harness(Path(directory), stdout, stderr, returncode)
        # No inherited credentials, real executable paths, or user configuration.
        with patch.dict(os.environ, harness.env, clear=True):
            yield harness


def assert_numeric_selection():
    for family in ("sol", "luna"):
        entries = [
            model(f"gpt-7.9-{family}", priority=-100),
            model(f"gpt-7-{family}"),
            model(f"gpt-7.10.2-{family}", priority=9999),
            model(f"gpt-7.10-{family}"),
            model(f"gpt-7.10.1-{family}"),
        ]
        for ordered in (entries, list(reversed(entries))):
            with sandbox(json.dumps({"models": ordered})) as harness:
                result = harness.cli(family)
                assert result.returncode == 0, result.stderr
                assert result.stdout == f"gpt-7.10.2-{family}\n", result.stdout
                assert result.stderr == "", result.stderr
                assert harness.calls() == [["debug", "models"]]

        catalog = {"models": [model(f"gpt-9.99-{family}"), model(f"gpt-10-{family}")]}
        with sandbox(json.dumps(catalog)) as harness:
            result = harness.cli(family)
            assert result.returncode == 0, result.stderr
            assert result.stdout == f"gpt-10-{family}\n", result.stdout


def assert_filters():
    for family, other in (("sol", "luna"), ("luna", "sol")):
        entries = [
            model(f"gpt-7.1-{family}"),
            model(f"gpt-99-{family}", visibility="hide"),
            model(f"gpt-99.1-{family}", visibility="hidden"),
            model(f"gpt-99-{family}-preview"),
            model(f"gpt-99-preview-{family}"),
            model(f"gpt-99-{family}-2099-01-01"),
            model(f"gpt-99-{family}-snapshot"),
            model("gpt-99-astra"),
            model(f"gpt-99-{other}"),
            model("gpt-99-terra"),
            model(family),
        ]
        with sandbox(json.dumps({"models": entries})) as harness:
            result = harness.cli(family)
            assert result.returncode == 0, result.stderr
            assert result.stdout == f"gpt-7.1-{family}\n", result.stdout
            assert result.stderr == "", result.stderr
        with sandbox(json.dumps({"models": [model(f"gpt-99-{other}")]})) as harness:
            result = harness.cli(family)
            assert result.returncode == 1, result.stderr
            assert result.stdout == "", result.stdout


def assert_catalog_errors():
    cases = [
        "not JSON",
        "[]",
        "{}",
        '{"models": {}}',
        json.dumps({"models": [None]}),
        json.dumps({"models": [{"slug": "gpt-9-sol"}]}),
        json.dumps({"models": [{"slug": 9, "visibility": "list"}]}),
        json.dumps({"models": [{"slug": "gpt-9-sol", "visibility": True}]}),
        json.dumps({"models": [model("gpt-9-sol", visibility="")]}),
        json.dumps({"models": []}),
        json.dumps({"models": [model("gpt-99-sol", "hide"), model("gpt-99-astra")]}),
        json.dumps({"models": [model("gpt-9-sol"), model("gpt-09-sol")]}),
    ]
    for stdout in cases:
        with sandbox(stdout) as harness:
            result = harness.cli()
            assert result.returncode == 1, result.stderr
            assert result.stdout == "", result.stdout
            helper = harness.load_helper()
            try:
                helper.resolve_codex_model()
            except helper.CodexModelError:
                pass
            else:
                raise AssertionError(f"Invalid catalog produced a model: {stdout}")


def assert_discovery_failures():
    with sandbox(stderr="Synthetic catalog access denied", returncode=23) as harness:
        result = harness.cli()
        assert result.returncode != 0
        assert result.stdout == ""
        assert "Synthetic catalog access denied" in result.stderr, result.stderr
        helper = harness.load_helper()
        try:
            helper.resolve_codex_model()
        except helper.CodexModelError as error:
            assert "Synthetic catalog access denied" in str(error)
        else:
            raise AssertionError("The imported resolver hid a discovery failure.")

    with sandbox() as harness:
        (harness.bin / "codex").unlink()
        result = harness.cli()
        assert result.returncode != 0
        assert result.stdout == ""
        assert harness.calls() == []


def assert_explicit_ids_and_import_safety():
    with sandbox(stderr="Discovery must not run", returncode=91) as harness:
        imported = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.path.insert(0, sys.argv[1]); import codex_model",
                str(SCRIPTS),
            ],
            cwd=harness.root,
            env=harness.env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert imported.returncode == 0, imported.stderr
        assert imported.stdout == imported.stderr == ""
        helper = harness.load_helper()
        for explicit in ("gpt-7.4-sol", "gpt-8-sol-preview", "synthetic/exact-model"):
            assert helper.resolve_codex_model(explicit) == explicit
            result = harness.cli(explicit)
            assert result.returncode == 0, result.stderr
            assert result.stdout == explicit + "\n", result.stdout
            assert result.stderr == "", result.stderr
        for invalid in ("", " ", None):
            try:
                helper.resolve_codex_model(invalid)
            except helper.CodexModelError:
                pass
            else:
                raise AssertionError(f"Invalid model {invalid!r} was accepted.")
        result = harness.cli("")
        assert result.returncode != 0
        assert result.stdout == ""
        assert harness.calls() == [], "Import or an explicit ID triggered discovery."


def assert_resolution_is_not_cached():
    with sandbox(json.dumps({"models": [model("gpt-7-sol")]})) as harness:
        helper = harness.load_helper()
        assert helper.resolve_codex_model() == "gpt-7-sol"
        harness.set_response(json.dumps({"models": [model("gpt-8-sol")]}))
        assert helper.resolve_codex_model() == "gpt-8-sol"
        assert harness.calls() == [["debug", "models"], ["debug", "models"]]


def main():
    assert_numeric_selection()
    assert_filters()
    assert_catalog_errors()
    assert_discovery_failures()
    assert_explicit_ids_and_import_safety()
    assert_resolution_is_not_cached()
    print("Codex model resolver contracts passed.")


if __name__ == "__main__":
    main()
