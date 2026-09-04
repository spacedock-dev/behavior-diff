# Report Rendering Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split report data loading, shared copy, Markdown rendering, HTML rendering, CSS, and file output while preserving the three current report files byte-for-byte.

**Architecture:** Keep `render.py` as the only CLI and writer. Build one typed `ReportData` through `reporting/load.py`, serialize it as internal schema version 1, and pass the same object to pure Markdown and HTML renderers. Keep shared wording in `reporting/content.py`; keep format structure in the renderers; keep CSS in a source file that is inlined into standalone HTML.

**Tech Stack:** Python 3 standard library, Bash 3.2 contract tests, JSON, HTML/CSS, existing Ruff and deterministic repository checks.

**Design:** `plans/2026-09-04-report-rendering-structure.md`

---

## File structure

Create one private package beside the existing scripts:

```text
plugin/skills/behavior-diff/scripts/
├── render.py                     # compatible CLI and only file writer
└── reporting/
    ├── __init__.py               # marks the private package
    ├── schema.py                 # ReportData records and JSON conversion
    ├── content.py                # shared report wording
    ├── load.py                   # persisted evidence -> ReportData
    ├── render_markdown.py        # ReportData -> Markdown string
    ├── render_html.py            # ReportData + CSS -> HTML strings
    └── report.css                # CSS source with one result-color token
```

Tests and fixed synthetic output:

```text
tests/
├── live-report-contract.sh
├── report-schema-test.py
└── fixtures/report-rendering/
    ├── captured/
    │   ├── report.md
    │   ├── report.html
    │   └── report-artifact.html
    └── self-reported/
        ├── report.md
        ├── report.html
        └── report-artifact.html
```

Do not modify `behavior-diff.sh`, `run-trial.sh`, `decisions.py`, either public skill, the plugin manifests, or README. Their current contracts remain valid.

---

### Task 1: Freeze the current visible reports

**Files:**
- Modify: `tests/live-report-contract.sh:19-105,328-444`
- Create: `tests/fixtures/report-rendering/captured/report.md`
- Create: `tests/fixtures/report-rendering/captured/report.html`
- Create: `tests/fixtures/report-rendering/captured/report-artifact.html`
- Create: `tests/fixtures/report-rendering/self-reported/report.md`
- Create: `tests/fixtures/report-rendering/self-reported/report.html`
- Create: `tests/fixtures/report-rendering/self-reported/report-artifact.html`

- [ ] **Step 1: Add an explicit fixture-update mode to the contract test**

At the top of `tests/live-report-contract.sh`, accept either no argument or exactly `--update-report-fixtures`:

```bash
if (( $# > 1 )); then
  printf 'Usage: %s [--update-report-fixtures]\n' "$0" >&2
  exit 2
fi

update_report_fixtures=false
case ${1:-} in
  "") ;;
  --update-report-fixtures) update_report_fixtures=true ;;
  *)
    printf 'Usage: %s [--update-report-fixtures]\n' "$0" >&2
    exit 2
    ;;
esac
```

Add these helpers after `progress()`:

```bash
fixture_root=$here/fixtures/report-rendering

copy_report_fixtures() {
  local run=$1
  local kind=$2
  local out=$fixture_root/$kind
  mkdir -p "$out"
  cp "$run/report.md" "$out/report.md"
  cp "$run/report.html" "$out/report.html"
  cp "$run/report-artifact.html" "$out/report-artifact.html"
}

require_exact_report() {
  local actual=$1
  local expected=$2
  local message=$3
  if ! cmp -s "$expected" "$actual"; then
    diff -u "$expected" "$actual" >&2 || true
    fail "$message"
  fi
}
```

After the current renderer calls, update only when the explicit flag is present, then compare all three files for both modes:

