"""Validate the frozen, reviewed scenario record shown to assessment and reports.

The record is written before trials from private preparation notes. It explains
how the comparison tested the purpose and fixes the checks the assessment must
answer. Its source requirements bind each source-consistency check to the
recorded sources that must ground it; they are frozen configuration, not part
of a check definition the assessment restates. It never contains outcomes and
is never a trial input.
"""

from dataclasses import dataclass
from typing import Tuple
import re

from reporting.explanation import _text
from reporting.sources import SourceRequirementData, parse_source_requirements
from reporting.sources import sensitive_text
from reporting.target import EVIDENCE_KINDS, MODES

SUMMARY_LIMIT = 400
RATIONALE_LIMIT = 1200
ITEM_LIMIT = 300
CHECK_TEXT_LIMIT = 600
ID_LIMIT = 80

ARTIFACT_LIMIT = 16
ARTIFACT_PATH_LIMIT = 120


@dataclass(frozen=True)
class ArtifactRequirementData:
    check: str
    paths: Tuple[str, ...]


@dataclass(frozen=True)
class ScenarioCheckData:
    id: str
    goal: int
    text: str
    mode: str
    required_evidence: str
    evidence_kind: str


@dataclass(frozen=True)
class ScenarioData:
    summary: str
    rationale: str
    conditions: Tuple[str, ...]
    limitations: Tuple[str, ...]
    checks: Tuple[ScenarioCheckData, ...]
    source_requirements: Tuple[SourceRequirementData, ...]
    artifact_requirements: Tuple[ArtifactRequirementData, ...] = ()


def _texts(values, minimum, maximum):
    if type(values) is not list or not minimum <= len(values) <= maximum:
        raise ValueError("invalid scenario list")
    return tuple(_text(value, ITEM_LIMIT) for value in values)


def _check(raw, purpose):
    if type(raw) is not dict or set(raw) != set(ScenarioCheckData.__dataclass_fields__):
        raise ValueError("invalid scenario check fields")
    identifier = raw["id"]
    if type(identifier) is not str or _text(identifier, ID_LIMIT) != identifier:
        raise ValueError("invalid scenario check id")
    goal = raw["goal"]
    if type(goal) is not int or not 1 <= goal <= len(purpose):
        raise ValueError("scenario check names an unknown purpose goal")
    if raw["mode"] not in MODES or raw["evidence_kind"] not in EVIDENCE_KINDS:
        raise ValueError("invalid scenario check mode or evidence kind")
    return ScenarioCheckData(
        identifier,
        goal,
        _text(raw["text"], CHECK_TEXT_LIMIT),
        raw["mode"],
        _text(raw["required_evidence"], CHECK_TEXT_LIMIT),
        raw["evidence_kind"],
    )


def _artifact_requirements(raw, checks):
    allowed = {check.id for check in checks if check.evidence_kind != "recorded_action"}
    if type(raw) is not list or len(raw) > ARTIFACT_LIMIT:
        raise ValueError("invalid artifact requirements")
    result, seen, paths, aliases = [], set(), set(), {}
    for item in raw:
        if (
            type(item) is not dict
            or set(item) != {"check", "paths"}
            or type(item["check"]) is not str
            or item["check"] not in allowed
            or item["check"] in seen
            or type(item["paths"]) is not list
            or not 1 <= len(item["paths"]) <= ARTIFACT_LIMIT
        ):
            raise ValueError("invalid artifact requirement")
        selected = []
        for path in item["paths"]:
            if (
                type(path) is not str
                or not 1 <= len(path) <= ARTIFACT_PATH_LIMIT
                or sensitive_text(path)
                or (path.casefold() in aliases and aliases[path.casefold()] != path)
                or any(
                    not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*", part)
                    or re.match(
                        r"(?i)(?:private|eval|assessment|criteria|grader)", part
                    )
                    for part in path.split("/")
                )
                or path in selected
            ):
                raise ValueError("invalid or private artifact path")
            selected.append(path)
            aliases[path.casefold()] = path
            paths.add(path)
        seen.add(item["check"])
        result.append(ArtifactRequirementData(item["check"], tuple(selected)))
    if len(paths) > ARTIFACT_LIMIT:
        raise ValueError("too many required artifact paths")
    return tuple(result)


def parse_scenario(raw, purpose):
    """Return None for an unrecorded scenario, else a validated ScenarioData."""
    if raw is None:
        return None
    if not purpose:
        raise ValueError("a scenario record needs frozen purpose goals")
    fields = set(ScenarioData.__dataclass_fields__)
    if type(raw) is not dict or set(raw) not in (
        fields,
        fields - {"artifact_requirements"},
    ):
        raise ValueError("invalid scenario fields")
    checks = raw["checks"]
    if type(checks) is not list or not 1 <= len(checks) <= 16:
        raise ValueError("a scenario needs one to sixteen checks")
    parsed = tuple(_check(check, purpose) for check in checks)
    if len({check.id for check in parsed}) != len(parsed):
        raise ValueError("duplicate scenario check id")
    if {check.goal for check in parsed} != set(range(1, len(purpose) + 1)):
        raise ValueError("scenario checks must cover every purpose goal")
    requirements = parse_source_requirements(
        raw["source_requirements"],
        (check.id for check in parsed if check.evidence_kind == "source_consistency"),
    )
    return ScenarioData(
        _text(raw["summary"], SUMMARY_LIMIT),
        _text(raw["rationale"], RATIONALE_LIMIT),
        _texts(raw["conditions"], 1, 8),
        _texts(raw["limitations"], 0, 8),
        parsed,
        requirements,
        _artifact_requirements(raw.get("artifact_requirements", []), parsed),
    )
