"""Instruction evidence shared by extraction and report rendering."""

import difflib
import re
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DiffHunk:
    number: int
    header: str
    lines: Tuple[str, ...]


_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@(?: .*)?$")


def parse_diff_hunks(text) -> Tuple[DiffHunk, ...]:
    """Return complete unified hunks, not hunk-like headings in plain text."""
    lines = text.splitlines()
    hunks = []
    index = 0
    in_file = False
    while index < len(lines):
        line = lines[index]
        if (
            line.startswith("--- ")
            and index + 1 < len(lines)
            and lines[index + 1].startswith("+++ ")
        ):
            in_file = True
            index += 2
            continue
        match = _HUNK_HEADER.fullmatch(line) if in_file else None
        if match is None:
            in_file = False
            index += 1
            continue
        before, after = (
            int(value) if value is not None else 1 for value in match.groups()
        )
        header = line
        start = index + 1
        index = start
        changed = False
        while index < len(lines):
            body = lines[index]
            if body == "\\ No newline at end of file" and index > start:
                index += 1
                continue
            if before == after == 0:
                break
            if body.startswith(" ") and before > 0 and after > 0:
                before -= 1
                after -= 1
            elif body.startswith("-") and before > 0:
                before -= 1
                changed = True
            elif body.startswith("+") and after > 0:
                after -= 1
                changed = True
            else:
                break
            index += 1
        if before == after == 0 and changed:
            hunks.append(DiffHunk(len(hunks) + 1, header, tuple(lines[start:index])))
        else:
            in_file = False
    return tuple(hunks)


def normalize_edit_hunks(value, hunk_count) -> Tuple[int, ...]:
    """An invalid mapping is unavailable; it never invalidates the observations."""
    if type(value) is not list or any(
        type(number) is not int or not 1 <= number <= hunk_count for number in value
    ):
        return ()
    if len(set(value)) != len(value):
        return ()
    return tuple(value)


def rule_diff(run, capsule, target_file):
    before_project = run / "before-1" / "project"
    after_project = run / "after-1" / "project"
    before_file = before_project / target_file
    after_file = after_project / target_file
    if (
        before_project.is_dir()
        and after_project.is_dir()
        and (before_file.is_file() or after_file.is_file())
    ):
        before = before_file.read_text() if before_file.is_file() else ""
        after = after_file.read_text() if after_file.is_file() else ""
        return "".join(
            line if line.endswith("\n") else line + "\n\\ No newline at end of file\n"
            for line in difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile="{0} (before)".format(target_file),
                tofile="{0} (after)".format(target_file),
            )
        )
    try:
        return (capsule / "rule.md").read_text()
    except OSError:
        return "(no variant files or rule.md found — diff unavailable)"
