"""Authored synthetic evidence shared by report contracts and the local gallery.

Trace entries describe fictional actions; this module never executes them.
Only the shipped decision-ingest and report-render commands run during a build.
"""

import json
import os
import subprocess
import sys
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
        "non-outcome-narrative",
        "A changed evidence format leads ahead of the verdict",
        "The narrative explains the answer format while the primary verdict also changes.",
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
        "Complete invoice-review traces remain available without an extracted comparison.",
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
    Scenario(
        "timing-rule",
        "Retry timing leads alongside mixed recommendations",
        "Planned intervals and deadlines change; signoff remains required in both answers.",
    ),
    Scenario(
        "formula-writing",
        "Formula and writing choices vary without changing the verdict",
        "Two after answers simplify a formula and use bullets; source reads and approval stay the same.",
    ),
)


@dataclass(frozen=True)
class _Trial:
    actions: tuple[tuple[str, str], ...]
    final: str
    choices: dict[str, str]
    summary: str
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
    memberships = {}
    for side in ("before", "after"):
        branches = {}
        for number, trial in enumerate(trials[side], 1):
            branches.setdefault(trial.choices[topic], []).append(f"{side}-{number}")
        memberships[side] = branches
    return {
        "topic": topic,
        "decision": question,
        "anchor": anchor,
        "before": [
            {"choice": choice, "trials": names}
            for choice, names in memberships["before"].items()
        ],
        "after": [
            {"choice": choice, "trials": names}
            for choice, names in memberships["after"].items()
        ],
        "diverges": {
            choice: len(names) for choice, names in memberships["before"].items()
        }
        != {choice: len(names) for choice, names in memberships["after"].items()},
    }


def _trial_summaries(trials, comparisons):
    """Attach authored prose to the exact synthetic trial group identities."""
    if not len(trials["before"]) == len(trials["after"]) == len(comparisons):
        raise ValueError("Synthetic trial summaries must cover both sides.")
    return [
        {
            "before_trial": f"before-{number}",
            "after_trial": f"after-{number}",
            "takeaway": takeaway,
            "before": before.summary,
            "after": after.summary,
            "caveat": caveat,
        }
        for number, (before, after, (takeaway, caveat)) in enumerate(
            zip(trials["before"], trials["after"], comparisons), 1
        )
    ]