```bash
if $update_report_fixtures; then
  copy_report_fixtures "$captured_run" captured
  copy_report_fixtures "$self_run" self-reported
fi

for kind in captured self-reported; do
  case $kind in
    captured) actual_run=$captured_run ;;
    self-reported) actual_run=$self_run ;;
  esac
  for report_name in report.md report.html report-artifact.html; do
    require_exact_report \
      "$actual_run/$report_name" \
      "$fixture_root/$kind/$report_name" \
      "$kind $report_name changed"
  done
done
```

Do not remove the existing focused assertions. They explain whether a mismatch concerns provenance, ordering, escaping, labels, decisions, flow, or answers.

- [ ] **Step 2: Generate the goldens from the current renderer**

Run:

```bash
bash tests/live-report-contract.sh --update-report-fixtures
```

Expected: `ok — live report contract passed`, with six new synthetic fixture files. Review every fixture for invented content only: `Live contract`, `Original project instructions`, `Updated project instructions`, `Before answer`, `After answer`, and the synthetic decision row.

- [ ] **Step 3: Verify normal mode cannot rewrite fixtures**

Run:

```bash
bash tests/live-report-contract.sh
```

Expected: `ok — live report contract passed` and no fixture changes.

- [ ] **Step 4: Commit the characterization boundary**

```bash
git add tests/live-report-contract.sh tests/fixtures/report-rendering
git commit --signoff -m "test: freeze report rendering output"
```

---

### Task 2: Define the typed report schema

**Files:**
- Create: `plugin/skills/behavior-diff/scripts/reporting/__init__.py`
- Create: `plugin/skills/behavior-diff/scripts/reporting/schema.py`
- Create: `tests/report-schema-test.py`
- Modify: `tests/live-report-contract.sh`

- [ ] **Step 1: Write the failing schema test**

Create `tests/report-schema-test.py`. It must import the private package from the shipped scripts directory, construct a complete synthetic schema-v1 dictionary, load it with `ReportData.from_dict`, and compare the deterministic round trip:

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

scripts = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(scripts))

from reporting.schema import ReportData  # noqa: E402


def main():
    source = Path(sys.argv[1]) if len(sys.argv) == 2 else None
    if source:
        raw = json.loads(source.read_text())
    else:
        raw = {
            "schema_version": 1,
            "metadata": {
                "model": "synthetic/model",
                "mode": "review",
                "vocab": "generic",
                "trace_source": "captured",
                "target_file": "AGENTS.md",
                "before_label": "current file",
                "after_label": "your change applied",
            },
            "content": {
                "title": "Synthetic report",
                "subtitle": "Synthetic subtitle.",
                "observation": "",
                "scenario_heading": "Scenario",
                "scenario": "Compare two synthetic files.",
                "expected_heading": "Expected behavior",
                "expected": None,
                "diff_heading": "Diff of AGENTS.md — the only difference between the variants",
                "decision_heading": "Decision diff — top divergences",
                "decision_blurb": "Synthetic decision explanation.",
                "flow_heading": "Flow diff — where the variants diverge",
                "result_heading": "Result",
                "boundary": "Synthetic evidence only.",
            },
            "rule_diff": "--- before\n+++ after\n",
            "result": {"text": "No automatic verdict", "kind": "neutral"},
            "variants": {
                "before": {
                    "label": "Before",
                    "note": "current file",
                    "passed": 0,
                    "blocked": 0,
                    "valid": 1,
                    "total": 1,
                    "count_text": "1 valid trial(s)",
                    "count_suffix": " (blocked: 0)",
                    "count_emphasized": False,
                    "trials": [
                        {
                            "name": "before-1",
                            "verdict": "REVIEW",
                            "actions": "-",
                            "commands": ["read AGENTS.md"],
                            "final": "Before answer",
                            "outcome": None,
                        }
                    ],
                },
                "after": {
                    "label": "After",
                    "note": "your change applied",
                    "passed": 0,
                    "blocked": 0,
                    "valid": 1,
                    "total": 1,
                    "count_text": "1 valid trial(s)",
                    "count_suffix": " (blocked: 0)",
                    "count_emphasized": False,
                    "trials": [
                        {
                            "name": "after-1",
                            "verdict": "REVIEW",
                            "actions": "-",
                            "commands": ["read AGENTS.md", "run tests"],
                            "final": "After answer",
                            "outcome": None,
                        }
                    ],
                },
            },
            "command_flow": {
                "enabled": True,
                "same": False,
                "shared": ["Read files"],
                "before": {"prefix": [], "paths": [], "total": 1},
                "after": {
                    "prefix": ["Run tests"],
                    "paths": [],
                    "total": 1,
                },
            },
            "decisions": {
                "rows": [],
                "fork": None,
                "fork_note": "",
                "dropped": 0,
                "extractor": "",
                "before_count": 1,
                "after_count": 1,
            },
        }

    report = ReportData.from_dict(raw)
    assert report.schema_version == 1
    assert report.to_dict() == raw
    encoded = report.to_json()
    assert encoded == json.dumps(raw, indent=2, sort_keys=True) + "\n"

    bad = dict(raw, schema_version=2)
    try:
        ReportData.from_dict(bad)
    except ValueError as error:
        assert str(error) == "unsupported report-data schema version: 2"
    else:
        raise AssertionError("schema version 2 was accepted")


