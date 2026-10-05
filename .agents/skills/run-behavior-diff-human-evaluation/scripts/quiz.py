"""Private, loopback-only human evaluation UI. No model calls or renderer imports."""

import hashlib
import html
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import random
import re
import tempfile
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[4]
ASSETS = Path(__file__).resolve().parent.parent / "assets"
LETTERS = "ABCD"
MAX_BODY = 32768


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _private_session(session):
    session = Path(session).resolve()
    if session == ROOT or ROOT in session.parents:
        raise ValueError("Evaluation sessions must be outside the checkout.")
    if not session.is_dir():
        raise ValueError("Session directory does not exist.")
    return session


def _text(value, label, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(
            f"{label} must be nonempty text, at most {maximum} characters."
        )
    if any(ord(char) < 32 and char not in "\n\t\r" for char in value):
        raise ValueError(f"{label} contains control characters.")
    return value


def _cases(manifest):
    if (
        manifest.get("schema_version") != 1
        or manifest.get("source_repo") != "DataRecce/recce-team"
    ):
        raise ValueError("Unsupported evaluation session.")
    _text(manifest.get("id"), "Session id", 200)
    if type(manifest.get("seed")) is not int:
        raise ValueError("Session seed must be an integer.")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) != 5:
        raise ValueError("Exactly five cases are required.")
    if any(
        not isinstance(case, dict) or type(case.get("id")) is not int for case in cases
    ):
        raise ValueError("Case ids must be integers.")
    if sorted(case["id"] for case in cases) != list(range(1, 6)):
        raise ValueError("Case ids must be exactly 1 through 5.")
    for case in cases:
        for field in ("sha", "before_sha"):
            if not isinstance(case.get(field), str) or not re.fullmatch(
                r"[0-9a-f]{40}", case[field]
            ):
                raise ValueError(f"Case {case['id']} requires a full {field}.")
        _text(case.get("skill_path"), "Skill path", 1000)
    return sorted(cases, key=lambda case: case["id"])


def _atomic_file(path, data, exclusive=False):
    """Publish a fully written private file, never an incomplete submission."""
    fd, name = tempfile.mkstemp(prefix=".quiz-", dir=str(path.parent))
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            os.link(str(temporary), str(path))
        else:
            os.replace(str(temporary), str(path))
    finally:
        temporary.unlink(missing_ok=True)


def freeze_questions(session: Path, manifest: dict) -> None:
    """Validate and shuffle all authored questions before any live results exist."""
    session = _private_session(session)
    cases = _cases(manifest)
    key_path = session / "answer-key.json"
    public = session / "public"
    question_path = public / "questions.json"
    if key_path.exists() or question_path.exists():
        raise ValueError("Questions are already frozen; create a new session instead.")
    for case in cases:
        runs = session / f"case-{case['id']}" / "state" / "runs"
        if runs.exists() and any(runs.iterdir()):
            raise ValueError("Questions must be frozen before any trial results exist.")
    rng = random.Random(manifest["seed"])
    questions = []
    for case in cases:
        question = _json(session / f"case-{case['id']}" / "question.json")
        if not isinstance(question, dict):
            raise ValueError("Question must be an object.")
        stem = _text(question.get("stem"), "Question stem", 1000)
        scope = _text(question.get("scope"), "Question scope", 2000)
        options = question.get("options")
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError("Each question requires exactly four options.")
        checked = []
        for option in options:
            if not isinstance(option, dict) or type(option.get("correct")) is not bool:
                raise ValueError("Each correct flag must be a strict boolean.")
            checked.append(
                {
                    "statement": _text(
                        option.get("statement"), "Option statement", 600
                    ),
                    "correct": option["correct"],
                    "rationale": _text(
                        option.get("rationale"), "Option rationale", 2000
                    ),
                }
            )
        if (
            len(
                {" ".join(option["statement"].split()).casefold() for option in checked}
            )
            != 4
        ):
            raise ValueError("Option statements must be distinct.")
        if sum(option["correct"] for option in checked) != 1:
            raise ValueError("Each question must have exactly one true option.")
        rng.shuffle(checked)
        labeled = [
            dict(option, letter=letter) for letter, option in zip(LETTERS, checked)
        ]
        questions.append(
            {
                "id": case["id"],
                "stem": stem,
                "scope": scope,
                "correct": next(
                    option["letter"] for option in labeled if option["correct"]
                ),
                "commit": case,
                "options": labeled,
            }
        )
    key = {"session_id": manifest["id"], "questions": questions}
    visible = [
        {
            "id": question["id"],
            "stem": question["stem"],
            "options": [
                {"letter": option["letter"], "statement": option["statement"]}
                for option in question["options"]
            ],
        }
        for question in questions
    ]
    public.mkdir(mode=0o700, exist_ok=True)
    _atomic_file(key_path, _bytes(key), exclusive=True)
    try:
        _atomic_file(question_path, _bytes(visible), exclusive=True)
    except Exception:
        key_path.unlink()
        raise


