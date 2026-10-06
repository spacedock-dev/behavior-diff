"""Validate optional, evidence-linked explanations without generating new evidence."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from reporting.schema import EvidenceClaimData


@dataclass(frozen=True)
class ExplanationStepData:
    title: str
    before: str
    after: str
    meaning: str
    decisions: Tuple[int, ...]


@dataclass(frozen=True)
class ExplanationExampleData:
    side: str
    trial: str
    text: str


@dataclass(frozen=True)
class ChangeExplanationData:
    headline: str
    overview: str
    steps: Tuple[ExplanationStepData, ...]
    unchanged: Tuple["EvidenceClaimData", ...]
    limits: Tuple["EvidenceClaimData", ...]
    examples: Tuple[ExplanationExampleData, ...]


# Comparison operators and formula punctuation are plain text, not markup.
_MARKUP = re.compile(
    r"</?[A-Za-z][^>]*>|<!--|```|`|\*\*|__|\[[^\]]*\]\([^)]*\)|^\s{0,3}#{1,6}\s",
    re.MULTILINE,
)


def _text(value, limit, excerpt=False):
    if type(value) is not str or not value.strip() or len(value) > limit:
        raise ValueError("invalid explanation text")
    if any(
        (ord(char) < 32 and (not excerpt or char not in "\n\t"))
        or 127 <= ord(char) <= 159
        for char in value
    ):
        raise ValueError("unsafe explanation control character")
    if not excerpt and _MARKUP.search(value):
        raise ValueError("explanation narrative must be plain text")
    return value if excerpt else value.strip()


def _items(raw, name, minimum=0):
    values = raw[name]
    if type(values) is not list or not minimum <= len(values) <= 8:
        raise ValueError("invalid explanation list")
    if any(type(value) is not dict for value in values):
        raise ValueError("invalid explanation entry")
    return values


def _changed(row):
    from reporting.content import choices_changed

    # Extraction has already recomputed this flag; serialized report rows must
    # be checked from their actual distributions rather than a supplied flag.
    if type(row) is dict:
        return row["diverges"]
    return choices_changed(row.before, row.after)


def _references(raw, positions):
    refs = raw["decisions"]
    if (
        type(refs) is not list
        or not refs
        or any(type(ref) is not int or ref not in positions for ref in refs)
        or len(set(refs)) != len(refs)
    ):
        raise ValueError("invalid explanation references")
    return tuple(positions[ref] for ref in refs)


def parse_explanation(raw, rows, final_answers, positions=None):
    """Omit malformed interpretation; validate quotes against their named source.

    ``final_answers`` maps side to exact trial name to the recorded final answer.
    ``positions`` maps extractor row indexes to surviving, sorted row indexes.
    An absent explanation is unavailable, not evidence of unchanged behavior.
    """
    from reporting.schema import EvidenceClaimData

    if type(raw) is not dict:
        return None
    if positions is None:
        positions = {index: index for index in range(1, len(rows) + 1)}
    try:
        steps = tuple(
            ExplanationStepData(
                _text(item["title"], 120),
                _text(item["before"], 480),
                _text(item["after"], 480),
                _text(item["meaning"], 480),
                _references(item, positions),
            )
            for item in _items(raw, "steps", minimum=1)
        )
        claims = {}
        for name in ("unchanged", "limits"):
            values = []
            for item in _items(raw, name):
                refs = _references(item, positions)
                if name == "unchanged" and any(_changed(rows[ref - 1]) for ref in refs):
                    raise ValueError("unchanged claim cites changed behavior")
                values.append(EvidenceClaimData(_text(item["text"], 480), refs))
            claims[name] = tuple(values)
        examples = []
        seen = set()
        for item in _items(raw, "examples"):
            side, trial = item["side"], item["trial"]
            if (
                type(side) is not str
                or side not in ("before", "after")
                or type(trial) is not str
                or not trial.startswith(side + "-")
                or type(final_answers) is not dict
                or type(final_answers.get(side)) is not dict
            ):
                raise ValueError("invalid explanation example source")
            final = final_answers[side].get(trial)
            text = _text(item["text"], 1200, excerpt=True)
            identity = (side, trial, text)
            if type(final) is not str or text not in final or identity in seen:
                raise ValueError("explanation example is not an exact final excerpt")
            seen.add(identity)
            examples.append(ExplanationExampleData(side, trial, text))
        return ChangeExplanationData(
            _text(raw["headline"], 120),
            _text(raw["overview"], 600),
            steps,
            claims["unchanged"],
            claims["limits"],
            tuple(examples),
        )
    except (KeyError, TypeError, ValueError, IndexError):
        return None
