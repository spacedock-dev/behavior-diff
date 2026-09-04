"""Format-neutral wording for Behavior Diff reports."""

from reporting.schema import ContentData


def subtitle(self_reported):
    if self_reported:
        return (
            "Same scenario, same recorded settings, six fresh agent runs. "
            "The only difference between the two columns is one proposed "
            "rule in the project's CLAUDE.md. Each trial shows the agent's "
            "self-reported actions, not captured traces."
        )
    return (
        "Same scenario, same recorded settings, six fresh agent runs. "
        "The only difference between the two columns is one proposed "
        "rule in the project's CLAUDE.md. Each trial is graded from "
        "the agent's actual tool calls, never its self-report."
    )


def boundary():
    return (
        "This is simulation evidence. Real-use evidence is still pending.\n"
        "It does not repair the original incident; it tests the change "
        "for future tasks."
    )


def result_data(mode, self_reported, before, after, trial_count, has_decisions):
    if mode == "review":
        text = (
            "No automatic verdict — compare the reported actions and final answers"
            if self_reported
            else "No automatic verdict — compare the flows and final answers"
        )
        if self_reported and has_decisions:
            text = (
                "No automatic verdict — compare the reported actions, decision diff, "
                "and final answers"
            )
        return text, "neutral"
    if before["valid"] < before["total"] or after["valid"] < after["total"]:
        text, kind = "Could not test", "neutral"
    elif before["passed"] == 0 and after["passed"] == after["valid"]:
        text, kind = "Changed in this scenario", "good"
    elif before["passed"] == 0 and after["passed"] == 0:
        text, kind = "The proposed rule did not change behavior", "bad"
    elif before["passed"] == before["valid"] and after["passed"] == after["valid"]:
        text, kind = "The original problem was not reproduced", "neutral"
    elif before["passed"] == before["valid"] and after["passed"] == 0:
        text, kind = "The proposed rule made behavior worse", "bad"
    else:
        text, kind = "Behavior was inconsistent", "neutral"
    return text + single_run_suffix(mode, trial_count), kind


def single_run_suffix(mode, trial_count):
    if mode != "review" and trial_count == 1:
        return " — in this single run, weaker evidence"
    return ""


def count_data(mode, passed, valid, blocked):
    if mode == "review":
        return "{0} valid trial(s) · no automatic grading (blocked: {1})".format(
            valid, blocked
        ), False
    return "{0} of {1} valid trials met the expectation (blocked: {2})".format(
        passed, valid, blocked
    ), True


def decision_blurb(self_reported, trial_count):
    if self_reported:
        blurb = (
            "A decision is a point where the agent had a real choice. The "
            "decisions come from self-reported actions and final answers. Some "
            "decisions leave no reported action behind. Order follows the "
            "report: decisions visible in actions come in reported action "
            "order, and decisions visible only in the final answer come last. "
            "Extractor output can vary from run to run."
        )
    else:
        blurb = (
            "A decision is a point where the agent had a real choice. These "
            "are recovered from what the trials did and said, not from the "
            "instruction diff, and some of them leave no command behind. Order "
            "is real: decisions visible in commands come in command order, and "
            "decisions visible only in the final answer come last. The fork "
            "and main divergences are stable across extractions; minor rows "
            "can vary run to run."
        )
    if trial_count == 1:
        blurb += (
            " CAUTION — one trial per side: any divergence here can be "
            "run-to-run variation rather than a rule effect; confirm with "
            "repeated trials (behavior-diff 3+3) before acting on it."
        )
    return blurb


def observation(mode, decisions, before_count, after_count):
    if mode != "review" or not decisions.rows or not decisions.fork:
        return ""
    row = decisions.rows[decisions.fork - 1]
    title = row.topic or row.decision
    before = branch_text(row.before, decisions.before_count or before_count)
    after = branch_text(row.after, decisions.after_count or after_count)
    return (
        "Observed in this run — {0}: BEFORE {1} · AFTER {2}. "
        "Single-run observation, not a verdict."
    ).format(title, before, after)


def branch_text(choices, total):
    return " · ".join(
        choice.choice
        if choice.count == total
        else "{0} ({1}/{2})".format(choice.choice, choice.count, total)
        for choice in choices
    ) or "—"


def headings(target_file):
    return {
        "scenario": "Scenario",
        "expected": "Expected behavior",
        "diff": "Diff of {0} — the only difference between the variants".format(
            target_file
        ),
        "decision": "Decision diff — top divergences",
        "flow": "Flow diff — where the variants diverge",
        "result": "Result",
    }




def flow_fold_summary():
    return "Flow diff — command-derived (deterministic, no model involved)"



def decision_footer(rows, fork):
    divergent = sum(row.diverges for row in rows)
    if fork:
        rest = divergent - 1
        return (
            "One target decision changed (#{0}); {1} later difference{2} diverge "
            "downstream of it (the extractor's causal reading, not a measured chain)."
        ).format(fork, rest, "s" if rest != 1 else "")
    return "{0} of {1} decisions diverge.".format(divergent, len(rows))


def dropped_rows(dropped):
    return (
        "{0} extractor row(s) were dropped because their counts did not match the trials."
    ).format(dropped)



def build_content(
    config,
    scenario,
    mode,
    trace_source,
    target_file,
    decisions,
    before_total,
    after_total,
):
    self_reported = trace_source == "self-reported"
    names = headings(target_file)
    return ContentData(
        title=config.get("title", "rk-monitor Behavior Check"),
        subtitle=config.get("sub", subtitle(self_reported)),
        observation=observation(mode, decisions, before_total, after_total),
        scenario_heading=names["scenario"],
        scenario=scenario,
        expected_heading=names["expected"],
        expected=config.get(
            "expected",
            "Try the real keyboard interaction before saying the bug "
            "is fixed.\nIf that cannot be tested, say it is "
            "unverified.",
        ),
        diff_heading=names["diff"],
        decision_heading=names["decision"],
        decision_blurb=decision_blurb(self_reported, before_total),
        flow_heading=names["flow"],
        result_heading=names["result"],
        boundary=boundary(),
    )