def _write_extraction(
    run,
    rows,
    primary=None,
    fork=None,
    fork_note="",
    claims=(),
    summary=None,
    intent=None,
    trial_summaries=(),
    explanation=None,
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
            "trial_summaries": list(trial_summaries),
            "explanation": explanation,
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
                    summary=(
                        "Recorded reads include session notes, the branch patch, and scope; "
                        "the answer describes only the cache-expiry fix."
                        if side == "before"
                        else "Recorded reads use the branch patch and scope without session notes; "
                        "the answer still describes only the cache-expiry fix."
                    ),
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
        trial_summaries=_trial_summaries(
            trials,
            [
                (
                    "The PR description keeps the same scope while its recorded review sources change.",
                    "The answer describes regression coverage but says the test was not run.",
                )
            ]
            * 3,
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
    if scenario.name == "non-outcome-narrative":
        edited = edited.replace(
            "Return the verdict and one sentence of evidence.",
            "Return the verdict followed by separate evidence bullets.",
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
                if (
                    scenario.name in {"answer-details", "non-outcome-narrative"}
                    and side == "after"
                ):
                    presentation = "Verdict with separate evidence bullets"
                    history_note = (
                        "no LUM-104 payment." if inspect_history else "not checked."
                    )
                    final = (
                        "APPROVE\n"
                        "- Invoice: LUM-104 for 480 credits.\n"
                        "- Receipt: 480 credits received.\n"
                        "- Vendor: Lumen Paper is active.\n"
                        f"- Payment history: {history_note}\n"
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
            if blocked:
                sentence = (
                    "The recorded invoice read fails; the answer reports a blocked review "
                    "without inspecting the remaining records."
                )
            elif presentation == "Verdict with separate evidence bullets":
                sentence = (
                    "Recorded reads "
                    + ("include" if inspect_history else "omit")
                    + " payment history; the answer approves "
                    "and lists the evidence in separate bullets."
                )
            else:
                sentence = (
                    "The self-report describes " if reported else "Recorded reads show "
                )
                if verdict == "HOLD":
                    sentence += "a payment-history check; the answer holds the invoice for its prior payment."
                elif inspect_history:
                    sentence += "a payment-history check; the answer approves after finding no prior payment."
                elif mixed_primary:
                    sentence += (
                        "receipt then vendor checks"
                        if side == "before"
                        else "vendor then receipt checks"
                    ) + " without payment history; the answer approves the invoice."
                else:
                    sentence += (
                        "invoice, receipt, and vendor checks without payment history; "
                        "the answer approves the invoice."
                    )
            trials[side].append(
                _Trial(
                    actions=tuple(actions),
                    final=final,
                    choices=choices,
                    summary=sentence,
                    verdict="BLOCKED" if blocked else "REVIEW",
                    missing_files=("invoice.csv",) if blocked else (),
                )
            )
    _write_sources(run, scenario, task, rules, files, trials)
    if scenario.name == "missing-extraction":
        return
    comparisons = []
    for before, after in zip(trials["before"], trials["after"]):
        before_choices, after_choices = before.choices, after.choices
        if after.verdict == "BLOCKED":
            takeaway = (
                "After cannot complete the review because its invoice read fails."
            )
        elif before_choices["Review verdict"] != after_choices["Review verdict"]:
            takeaway = (
                "The answer changes from HOLD for a prior payment to APPROVE "
                "without checking payment history."
            )
        elif (
            before_choices["Answer presentation"]
            != after_choices["Answer presentation"]
        ):
            takeaway = "The verdict stays APPROVE, but After lists the evidence in separate bullets."
        elif before_choices["Record checks"] != after_choices["Record checks"]:
            takeaway = (
                "Both answers approve without checking payment history, "
                "but the supporting records are read in a different order."
            )
        elif before_choices["Review verdict"] == "HOLD":
            takeaway = "Both reviews check payment history and answer HOLD for the prior payment."
        else:
            takeaway = "Both reviews perform the same checks and answer APPROVE."
        comparisons.append((takeaway, ""))
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
    if scenario.name in {"answer-details", "non-outcome-narrative"}:
        rows.append(
            _row(
                "Answer presentation",
                "How was the review evidence presented?",
                "answer",
                trials,
            )
        )
        if scenario.name == "non-outcome-narrative":
            rows[-1]["edit_hunks"] = [1]
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
    if scenario.name in {"answer-details", "non-outcome-narrative"}:
        summary = {
            "decision": 5,
            "headline": (
                "The review still approves the invoice; only its explanation changes."
                if scenario.name == "answer-details"
                else "The review now lists the evidence record by record."
            ),
            "scenario": "An agent explains an invoice review without making a payment.",
            "evidence_kind": "answers",
            "before": {
                "icon": "report",
                "choices": [
                    {
                        "choice": "Verdict with one evidence sentence",
                        "label": "One evidence sentence",
                        "detail": "The answer combines the supporting records in a sentence.",
                    }
                ],
            },
            "after": {
                "icon": "report",
                "choices": [
                    {
                        "choice": "Verdict with separate evidence bullets",
                        "label": "Evidence by record",
                        "detail": "The answer lists the invoice, receipt, vendor, and history separately.",
                    }
                ],
            },
            "why": {
                "text": "Supporting records are listed separately rather than combined.",
                "decisions": [5],
            },
            "caution": None
            if scenario.name == "answer-details"
            else {
                "text": "An approval answer does not mean a payment occurred.",
                "decisions": [4],
            },
        }
    _write_extraction(
        run,
        rows,
        primary="Review verdict",
        fork=fork,
        fork_note=fork_note,
        claims=claims,
        summary=summary,
        trial_summaries=_trial_summaries(trials, comparisons),
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
                    summary=(
                        "Recorded reads cover the migration and pending deployment; "
                        "the answer describes the schema addition without a rollout verdict."
                        if side == "before"
                        else "Recorded reads also cover rollback notes; the answer adds "
                        "the backup prerequisite without a rollout verdict."
                    ),
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
        trial_summaries=_trial_summaries(
            trials,
            [
                (
                    "After adds a rollback prerequisite, but neither answer decides rollout readiness.",
                    "The records show inspection, not execution of the migration.",
                )
            ]
            * 3,
        ),
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
                    summary=(
                        "Recorded actions include source inspection and a passing test run; "
                        "the answer approves the implementation."
                        if run_tests
                        else "Recorded actions show source inspection without a test run; "
                        "the answer approves the implementation."
                    ),
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
        trial_summaries=_trial_summaries(
            trials,
            [
                (
                    "After adds a passing test run while the review answer stays APPROVE."
                    if trial.choices["Test execution"] != "Did not run tests"
                    else "Both reviews inspect the source without running tests and answer APPROVE.",
                    "",
                )
                for trial in trials["after"]
            ],
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
            sentence = (
                f"The recorded query uses the {'old' if side == 'before' else 'new'} "
                f"interface on {'archived' if source == 'archive.csv' else 'current'} records; "
                f"the answer identifies {result} as the largest amount."
                if flip
                else "The recorded read inspects the authentication code; the answer "
                "flags predictable tokens and unsafe secret comparison."
            )
            trials[side].append(_Trial(actions, final, choices, sentence))
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
    _write_extraction(
        run,
        rows,
        primary=primary,
        trial_summaries=_trial_summaries(
            trials,
            [
                (
                    (
                        "After queries archived rather than current records with a new interface; "
                        "the answer changes from North to West."
                        if number == 2
                        else "The query interface changes, but both answers identify North."
                    )
                    if flip
                    else "Both answers flag the same security problems and say not to ship.",
                    "",
                )
                for number in range(3)
            ],
        ),
    )


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
                summary=(
                    "The answer proposes to "
                    + choice
                    + "; only an instruction read is recorded."
                ),
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
        trial_summaries=_trial_summaries(
            trials,
            [
                (
                    "The proposed next step changes from reviewing the failure to repairing it.",
                    "Neither proposed step is recorded as executed.",
                )
            ]
            * 3,
        ),
        intent={
            "text": "Ask for a repair plan rather than another review step.",
            "edit_hunks": [1],
        },
    )


def _timing_rule(run, scenario):
    rules = {
        "before": (
            "# Retry review\n"
            "State a retry plan: after signoff, poll every 5 minutes for 15 minutes.\n"
        ),
        "after": (
            "# Retry review\n"
            "State a retry plan. Do not poll until signoff; then poll every "
            "10 minutes for 30 minutes.\n"
        ),
    }
    plans = (
        "After signoff, poll every 5 minutes for 15 minutes",
        "After signoff, poll every 10 minutes for 30 minutes",
        "After signoff, check once at the 30-minute deadline",
    )
    details = (
        "It would wait for signoff, then poll every 5 minutes until a 15-minute deadline.",
        "It would wait for signoff, then poll every 10 minutes until a 30-minute deadline.",
        "It would wait for signoff, then check once at the 30-minute deadline.",
    )
    trials = {"before": [], "after": []}
    for side in trials:
        for number in range(1, 4):
            plan = 0 if side == "before" else 1 if number != 3 else 2
            deferred = number == (3 if side == "before" else 2)
            recommendation = (
                "Recommend deferring" if deferred else "Recommend proceeding"
            )
            trials[side].append(
                _Trial(
                    actions=(("cat AGENTS.md", rules[side]),),
                    final=(
                        details[plan]
                        + " "
                        + recommendation
                        + " with this retry plan. No polling or signoff is recorded."
                    ),
                    choices={
                        "Retry plan": plans[plan],
                        "Recommendation": recommendation,
                    },
                    summary=details[plan],
                )
            )
    _write_sources(
        run,
        scenario,
        "Synthetic task: State your retry plan and recommend proceeding or deferring.",
        rules,
        {},
        trials,
    )
    rows = [
        _row("Retry plan", "What retry plan is stated?", "answer", trials),
        _row("Recommendation", "What is recommended?", "answer", trials),
    ]
    rows[0]["edit_hunks"] = [1]
    _write_extraction(
        run,
        rows,
        primary="Recommendation",
        summary={
            "decision": 1,
            "headline": "Retry plans extend the deadline; some use longer intervals.",
            "scenario": "An agent proposes retry timing without executing the plan.",
            "evidence_kind": "plans",
            "before": {
                "icon": "inspect",
                "choices": [
                    {
                        "choice": plans[0],
                        "label": "Plan five-minute polling",
                        "detail": details[0],
                    }
                ],
            },
            "after": {
                "icon": "inspect",
                "choices": [
                    {
                        "choice": plans[index],
                        "label": label,
                        "detail": details[index],
                    }
                    for index, label in (
                        (1, "Plan ten-minute polling"),
                        (2, "Plan one deadline check"),
                    )
                ],
            },
            "why": None,
            "caution": None,
        },
        intent={
            "text": "Restate the signoff gate and extend retry intervals and deadline.",
            "edit_hunks": [1],
        },
        trial_summaries=_trial_summaries(
            trials,
            [
                (
                    "Both plans wait for signoff; After extends the interval and deadline.",
                    "Neither retry plan is recorded as executed.",
                ),
                (
                    "Both plans wait for signoff; After extends the interval and deadline.",
                    "Neither retry plan is recorded as executed.",
                ),
                (
                    "Both plans wait for signoff; After proposes one later deadline check.",
                    "Neither retry plan is recorded as executed.",
                ),
            ],
        ),
        explanation={
            "headline": "The retry window extends, but a minority proposes only one check.",
            "overview": "The answers describe future plans rather than executed polling.",
            "steps": [
                {
                    "title": "After signoff",
                    "before": "All three plan five-minute polling until 15 minutes.",
                    "after": "Two plan ten-minute polling until 30 minutes; one plans one deadline check.",
                    "meaning": "The longer window is consistent; repeated polling is not.",
                    "decisions": [1],
                },
            ],
            "unchanged": [],
            "limits": [
                {
                    "text": "No polling or signoff is recorded; recommendations remain mixed.",
                    "decisions": [1, 2],
                },
            ],
            "examples": [
                {"side": side, "trial": f"{side}-1", "text": trials[side][0].final}
                for side in ("before", "after")
            ],
        },
    )


def _formula_writing(run, scenario):
    rules = {
        "before": "# Review\nExplain the bounded availability formula in a paragraph.\n",
        "after": "# Review\nPrefer a concise equivalent formula and evidence bullets.\n",
    }
    trials = {"before": [], "after": []}
    for side in trials:
        for number in range(1, 4):
            simplified = side == "after" and number < 3
            formula = (
                "max(stock - reserved, 0)"
                if simplified
                else ("stock - reserved if stock >= reserved else 0")
            )
            final = (
                f"- Formula: {formula}\n- Verdict: APPROVE"
                if simplified
                else f"Formula: {formula}. Verdict: APPROVE."
            )
            trials[side].append(
                _Trial(
                    actions=(
                        ("cat availability.py", "return max(stock - reserved, 0)\n"),
                    ),
                    final=final,
                    choices={
                        "Source inspection": "Read availability.py",
                        "Formula representation": formula,
                        "Answer presentation": "Evidence bullets"
                        if simplified
                        else "Paragraph",
                        "Review verdict": "APPROVE",
                    },
                    summary="Reads the implementation and returns APPROVE.",
                )
            )
    _write_sources(
        run,
        scenario,
        "Synthetic task: Explain bounded availability for non-negative integer inputs.",
        rules,
        {"availability.py": "return max(stock - reserved, 0)\n"},
        trials,
    )
    rows = [
        _row("Source inspection", "Which source was inspected?", 1, trials),
        _row("Formula representation", "Which formula is written?", "answer", trials),
        _row("Answer presentation", "How is the evidence presented?", "answer", trials),
        _row("Review verdict", "What verdict is returned?", "answer", trials),
    ]
    rows[1]["edit_hunks"] = [1]
    rows[2]["edit_hunks"] = [1]
    _write_extraction(
        run,
        rows,
        primary="Review verdict",
        trial_summaries=_trial_summaries(
            trials,
            [
                (
                    "After uses max notation and bullets; both return APPROVE.",
                    "The answers do not establish behavior outside the stated inputs.",
                ),
                (
                    "After uses max notation and bullets; both return APPROVE.",
                    "The answers do not establish behavior outside the stated inputs.",
                ),
                (
                    "Both retain conditional notation, paragraph presentation and APPROVE.",
                    "This trial does not adopt the proposed presentation change.",
                ),
            ],
        ),
        explanation={
            "headline": "Two answers simplify notation and switch to bullets.",
            "overview": "This is a presentation distinction, not a changed availability result.",
            "steps": [
                {
                    "title": "Formula notation",
                    "before": "All three answers write an explicit conditional.",
                    "after": "Two use max(stock - reserved, 0); one retains the conditional.",
                    "meaning": "Both formulas clamp subtraction at zero for the stated inputs.",
                    "decisions": [2],
                },
                {
                    "title": "Evidence presentation",
                    "before": "All three answers use a paragraph.",
                    "after": "Two use bullets; one still uses a paragraph.",
                    "meaning": "The format change is not consistent across all trials.",
                    "decisions": [3],
                },
            ],
            "unchanged": [
                {
                    "text": "Every trial reads availability.py and returns APPROVE.",
                    "decisions": [1, 4],
                },
            ],
            "limits": [
                {
                    "text": "These answers do not establish behavior for negative or non-integer inputs.",
                    "decisions": [2],
                },
            ],
            "examples": [
                {"side": side, "trial": f"{side}-1", "text": trials[side][0].final}
                for side in ("before", "after")
            ],
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
        elif scenario.name == "timing-rule":
            _timing_rule(run, scenario)
        elif scenario.name == "formula-writing":
            _formula_writing(run, scenario)
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
