#!/usr/bin/env python3
"""Resolve Behavior Diff's sol/luna selectors without a model inference call."""

import argparse
import json
import re
import subprocess
import sys


class CodexModelError(RuntimeError):
    """Codex model discovery could not safely resolve the requested selector."""


_STABLE_MODEL = re.compile(r"gpt-([0-9]+(?:\.[0-9]+)*)-(sol|luna)")
_EXPLICIT_ID_HINT = "Pass an explicit Codex model ID instead of a family selector."


def resolve_codex_model(model="sol") -> str:
    """Return an explicit ID or discover the newest visible stable family member."""
    if not isinstance(model, str) or not model.strip():
        raise CodexModelError(
            "A nonempty Codex model ID, 'sol', or 'luna' is required."
        )
    if model not in ("sol", "luna"):
        return model

    try:
        result = subprocess.run(
            ["codex", "debug", "models"], capture_output=True, text=True, check=False
        )
    except (OSError, UnicodeError) as error:
        raise CodexModelError(
            f"Cannot run 'codex debug models': {error}. {_EXPLICIT_ID_HINT}"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or "no diagnostic on stderr"
        raise CodexModelError(
            f"'codex debug models' failed (exit {result.returncode}): "
            f"{detail}. {_EXPLICIT_ID_HINT}"
        )
    try:
        catalog = json.loads(result.stdout)
    except ValueError as error:
        raise CodexModelError(
            f"'codex debug models' returned invalid JSON: {error}. {_EXPLICIT_ID_HINT}"
        ) from error
    if not isinstance(catalog, dict) or not isinstance(catalog.get("models"), list):
        raise CodexModelError(
            "'codex debug models' must return an object with a models array. "
            + _EXPLICIT_ID_HINT
        )

    candidates = {}
    for index, entry in enumerate(catalog["models"]):
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("slug"), str)
            or not entry["slug"]
            or not isinstance(entry.get("visibility"), str)
            or not entry["visibility"]
        ):
            raise CodexModelError(
                f"'codex debug models' returned an invalid model entry at index {index}; "
                f"slug and visibility must be nonempty strings. {_EXPLICIT_ID_HINT}"
            )
        match = _STABLE_MODEL.fullmatch(entry["slug"])
        if entry["visibility"] == "list" and match and match.group(2) == model:
            version = tuple(int(part) for part in match.group(1).split("."))
            candidates.setdefault(version, set()).add(entry["slug"])

    if not candidates:
        raise CodexModelError(
            f"'codex debug models' listed no visible stable gpt-<version>-{model} model. "
            + _EXPLICIT_ID_HINT
        )
    newest = candidates[max(candidates)]
    if len(newest) != 1:
        raise CodexModelError(
            f"'codex debug models' listed ambiguous newest {model} IDs: "
            f"{', '.join(sorted(newest))}. {_EXPLICIT_ID_HINT}"
        )
    return next(iter(newest))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="?", default="sol")
    args = parser.parse_args()
    try:
        model = resolve_codex_model(args.model)
    except CodexModelError as error:
        print(f"Codex model resolution failed: {error}", file=sys.stderr)
        return 1
    print(model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