if __name__ == "__main__":
    main()
```

Call it from `tests/live-report-contract.sh` before the fixture runs:

```bash
python3 "$here/report-schema-test.py"
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
bash tests/live-report-contract.sh
```

Expected: nonzero with `ModuleNotFoundError: No module named 'reporting'`.

- [ ] **Step 3: Implement the immutable schema records**

Create an empty `reporting/__init__.py` and implement frozen dataclasses in `reporting/schema.py`:

```python
from typing import Dict, Optional, Tuple, Union

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class TrialData:
    name: str
    verdict: str
    actions: str
    commands: Tuple[str, ...]
    final: str
    outcome: Optional[str]


@dataclass(frozen=True)
class VariantData:
    label: str
    note: str
    passed: int
    blocked: int
    valid: int
    total: int
    count_text: str
    count_suffix: str
    count_emphasized: bool
    trials: Tuple[TrialData, ...]


@dataclass(frozen=True)
class VariantsData:
    before: VariantData
    after: VariantData


@dataclass(frozen=True)
class FlowPathData:
    steps: Tuple[str, ...]
    count: int


@dataclass(frozen=True)
class FlowBranchData:
    prefix: Tuple[str, ...]
    paths: Tuple[FlowPathData, ...]
    total: int


@dataclass(frozen=True)
class CommandFlowData:
    enabled: bool
    same: bool
    shared: Tuple[str, ...]
    before: FlowBranchData
    after: FlowBranchData


@dataclass(frozen=True)
class DecisionChoiceData:
    choice: str
    count: int


@dataclass(frozen=True)
class DecisionRowData:
    decision: str
    topic: str
    anchor: Union[int, str]
    diverges: bool
    note: str
    before: Tuple[DecisionChoiceData, ...]
    after: Tuple[DecisionChoiceData, ...]


@dataclass(frozen=True)
class DecisionData:
    rows: Tuple[DecisionRowData, ...]
    fork: Optional[int]
    fork_note: str
    dropped: int
    extractor: str
    before_count: int
    after_count: int


@dataclass(frozen=True)
class MetadataData:
    model: str
    mode: str
    vocab: str
    trace_source: str
    target_file: str
    before_label: str
    after_label: str


@dataclass(frozen=True)
class ContentData:
    title: str
    subtitle: str
    observation: str
    scenario_heading: str
    scenario: str
    expected_heading: str
    expected: Optional[str]
    diff_heading: str
    decision_heading: str
    decision_blurb: str
    flow_heading: str
    result_heading: str
    boundary: str


@dataclass(frozen=True)
class ResultData:
    text: str
    kind: str


@dataclass(frozen=True)
class ReportData:
    schema_version: int
    metadata: MetadataData
    content: ContentData
    rule_diff: str
    result: ResultData
    variants: VariantsData
    command_flow: CommandFlowData
    decisions: DecisionData
