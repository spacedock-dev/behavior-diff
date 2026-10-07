"""Bundled decorative illustrations; report text never supplies SVG markup."""

from reporting.attention import ATTENTION_ICONS

_PAPER = (
    '<rect x="32" y="21" width="112" height="134" rx="14" '
    'fill="var(--summary-paper)" stroke="currentColor" stroke-width="3"/>'
    '<path d="M55 52h64M55 69h42M55 104h35M55 121h25" '
    'stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity=".38"/>'
)
_ICONS = {
    "neutral": _PAPER,
    "report": _PAPER + '<rect x="110" y="71" width="98" height="72" rx="14" '
    'fill="var(--summary-accent-bg)" stroke="currentColor" stroke-width="3"/>'
    '<path d="m131 142-8 16 33-15M132 94h51M132 112h34" '
    'fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>',
    "edit": _PAPER
    + '<circle cx="162" cy="106" r="48" fill="var(--summary-accent-bg)"/>'
    '<svg x="114" y="58" width="96" height="96" viewBox="0 0 100 100">'
    '<g transform="translate(65 28) rotate(45)" fill="currentColor">'
    '<path d="M0 8V60" fill="none" stroke="currentColor" '
    'stroke-width="10" stroke-linecap="round"/>'
    '<path d="M-9-14C-20-9-21 5-11 12C-5 17 5 17 11 12'
    'C21 5 20-9 9-14V-2L0 3L-9-2Z"/></g></svg>',
    "inspect": _PAPER
    + '<circle cx="151" cy="94" r="33" fill="var(--summary-accent-bg)" '
    'stroke="currentColor" stroke-width="6"/>'
    '<path d="m175 119 29 29" stroke="currentColor" stroke-width="12" stroke-linecap="round"/>',
    "test": _PAPER
    + '<circle cx="161" cy="110" r="45" fill="var(--summary-accent-bg)"/>'
    '<path d="m136 110 18 18 34-37" fill="none" stroke="currentColor" '
    'stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>',
    "continue": _PAPER
    + '<circle cx="161" cy="110" r="45" fill="var(--summary-accent-bg)"/>'
    '<path d="M135 110h51m-20-20 20 20-20 20" fill="none" '
    'stroke="currentColor" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>',
    "stop": _PAPER
    + '<circle cx="161" cy="110" r="45" fill="var(--summary-accent-bg)"/>'
    '<rect x="140" y="89" width="42" height="42" rx="5" fill="currentColor"/>',
    "delegate": _PAPER + '<circle cx="166" cy="84" r="19" fill="currentColor"/>'
    '<path d="M130 143v-14a36 36 0 0 1 72 0v14z" '
    'fill="var(--summary-accent-bg)" stroke="currentColor" stroke-width="3"/>'
    '<path d="M85 92h35m-12-12 12 12-12 12" fill="none" '
    'stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>',
    "agent": '<rect x="59" y="39" width="122" height="103" rx="20" '
    'fill="var(--summary-accent-bg)" stroke="currentColor" stroke-width="4"/>'
    '<circle cx="98" cy="85" r="8" fill="currentColor"/>'
    '<circle cx="142" cy="85" r="8" fill="currentColor"/>'
    '<path d="M96 116h48M120 39V23" stroke="currentColor" stroke-width="5" '
    'stroke-linecap="round"/>',
    "person": '<circle cx="120" cy="55" r="25" fill="var(--summary-accent-bg)" '
    'stroke="currentColor" stroke-width="4"/>'
    '<path d="M68 151v-24a52 52 0 0 1 104 0v24z" '
    'fill="var(--summary-accent-bg)" stroke="currentColor" stroke-width="4"/>',
    "clock": '<circle cx="120" cy="88" r="59" fill="var(--summary-accent-bg)" '
    'stroke="currentColor" stroke-width="4"/>'
    '<path d="M120 48v42l29 18" fill="none" stroke="currentColor" stroke-width="6" '
    'stroke-linecap="round" stroke-linejoin="round"/>',
    "file": _PAPER,
    "shared": '<circle cx="85" cy="55" r="21" fill="var(--summary-accent-bg)" '
    'stroke="currentColor" stroke-width="4"/>'
    '<circle cx="157" cy="55" r="21" fill="var(--summary-accent-bg)" '
    'stroke="currentColor" stroke-width="4"/>'
    '<path d="M47 145v-18a38 38 0 0 1 76 0v18zM120 145v-18a38 38 0 0 1 76 0v18z" '
    'fill="var(--summary-accent-bg)" stroke="currentColor" stroke-width="4"/>',
    "optional": _PAPER
    + '<circle cx="164" cy="112" r="41" fill="var(--summary-accent-bg)" '
    'stroke="currentColor" stroke-width="4"/>'
    '<path d="M151 98a13 13 0 1 1 20 11l-7 6v7M164 135v1" fill="none" '
    'stroke="currentColor" stroke-width="6" stroke-linecap="round"/>',
    "required": _PAPER
    + '<circle cx="164" cy="112" r="41" fill="var(--summary-accent-bg)" '
    'stroke="currentColor" stroke-width="4"/>'
    '<path d="M164 88v32M164 135v1" fill="none" stroke="currentColor" '
    'stroke-width="7" stroke-linecap="round"/>',
}


def illustration(icon: str) -> str:
    """Return only a fixed, decorative enum illustration with neutral fallback."""
    icon = icon if icon in ATTENTION_ICONS else "neutral"
    return (
        '<svg class="summary-picture" viewBox="0 0 240 175" '
        'aria-hidden="true" focusable="false">'
        + _ICONS.get(icon, _ICONS["neutral"])
        + "</svg>"
    )
