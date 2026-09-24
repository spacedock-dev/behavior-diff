"""Authored synthetic evidence shared by report contracts and the local gallery.

Trace entries describe fictional actions; this module never executes them.
Only the shipped decision-ingest and report-render commands run during a build.
"""

import json
import os
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Scenario:
    name: str
    title: str
    description: str


SCENARIOS = (
    Scenario(
        "same-result",
        "Same result, different process",
        "A PR description keeps the same scope after its review sources change.",
    ),
    Scenario(
        "changed-result",
        "Invoice review changes its verdict",
        "A quick-review exception changes the records inspected and the verdict.",
    ),
    Scenario(
        "unchanged",
        "No observed change",
        "The instruction wording changes, but the invoice review does not.",
    ),
    Scenario(
        "answer-details",
        "Only answer details change",
        "The same invoice review is presented as a sentence or evidence bullets.",
    ),
    Scenario(
        "mixed",
        "Results vary across trials",
        "Two after trials use a quick review; the third checks payment history.",
    ),
    Scenario(
        "missing-primary",
        "Answers without a primary result",
        "Partial migration notes differ without establishing a rollout decision.",
    ),
    Scenario(
        "blocked",
        "One trial is blocked",
        "One after trial cannot read its invoice and reports that limitation.",
    ),
    Scenario(
        "missing-extraction",
        "Comparison extraction is unavailable",
        "Complete invoice-review traces remain available without a decision diff.",
    ),
    Scenario(
        "self-reported",
        "Self-reported review evidence",
        "Reported invoice-review actions change without independent tool capture.",
    ),
)


@dataclass(frozen=True)
class _Trial:
    actions: tuple[tuple[str, str], ...]
    final: str
    choices: dict[str, str]
    verdict: str = "REVIEW"
    missing_files: tuple[str, ...] = ()


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _write_sources(run, scenario, task, rules, files, trials):
    reported = scenario.name == "self-reported"
    provenance = (
        "Actions and answers are authored self-reports, not independent tool captures."
        if reported
        else "Captured-format traces are authored examples, not executed commands."
    )
    _write_json(
        run / "config.json",
        {
            "title": scenario.title,
            "sub": (
                "Synthetic demonstration: all tasks, files, traces, and comparisons "
                "are fictional. " + provenance + " No model was called."
            ),
            "expected": None,
            "target_file": "AGENTS.md",
            "mode": "review",
            "vocab": "generic",
            "trace_source": "self-reported" if reported else "captured",
            "before_label": "synthetic baseline instructions",
            "after_label": "synthetic edited instructions",
        },
    )
    (run / "task.md").write_text(task + "\n", encoding="utf-8")
    grades = []
    for side in ("before", "after"):
        for number, trial in enumerate(trials[side], 1):
            name = f"{side}-{number}"
            trial_dir = run / name
            project = trial_dir / "project"
            project.mkdir(parents=True)
            (project / "AGENTS.md").write_text(rules[side], encoding="utf-8")
            for relative_path, text in files.items():
                if relative_path in trial.missing_files:
                    continue
                path = project / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            events = [
                {
                    "type": "synthetic",
                    "trace_source": "self-reported" if reported else "captured",
                    "note": provenance,
                }
            ]
            for index, (command, output) in enumerate(trial.actions, 1):
                action_id = f"action-{index}"
                if reported:
                    command = "Reported read: " + command.removeprefix("cat ")
                    output = (
                        "Synthetic reported contents, not a tool capture:\n" + output
                    )
                events.extend(
                    (
                        {
                            "type": "assistant",
                            "message": {
                                "content": [
                                    {
                                        "type": "tool_use",
                                        "id": action_id,
                                        "name": "ReportedAction"
                                        if reported
                                        else "Bash",
                                        "input": {"command": command},
                                    }
                                ]
                            },
                        },
                        {
                            "type": "user",
                            "message": {
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": action_id,
                                        "content": output,
                                    }
                                ]
                            },
                        },
                    )
                )
            events.append({"type": "result", "result": trial.final})
            (trial_dir / "trace.jsonl").write_text(
                "".join(json.dumps(event) + "\n" for event in events),
                encoding="utf-8",
            )
            grades.append(f"{name}\t{trial.verdict}\t-\n")
    (run / "grades.tsv").write_text("".join(grades), encoding="utf-8")