```

Implement `ReportData.from_dict`, `to_dict`, and `to_json`. Rebuild every nested dataclass explicitly in `from_dict`; do not store unvalidated nested dictionaries. Use `dataclasses.asdict`, then recursively convert tuples to lists so `to_dict` contains only JSON-shaped values; do not serialize and parse JSON to perform that conversion. Convert the `DecisionChoiceData.count` field from the persisted `decisions.json` key `n` while loading; `report-data.json` itself uses `count` consistently.

`to_json` must be exactly:

```python
def to_json(self):
    return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
```

- [ ] **Step 4: Run the focused tests and verify GREEN**

```bash
python3 tests/report-schema-test.py
bash tests/live-report-contract.sh
```

Expected: both exit `0`; the six visible output fixtures remain exact.

- [ ] **Step 5: Commit the schema**

```bash
git add \
  plugin/skills/behavior-diff/scripts/reporting/__init__.py \
  plugin/skills/behavior-diff/scripts/reporting/schema.py \
  tests/report-schema-test.py tests/live-report-contract.sh
git commit --signoff -m "feat: define internal report data schema"
```

---

### Task 3: Extract report loading and shared copy

**Files:**
- Create: `plugin/skills/behavior-diff/scripts/reporting/content.py`
- Create: `plugin/skills/behavior-diff/scripts/reporting/load.py`
- Modify: `plugin/skills/behavior-diff/scripts/render.py:16-448,918-923`
- Modify: `plugin/skills/behavior-diff/scripts/reporting/schema.py`
- Modify: `tests/live-report-contract.sh`
- Modify: `tests/report-schema-test.py`

- [ ] **Step 1: Add failing generated-data assertions**

After each current renderer invocation in `tests/live-report-contract.sh`, require the new artifact and validate it through the shipped schema:

```bash
for report_run in "$captured_run" "$self_run"; do
  [[ -f $report_run/report-data.json ]] ||
    fail "renderer did not write report-data.json: $report_run"
  python3 "$here/report-schema-test.py" "$report_run/report-data.json"
done
```

Add focused JSON checks:

```bash
[[ $(jq -r '.schema_version' "$captured_run/report-data.json") == 1 ]] ||
  fail 'captured report-data schema version changed'
[[ $(jq -r '.metadata.trace_source' "$captured_run/report-data.json") == captured ]] ||
  fail 'captured report-data lost its provenance'
[[ $(jq -r '.metadata.trace_source' "$self_run/report-data.json") == self-reported ]] ||
  fail 'self-reported report-data lost its provenance'
[[ $(jq -r '.variants.after.trials[0].commands[1]' \
  "$captured_run/report-data.json") == \
  'Test: bash behavior-diff/tests/live-report-contract.sh' ]] ||
  fail 'report-data changed trial command order'
