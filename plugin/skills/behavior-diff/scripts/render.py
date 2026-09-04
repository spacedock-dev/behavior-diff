#!/usr/bin/env python3
"""Render a Behavior Diff run into report.md + report.html (+ artifact body).

Usage: render.py RUN_DIR CAPSULE_DIR MODEL [CONFIG_JSON]
"""

import sys
from pathlib import Path

from reporting.load import load_report
from reporting.render_html import render_artifact, render_document
from reporting.render_markdown import render_markdown


run = Path(sys.argv[1]).resolve()
capsule = Path(sys.argv[2]).resolve()
model = sys.argv[3]
config_path = Path(sys.argv[4]) if len(sys.argv) > 4 else None
report = load_report(run, capsule, model, config_path)

report_json = report.to_json()
markdown = render_markdown(report)
css = (Path(__file__).parent / "reporting/report.css").read_text()
artifact_html = render_artifact(report, css)
document_html = render_document(artifact_html)

(run / "report-data.json").write_text(report_json)
(run / "report.md").write_text(markdown)
(run / "report-artifact.html").write_text(artifact_html)
(run / "report.html").write_text(document_html)

print(
    f"mode {report.metadata.mode} · BEFORE pass {report.variants.before.passed}/{report.variants.before.valid} · "
    f"AFTER pass {report.variants.after.passed}/{report.variants.after.valid} → {report.result.text}"
)
print(f"report: {run / 'report.md'}")
print(f"page:   {run / 'report.html'}")
