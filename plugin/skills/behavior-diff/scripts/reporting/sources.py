"""Identify recorded source descriptors and the frozen sources a check requires.

Patterns are bounded `fnmatchcase` globs over a captured record's `source`
descriptor (tool name plus recorded arguments). They never inspect returned
content or model explanations, and nothing here runs or fetches a source.
"""

from dataclasses import dataclass
from fnmatch import fnmatchcase
import re
from typing import Tuple

SENSITIVE_SOURCE = "[sensitive source omitted]"
DESCRIPTOR_TRUNCATED = " [descriptor truncated]"
PATTERN_LIMIT = 200
PATTERNS_PER_GROUP = 8
GROUP_LIMIT = 32

_SENSITIVE = re.compile(
    r"(?i)(?:\b(?:api[_ -]?key|access[_ -]?token|password|passwd|client[_ -]?secret)"
    r"(?:\\?[\"'])?\s*[:=]\s*\S+|\bbearer\s+\S+|-----BEGIN [^-]*PRIVATE KEY-----|"
    r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|AKIA[A-Z0-9]{16})\b|"
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})"
)
_PRIVATE_PATH = re.compile(
    r"(?i)(?:^|[:/\\\s\"'])(?:\.env(?:\.[^/\\\s]*)?|\.ssh|\.aws|\.gnupg|"
    r"credentials(?:\.[^/\\\s]*)?|secrets?(?:\.[^/\\\s]*)?|auth\.json|"
    r"id_rsa|id_ed25519)(?:$|[/\\\s\"':])"
)
# A selector needs one literal run that names a path, endpoint, or identifier
# (a delimiter inside a name, or letters with a number), not merely a tool name,
# a common word, or a bare extension.
_IDENTITY = re.compile(
    r"(?=.{4})(?:.*[A-Za-z0-9][./:#_\-][A-Za-z0-9]|(?=.*[A-Za-z]).*[0-9]).*"
)


@dataclass(frozen=True)
class SourceRequirementData:
    check: str
    any_of: Tuple[str, ...]


def sensitive_text(value):
    """Return whether text matches known credential, email, or private-path forms."""
    return bool(_SENSITIVE.search(value) or _PRIVATE_PATH.search(value))


def _pattern(value):
    if (
        type(value) is not str
        or not 0 < len(value) <= PATTERN_LIMIT
        or value != value.strip()
        or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value)
        or "[" in value
        or "]" in value
    ):
        # Brackets would be character classes; omitted descriptors carry them too.
        raise ValueError("invalid source requirement pattern")
    if not any(_IDENTITY.fullmatch(run) for run in re.split(r"[*?]+", value)):
        raise ValueError("source requirement pattern is too broad")
    # Wildcards stand in for path delimiters when checking private selectors.
    if sensitive_text(value) or sensitive_text(re.sub(r"[*?]", " ", value)):
        raise ValueError("source requirement pattern names a sensitive source")
    return value


def parse_source_requirements(raw, source_checks):
    """Validate frozen groups; every `source_checks` id needs at least one group."""
    source_checks = tuple(source_checks)
    if type(raw) is not list or len(raw) > GROUP_LIMIT:
        raise ValueError("invalid source requirements")
    parsed = []
    seen = set()
    for item in raw:
        if type(item) is not dict or set(item) != {"check", "any_of"}:
            raise ValueError("invalid source requirement fields")
        check = item["check"]
        if type(check) is not str or check not in source_checks:
            raise ValueError("source requirement names a non-source-consistency check")
        patterns = item["any_of"]
        if type(patterns) is not list or not 1 <= len(patterns) <= PATTERNS_PER_GROUP:
            raise ValueError("a source requirement needs one to eight patterns")
        patterns = tuple(_pattern(pattern) for pattern in patterns)
        if len(set(patterns)) != len(patterns):
            raise ValueError("duplicate source requirement pattern")
        identity = (check, frozenset(patterns))
        if identity in seen:
            raise ValueError("duplicate source requirement group")
        seen.add(identity)
        parsed.append(SourceRequirementData(check, patterns))
    if {requirement.check for requirement in parsed} != set(source_checks):
        raise ValueError("every source consistency check needs a source requirement")
    return tuple(parsed)


def source_matches(source, patterns):
    """Match a trustworthy recorded descriptor against validated patterns."""
    if (
        type(source) is not str
        or source == SENSITIVE_SOURCE
        or source.endswith(DESCRIPTOR_TRUNCATED)
    ):
        return False
    return any(fnmatchcase(source, pattern) for pattern in patterns)


def unmet_source_requirements(requirements, check, sources):
    """Return `check`'s groups that none of the given descriptors satisfies.

    Pass only descriptors of referenced, readable, proven recorded calls.
    """
    sources = tuple(sources)
    return tuple(
        requirement
        for requirement in requirements
        if requirement.check == check
        and not any(source_matches(source, requirement.any_of) for source in sources)
    )
