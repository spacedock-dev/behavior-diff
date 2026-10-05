"""Validate optional human summaries against exact trial evidence group identities."""

import re
from collections import Counter
from dataclasses import dataclass
from itertools import zip_longest
from typing import Tuple


@dataclass(frozen=True)
class TrialSummaryData:
    before_trial: str
    after_trial: str
    takeaway: str
    before: str
    after: str
    caveat: str


def trial_group_names(before, after):
    """Use persisted variant order, not numeric suffixes or execution pairing."""
    return tuple(zip_longest(before, after, fillvalue=""))


def _text(value, required):
    if type(value) is not str:
        raise ValueError("invalid trial summary text")
    text = value.strip()
    if (
        (required and not text)
        or len(text) > 240
        or len(text.split()) > 40
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
        or any(char in value for char in "<>`")
        or re.search(r"\*\*|__|!\[|\[[^\]]*\]\(|^#{1,6}\s", value)
    ):
        raise ValueError("trial summary must be short plain text")
    return text


def parse_trial_summaries(raw, groups=None) -> Tuple[TrialSummaryData, ...]:
    """Discard invalid/ambiguous summaries without discarding underlying evidence.

    When groups are supplied, both trial names must match one positional group
    exactly. Duplicate identities invalidate all copies, even a malformed copy.
    """
    if type(raw) is not list:
        return ()
    identities = Counter(
        (item["before_trial"], item["after_trial"])
        for item in raw
        if type(item) is dict
        and type(item.get("before_trial")) is str
        and type(item.get("after_trial")) is str
    )
    groups = tuple(groups) if groups is not None else None
    allowed = set(groups) if groups is not None else None
    parsed = {}
    for item in raw:
        if type(item) is not dict:
            continue
        before_trial, after_trial = item.get("before_trial"), item.get("after_trial")
        if type(before_trial) is not str or type(after_trial) is not str:
            continue
        identity = (before_trial, after_trial)
        if (
            not any(identity)
            or identities[identity] != 1
            or (allowed is not None and identity not in allowed)
            or (before_trial and not before_trial.startswith("before-"))
            or (after_trial and not after_trial.startswith("after-"))
        ):
            continue
        try:
            takeaway = _text(item.get("takeaway"), True)
            before = _text(item.get("before"), bool(before_trial))
            after = _text(item.get("after"), bool(after_trial))
            caveat = _text(item.get("caveat", ""), False)
            if (not before_trial and before) or (not after_trial and after):
                continue
            parsed[identity] = TrialSummaryData(
                before_trial, after_trial, takeaway, before, after, caveat
            )
        except ValueError:
            continue
    order = groups if groups is not None else parsed
    return tuple(parsed[identity] for identity in order if identity in parsed)