```

- [ ] **Step 2: Run the test and verify RED**

```bash
bash tests/live-report-contract.sh
```

Expected: `FAIL: renderer did not write report-data.json`.

- [ ] **Step 3: Move shared copy into `content.py`**

Move the current default subtitle, boundary, result matrix, count wording, decision explanation, observation wording, and section headings behind these pure functions:

- `result_data(mode: str, self_reported: bool, before: VariantData, after: VariantData) -> ResultData` copies the current result matrix and single-run suffix from `render.py:250-271`.
- `count_data(mode: str, passed: int, valid: int, blocked: int) -> Tuple[str, str, bool]` returns plain main count text, the plain blocked-count suffix, and whether Markdown emphasizes only the main text. This keeps shared copy format-neutral while preserving the graded report's exact emphasis boundary.
- `decision_blurb(self_reported: bool, single_trial: bool) -> str` copies `DEC_BLURB` and `DEC_N1` from `render.py:315-364`.
- `observation(decisions: DecisionData) -> str` copies the fork observation from `render.py:438-447`.
- `build_content(config: Dict[str, object], target_file: str, scenario: str, result: ResultData, observation_text: str, decision_text: str) -> ContentData` applies current defaults and builds the shared headings and boundary.

The returned strings must be copied exactly from the current `render.py`. Do not edit punctuation, capitalization, spacing, or warnings.

- [ ] **Step 4: Move evidence loading and comparison into `load.py`**

Expose one public function: `load_report(run: Path, capsule: Path, model: str, config_path: Optional[Path]) -> ReportData`.

Move the current logic into private functions with explicit arguments:

- `_read_config(config_path)` reads JSON and applies the existing defaults.
- `_read_grades(run)` parses the required TSV rows without changing its strict split behavior.
- `_read_trial(run, name, grade)` reads ordered tools and the final result from canonical JSONL.
- `_classify(command, vocab)` contains the current demo, generic, and Spacedock buckets.
- `_trial_sequence(trial, mode, vocab)` adds the current optional outcome step.
- `_common_prefix(sequences)` and `_build_flow(before_trials, after_trials, mode, trace_source, vocab)` preserve the current flow algorithm and counts.
- `_read_rule_diff(run, capsule, target_file)` keeps target-file and `rule.md` fallback behavior.
- `_read_decisions(run, before_total, after_total, self_reported)` converts every valid decision choice from persisted key `n` to `DecisionChoiceData.count`.

Preserve these exact behaviors:

- invalid `trace_source` exits with `trace_source must be either "captured" or "self-reported"`;
- malformed trace lines are skipped;
- the last non-empty result remains the final answer;
- missing or malformed `decisions.json` produces an empty `DecisionData`;
- trial names retain lexical order;
- self-reported runs disable command flow;
- all current vocab classifiers and result outcomes remain;
- run and capsule may be different paths.

Construct every `ReportData` field only after all required inputs and derived facts are available. Set `schema_version=SCHEMA_VERSION`; do not use a partial constructor or default missing evidence.

- [ ] **Step 5: Use `ReportData` in `render.py` without moving format blocks yet**

At the top-level command path:

```python
report = load_report(run, capsule, model, config_path)
```

Temporarily unpack the exact fields needed by the existing Markdown and HTML blocks. This bridge is private to `render.py` and must be deleted in Task 6. Do not add compatibility methods or aliases to `ReportData`.

After both current format strings are successfully built, add `report-data.json` to the write phase:

```python
report_json = report.to_json()
# Build Markdown and both HTML strings first.
(run / "report-data.json").write_text(report_json)
```

Do not change the three existing report strings or stdout.

- [ ] **Step 6: Verify the data boundary and exact visible output**

```bash
python3 tests/report-schema-test.py
bash tests/live-report-contract.sh
```

Expected: `report-data.json` checks pass, and all six visible fixtures remain byte-for-byte exact.

- [ ] **Step 7: Commit loading and shared content**

```bash
git add \
  plugin/skills/behavior-diff/scripts/reporting/content.py \
  plugin/skills/behavior-diff/scripts/reporting/load.py \
  plugin/skills/behavior-diff/scripts/render.py \
  tests/report-schema-test.py tests/live-report-contract.sh
git commit --signoff -m "refactor: separate report data assembly"
```

---

### Task 4: Extract the Markdown renderer

**Files:**
- Create: `plugin/skills/behavior-diff/scripts/reporting/render_markdown.py`
- Modify: `plugin/skills/behavior-diff/scripts/render.py:449-542`
- Modify: `tests/report-schema-test.py`

- [ ] **Step 1: Add a failing pure-renderer check**

Extend `tests/report-schema-test.py` when a `report-data.json` path is supplied:

```python
from reporting.render_markdown import render_markdown

expected_markdown = source.with_name("report.md").read_text()
assert render_markdown(report) == expected_markdown
```

- [ ] **Step 2: Run the test and verify RED**

```bash
bash tests/live-report-contract.sh
```

Expected: `ModuleNotFoundError: No module named 'reporting.render_markdown'`.

- [ ] **Step 3: Move Markdown assembly behind one pure function**

Create:

```python
def render_markdown(report: ReportData) -> str:
    parts = []
    # Existing Markdown assembly, with ReportData attributes instead of globals.
    return "\n".join(parts)
