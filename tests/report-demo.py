#!/usr/bin/env python3
"""Generate a synthetic report gallery, with an optional loopback-only server."""

import argparse
from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import quote

from report_fixtures import SCENARIOS, build_reports


STYLE = """
:root {
  color-scheme: light;
  --ground: #f6f8f9; --panel: #fff; --ink: #1c2733; --muted: #5b6b7a;
  --border: #d9e1e7; --accent: #0b6e75; --accent-soft: #e3f0f1;
}
* { box-sizing: border-box; }
body {
  margin: 0 auto; padding: 3rem 1.25rem; max-width: 1080px;
  background: var(--ground); color: var(--ink);
  font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
a { color: var(--accent); text-underline-offset: .2em; }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
.eyebrow {
  color: var(--accent); font-size: .75rem; font-weight: 700;
  letter-spacing: .1em; text-transform: uppercase; margin: 0 0 .5rem;
}
h1 { font-size: clamp(1.8rem, 5vw, 2.5rem); line-height: 1.2; margin: 0; }
.intro { color: var(--muted); max-width: 70ch; margin: .8rem 0 1.5rem; }
.notice {
  background: var(--accent-soft); border-left: 3px solid var(--accent);
  border-radius: 4px; padding: 1rem 1.2rem; margin-bottom: 2rem;
}
.notice p { margin: .25rem 0; }
.gallery {
  list-style: none; padding: 0; margin: 0; display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
  gap: 1rem;
}
.card {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 8px; padding: 1.3rem; display: flex; flex-direction: column;
}
h2 { font-size: 1.05rem; line-height: 1.35; margin: 0; }
.description { color: var(--muted); margin: .7rem 0 1.3rem; }
.links { display: flex; flex-wrap: wrap; gap: .65rem 1.1rem; margin-top: auto; }
.primary { font-weight: 600; }
footer { border-top: 1px solid var(--border); margin-top: 2rem; padding-top: 1rem;
  color: var(--muted); font-size: .85rem; }
"""


def write_index(root: Path) -> Path:
    cards = []
    for scenario in SCENARIOS:
        case_path = quote(scenario.name, safe="")
        cards.append(
            f"""<li class="card">
<h2>{escape(scenario.title)}</h2>
<p class="description">{escape(scenario.description)}</p>
<nav class="links" aria-label="{escape(scenario.title, quote=True)} reports">
<a class="primary" href="{case_path}/report.html#panel-summary">Open report</a>
<a href="{case_path}/report.md">Markdown</a>
</nav>
</li>"""
        )
    cards_html = "\n".join(cards)
    index = root / "index.html"
    index.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Behavior Diff — synthetic report gallery</title>
<style>{STYLE}</style>
</head>
<body>
<header>
<p class="eyebrow">Behavior Diff · Synthetic demo</p>
<h1>Report gallery</h1>
<p class="intro">Explore how reports show changed behavior, unchanged results,
and limits in the available evidence.</p>
</header>
<aside class="notice" aria-label="Evidence limits">
<p><strong>Synthetic inputs. No model calls. Reporting-only evidence.</strong></p>
<p>These authored examples exercise the real report pipeline.
They do not prove model behavior or the effectiveness of an instruction.</p>
</aside>
<main aria-label="Report scenarios">
<ul class="gallery">
{cards_html}
</ul>
</main>
<footer>Each report uses the same synthetic fixtures as the deterministic report checks.
No live agent sessions or private transcripts appear here.</footer>
</body>
</html>
""",
        encoding="utf-8",
    )
    return index


def port_number(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use an integer from 0 to 65535") from exc
    if not 0 <= port <= 65535:
        raise argparse.ArgumentTypeError("use an integer from 0 to 65535")
    return port


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate synthetic Behavior Diff reports without model calls."
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="serve the gallery at 127.0.0.1 until Ctrl+C",
    )
    parser.add_argument(
        "--port",
        type=port_number,
        default=8767,
        help="server port (default: 8767; use 0 for an available port)",
    )
    args = parser.parse_args()
    root = None
    retain_output = False
    serving = False
    status = 0
    operation = "generate the gallery"
    try:
        root = Path(tempfile.mkdtemp(prefix="behavior-diff-report-demo-")).resolve()
        build_reports(root)
        index = write_index(root)
        if args.serve:
            operation = f"serve the gallery at 127.0.0.1:{args.port}"
            handler = partial(SimpleHTTPRequestHandler, directory=str(root))
            with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
                serving = True
                print(f"http://127.0.0.1:{server.server_port}/index.html", flush=True)
                print(
                    "Press Ctrl+C to stop and remove temporary files.", file=sys.stderr
                )
                server.serve_forever()
        else:
            print(index.as_uri(), flush=True)
            print(f"Gallery files remain at {root}", file=sys.stderr)
            retain_output = True
    except KeyboardInterrupt:
        print(
            "Gallery stopped." if serving else "Generation interrupted.",
            file=sys.stderr,
        )
        status = 0 if serving else 130
    except subprocess.CalledProcessError as exc:
        print(f"Cannot {operation}: {exc}", file=sys.stderr)
        if exc.stderr:
            detail = exc.stderr
            if isinstance(detail, bytes):
                detail = detail.decode("utf-8", errors="replace")
            print(detail.rstrip(), file=sys.stderr)
        status = 1
    except (OSError, ValueError) as exc:
        print(f"Cannot {operation}: {exc}", file=sys.stderr)
        status = 1
    finally:
        if root is not None and not retain_output:
            try:
                shutil.rmtree(root)
            except OSError as exc:
                print(f"Cannot remove temporary gallery {root}: {exc}", file=sys.stderr)
                status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
