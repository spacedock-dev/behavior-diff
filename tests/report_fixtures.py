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
        "mixed-primary",
        "A mixed result matters more than a consistent reading-order change",
        "Two before reviews flag a prior payment; no after review does.",
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
    Scenario(
        "flow-changed",
        "Every review adds a test run",
        "All after trials run the availability tests; the review verdict stays the same.",
    ),
    Scenario(
        "flow-mixed",
        "Some reviews add an optional test",
        "Two after trials run optional availability tests; all review verdicts agree.",
    ),
    Scenario(
        "intent-flip",
        "A consistent tool switch amid mixed results",
        "The query interface changes in every trial while input and result choices vary.",
    ),
    Scenario(
        "intent-unchanged",
        "Targeted review findings stay the same",
        "Both instruction versions flag the same two security mistakes.",
    ),
    Scenario(
        "planned-actions",
        "A different next step is proposed",
        "The answers propose a repair instead of another review; neither is executed.",
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


def _write_extraction(
    run,
    rows,
    primary=None,
    fork=None,
    fork_note="",
    claims=(),
    summary=None,
    intent=None,
):
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
            "summary": summary,
            "intent": intent,
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
    mixed_primary = scenario.name == "mixed-primary"
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
    if mixed_primary:
        rules["before"] = edited
        rules["after"] = edited + (
            "Prefer the quick review; read the vendor record before the receipt.\n"
        )
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
                (side == "before" and not (mixed_primary and number == 3))
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
                if mixed_primary and side == "after":
                    paths = ["invoice.csv", "vendor.csv", "receipt.csv"]
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
                if mixed_primary:
                    choices["Record checks"] = (
                        "Matched receipt then active vendor"
                        if side == "before"
                        else "Matched active vendor then receipt"
                    )
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
    if scenario.name in {"changed-result", "mixed", "mixed-primary", "self-reported"}:
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
    summary = None
    if scenario.name in {"changed-result", "mixed", "mixed-primary", "self-reported"}:
        summary = {
            "decision": 4,
            "headline": "The review no longer always holds an already-paid invoice.",
            "scenario": "An agent reviews an invoice without making a payment.",
            "evidence_kind": "answers",
            "before": {
                "icon": "stop",
                "choices": [
                    {
                        "choice": branch["choice"],
                        "label": "Hold the invoice"
                        if branch["choice"] == "HOLD"
                        else "Approve the invoice",
                        "detail": "The answer flags the payment already on record."
                        if branch["choice"] == "HOLD"
                        else "This answer approves without checking payment history.",
                    }
                    for branch in rows[3]["before"]
                ],
            },
            "after": {
                "icon": "report",
                "choices": [
                    {
                        "choice": branch["choice"],
                        "label": "Approve the invoice"
                        if branch["choice"] == "APPROVE"
                        else "Hold the invoice",
                        "detail": "The answer permits approval without checking payment history."
                        if branch["choice"] == "APPROVE"
                        else "This answer still flags the earlier payment.",
                    }
                    for branch in rows[3]["after"]
                ],
            },
            "why": {
                "text": "Some answers no longer flag the earlier payment.",
                "decisions": [3, 4],
            },
            "caution": {
                "text": "An approval answer does not mean a payment occurred.",
                "decisions": [4],
            },
        }
        if mixed_primary:
            summary["headline"] = "After the edit, no review flags the prior payment."
    _write_extraction(
        run,
        rows,
        primary="Review verdict",
        fork=fork,
        fork_note=fork_note,
        claims=claims,
        summary=summary,
        intent={
            "text": (
                "Prefer quick review and check the vendor before the receipt."
                if mixed_primary
                else "Allow a quick review without checking payment history."
            ),
            "edit_hunks": [1],
        }
        if not full_review
        else None,
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


def _availability_review(run, scenario):
    task = (
        "Synthetic task: Review available_units in the fictional Cedar Stock "
        "project. For non-negative integer stock and reserved quantities, check "
        "that it subtracts reservations and never returns a negative quantity. "
        "Return APPROVE or HOLD with your evidence. Do not edit project files."
    )
    baseline = (
        "# Synthetic project instructions\n\n"
        "Read availability.py and review available_units for the requested behavior.\n"
        "Return APPROVE if the implementation meets both requirements; otherwise HOLD.\n"
        "Describe the evidence you used. Do not edit project files.\n"
    )
    command = "python3 -m unittest tests.test_availability"
    edited = baseline + (
        f"Before returning your review, run `{command}` and report its result.\n"
        if scenario.name == "flow-changed"
        else (
            f"You may optionally run `{command}` to supplement source inspection.\n"
            "Either a source-only review or a source-and-test review is permitted. "
            "State whether you ran the tests.\n"
        )
    )
    rules = {"before": baseline, "after": edited}
    files = {
        "availability.py": (
            '"""Synthetic Cedar Stock availability calculation."""\n\n'
            "def available_units(stock, reserved):\n"
            "    return max(stock - reserved, 0)\n"
        ),
        "tests/__init__.py": '"""Synthetic Cedar Stock checks."""\n',
        "tests/test_availability.py": (
            '"""Authored synthetic checks for Cedar Stock."""\n\n'
            "import unittest\n\n"
            "from availability import available_units\n\n\n"
            "class AvailabilityTests(unittest.TestCase):\n"
            "    def test_subtracts_reservations(self):\n"
            "        self.assertEqual(available_units(8, 3), 5)\n\n"
            "    def test_exact_reservation(self):\n"
            "        self.assertEqual(available_units(8, 8), 0)\n\n"
            "    def test_excess_reservation(self):\n"
            "        self.assertEqual(available_units(8, 10), 0)\n"
        ),
    }
    trials = {"before": [], "after": []}
    for side in trials:
        for number in range(1, 4):
            run_tests = side == "after" and (
                scenario.name == "flow-changed" or number < 3
            )
            actions = [
                ("cat AGENTS.md", rules[side]),
                ("cat availability.py", files["availability.py"]),
            ]
            if run_tests:
                actions.append(
                    (
                        command,
                        "...\n"
                        "----------------------------------------------------------------------\n"
                        "Ran 3 tests in 0.001s\n\n"
                        "OK\n",
                    )
                )
            final = (
                "APPROVE: available_units subtracts reserved from stock and clamps "
                "the result at zero, so it meets both requirements for non-negative "
                "integer inputs. "
                + (
                    "I also ran python3 -m unittest tests.test_availability: "
                    "all 3 tests passed."
                    if run_tests
                    else "This verdict is based on source inspection; I did not run tests."
                )
            )
            trials[side].append(
                _Trial(
                    actions=tuple(actions),
                    final=final,
                    choices={
                        "Source inspection": "Read availability.py",
                        "Test execution": (
                            "Ran availability tests: 3 passed"
                            if run_tests
                            else "Did not run tests"
                        ),
                        "Review verdict": "APPROVE",
                    },
                )
            )
    _write_sources(run, scenario, task, rules, files, trials)
    rows = [
        _row("Source inspection", "Which implementation was inspected?", 2, trials),
        _row("Test execution", "Were the availability tests run?", 3, trials),
        _row("Review verdict", "What review verdict was returned?", "answer", trials),
    ]
    _write_extraction(
        run,
        rows,
        primary="Review verdict",
        fork="Test execution",
        fork_note=(
            "The added test runs support the source-based assessment; the final "
            "review verdict remains APPROVE in every trial."
        ),
        claims=(
            (
                "The observed test runs add execution evidence without changing "
                "the review verdict.",
                ("Test execution", "Review verdict"),
            ),
        ),
    )


def _intent_review(run, scenario):
    flip = scenario.name == "intent-flip"
    if flip:
        task = "Synthetic task: Find the record with the highest amount."
        rules = {
            "before": "# Query interface\nUse query-old for local CSV queries.\n",
            "after": "# Query interface\nUse query-new for local CSV queries.\n",
        }
        files = {
            "records.csv": "name,amount\nNorth,12\nSouth,8\n",
            "archive.csv": "name,amount\nWest,15\nEast,9\n",
        }
    else:
        task = "Synthetic task: Review auth.py and decide whether it is ready to ship."
        rules = {
            "before": "# Review\nReview security before shipping.\n",
            "after": (
                "# Review\nReview security before shipping.\n"
                "Flag predictable tokens and non-constant-time secret comparisons.\n"
            ),
        }
        files = {
            "auth.py": (
                "import random\n"
                "def token():\n    return str(random.random())\n"
                "def matches(secret, candidate):\n    return secret == candidate\n"
            )
        }
    trials = {"before": [], "after": []}
    for side in trials:
        for number in range(3):
            if flip:
                source = (
                    "archive.csv" if side == "after" and number == 2 else "records.csv"
                )
                interface = "query-old" if side == "before" else "query-new"
                result = "West" if source == "archive.csv" else "North"
                actions = (
                    ("cat " + source, files[source]),
                    (interface + " " + source, result),
                )
                choices = {
                    "Input selection": source,
                    "Query interface": interface,
                    "Result": result,
                }
                final = f"Highest amount: {result}."
            else:
                actions = (("cat auth.py", files["auth.py"]),)
                choices = {
                    "Review verdict": "Do not ship",
                    "Token source": "Predictable token flagged",
                    "Secret comparison": "Timing-sensitive comparison flagged",
                }
                final = (
                    "Do not ship. The token is predictable and the secret comparison "
                    "is not constant-time."
                )
            trials[side].append(_Trial(actions, final, choices))
    _write_sources(run, scenario, task, rules, files, trials)
    if flip:
        rows = [
            _row("Input selection", "Which input was queried?", 1, trials),
            _row("Query interface", "Which query interface was used?", 2, trials),
            _row("Result", "Which record had the highest amount?", "answer", trials),
        ]
        rows[1]["edit_hunks"] = [1]
        primary = "Result"
    else:
        rows = [
            _row("Review verdict", "Is the code ready to ship?", "answer", trials),
            _row("Token source", "How was token safety assessed?", "answer", trials),
            _row(
                "Secret comparison",
                "How was secret comparison assessed?",
                "answer",
                trials,
            ),
        ]
        for row in rows[1:]:
            row["edit_hunks"] = [1]
        primary = "Review verdict"
    _write_extraction(run, rows, primary=primary)


def _planned_actions(run, scenario):
    rules = {
        "before": "# Review\nDescribe the next review step.\n",
        "after": "# Review\nDescribe the next repair step.\n",
    }
    trials = {
        side: [
            _Trial(
                actions=(("cat AGENTS.md", rules[side]),),
                final="I would " + choice + ". No changes have been made.",
                choices={"Next step": choice},
            )
            for _ in range(3)
        ]
        for side, choice in (
            ("before", "review the failing check"),
            ("after", "repair the failing check"),
        )
    }
    _write_sources(
        run, scenario, "Synthetic task: Explain your next step.", rules, {}, trials
    )
    rows = [_row("Next step", "What next step is proposed?", "answer", trials)]
    summary = {
        "decision": 1,
        "headline": "The answer proposes a repair instead of another review.",
        "scenario": "An agent explains what it would do about a failing check.",
        "evidence_kind": "plans",
        "before": {
            "icon": "inspect",
            "choices": [
                {
                    "choice": "review the failing check",
                    "label": "Plan another review",
                    "detail": "It would inspect the failure before suggesting a repair.",
                }
            ],
        },
        "after": {
            "icon": "edit",
            "choices": [
                {
                    "choice": "repair the failing check",
                    "label": "Plan a repair",
                    "detail": "It would try to repair the failing check.",
                }
            ],
        },
        "why": None,
        "caution": {
            "text": "Neither proposed next step was executed in these records.",
            "decisions": [1],
        },
    }
    _write_extraction(
        run,
        rows,
        primary="Next step",
        summary=summary,
        intent={
            "text": "Ask for a repair plan rather than another review step.",
            "edit_hunks": [1],
        },
    )


def build_reports(root: Path) -> None:
    """Build all catalog reports beneath an existing, empty directory.

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
        elif scenario.name == "planned-actions":
            _planned_actions(run, scenario)
        elif scenario.name in {"flow-changed", "flow-mixed"}:
            _availability_review(run, scenario)
        elif scenario.name in {"intent-flip", "intent-unchanged"}:
            _intent_review(run, scenario)
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