```

Move all Markdown-only behavior into this module:

- Markdown headings and section order;
- diff fence;
- decision lists;
- `md_branch` flow formatting;
- conditional flow `<details>`;
- trial `<details>` blocks;
- no `$ ` prefix for captured commands.

Keep the current strings and blank lines exactly. The function must not access the filesystem or mutate `ReportData`.

Replace the old Markdown block in `render.py` with:

```python
markdown = render_markdown(report)
```

Do not write it until all remaining format strings have been built.

- [ ] **Step 4: Verify the pure function and golden output**

```bash
python3 tests/report-schema-test.py
bash tests/live-report-contract.sh
```

Expected: the pure function equals each generated `report.md`, and both Markdown goldens remain exact.

- [ ] **Step 5: Commit the Markdown renderer**

```bash
git add \
  plugin/skills/behavior-diff/scripts/reporting/render_markdown.py \
  plugin/skills/behavior-diff/scripts/render.py \
  tests/report-schema-test.py
git commit --signoff -m "refactor: isolate Markdown report rendering"
```

---

### Task 5: Extract the HTML renderer and CSS

**Files:**
- Create: `plugin/skills/behavior-diff/scripts/reporting/render_html.py`
- Create: `plugin/skills/behavior-diff/scripts/reporting/report.css`
- Modify: `plugin/skills/behavior-diff/scripts/render.py:544-916`
- Modify: `tests/report-schema-test.py`

- [ ] **Step 1: Add failing pure HTML checks**

Extend the path-backed branch in `tests/report-schema-test.py`:

```python
from reporting.render_html import render_artifact, render_document

css_path = scripts / "reporting/report.css"
css = css_path.read_text()
artifact = render_artifact(report, css)
assert artifact == source.with_name("report-artifact.html").read_text()
assert render_document(artifact) == source.with_name("report.html").read_text()
```

- [ ] **Step 2: Run the test and verify RED**

```bash
bash tests/live-report-contract.sh
```

Expected: `ModuleNotFoundError: No module named 'reporting.render_html'`.

- [ ] **Step 3: Extract the CSS source with one explicit result-color token**

Copy the generated CSS text between the current `<style>` newline and `</style>` into `reporting/report.css`. The file starts with `:root {`, uses normal single CSS braces, and ends with one newline after the final `}`.

Replace only the current dynamic result background value with:

```css
.result { background:__RESULT_BG__; color:#fff; border-radius:8px;
```

Keep every other declaration, space, and line break unchanged. Keep the Google Fonts `<link>` in the HTML renderer.

- [ ] **Step 4: Move HTML assembly behind pure functions**

Expose `render_artifact(report: ReportData, css: str) -> str` and `render_document(artifact: str) -> str`.

Resolve the one CSS token inside the HTML renderer:

```python
RESULT_BACKGROUNDS = {
    "good": "var(--pass)",
    "bad": "var(--fail)",
    "neutral": "var(--accent)",
}


def _resolve_css(css, result_kind):
    if css.count("__RESULT_BG__") != 1:
        raise ValueError("report.css must contain __RESULT_BG__ exactly once")
    return css.replace("__RESULT_BG__", RESULT_BACKGROUNDS[result_kind])


def render_document(artifact):
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "</head><body>" + artifact + "</body></html>"
    )