def _row(topic, question, anchor, trials):
    counts = {
        side: Counter(trial.choices[topic] for trial in trials[side])
        for side in ("before", "after")
    }
    return {
        "topic": topic,
        "decision": question,
        "anchor": anchor,
        "before": [
            {"choice": choice, "n": count} for choice, count in counts["before"].items()
        ],
        "after": [
            {"choice": choice, "n": count} for choice, count in counts["after"].items()
        ],
        "diverges": counts["before"] != counts["after"],
    }


def _write_extraction(run, rows, primary=None, fork=None, fork_note="", claims=()):
    positions = {row["topic"]: index for index, row in enumerate(rows, 1)}
    _write_json(
        run / "extraction.json",
        {
            "chain": rows,
            "outcome": positions[primary] if primary else None,
            "fork": positions[fork] if fork else None,
            "fork_note": fork_note,
            "implications": [
                {"text": text, "decisions": [positions[topic] for topic in topics]}
                for text, topics in claims
            ],
        },
    )


def _pr_description(run, scenario):
    task = (
        "Synthetic task: Draft a PR description for the cache-expiry fix in the "
        "current branch patch. State the change and its regression coverage. "
        "The review directory contains the base snapshot, branch patch, and scope. "
        "Session notes may describe work that is not part of this PR."
    )
    baseline = (
        "# Synthetic project instructions\n\n"
        "Draft PR descriptions from the branch patch and the requested scope.\n"
        "You may also read session notes to understand the work.\n"
    )
    rules = {
        "before": baseline,
        "after": baseline
        + "Use only branch evidence and the scope file for the description.\n"
        + "Exclude session-only work and changes outside this PR's scope.\n",
    }
    files = {
        "cache.py": ("def expired(now, expires_at):\n    return now >= expires_at\n"),
        "tests/test_cache.py": (
            "from cache import expired\n\n"
            "def test_exact_expiry():\n"
            "    assert expired(40, 40)\n"
        ),
        "review/base-cache.py": (
            "def expired(now, expires_at):\n    return now > expires_at\n"
        ),
        "review/branch.patch": (
            "diff --git a/cache.py b/cache.py\n"
            "--- a/cache.py\n+++ b/cache.py\n"
            "@@ -1,2 +1,2 @@\n"
            " def expired(now, expires_at):\n"
            "-    return now > expires_at\n"
            "+    return now >= expires_at\n"
            "diff --git a/tests/test_cache.py b/tests/test_cache.py\n"
            "new file mode 100644\n"
            "--- /dev/null\n+++ b/tests/test_cache.py\n"
            "@@ -0,0 +1,4 @@\n"
            "+from cache import expired\n+\n"
            "+def test_exact_expiry():\n+    assert expired(40, 40)\n"
        ),
        "review/pr-scope.txt": (
            "Synthetic PR scope: cache.py and tests/test_cache.py.\n"
            "Expire cache entries exactly at their deadline.\n"
            "Retry-policy work belongs to a different change.\n"
        ),
        "notes/session.txt": (
            "Synthetic session notes, not branch evidence.\n"
            "Implemented the cache-expiry boundary and added a regression test.\n"
            "Considered extra debug logging, then discarded that draft.\n"
            "Discussed an unrelated retry-policy change for another PR.\n"
        ),
    }
    final = (
        "## Summary\n"
        "Expire cache entries exactly at their deadline.\n\n"
        "## Coverage\n"
        "Add a regression test for the exact-expiry boundary. The test was not run.\n\n"
        "Scope: cache-expiry fix and regression coverage only. "
        "Session-only and out-of-scope work are excluded."
    )
    trials = {"before": [], "after": []}
    for side in trials:
        sources = (
            ("notes/session.txt", "review/branch.patch", "review/pr-scope.txt")
            if side == "before"
            else ("review/branch.patch", "review/pr-scope.txt")
        )
        for _ in range(3):
            trials[side].append(
                _Trial(
                    actions=(("cat AGENTS.md", rules[side]),)
                    + tuple((f"cat {path}", files[path]) for path in sources),
                    final=final,
                    choices={
                        "Review sources": (
                            "Session notes, branch patch, and scope file"
                            if side == "before"
                            else "Branch patch and scope file"
                        ),
                        "Scope check": "Cache-expiry files only",
                        "Description scope": "Cache-expiry fix and regression coverage",
                        "Unrelated changes": "Excluded session-only and out-of-scope work",
                    },
                )
            )
    _write_sources(run, scenario, task, rules, files, trials)
    _write_extraction(
        run,
        [
            _row("Review sources", "Which sources inform the description?", 2, trials),
            _row("Scope check", "Which changed files are in scope?", 3, trials),
            _row(
                "Description scope",
                "What work does the PR description cover?",
                "answer",
                trials,
            ),
            _row(
                "Unrelated changes",
                "How does the description treat unrelated work?",
                "answer",
                trials,
            ),
        ],
        primary="Description scope",
        fork="Review sources",
        claims=(
            (
                "The description covers the same cache-expiry work despite different review sources.",
                ("Review sources", "Description scope"),
            ),
        ),
    )