class _Node:
    def __init__(self, tag, attrs=(), children=None):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = [] if children is None else children

    def has_class(self, name):
        return name in self.attrs.get("class", "").split()


VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class _ReportParser(HTMLParser):
    """Minimal tree parser; reject malformed nesting rather than guess a panel."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        if len({name for name, _ in attrs}) != len(attrs):
            raise ValueError("Duplicate report HTML attributes.")
        node = _Node(tag, [(name, value or "") for name, value in attrs])
        # The current saved renderer omits only this wrapper's closing div.
        # Its explicit summary-boundary is the known end of the story; do not
        # apply general browser-style error recovery to unknown structures.
        if (
            tag == "p"
            and node.has_class("summary-boundary")
            and self.stack[-1].has_class("short-story-summary")
            and self.stack[-1].tag == "div"
        ):
            self.stack.pop()
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if len(self.stack) == 1 or self.stack[-1].tag != tag:
            raise ValueError("Unknown or malformed report HTML nesting.")
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def finish(self, source):
        self.feed(source)
        self.close()
        if len(self.stack) != 1:
            raise ValueError("Unclosed report HTML element.")
        return self.root


def _walk(node):
    if isinstance(node, _Node):
        yield node
        for child in node.children:
            yield from _walk(child)


def _children(node):
    return [child for child in node.children if isinstance(child, _Node)]


def _plain(node):
    return "".join(
        _plain(child) if isinstance(child, _Node) else child for child in node.children
    )


def _single(nodes, label):
    if len(nodes) != 1:
        raise ValueError(f"Unknown report shape: expected one {label}.")
    return nodes[0]


def _shape(node, expected):
    children = _children(node)
    if len(children) != len(expected) or any(
        child.tag != tag or (css_class and not child.has_class(css_class))
        for child, (tag, css_class) in zip(children, expected)
    ):
        raise ValueError(f"Unknown summary structure inside {node.tag}.")
    return children


SAFE_TAGS = {
    "section",
    "div",
    "h2",
    "h3",
    "h4",
    "h5",
    "p",
    "strong",
    "em",
    "b",
    "i",
    "ol",
    "ul",
    "li",
    "span",
    "details",
    "summary",
    "br",
    "code",
    "pre",
    "svg",
    "path",
    "circle",
    "rect",
    "line",
    "polyline",
    "polygon",
    "g",
}
SAFE_ATTRS = {
    "class",
    "role",
    "aria-label",
    "aria-hidden",
    "viewbox",
    "width",
    "height",
    "fill",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
    "d",
    "cx",
    "cy",
    "r",
    "x",
    "y",
    "x1",
    "x2",
    "y1",
    "y2",
    "rx",
    "ry",
    "points",
    "transform",
    "focusable",
    "opacity",
}
DROP_CLASSES = {
    "evidence-links",
    "summary-evidence-button",
    "summary-provenance-source",
}


def _safe_fragment(node):
    if isinstance(node, str):
        return html.escape(node)
    if node.tag in {
        "nav",
        "script",
        "style",
        "link",
        "iframe",
        "object",
        "embed",
        "img",
    }:
        return ""
    if DROP_CLASSES.intersection(node.attrs.get("class", "").split()):
        return ""
    if node.tag == "a":
        # Evidence navigation carries source/instruction references, not report claims.
        return ""
    if node.tag not in SAFE_TAGS:
        raise ValueError(f"Unknown summary element: {node.tag}.")
    if any(
        re.search(r"url\s*\(|javascript:|data:", value, re.I)
        for name, value in node.attrs.items()
        if name in SAFE_ATTRS
    ):
        raise ValueError("Unsupported resource in summary attributes.")
    attrs = "".join(
        f' {name}="{html.escape(value, quote=True)}"'
        for name, value in node.attrs.items()
        if name in SAFE_ATTRS
    )
    # SVG attribute names are case-sensitive in XML; preserve the renderer's viewBox.
    attrs = attrs.replace(" viewbox=", " viewBox=")
    body = "".join(_safe_fragment(child) for child in node.children)
    return f"<{node.tag}{attrs}>" + ("" if node.tag in VOID else f"{body}</{node.tag}>")


def _blinded_report(source):
    root = _ReportParser().finish(source)
    nodes = list(_walk(root))
    panel = _single(
        [node for node in nodes if node.attrs.get("id") == "panel-summary"],
        "Summary panel",
    )
    if panel.tag != "section" or not panel.has_class("panel"):
        raise ValueError("Unknown Summary panel container.")
    direct = _children(panel)
    story = _single(
        [node for node in direct if node.has_class("short-story-summary")],
        "summary story",
    )
    if (
        len(direct) != 5
        or direct[0] is not story
        or direct[1].tag != "p"
        or not direct[1].has_class("summary-boundary")
    ):
        raise ValueError("Unknown Summary panel sections.")
    details = direct[2:]
    if any(
        node.tag != "details" or not node.has_class("summary-details")
        for node in details
    ):
        raise ValueError("Unknown Summary disclosures.")
    headings = [
        _single(
            [node for node in _children(detail) if node.tag == "summary"],
            "disclosure heading",
        )
        for detail in details
    ]
    if (
        _plain(headings[0]).strip() != "Full scenario and expected behavior"
        or _plain(headings[1]).strip() != "Other findings"
    ):
        raise ValueError("Unknown Summary disclosure order.")
    if not any(node.has_class("evidence-limits") for node in _walk(details[2])):
        raise ValueError("Missing evidence limits.")
    story_children = _children(story)
    if (
        len(story_children) != 2
        or story_children[0].tag != "h2"
        or not story_children[0].has_class("summary-headline")
        or story_children[1].tag != "ol"
        or not story_children[1].has_class("story-steps")
    ):
        raise ValueError("Unknown summary story structure.")
    steps = _children(story_children[1])
    if len(steps) != 3 or any(
        node.tag != "li" or not node.has_class("story-step") for node in steps
    ):
        raise ValueError("Unknown story steps.")
    if not any(node.has_class("intent-heading") for node in _walk(steps[0])):
        raise ValueError("Unknown intended-change step.")
    bodies = [
        _shape(step, [("span", "story-number"), ("div", "story-body")])[1]
        for step in steps
    ]
    evidence_shape = [("h3", None)]
    if any(node.has_class("summary-context") for node in _children(bodies[1])):
        evidence_shape.append(("p", "summary-context"))
    evidence_shape.extend(
        [
            ("p", "summary-provenance"),
            ("p", "summary-status"),
            ("div", "summary-pair"),
        ]
    )
    if any(node.has_class("primary-result-context") for node in _children(bodies[1])):
        evidence_shape.append(("section", "primary-result-context"))
    evidence_shape.append(("nav", "evidence-nav"))
    evidence_body = _shape(bodies[1], evidence_shape)
    if _plain(evidence_body[0]) != "What the evidence shows":
        raise ValueError("Unknown evidence heading.")
    pair = _single(
        [node for node in evidence_body if node.has_class("summary-pair")],
        "summary pair",
    )
    cards = _shape(
        pair,
        [
            ("section", "summary-before"),
            ("span", "summary-arrow"),
            ("section", "summary-after"),
        ],
    )
    for card in (cards[0], cards[2]):
        children = _children(card)
        empty = bool(children and children[-1].has_class("summary-empty"))
        _shape(
            card,
            [
                ("h4", "summary-side-label"),
                ("svg", "summary-picture"),
                ("p", "summary-empty") if empty else ("ul", "summary-choices"),
            ],
        )
    meaning_shape = [("h3", None)]
    for css_class in ("summary-why", "summary-caution"):
        if any(node.has_class(css_class) for node in _children(bodies[2])):
            meaning_shape.append(("div", css_class))
    meaning_shape.append(("ul", "summary-notices"))
    meaning = _shape(bodies[2], meaning_shape)
    if _plain(meaning[0]) != "What this means":
        raise ValueError("Unknown meaning heading.")
    for claim in meaning[1:-1]:
        _shape(claim, [("strong", None), ("p", None), ("span", "evidence-links")])
    findings_shape = [("summary", None)]
    if any(node.has_class("other-findings") for node in _children(details[1])):
        findings_shape.append(("ul", "other-findings"))
    findings_shape.extend([("p", "note"), ("nav", "evidence-nav")])
    _shape(details[1], findings_shape)
    _shape(details[2], [("summary", None), ("ul", "evidence-limits")])
    # Remove the entire intent step and full scenario disclosure. Retain the renderer's
    # exact generated text for headline, evidence, cards, meaning, findings and limits.
    trimmed_story = _Node(
        story.tag,
        story.attrs.items(),
        [story_children[0], _Node("ol", story_children[1].attrs.items(), steps[1:])],
    )
    fragment = "".join(
        _safe_fragment(node)
        for node in (trimmed_story, direct[1], details[1], details[2])
    )
    styles = [node for node in nodes if node.tag == "style"]
    css = _plain(_single(styles, "inline report stylesheet"))
    if re.search(r"url\s*\(|@import|expression\s*\(|</style|\\", css, re.I):
        raise ValueError("Report stylesheet contains unsupported resources or escapes.")
    # Only the saved stylesheet is used, never the current renderer implementation.
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Blinded Behavior Diff summary</title><style>"
        + css
        + "\nbody{padding:1rem;max-width:100%;}.story-number{display:none}"
        ".story-steps{list-style:none}.story-step{display:block}.panel{display:block}</style></head><body>"
        + fragment
        + "</body></html>"
    )


def _load_key(session, manifest):
    key = _json(session / "answer-key.json")
    cases = _cases(manifest)
    if not isinstance(key, dict) or key.get("session_id") != manifest["id"]:
        raise ValueError("Answer key belongs to a different session.")
    questions = key.get("questions")
    if not isinstance(questions, list) or len(questions) != 5:
        raise ValueError("Invalid answer key.")
    for question, case in zip(questions, cases):
        if (
            not isinstance(question, dict)
            or question.get("id") != case["id"]
            or question.get("commit") != case
        ):
            raise ValueError("Answer key case provenance does not match the session.")
        _text(question.get("stem"), "Question stem", 1000)
        _text(question.get("scope"), "Question scope", 2000)
        options = question.get("options")
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError("Invalid frozen options.")
        for option, letter in zip(options, LETTERS):
            if (
                not isinstance(option, dict)
                or option.get("letter") != letter
                or type(option.get("correct")) is not bool
            ):
                raise ValueError("Invalid frozen option labels or flags.")
            _text(option.get("statement"), "Option statement", 600)
            _text(option.get("rationale"), "Option rationale", 2000)
        if (
            len(
                {" ".join(option["statement"].split()).casefold() for option in options}
            )
            != 4
        ):
            raise ValueError("Frozen option statements must be distinct.")
        correct = [option["letter"] for option in options if option["correct"]]
        if len(correct) != 1 or question.get("correct") != correct[0]:
            raise ValueError("Invalid frozen correct answer.")
    return key


def build_quiz(session: Path, repo_root: Path) -> None:
    """Build only from real saved reports, keeping source and answer key private."""
    session = _private_session(session)
    manifest = _json(session / "session.json")
    key = _load_key(session, manifest)
    if Path(repo_root).resolve() != Path(manifest["code"]["root"]).resolve():
        raise ValueError("Build checkout does not match session provenance.")
    public = session / "public"
    visible = [
        {
            "id": question["id"],
            "stem": question["stem"],
            "options": [
                {"letter": option["letter"], "statement": option["statement"]}
                for option in question["options"]
            ],
        }
        for question in key["questions"]
    ]
    if _json(public / "questions.json") != visible:
        raise ValueError("Public questions do not match the frozen answer key.")
    files = {
        name: (ASSETS / name).read_bytes()
        for name in ("index.html", "quiz.js", "quiz.css")
    }
    reports = {}
    for case in _cases(manifest):
        case_id = case["id"]
        runs = session / f"case-{case_id}" / "state" / "runs"
        candidates = (
            sorted(path for path in runs.iterdir() if path.is_dir())
            if runs.is_dir()
            else []
        )
        if len(candidates) != 1:
            raise ValueError(
                f"Case {case_id} requires exactly one saved run; found {len(candidates)}."
            )
        run = candidates[0]
        record = {}
        for name in ("report.html", "report.md", "decisions.json", "report-data.json"):
            path = run / name
            if name == "decisions.json" and not path.exists() and not path.is_symlink():
                record[name] = {
                    "path": str(path.relative_to(session)),
                    "sha256": None,
                    "availability": "unavailable",
                }
                continue
            if (
                path.is_symlink()
                or not path.is_file()
                or session not in path.resolve().parents
            ):
                raise ValueError(
                    f"Missing or nonlocal private report: case {case_id}/{name}."
                )
            data = path.read_bytes()
            if not data:
                raise ValueError(f"Empty private report: case {case_id}/{name}.")
            if name.endswith(".json"):
                json.loads(data)
            record[name] = {
                "path": str(path.relative_to(session)),
                "sha256": _hash(data),
            }
            if name == "report.html":
                files[f"summary-{case_id}.html"] = _blinded_report(
                    data.decode("utf-8")
                ).encode("utf-8")
        reports[str(case_id)] = record
    files["session-public.json"] = _bytes(
        {"session_id": manifest["id"], "case_count": 5}
    )
    # Validate every input before changing any public build output.
    for name, data in files.items():
        _atomic_file(public / name, data)
    hashes = {name: _hash(data) for name, data in files.items()}
    hashes["questions.json"] = _hash((public / "questions.json").read_bytes())
    receipt = {
        "schema_version": 1,
        "session_id": manifest["id"],
        "public": hashes,
        "reports": reports,
        "answer_key_sha256": _hash((session / "answer-key.json").read_bytes()),
        "session_sha256": _hash((session / "session.json").read_bytes()),
        "summary_method": "saved-html-summary-panel-v1",
    }
    _atomic_file(session / "quiz-build.json", _bytes(receipt))


def _load_build(session):
    manifest = _json(session / "session.json")
    key = _load_key(session, manifest)
    receipt = _json(session / "quiz-build.json")
    if (
        receipt.get("schema_version") != 1
        or receipt.get("session_id") != manifest["id"]
    ):
        raise ValueError("Invalid quiz build identity.")
    for filename, field in (
        ("answer-key.json", "answer_key_sha256"),
        ("session.json", "session_sha256"),
    ):
        if _hash((session / filename).read_bytes()) != receipt.get(field):
            raise ValueError(f"Quiz build input changed: {filename}.")
    expected = {
        "index.html",
        "quiz.js",
        "quiz.css",
        "questions.json",
        "session-public.json",
    } | {f"summary-{number}.html" for number in range(1, 6)}
    if set(receipt.get("public", {})) != expected:
        raise ValueError("Invalid public asset allowlist.")
    files = {}
    for name, digest in receipt["public"].items():
        path = session / "public" / name
        if path.is_symlink() or session not in path.resolve().parents:
            raise ValueError("Nonlocal quiz asset.")
        data = path.read_bytes()
        if _hash(data) != digest:
            raise ValueError(f"Quiz asset changed: {name}.")
        files["/" + name] = data
    if set(receipt.get("reports", {})) != {str(number) for number in range(1, 6)}:
        raise ValueError("Invalid report allowlist.")
    reviews = {}
    for case_id, reports in receipt["reports"].items():
        if set(reports) != {
            "report.html",
            "report.md",
            "decisions.json",
            "report-data.json",
        }:
            raise ValueError("Incomplete private report receipt.")
        for name, record in reports.items():
            path = session / record["path"]
            if path.is_symlink() or session not in path.resolve().parents:
                raise ValueError("Nonlocal private report.")
            if name == "decisions.json" and record.get("sha256") is None:
                if (
                    path.exists()
                    or path.is_symlink()
                    or record.get("availability") != "unavailable"
                ):
                    raise ValueError("Unavailable extraction changed after quiz build.")
                continue
            data = path.read_bytes()
            if _hash(data) != record["sha256"]:
                raise ValueError("Private report changed after quiz build.")
            if name == "report.html":
                reviews["/review/" + case_id] = data
    return manifest, key, files, reviews


def _validate_submission(payload, session_id):
    if (
        not isinstance(payload, dict)
        or set(payload) != {"session_id", "answers"}
        or payload["session_id"] != session_id
    ):
        raise ValueError("Submission session identity is missing or incorrect.")
    answers = payload["answers"]
    if not isinstance(answers, list) or len(answers) != 5:
        raise ValueError("Complete all five questions before submitting.")
    checked = []
    for answer in answers:
        if (
            not isinstance(answer, dict)
            or not {"id", "letter", "confidence", "insufficient"} <= set(answer)
            or set(answer) - {"id", "letter", "confidence", "insufficient", "note"}
        ):
            raise ValueError("Invalid answer fields.")
        if type(answer["id"]) is not int or answer["id"] not in range(1, 6):
            raise ValueError("Invalid case id.")
        if (
            not isinstance(answer["letter"], str)
            or answer["letter"] not in LETTERS
            or len(answer["letter"]) != 1
        ):
            raise ValueError("Choose exactly one option per question.")
        if answer["confidence"] not in ("low", "medium", "high"):
            raise ValueError("Confidence is required for each question.")
        if type(answer["insufficient"]) is not bool:
            raise ValueError("Insufficient-evidence flag must be a boolean.")
        note = answer.get("note", "")
        if not isinstance(note, str) or len(note) > 2000:
            raise ValueError("Notes must be text of at most 2000 characters.")
        checked.append(dict(answer, note=note))
    if sorted(answer["id"] for answer in checked) != list(range(1, 6)):
        raise ValueError("Answer each case exactly once.")
    return {
        "session_id": session_id,
        "answers": sorted(checked, key=lambda answer: answer["id"]),
    }


def _score(key, submission):
    submission = _validate_submission(
        {name: submission[name] for name in ("session_id", "answers")},
        key["session_id"],
    )
    answers = []
    for question, answer in zip(key["questions"], submission["answers"]):
        selected = next(
            option
            for option in question["options"]
            if option["letter"] == answer["letter"]
        )
        sha = question["commit"]["sha"]
        before = question["commit"]["before_sha"]
        answers.append(
            dict(
                answer,
                correct=answer["letter"] == question["correct"],
                correct_letter=question["correct"],
                statement=selected["statement"],
                rationale=selected["rationale"],
                scope=question["scope"],
                sufficient_evidence=not answer["insufficient"],
                options=question["options"],
                commit=question["commit"],
                source_url=f"https://github.com/DataRecce/recce-team/commit/{sha}",
                before_source_url=f"https://github.com/DataRecce/recce-team/commit/{before}",
                review_url=f"/review/{question['id']}",
            )
        )
    return {
        "session_id": key["session_id"],
        "score": {"correct": sum(answer["correct"] for answer in answers), "total": 5},
        "answers": answers,
        "interpretation": "This is one person's comprehension score for five sampled cases, not overall model accuracy or proof of effectiveness.",
    }


def results(session: Path) -> dict:
    session = _private_session(session)
    _, key, _, _ = _load_build(session)
    path = session / "submission.json"
    if not path.is_file():
        raise ValueError("Results are available only after a complete submission.")
    saved = _json(path)
    result = _score(key, saved)
    result["submitted_at"] = saved["submitted_at"]
    return result


def make_server(session: Path, port: int = 0):
    """Create a bound server, also usable by deterministic integration tests."""
    session = _private_session(session)
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("Port must be an integer from 0 to 65535.")
    manifest, key, files, reviews = _load_build(session)
    submission_path = session / "submission.json"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def _reply(
            self,
            status,
            data,
            content_type="application/json; charset=utf-8",
            report=False,
        ):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            policy = (
                "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; frame-ancestors 'self'"
                if report
                else "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; frame-src 'self'; connect-src 'self'; frame-ancestors 'self'"
            )
            self.send_header(
                "Content-Security-Policy",
                policy + "; base-uri 'none'; form-action 'self'",
            )
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)
            self.close_connection = True

        def _error(self, status, message):
            self._reply(status, _bytes({"error": message}))

        def _security(self, submission=False):
            authority = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get_all("Host", []) != [authority]:
                self._error(403, "Host is not this loopback evaluation server.")
                return False
            origins = self.headers.get_all("Origin", [])
            if (origins and origins != ["http://" + authority]) or (
                submission and not origins
            ):
                self._error(403, "Only same-origin requests are accepted.")
                return False
            if self.headers.get("Sec-Fetch-Site") not in (None, "none", "same-origin"):
                self._error(403, "Cross-origin requests are denied.")
                return False
            return True

        def _saved_result(self):
            saved = _json(submission_path)
            result = _score(key, saved)
            result["submitted_at"] = saved["submitted_at"]
            return result

        def do_GET(self):
            if not self._security():
                return
            path = "/index.html" if self.path == "/" else self.path
            if path == "/results":
                if not submission_path.is_file():
                    self._error(403, "Submit all answers before viewing results.")
                else:
                    self._reply(200, _bytes(self._saved_result()))
            elif path in reviews:
                if not submission_path.is_file():
                    self._error(403, "Full reports remain private until submission.")
                else:
                    self._reply(
                        200, reviews[path], "text/html; charset=utf-8", report=True
                    )
            elif path in files:
                suffix = Path(path).suffix
                content_type = {
                    ".html": "text/html; charset=utf-8",
                    ".js": "text/javascript; charset=utf-8",
                    ".css": "text/css; charset=utf-8",
                    ".json": "application/json; charset=utf-8",
                }[suffix]
                self._reply(200, files[path], content_type)
            else:
                self._error(404, "Resource is not in the public allowlist.")

        def do_POST(self):
            if not self._security(submission=True):
                return
            if self.path != "/submit":
                self._error(404, "Unknown submission endpoint.")
                return
            if (
                self.headers.get_all("Content-Type", []) != ["application/json"]
                or self.headers.get("Transfer-Encoding") is not None
            ):
                self._error(415, "Use application/json without transfer encoding.")
                return
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or not re.fullmatch(r"[0-9]+", lengths[0]):
                self._error(411, "A valid Content-Length is required.")
                return
            length = int(lengths[0])
            if not 1 <= length <= MAX_BODY:
                self._error(413, "Submission body size is invalid.")
                return
            try:
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError("Incomplete request body.")
                if submission_path.is_file():
                    self._reply(200, _bytes(self._saved_result()))
                    return
                payload = _validate_submission(json.loads(raw), manifest["id"])
                payload["submitted_at"] = datetime.now(timezone.utc).isoformat()
                try:
                    _atomic_file(submission_path, _bytes(payload), exclusive=True)
                except FileExistsError:
                    pass  # Another complete first submission won the atomic publication.
                self._reply(200, _bytes(self._saved_result()))
            except (ValueError, KeyError, UnicodeError) as exc:
                self._error(400, str(exc))

        def do_OPTIONS(self):
            if self._security():
                self._error(405, "Cross-origin access is not supported.")

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    # A stalled body must not occupy a request thread indefinitely.
    original_get_request = server.get_request

    def get_request():
        connection, address = original_get_request()
        connection.settimeout(10)
        return connection, address

    server.get_request = get_request
    return server


def serve(session: Path, port: int) -> None:
    with make_server(session, port) as server:
        print(f"http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