```

`render_artifact` must call `_resolve_css` and insert the result as `<style>\n{resolved_css}</style>\n`. This reproduces the current generated bytes while keeping the source CSS editable.

Move `card`, `lane`, `branch_html`, `dec_choices`, `dec_label`, decision HTML, flow HTML, trial columns, escaping, footer, and body assembly into `render_html.py`. Keep captured `$ ` prefixes, self-reported labels, open review-mode answers, HTML escaping, section order, and all source whitespace exact.

The functions must not read or write files. Pass CSS explicitly.

Replace the old HTML block in `render.py` with:

```python
css = (Path(__file__).parent / "reporting/report.css").read_text()
artifact_html = render_artifact(report, css)
html_document = render_document(artifact_html)
```

- [ ] **Step 5: Verify both HTML outputs exactly**

```bash
python3 tests/report-schema-test.py
bash tests/live-report-contract.sh
```

Expected: pure renderer strings equal the generated files; captured and self-reported HTML and artifact goldens remain exact.

- [ ] **Step 6: Commit the HTML renderer and style source**

```bash
git add \
  plugin/skills/behavior-diff/scripts/reporting/render_html.py \
  plugin/skills/behavior-diff/scripts/reporting/report.css \
  plugin/skills/behavior-diff/scripts/render.py \
  tests/report-schema-test.py
git commit --signoff -m "refactor: isolate HTML report rendering"
```

---

### Task 6: Reduce `render.py` to orchestration and writes

**Files:**
- Modify: `plugin/skills/behavior-diff/scripts/render.py`
- Modify: `.github/workflows/ci.yml:76-81`
- Modify: `CODING_GUIDELINES.md:155-157`
- Modify: `tests/report-schema-test.py`

- [ ] **Step 1: Add a failing import-safety check**

In `tests/report-schema-test.py`, load `render.py` without command arguments inside a fresh temporary directory:

```python
import importlib.util
import io
import os
from contextlib import redirect_stderr, redirect_stdout
from tempfile import TemporaryDirectory

with TemporaryDirectory() as tmp:
    stdout = io.StringIO()
    stderr = io.StringIO()
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp)
        spec = importlib.util.spec_from_file_location(
            "behavior_diff_render", scripts / "render.py"
        )
        module = importlib.util.module_from_spec(spec)
        with redirect_stdout(stdout), redirect_stderr(stderr):
            spec.loader.exec_module(module)
    finally:
        os.chdir(old_cwd)
    assert list(Path(tmp).iterdir()) == []
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""
    assert callable(module.main)
