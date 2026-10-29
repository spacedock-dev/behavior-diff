#!/usr/bin/env python3
"""Read the reviewed, frozen scenario record against its frozen purpose."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from purpose import read_purpose
from reporting.scenario import parse_scenario
from reporting.target import parse_purpose


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate scenario JSON field")
        result[key] = value
    return result


def read_scenario(path, purpose_path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Scenario must be a regular JSON file")
    with path.open(encoding="utf-8") as stream:
        raw = json.load(stream, object_pairs_hook=unique_object)
    scenario = parse_scenario(raw, parse_purpose(read_purpose(purpose_path)))
    if scenario is None:
        return None
    result = asdict(scenario)
    if "artifact_requirements" not in raw:
        result.pop("artifact_requirements")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--purpose-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        scenario = read_scenario(args.file, args.purpose_file)
    except (OSError, ValueError, TypeError):
        # Do not expose rejected data or private paths in error messages.
        print(
            "behavior-diff: invalid --scenario-file JSON; use null or "
            "{summary,rationale,conditions,limitations,checks,"
            "source_requirements} with summary "
            "<=400 and rationale <=1200 characters, 1..8 conditions and 0..8 "
            "limitations (<=300 each), and 1..16 checks "
            "{id,goal,text,mode,required_evidence,evidence_kind} with unique "
            "ids (<=80), 1-based goal numbers covering every purpose goal, mode "
            "correction|new|change|preservation, evidence_kind "
            "output|source_consistency|recorded_action, text and "
            "required_evidence <=600; plain text only. source_requirements is "
            "0..32 distinct {check,any_of} groups naming only "
            "source_consistency check ids, covering every such check, each "
            "with 1..8 distinct fnmatch patterns (<=200, no brackets, no edge "
            "spaces) over recorded source descriptors; each pattern needs a "
            "literal path, endpoint, or identifier and must not name a "
            "sensitive source. Optional artifact_requirements is 0..16 "
            "{check,paths} groups naming output/source_consistency checks, "
            "with at most 16 distinct exact project-relative text paths "
            "(<=120 characters); no aliases, hidden, private, evaluator or secret paths",
            file=sys.stderr,
        )
        return 2
    print(json.dumps(scenario, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