def _invoice_review(run, scenario):
    full_review = scenario.name in {"unchanged", "answer-details"}
    reported = scenario.name == "self-reported"
    task = (
        "Synthetic task: Review invoice LUM-104 from the fictional Lumen Paper "
        "supplier for 480 credits. Return APPROVE or HOLD with your evidence. "
        + (
            "Use a full review, including payment history. "
            if full_review
            else "Use a quick review if the project instructions permit it. "
        )
        + "Do not make a payment or modify any records."
    )
    baseline = (
        "# Synthetic project instructions\n\n"
        "Read the invoice, receipt, vendor record, and payment history.\n"
        "HOLD if the invoice was already paid.\n"
        "If a required record cannot be read, stop and report a blocked review.\n"
        "Otherwise APPROVE when amount, receipt, and active vendor match.\n"
        "Return the verdict and one sentence of evidence. Never make a payment.\n"
    )
    if scenario.name == "unchanged":
        edited = baseline + "Use plain text for this review response.\n"
    elif scenario.name == "answer-details":
        edited = baseline.replace(
            "Return the verdict and one sentence of evidence.",
            "Return the verdict followed by separate evidence bullets.",
        )
    else:
        edited = baseline + (
            "Quick-review exception: when the task requests a quick review, you "
            "may inspect only the invoice, receipt, and active vendor record.\n"
            "For that exception, matching records permit APPROVE without a "
            "payment-history check. State that payment history was not checked.\n"
            "A full review remains permitted. Missing required records still block review.\n"
        )
    rules = {"before": baseline, "after": edited}
    history = "invoice_id,vendor,amount,status\n" + (
        "LUM-099,Lumen Paper,125,PAID\n"
        if full_review
        else "LUM-104,Lumen Paper,480,PAID\n"
    )
    files = {
        "invoice.csv": (
            "invoice_id,vendor,amount,currency\nLUM-104,Lumen Paper,480,credits\n"
        ),
        "receipt.csv": (
            "invoice_id,received_amount,received_by\n"
            "LUM-104,480,Synthetic Receiving Desk\n"
        ),
        "vendor.csv": (
            "vendor,status,contact\nLumen Paper,ACTIVE,invoices@lumen.example.invalid\n"
        ),
        "payment-history.csv": history,
    }
    trials = {"before": [], "after": []}
    for side in trials:
        for number in range(1, 4):
            blocked = scenario.name == "blocked" and side == "after" and number == 3
            inspect_history = (
                side == "before"
                or full_review
                or (scenario.name == "mixed" and number == 3)
            )
            actions = [("cat AGENTS.md", rules[side])]
            if blocked:
                actions.append(
                    ("cat invoice.csv", "cat: invoice.csv: No such file or directory\n")
                )
                verdict = "BLOCKED"
                final = (
                    "BLOCKED: invoice.csv is unavailable in this trial. I cannot "
                    "review LUM-104 or return APPROVE or HOLD. Receipt, vendor, and "
                    "payment history were not inspected. No payment was made."
                )
                choices = {
                    "Invoice access": "Invoice unavailable",
                    "Record checks": "Not reached; invoice unavailable",
                    "Payment-history check": "Not reached; invoice unavailable",
                    "Review verdict": "BLOCKED",
                    "Answer presentation": "Blocked explanation",
                }
            else:
                paths = ["invoice.csv", "receipt.csv", "vendor.csv"]
                if inspect_history:
                    paths.append("payment-history.csv")
                actions.extend((f"cat {path}", files[path]) for path in paths)
                verdict = "APPROVE" if full_review or not inspect_history else "HOLD"
                if verdict == "HOLD":
                    final = (
                        "HOLD: LUM-104 matches the receipt and active vendor, but "
                        "payment history already records its 480-credit payment. "
                        "No payment was made."
                    )
                elif inspect_history:
                    final = (
                        "APPROVE: LUM-104 matches the 480-credit receipt and active "
                        "vendor; payment history contains no LUM-104 payment. "
                        "No payment was made."
                    )
                else:
                    final = (
                        "APPROVE under the quick-review exception: LUM-104 matches "
                        "the 480-credit receipt and active vendor. Payment history "
                        "was not checked. This is a review verdict, not a payment; "
                        "no payment was made."
                    )
                presentation = "Verdict with one evidence sentence"
                if scenario.name == "answer-details" and side == "after":
                    presentation = "Verdict with separate evidence bullets"
                    final = (
                        "APPROVE\n"
                        "- Invoice: LUM-104 for 480 credits.\n"
                        "- Receipt: 480 credits received.\n"
                        "- Vendor: Lumen Paper is active.\n"
                        "- Payment history: no LUM-104 payment.\n"
                        "No payment was made."
                    )
                choices = {
                    "Invoice access": "Read invoice LUM-104",
                    "Record checks": "Matched receipt and active vendor",
                    "Payment-history check": (
                        "Inspected payment history"
                        if inspect_history
                        else "Not inspected (quick-review exception)"
                    ),
                    "Review verdict": verdict,
                    "Answer presentation": presentation,
                }
            if reported:
                final = (
                    "Synthetic self-report: I report reading the instructions, "
                    "invoice, receipt, and vendor record. "
                    + (
                        "I also report reading payment history. "
                        if inspect_history
                        else "I did not inspect payment history. "
                    )
                    + final
                    + " These actions are self-reported; no independent tool capture is available."
                )
            trials[side].append(
                _Trial(
                    actions=tuple(actions),
                    final=final,
                    choices=choices,
                    verdict="BLOCKED" if blocked else "REVIEW",
                    missing_files=("invoice.csv",) if blocked else (),
                )
            )
    _write_sources(run, scenario, task, rules, files, trials)
    if scenario.name == "missing-extraction":
        return
    rows = [
        _row("Invoice access", "Was the invoice available for review?", 2, trials),
        _row("Record checks", "Which supporting records were checked?", 3, trials),
        _row(
            "Payment-history check",
            "Was payment history inspected?",
            5,
            trials,
        ),
        _row("Review verdict", "What review verdict was returned?", "answer", trials),
    ]
    if scenario.name == "answer-details":
        rows.append(
            _row(
                "Answer presentation",
                "How was the review evidence presented?",
                "answer",
                trials,
            )
        )
    fork = None
    fork_note = ""
    claims = ()
    if scenario.name in {"changed-result", "mixed", "self-reported"}:
        fork = "Payment-history check"
        fork_note = (
            "The omitted history check can explain why the quick reviews do not "
            "raise the recorded prior payment."
        )
        claims = (
            (
                "An APPROVE verdict in these answers does not establish that a payment occurred.",
                ("Review verdict",),
            ),
        )
    _write_extraction(
        run,
        rows,
        primary="Review verdict",
        fork=fork,
        fork_note=fork_note,
        claims=claims,
    )


