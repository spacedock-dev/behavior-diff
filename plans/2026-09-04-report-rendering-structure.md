# Report Rendering Structure Design

**Status:** Approved in conversation on 2026-09-04

## Goal

Make the Behavior Diff report pipeline easy to change without coupling report data, shared wording, Markdown structure, HTML structure, and HTML style.

This change restructures report generation only. For fixed synthetic inputs, the existing `report.md`, `report.html`, and `report-artifact.html` outputs must remain byte-for-byte unchanged.

## Problem

`plugin/skills/behavior-diff/scripts/render.py` is one 923-line script. It currently:

1. reads config, grades, traces, the task, the instruction diff, and optional decisions;
2. computes trial and variant facts;
3. chooses result and explanatory wording;
4. builds command and decision flows;
5. renders Markdown;
6. renders HTML and embedded CSS;
7. writes all report files.

Most of this work happens at module load through global values. The HTML and Markdown paths repeat decision and flow logic. Some data is already formatted for Markdown and then changed for HTML. For example, HTML removes Markdown `**` markers from a shared count string.

This makes a small style or wording change risky. A change in one format can affect data calculation or the other format.

## Current input boundary

The existing persisted run files remain the source of evidence:

- `config.json`
- `task.md`
- `grades.tsv`
- each trial's canonical `trace.jsonl`
- the before and after target files, or `rule.md` as the existing fallback
- optional `decisions.json`

`behavior-diff.sh` and `behavior-diff-live` both produce this shape. The restructure must not create a second pipeline for either skill.

## Accepted constraints

- Keep the current `render.py RUN_DIR CAPSULE_DIR MODEL [CONFIG_JSON]` command.
- Keep its stdout text, required-input errors, config errors, and optional-decisions fallback.
- Keep writing `report.md`, `report-artifact.html`, and `report.html`.
- Add `report-data.json` as an internal, versioned artifact.
- Keep one in-memory typed report structure and serialize that same structure to JSON.
- Keep all generated reports deterministic.
- Keep Python standard-library only.
- Keep `report.html` as one portable file. Maintain CSS separately in the source tree, then inline it during generation.
- Keep shared wording in one content layer by default.
- Allow a renderer to own wording only when the formats intentionally differ.
- Preserve captured and self-reported evidence rules.
- Do not change trials, grading, decision extraction, report opening, report content, or visual style.
- Keep latent graded/demo mode and the existing separate run/capsule input contract in this phase.

## Chosen architecture

Use one layered Python package behind the existing `render.py` entry point.

```text
run artifacts
  config.json · task.md · grades.tsv · trace.jsonl · decisions.json
        |
        v
reporting/load.py
  parse evidence · compute counts · flow · result · diff
        |
        v
reporting/schema.py + reporting/content.py
  typed ReportData · shared wording · schema_version: 1
        |
        +----------------> report-data.json
        |
        +----------------> reporting/render_markdown.py -> report.md
        |
        +----------------> reporting/render_html.py + report.css
                                                    -> report-artifact.html
                                                    -> report.html

render.py remains the only command entry point and file writer.
```

### `reporting/schema.py`

Own the typed report structure. Do not use `model.py`; “model” is easy to confuse with an AI model.

The main type is `ReportData`. Nested immutable records cover:

- configuration and metadata;
- trials and variants;
- result state;
- command-derived flow;
- decision rows and choices;
- shared report content.

`schema.py` also owns deterministic `to_dict` and `from_dict` conversion. It does not read files, write files, render markup, or call an AI model.

### `reporting/load.py`

Read the current run artifacts and build `ReportData`.

It owns the format-neutral behavior currently mixed into `render.py`:

- canonical trace parsing;
- variant totals and blocked counts;
- result kind selection;
- command classification and flow calculation;
- target-file diff calculation;
- optional decision loading and validation fallback;
- the observed single-run summary facts.

It imports shared copy functions from `content.py`. It does not create Markdown, HTML, CSS, or output files.

### `reporting/content.py`

Own shared human-readable copy:

- title and subtitle defaults;
- section names;
- result text;
- count text;
- observation text;
- the decision explanation;
- the simulation boundary.

HTML and Markdown use this copy unless the current outputs intentionally differ. Existing intentional differences remain renderer-owned. These include HTML's captured-command `$ ` prefix, the formats' different heading markup, and their currently different flow explanations.

### `reporting/render_markdown.py`

Expose one pure function:

```python
render_markdown(report: ReportData) -> str
```

It owns only Markdown presentation:

- section order;
- headings;
- fenced blocks;
- Markdown lists;
- `<details>` blocks already used by the current Markdown report;
- Markdown-specific command display.

It does not read run files or write `report.md`.

### `reporting/render_html.py`

Expose pure functions:

```python
render_artifact(report: ReportData, css: str) -> str
render_document(artifact: str) -> str
```

It owns:

- HTML escaping;
- the report DOM and component layout;
- HTML-only command display;
- the embedded style element;
- the standalone document wrapper.

It does not read run files or write output files.

### `reporting/report.css`

Contain the current CSS in generated form, with one `__RESULT_BG__` token where the result color varies by `result.kind`. `render.py` reads this source and passes it to the HTML renderer. The renderer must find the token exactly once, replace it with the current allowed CSS variable, and inline the result. Generated HTML stays byte-for-byte compatible and portable.

### `render.py`

Remain the compatible command and the only file-writing layer:

1. parse the existing arguments;
2. call `load.py` to build `ReportData`;
3. serialize the data deterministically;
4. render Markdown, artifact HTML, and standalone HTML in memory;
5. after every renderer succeeds, write all four files;
6. print the existing summary and output paths unchanged.

