#!/usr/bin/env python3
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple

VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
MANIFESTS = (
    Path("plugin/.claude-plugin/plugin.json"),
    Path("plugin/.codex-plugin/plugin.json"),
)
CONTRACT = Path("tests/live-report-contract.sh")


class ReleaseError(ValueError):
    pass


def _version(value: object, field: str) -> Tuple[int, int, int]:
    if type(value) is not str or VERSION_RE.fullmatch(value) is None:
        raise ReleaseError("{0} must use stable X.Y.Z: {1}".format(field, value))
    major, minor, patch = (int(part) for part in value.split("."))
    return major, minor, patch


def _manifest(path: Path) -> Tuple[str, str]:
    try:
        text = path.read_text()
        data = json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ReleaseError("invalid plugin manifest {0}: {1}".format(path, error))
    version = data.get("version") if type(data) is dict else None
    _version(version, "manifest version")
    return version, text


def _contract_lines(version: str) -> Tuple[str, ...]:
    return (
        "[[ $(jq -r '.version' \"$claude_manifest\") == {0} ]] ||".format(version),
        "  fail 'Claude manifest version is not {0}'".format(version),
        "[[ $(jq -r '.version' \"$codex_manifest\") == {0} ]] ||".format(version),
        "  fail 'Codex manifest version is not {0}'".format(version),
    )


def _replace_once(text: str, old: str, new: str, field: str) -> str:
    if text.count(old) != 1:
        raise ReleaseError("{0} does not match {1}".format(field, old))
    return text.replace(old, new)


def _bump(root: Path, requested: Optional[str]) -> str:
    claude, claude_text = _manifest(root / MANIFESTS[0])
    codex, codex_text = _manifest(root / MANIFESTS[1])
    if claude != codex:
        raise ReleaseError(
            "plugin manifest versions differ: Claude {0}, Codex {1}".format(
                claude, codex
            )
        )

    current = _version(claude, "manifest version")
    if requested is None:
        target = current[0], current[1], current[2] + 1
        new_version = ".".join(str(part) for part in target)
    else:
        target = _version(requested, "version")
        if target <= current:
            raise ReleaseError(
                "new version must be greater than {0}: {1}".format(claude, requested)
            )
        new_version = requested

    old_manifest_token = '"version": "{0}"'.format(claude)
    new_manifest_token = '"version": "{0}"'.format(new_version)
    new_claude = _replace_once(
        claude_text, old_manifest_token, new_manifest_token, str(MANIFESTS[0])
    )
    new_codex = _replace_once(
        codex_text, old_manifest_token, new_manifest_token, str(MANIFESTS[1])
    )

    contract_path = root / CONTRACT
    contract_text = contract_path.read_text()
    new_contract = contract_text
    for old, new in zip(_contract_lines(claude), _contract_lines(new_version)):
        if new_contract.count(old) != 1:
            raise ReleaseError(
                "active version contract does not match {0}".format(claude)
            )
        new_contract = new_contract.replace(old, new)

    updates = (
        (root / MANIFESTS[0], new_claude),
        (root / MANIFESTS[1], new_codex),
        (contract_path, new_contract),
    )
    for path, text in updates:
        path.write_text(text)

    updated_claude, _ = _manifest(root / MANIFESTS[0])
    updated_codex, _ = _manifest(root / MANIFESTS[1])
    if updated_claude != new_version or updated_codex != new_version:
        raise ReleaseError("updated plugin manifest versions do not match")
    return new_version


def _fixture(root: Path, claude: str = "0.3.2", codex: str = "0.3.2") -> None:
    for relative, version in zip(MANIFESTS, (claude, codex)):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '{\n  "name": "behavior-diff",\n  "version": "' + version + '"\n}\n'
        )
    contract = root / CONTRACT
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(
        "[[ $(jq -r '.version' \"$claude_manifest\") == 0.3.2 ]] ||\n"
        "  fail 'Claude manifest version is not 0.3.2'\n"
        "[[ $(jq -r '.version' \"$codex_manifest\") == 0.3.2 ]] ||\n"
        "  fail 'Codex manifest version is not 0.3.2'\n"
    )


def _expect_error(root: Path, requested: Optional[str], message: str) -> None:
    before = {path: (root / path).read_text() for path in (*MANIFESTS, CONTRACT)}
    try:
        _bump(root, requested)
    except ReleaseError as error:
        assert str(error) == message
    else:
        raise AssertionError("invalid release version was accepted")
    assert {path: (root / path).read_text() for path in before} == before


def _check() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root)
        assert _bump(root, None) == "0.3.3"
        assert json.loads((root / MANIFESTS[0]).read_text())["version"] == "0.3.3"
        assert json.loads((root / MANIFESTS[1]).read_text())["version"] == "0.3.3"
        assert (root / CONTRACT).read_text().count("0.3.3") == 4

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root)
        assert _bump(root, "0.4.0") == "0.4.0"

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root, codex="0.3.1")
        _expect_error(
            root,
            None,
            "plugin manifest versions differ: Claude 0.3.2, Codex 0.3.1",
        )

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root, claude="01.2.3")
        _expect_error(
            root,
            None,
            "manifest version must use stable X.Y.Z: 01.2.3",
        )

    for requested, message in (
        ("v0.3.3", "version must use stable X.Y.Z: v0.3.3"),
        ("0.3.2", "new version must be greater than 0.3.2: 0.3.2"),
        ("0.3.1", "new version must be greater than 0.3.2: 0.3.1"),
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _fixture(root)
            _expect_error(root, requested, message)

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root)
        contract = root / CONTRACT
        contract.write_text(contract.read_text().replace("0.3.2", "0.3.1", 1))
        _expect_error(
            root,
            None,
            "active version contract does not match 0.3.2",
        )

    print("bump-version.py self-check ok")


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args == ["--check"]:
        _check()
        return 0
    if len(args) > 1:
        print("Usage: bump-version.py [X.Y.Z]", file=sys.stderr)
        return 2
    try:
        print(_bump(Path.cwd(), args[0] if args else None))
    except (OSError, UnicodeError, ReleaseError) as error:
        print("release version error: {0}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
