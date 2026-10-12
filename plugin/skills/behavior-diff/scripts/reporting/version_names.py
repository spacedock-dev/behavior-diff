"""Mark clear references to the compared Before and After versions in prose.

Authored report prose uses capitalized ``Before`` and ``After`` both as the
names of the compared versions and as ordinary temporal words. Only clear
version references are marked; ambiguous uses stay plain text.
"""

import html
import re

# Quoted or code text, URLs, and identifiers keep their exact wording. Straight
# single quotes open and close only at word edges, so possessives stay prose.
_PROTECTED = re.compile(
    r"(?<!`)(?P<ticks>`+)(?!`)[\s\S]*?(?<!`)(?P=ticks)(?!`)"
    r"|\"[^\"]*\"|“[^”]*”|‘[^’]*’|(?<!\w)'[^'\n]*'(?!\w)"
    r"|\S*://\S*|\bwww\.\S+"
)
_TAIL = r"(?![\w/\\]|-\w|\.\w)"
_NAME = re.compile(r"(?<![\w\-/\\.@#=$])(Before|After)" + _TAIL)
_PAIR = re.compile(r"\s+(?:and|or|nor|vs\.?|versus)\s+(?:Before|After)" + _TAIL)
_CLOSING = re.compile(r"\s*(?:[,:;.!?)]|$)|['’]s\b")
_CLAUSE = re.compile(r"[^,;:.!?()]*")
_SENTENCE_END = ".!?"
_CLAUSE_START = "([,:;—–-*•"
_TRAILING_QUOTES = "\"'”’)]"
# Words that continue a version-named subject ("After cannot", "Before also").
_AUXILIARIES = frozenset(
    "is was has had does did can cannot could will would should may might must "
    "also still never always already isn't wasn't hasn't hadn't doesn't didn't "
    "can't won't wouldn't shouldn't".split()
)
# Words that open a temporal phrase even when they end like a verb.
_TEMPORAL = frozenset(
    "this its his hers ours yours theirs those whereas seconds minutes hours "
    "days weeks months years".split()
)
_IRREGULAR_PAST = frozenset(
    "wrote kept chose made took gave found sent built read ran saw left brought went".split()
)
# Object openers after a verb-like word mark a predicate ("Before deleted it",
# "After adds a"), not a noun phrase ("After failed checks").
_OBJECTS = frozenset(
    "it them him me us you the a an this that these those its their his her our "
    "your my "
    "each every all any some no both one two three several another".split()
)


def _opens_clause(text: str, start: int) -> bool:
    prefix = text[:start]
    stripped = prefix.rstrip()
    if not stripped or "\n" in prefix[len(stripped) :]:
        return True
    if stripped[-1] in _CLAUSE_START:
        return True
    unquoted = stripped.rstrip(_TRAILING_QUOTES)
    return not unquoted or unquoted[-1] in _SENTENCE_END


def _clear_opening(rest: str) -> bool:
    """Apply the conservative convention for a name that opens a clause.

    Punctuation, a possessive, a paired name, or an auxiliary marks a version
    name. A verb-like next word marks one when an object opener follows it.
    Other openings stay plain: a plural noun can resemble a present-tense verb
    ("After tests pass we deploy").
    """
    if _CLOSING.match(rest) or _PAIR.match(rest):
        return True
    clause = _CLAUSE.match(rest).group()
    words = clause.split()
    index = 1 if len(words) > 1 and words[0].endswith("ly") else 0
    if not words or not re.fullmatch(r"[a-z][a-z'’]*", words[index]):
        return False
    word = words[index].replace("’", "'")
    if word in _AUXILIARIES:
        return True
    if (
        word in _TEMPORAL
        or word.endswith("ing")
        or (len(word) <= 3 and word not in _IRREGULAR_PAST)
    ):
        return False
    present = word.endswith("s") and not word.endswith(("ss", "us", "is"))
    past = (word.endswith("ed") and not word.endswith("eed")) or word in _IRREGULAR_PAST
    following = words[index + 1] if len(words) > index + 1 else ""
    return (present or past) and following in _OBJECTS


def version_name_html(text: str) -> str:
    """Escape prose and wrap clear version names in a version label."""
    protected = [match.span() for match in _PROTECTED.finditer(text)]
    parts = []
    position = 0
    for match in _NAME.finditer(text):
        start, end = match.span()
        if any(low <= start < high for low, high in protected):
            continue
        if _opens_clause(text, start) and not _clear_opening(text[end:]):
            continue
        parts.append(html.escape(text[position:start]))
        parts.append(f'<strong class="version-label">{match.group()}</strong>')
        position = end
    parts.append(html.escape(text[position:]))
    return "".join(parts)