Building every output string before writing prevents a renderer error from pairing one newly written report with stale files from another format.

## Internal `report-data.json` contract

`report-data.json` is internal. It is not a public plugin API and has no cross-release compatibility promise. It must contain `"schema_version": 1` so repository code can reject or migrate a different shape deliberately.

The top-level shape is:

```text
schema_version
metadata
content
rule_diff
result
variants
command_flow
decisions
```

The data must contain the facts and shared copy needed to regenerate both visible formats. It must not contain rendered Markdown, rendered HTML, CSS, filesystem paths outside the report evidence, or raw model/provider credentials.

Both renderers consume the same in-memory `ReportData`. `report-data.json` is the deterministic serialized copy of that object. `ReportData.from_dict` must load the file for tests and future internal tools.

## Evidence separation

Captured and self-reported runs must stay distinct.

- Captured traces may produce the command-derived flow.
- Self-reported actions must never enter command classification.
- Self-reported reports keep their current evidence warning.
- Missing or invalid optional `decisions.json` removes only the decision section and keeps the current fallback report.
- Trial command/action order and final answers remain unchanged.

## Exact-output contract

Before moving production code, capture current outputs from fixed synthetic captured and self-reported runs:

```text
tests/fixtures/report-rendering/captured/report.md
tests/fixtures/report-rendering/captured/report.html
tests/fixtures/report-rendering/captured/report-artifact.html
tests/fixtures/report-rendering/self-reported/report.md
tests/fixtures/report-rendering/self-reported/report.html
tests/fixtures/report-rendering/self-reported/report-artifact.html
```

`tests/live-report-contract.sh` must compare each generated file byte-for-byte with its fixture. The existing focused wording, ordering, escaping, provenance, and invalid-config assertions remain because they explain what a mismatch means.

The new JSON contract must check:

- `report-data.json` exists;
- `schema_version` is `1`;
- both variants and their ordered trials exist;
- captured and self-reported provenance stays explicit;
- `ReportData` survives a `to_dict` / `from_dict` round trip;
- both renderers accept `ReportData` and return strings without writing files.

The committed fixtures remain synthetic and must not contain customer data, private code, credentials, or real transcripts.

## Migration sequence

1. Add byte-for-byte characterization fixtures for both report modes while the current renderer is still authoritative.
2. Add a failing contract for the missing `report-data.json` and typed round trip.
3. Add `schema.py`, `load.py`, and `content.py`. Keep the existing Markdown and HTML blocks in `render.py` until the report data and JSON contract pass.
4. Move Markdown assembly to `render_markdown.py`. Confirm the Markdown fixtures remain exact.
5. Move HTML assembly and the CSS source to `render_html.py` and `report.css`. Confirm both HTML fixtures remain exact.
6. Reduce `render.py` to argument handling, orchestration, writes, and existing stdout.
7. Run the complete deterministic suite and inspect both generated formats from the same synthetic run.

Each move is a clean cutover. Do not leave duplicate renderers, compatibility aliases, or deprecated paths.

## Failure behavior

- Keep current required-input errors and config parsing errors.
- Keep rejecting an invalid `trace_source` with the current message.
- Keep malformed optional `decisions.json` as a missing-decision fallback.
- Do not silently invent missing evidence.
- A renderer exception must occur before any of the four output files are replaced during that invocation.
- Do not catch renderer errors only to emit a partial report.

## Non-goals

- New report wording.
- New HTML layout, typography, color, or spacing.
- New Markdown section order or syntax.
- A public report-data API.
- A generic template engine or Jinja2 dependency.
- Separate renderer commands.
- Changes to `behavior-diff.sh`, `run-trial.sh`, `decisions.py`, or trial stack behavior.
- Removing `report-artifact.html` without first finding and approving every external consumer.
- Removing graded/demo mode or merging run and capsule directories.

## Risks and controls

| Risk | Control |
| --- | --- |
| Moving strings changes whitespace or escaping | Exact captured and self-reported fixtures for all three current files |
| Shared copy changes one format unintentionally | `content.py` owns shared wording; intentional differences are named in renderer tests |
| JSON becomes an accidental public API | Mark it internal in code and docs; include a version instead of compatibility shims |
| HTML source CSS becomes detached from generated output | `render_html.py` requires one result-color token; `render.py` always reads and inlines the bundled `report.css` |
| Self-reported actions leak into command flow | Keep provenance in `ReportData` and preserve the current no-flow contract |
| Optional decisions break the whole report | Preserve the current missing/malformed decisions fallback |
| Partial writes mix old and new reports | Render every string before writing any output file |

## Acceptance criteria

- The existing renderer CLI and direct callers require no changes.
- Fixed captured and self-reported fixtures produce byte-for-byte identical `report.md`, `report.html`, and `report-artifact.html` before and after the refactor.
- `report-data.json` is written with `schema_version: 1`.
- HTML and Markdown consume the same typed `ReportData`.
- Shared copy has one owner in `content.py`.
- Markdown structure changes require edits only in `render_markdown.py` and its fixtures/tests.
- HTML structure changes require edits only in `render_html.py` and its fixtures/tests.
- HTML style changes require edits only in `report.css` and HTML fixtures/tests.
- Loading or comparison changes require edits only in `load.py`, `schema.py`, and data-contract tests.
- Generated HTML remains a standalone file.
- Existing provenance, flow, decisions, ordering, escaping, labels, final answers, fallbacks, and stdout remain unchanged.
- The full deterministic repository suite passes without a live model call.
