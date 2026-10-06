"""Bundled decorative illustrations; report text never supplies SVG markup."""

# Keep this notice in the source and exported SVG: reports distribute the icon.
_LUCIDE_WRENCH_NOTICE = """<!--
Lucide wrench: https://lucide.dev/icons/wrench
ISC License

Copyright (c) 2026 Lucide Icons and Contributors

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
-->"""

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
    + _LUCIDE_WRENCH_NOTICE
    + '<svg x="122" y="66" width="80" height="80" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0'
    "l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057"
    "l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259"
    'c.438.12.54.662.219.984z"/></svg>',
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