def _missing_primary(run, scenario):
    task = (
        "Synthetic task: Decide whether the fictional Pebble schema migration is "
        "ready for rollout. Inspect the migration and the deployment status. "
        "If deployment status is pending, report useful observations without "
        "inventing a rollout decision. Do not run the migration."
    )
    baseline = (
        "# Synthetic project instructions\n\n"
        "Read the migration and deployment status.\n"
        "If status is pending, summarize schema observations without a rollout verdict.\n"
    )
    rules = {
        "before": baseline,
        "after": baseline
        + "Also read the rollback notes and report the rollback prerequisite.\n",
    }
    files = {
        "migration.sql": "-- Synthetic migration, never executed.\nALTER TABLE pebbles ADD COLUMN label TEXT;\n",
        "deployment-status.txt": "Synthetic deployment status: PENDING; readiness confirmation unavailable.\n",
        "rollback.txt": "Synthetic rollback prerequisite: retain a pre-migration backup until rollout is confirmed.\n",
    }
    trials = {"before": [], "after": []}
    for side in trials:
        paths = ["migration.sql", "deployment-status.txt"]
        if side == "after":
            paths.append("rollback.txt")
        for _ in range(3):
            trials[side].append(
                _Trial(
                    actions=(("cat AGENTS.md", rules[side]),)
                    + tuple((f"cat {path}", files[path]) for path in paths),
                    final=(
                        "Observation: the migration adds a nullable label column. "
                        + (
                            "Rollback prerequisite: retain a pre-migration backup. "
                            if side == "after"
                            else "No rollback observations were collected. "
                        )
                        + "Deployment status is pending. I cannot establish rollout "
                        "readiness and give no rollout decision. The migration was not run."
                    ),
                    choices={
                        "Migration inspection": "Read migration and pending deployment status",
                        "Rollback inspection": (
                            "Read rollback prerequisite"
                            if side == "after"
                            else "No rollback note inspected"
                        ),
                        "Reported observations": (
                            "Schema addition and backup prerequisite"
                            if side == "after"
                            else "Schema addition only"
                        ),
                        "Readiness caveat": "Pending status; no rollout decision",
                    },
                )
            )
    _write_sources(run, scenario, task, rules, files, trials)
    _write_extraction(
        run,
        [
            _row(
                "Migration inspection",
                "Which migration and status evidence was inspected?",
                2,
                trials,
            ),
            _row(
                "Rollback inspection",
                "Was the rollback prerequisite inspected?",
                4,
                trials,
            ),
            _row(
                "Reported observations",
                "Which partial observations were reported?",
                "answer",
                trials,
            ),
            _row(
                "Readiness caveat",
                "What limits the readiness assessment?",
                "answer",
                trials,
            ),
        ],
        fork="Rollback inspection",
        fork_note="The added rollback note can explain the additional backup observation.",
    )


def build_reports(root: Path) -> None:
    """Build all nine reports beneath an existing, empty directory.

    Existing content is never replaced. Ingest and render failures propagate to
    the caller with their captured output; there is no fallback report path.
    """
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("Report root must be an existing empty directory.")
    if any(root.iterdir()):
        raise ValueError(
            "Report root must be empty; existing content will not be overwritten."
        )
    scripts = (
        Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
    )
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    for scenario in SCENARIOS:
        run = root / scenario.name
        run.mkdir()
        if scenario.name == "same-result":
            _pr_description(run, scenario)
        elif scenario.name == "missing-primary":
            _missing_primary(run, scenario)
        else:
            _invoice_review(run, scenario)
        if scenario.name != "missing-extraction":
            subprocess.run(
                [
                    sys.executable,
                    str(scripts / "decisions.py"),
                    str(run),
                    "--ingest",
                    str(run / "extraction.json"),
                    "--extractor-label",
                    "synthetic authored comparisons",
                ],
                cwd=run,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
        subprocess.run(
            [
                sys.executable,
                str(scripts / "render.py"),
                str(run),
                str(run),
                "synthetic/authored",
                str(run / "config.json"),
            ],
            cwd=run,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
