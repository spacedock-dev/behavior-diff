#!/usr/bin/env python3
"""Coordinate existing grading, combined extraction, and rendering mechanics.

Trial launch/collection remains in Bash. This adapter does not split observation
from assessment or change the model payload, report schema, or failure policy.
"""

import argparse
import json
import subprocess
from pathlib import Path

from pipeline import Pipeline, Stage
from stage_contract import StageResult

SCRIPTS = Path(__file__).resolve().parent


def record_run(run, fields):
    # The adapter owns a separate record; Bash retains status.json and its traps.
    # Progress failures must not change execution results.
    subprocess.run(
        [
            "python3",
            str(SCRIPTS / "progress.py"),
            str(run / "coordinator-status.json"),
            "run",
            json.dumps(fields),
        ],
        check=False,
    )


def milestone(run, text):
    print(f"behavior-diff {run.name}: {text}", flush=True)


def run_posttrial(run, trials, model, extract_agent, extract_model):
    def grade(dependencies):
        record_run(
            run,
            {
                "run_id": run.name,
                "trials": trials,
                "state": "running",
                "phase": "checking_results",
            },
        )
        milestone(run, "all trials ended; checking trial results")
        rows = []
        for variant in ("before", "after"):
            for number in range(1, trials + 1):
                name = f"{variant}-{number}"
                # Retain the runner's exact reviewability check, including jq's
                # treatment of malformed/missing traces. Native failure handling
                # remains in report loading, not this neutral completeness grade.
                result = subprocess.run(
                    [
                        "jq",
                        "-e",
                        "-s",
                        '[.[] | select(.type == "result" '
                        'and ((.result // "") | length > 0))] | length > 0',
                        str(run / name / "trace.jsonl"),
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                verdict = "REVIEW" if result.returncode == 0 else "BLOCKED"
                rows.append(f"{name}\t{verdict}\t-\n")
        (run / "grades.tsv").write_text("".join(rows), encoding="utf-8")
        print(flush=True)
        return StageResult("completed", output={"path": str(run / "grades.tsv")})

    def extract(dependencies):
        record_run(run, {"phase": "comparing_evidence"})
        milestone(run, "comparing evidence")
        command = ["python3", str(SCRIPTS / "decisions.py"), str(run)]
        if extract_agent:
            command.extend(["--agent", extract_agent])
        if extract_model:
            command.extend(["--model", extract_model])
        code = subprocess.run(command, check=False).returncode
        if code:
            return StageResult(
                "failed", output={"exit_code": code}, error="combined extraction failed"
            )
        # decisions.py can return zero after a skipped or unavailable extraction.
        # Keep its semantic availability separate from process completion.
        try:
            assessment = json.loads((run / "assessment-status.json").read_text())
        except (OSError, ValueError):
            return StageResult("failed", error="assessment status unavailable")
        state = assessment.get("state")
        if state == "available":
            return StageResult(
                "completed", output={"path": str(run / "decisions.json")}
            )
        if state == "skipped":
            return StageResult("skipped", error="combined extraction skipped")
        return StageResult("failed", error="combined extraction unavailable")

    render_code = None

    def render(dependencies):
        nonlocal render_code
        record_run(run, {"phase": "rendering"})
        milestone(run, "rendering report")
        render_code = subprocess.run(
            [
                "python3",
                str(SCRIPTS / "render.py"),
                str(run),
                str(run),
                model,
                str(run / "config.json"),
            ],
            check=False,
        ).returncode
        if render_code < 0:
            render_code = 128 - render_code
        report = run / "report.html"
        available = render_code == 0 and report.is_file() and report.stat().st_size > 0
        record_run(
            run,
            {
                "report": {
                    "state": "available" if available else "failed",
                    "path": str(report) if available else None,
                }
            },
        )
        if available:
            milestone(run, f"report ready: {report}")
        else:
            milestone(run, f"report not produced (renderer exit {render_code})")
        output = {"exit_code": render_code, "path": str(report) if available else None}
        return (
            StageResult("completed", output=output)
            if available
            else StageResult("failed", output=output, error="report not produced")
        )

    pipeline = Pipeline(
        [
            Stage("grading", run=grade),
            Stage("extraction", required=("grading",), run=extract),
            Stage(
                "rendering", required=("grading",), optional=("extraction",), run=render
            ),
        ],
        record_dir=run / "stages",
        outputs={
            "grading": (run / "grades.tsv",),
            "extraction": (run / "decisions.json",),
            "rendering": (run / "report.html",),
        },
        producer="behavior-diff-posttrial",
    )
    pipeline.run()
    # Match the shell contract exactly: extraction is best effort; a renderer
    # exit is propagated even when an old file exists, and missing output after
    # a zero exit is reported unavailable without inventing a different exit.
    return render_code if render_code is not None else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--trials", type=int, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--extract-agent", default="")
    parser.add_argument("--extract-model", default="")
    args = parser.parse_args(argv)
    if args.trials < 1:
        parser.error("--trials must be positive")
    return run_posttrial(
        args.run, args.trials, args.model, args.extract_agent, args.extract_model
    )


if __name__ == "__main__":
    raise SystemExit(main())
