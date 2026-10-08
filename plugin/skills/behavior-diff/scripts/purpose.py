#!/usr/bin/env python3
"""Read reviewed assessment-only purpose using the report's shared validator."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from reporting.target import parse_purpose


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate purpose JSON field")
        result[key] = value
    return result


def read_purpose(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Purpose must be a regular JSON file")
    with path.open(encoding="utf-8") as stream:
        raw = json.load(stream, object_pairs_hook=unique_object)
    goals = parse_purpose(raw)
    return {"goals": [asdict(goal) for goal in goals]} if goals else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        purpose = read_purpose(args.file)
    except (OSError, ValueError, TypeError):
        # Do not expose rejected data or private paths in error messages.
        print(
            "behavior-diff: invalid --purpose-file JSON; use null or "
            "{goals:[{text,source,basis,reference}]} with 1..8 distinct concise "
            "goals (text <=1200, reference <=240 characters), source "
            "session|commit|diff, basis explicit|inferred; diff goals must be inferred",
            file=sys.stderr,
        )
        return 2
    print(json.dumps(purpose, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
