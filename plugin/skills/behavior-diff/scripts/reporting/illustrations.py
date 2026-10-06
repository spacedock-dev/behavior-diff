"""Bundled decorative illustrations; report text never supplies SVG markup."""

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
}


def illustration(icon: str) -> str:
    """Return only a fixed, decorative enum illustration with neutral fallback."""
    return (
        '<svg class="summary-picture" viewBox="0 0 240 175" '
        'aria-hidden="true" focusable="false">'
        + _ICONS.get(icon, _ICONS["neutral"])
        + "</svg>"
    )