```

- [ ] **Step 2: Run the test and verify RED**

```bash
python3 tests/report-schema-test.py
```

Expected: the current top-level renderer exits or reads `sys.argv`; `main` is not available.

- [ ] **Step 3: Implement the thin import-safe facade**

`render.py` must contain only imports, argument parsing, orchestration, writes, stdout, and `main()`:

```python
def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    run = Path(args[0]).resolve()
    capsule = Path(args[1]).resolve()
    model = args[2]
    config_path = Path(args[3]) if len(args) > 3 else None

    report = load_report(run, capsule, model, config_path)
    report_json = report.to_json()
    markdown = render_markdown(report)
    css = (Path(__file__).parent / "reporting/report.css").read_text()
    artifact_html = render_artifact(report, css)
    html_document = render_document(artifact_html)

    (run / "report-data.json").write_text(report_json)
    (run / "report.md").write_text(markdown)
    (run / "report-artifact.html").write_text(artifact_html)
    (run / "report.html").write_text(html_document)

    before = report.variants.before
    after = report.variants.after
    print(
        f"mode {report.metadata.mode} · BEFORE pass {before.passed}/{before.valid} · "
        f"AFTER pass {after.passed}/{after.valid} → {report.result.text}"
    )
    print(f"report: {run / 'report.md'}")
    print(f"page:   {run / 'report.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Keep the current natural Python errors for missing positional arguments and unreadable required files. Do not add a new CLI parser or change diagnostics in this refactor.

Delete all temporary field-unpacking code and every moved helper from `render.py`. There must be one implementation of each loader, copy rule, Markdown section, HTML component, and CSS declaration.

- [ ] **Step 4: Expand deterministic Python compilation**

In `.github/workflows/ci.yml` and `CODING_GUIDELINES.md`, keep the existing files and add:

```text
plugin/skills/behavior-diff/scripts/reporting/*.py
```

The CI command becomes:

```bash
python3 -m py_compile \
  plugin/skills/behavior-diff/scripts/decisions.py \
  plugin/skills/behavior-diff/scripts/render.py \
  plugin/skills/behavior-diff/scripts/reporting/*.py
```

- [ ] **Step 5: Verify the facade and focused report contracts**

```bash
python3 tests/report-schema-test.py
bash tests/live-report-contract.sh
python3 -m py_compile \
  plugin/skills/behavior-diff/scripts/decisions.py \
  plugin/skills/behavior-diff/scripts/render.py \
  plugin/skills/behavior-diff/scripts/reporting/*.py
```

Expected: all commands exit `0`; all visible output remains exact; import produces no files or stdout.

- [ ] **Step 6: Commit the final cutover**

```bash
git add \
  plugin/skills/behavior-diff/scripts/render.py \
  .github/workflows/ci.yml CODING_GUIDELINES.md \
  tests/report-schema-test.py
git commit --signoff -m "refactor: make report rendering import safe"
```

---

### Task 7: Run complete verification and inspect the real surfaces

**Files:**
- Verify only; no planned production changes.

- [ ] **Step 1: Run formatting checks**

```bash
docker run --rm -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -d -i 2 -ci .
uvx ruff@0.16.5 format --check --diff .
```

Expected: no Bash diff; Ruff reports every Python file already formatted.

- [ ] **Step 2: Run syntax and static checks**

```bash
bash -n \
  .github/scripts/*.sh \
  bin/behavior-diff \
  plugin/scripts/*.sh \
  plugin/skills/behavior-diff/scripts/*.sh \
  tests/*.sh
shellcheck \
  .github/scripts/*.sh \
  bin/behavior-diff \
  plugin/scripts/*.sh \
  plugin/skills/behavior-diff/scripts/*.sh \
  tests/*.sh
python3 -m py_compile \
  plugin/skills/behavior-diff/scripts/decisions.py \
  plugin/skills/behavior-diff/scripts/render.py \
  plugin/skills/behavior-diff/scripts/reporting/*.py
```

Expected: every command exits `0` with no diagnostics.

- [ ] **Step 3: Run the complete deterministic suite**

```bash
bash tests/hooks-test.sh
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
bash tests/live-report-contract.sh
bash tests/release-workflow-test.sh
git diff --check
```

Expected: all four repository checks pass and `git diff --check` has no output.

- [ ] **Step 4: Verify exact fixture stability independently**

Render the fixed captured and self-reported inputs through `tests/live-report-contract.sh`, then confirm the six comparisons ran without fixture-update mode. Run:

```bash
bash tests/live-report-contract.sh
```

Expected: the test passes without changing any file under `tests/fixtures/report-rendering/`.

- [ ] **Step 5: Inspect both output formats from one synthetic run**

Open `tests/fixtures/report-rendering/captured/report.html` in the browser and verify:

```text
title and subtitle render
scenario and instruction diff render
decision diff and command-derived flow render
before and after columns render
commands and final answers render in order
result and footer render
page has the same current typography, colors, spacing, and responsive layout
```

Read `tests/fixtures/report-rendering/captured/report.md` and verify the same evidence appears in the current section order. This is a visual/behavioral check, not a live model call.

- [ ] **Step 6: Confirm repository scope**

Verify:

```text
render.py is a thin facade
reporting modules have one responsibility each
report-data.json is marked internal and versioned
no duplicate old renderer blocks remain
behavior-diff.sh and both skills are unchanged
no real run, transcript, report, credential, or customer data is tracked
all commits contain DCO sign-off
```

- [ ] **Step 7: Request independent review before a PR**

Give one read-only reviewer the complete branch diff and require `REVIEWER_GUIDELINES.md`. Ask it to check exact-output evidence, schema boundaries, import safety, error/fallback preservation, CSS inlining, self-reported provenance, duplicate code, and unauthorized scope. Do not create or update a PR without an `APPROVE` verdict.
