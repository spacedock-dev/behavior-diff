---
name: elwp
description: Creates plain-language, illustrated HTML explanations of plans, architecture, and user journeys in this repository. Use when asked to explain a design with pictures, make an ELI5 web page, or reuse the style of verification-handoff-explained.html.
---

# Explain with pictures

Turn a technical proposal into a page the owner can use to understand a decision.
This is a repo-local maintainer skill, not plugin payload or a comparison runner.
It owns the explanation and page format; `anatomy` supplies illustration guidance
when available. Do not copy that skill or its toolkit into this repository.

## Quick start

Example request: “Use elwp to explain this architecture plan.
Show the user journey, the choices, and what remains unverified.”

Read the source plan and relevant implementation before drafting. Use
[the illustrated handoff page](../../../docs/verification-handoff-explained.html)
as the visual and interaction reference, and
[its source plan](../../../plans/2026-10-29-verification-handoff-journey-first-architecture.md)
as an example of linking the page to a technical document.
Reuse the presentation, not its case-specific claims or component names.

## Establish the explanation

1. Identify the reader's question and the decision the page should help them make.
   Use supplied context; ask only for a materially different scope or missing fact.
2. Separate current behavior, proposed changes, observed results, and unknowns.
   Label proposals and illustrative examples visibly. Never present an authored
   walkthrough as a successful test or invent evidence to make the story clearer.
3. Choose one familiar physical analogy whose parts map to the real responsibilities.
   The object should explain the idea: a workshop, desk, instrument, or machine,
   not decorative boxes with technical labels. Do not force every topic into the
   handoff page's three roles or imply another service must be built.
4. Explain in ordinary adult language: short sentences, concrete actions, and
   definitions before jargon. Keep technical names accurate; use the owner's
   agreed terms, but do not rename unrelated product concepts. ELI5 means clear,
   not childish. Put implementation details in optional disclosure sections.

## Build one local page

5. Update a named existing page when requested; otherwise create a descriptive
   `docs/<topic>-explained.html`. Preserve unrelated edits. Keep the result
   self-contained: inline CSS, SVG, and JavaScript, without remote fonts, scripts,
   analytics, CDNs, model calls, or product execution behind the controls.
6. Follow the reference page's structure, adapting the number of roles and steps:
   - A short headline, the reader's question, and the central idea.
   - Illustrated responsibility cards with recognizable physical objects.
   - A clickable journey showing each step, its owner, and the user's part.
   - Before/after differences or common misunderstandings where relevant.
   - Options with concrete benefits and costs, plus a recommendation and reason.
   - What needs proof, what remains unknown, and the next decision or action.
   - A relative link back to the source plan or technical explanation.
7. Read the installed `anatomy` skill before using its toolkit for new illustrations.
   Reuse appropriate existing SVG artwork without changing its meaning. If the
   skill is unavailable, use the reference page's standalone SVG approach and
   disclose that the toolkit was not used; never claim its audits ran.
   Match the reference's restrained palette, physical depth, consistent shading,
   framed figures, and purposeful detail. Keep labels outside the drawing and
   captions truthful. Never introduce WebGL or 3D just to decorate the page.
8. Support desktop and narrow screens, light/dark themes, readable contrast,
   keyboard operation, visible focus, and reduced motion. Give meaningful SVGs
   accessible names. Use real buttons and an exposed selected-step state. Include
   a useful no-JavaScript explanation; do not hide essential facts in interaction.
   Keep theme switching and walkthrough controls local and free of external effects.

## Verify the actual page

9. Open it in a real browser using a local file URL or a server bound to loopback
   that serves only the intended preview directory. Exercise every step, next-step
   wrapping, theme switching, disclosure controls, and the source-document link.
   Check keyboard navigation and selected-step state against the displayed text.
10. Inspect desktop and a 390-pixel-wide viewport in both themes. Check overflow,
    clipping, readable labels, focus visibility, and reduced-motion behavior.
    Capture and inspect screenshots, including illustration close-ups. For new
    toolkit geometry, run the applicable `anatomy` checks; do not claim checks on
    reused artwork that were not performed. Report unavailable checks explicitly.
11. Re-read the explanation against its sources: owners, permissions, costs,
    uncertainty, and proposed versus observed behavior must still agree. Browser
    checks establish presentation and interaction, not architecture correctness,
    comprehension, or successful execution of the illustrated workflow.

## Deliver

Link the finished page from its associated plan when one exists. Return the page
link, checks actually exercised, and any remaining limits. Keep one maintained
page, not a mirrored template or a new rendering framework. Remove owned temporary
build/check files and close owned browser tabs or preview servers after review.
Do not commit, push, publish a gallery entry, release, or run a live comparison
unless the user separately authorizes that action. Do not add wording-only tests
for this skill; use a local page walkthrough to check the workflow.
