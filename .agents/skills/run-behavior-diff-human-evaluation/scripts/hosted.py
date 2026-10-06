"""Saved-evidence package v1 and private hosted-response analysis; no network."""

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat

CASE_IDS = [f"case-{number}" for number in range(1, 6)]
LETTERS = list("ABCD")
PRODUCER_VERSION = "behavior-diff-hosted-export-v1"
SUMMARY_LIMIT = 256 * 1024
PACKAGE_LIMIT = 2 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")


def text(value, label, maximum, nonblank=True):
    require(
        isinstance(value, str)
        and len(value) <= maximum
        and (not nonblank or value.strip()),
        f"Invalid {label}",
    )
    # Reject lone surrogates, which cannot be represented in the package's UTF-8.
    value.encode("utf-8")
    return value


def safe_path(path):
    path = Path(os.path.abspath(str(Path(path).expanduser())))
    for component in (path, *path.parents):
        require(not component.is_symlink(), f"Symlink path is unsafe: {component}")
    return path


def outside_trees(path, repo_root):
    path = safe_path(path)
    for root in (
        Path(repo_root).resolve(),
        Path(repo_root).parent / "behavior-diff-evaluation",
    ):
        root = root.resolve()
        require(
            path != root and root not in path.parents and path not in root.parents,
            "Hosted artifacts must be outside both working trees",
        )
    return path


def read_json(path):
    path = safe_path(path)
    require(
        path.is_file() and stat.S_ISREG(path.stat().st_mode),
        f"Not a regular file: {path}",
    )

    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(path.read_bytes().decode("utf-8"), object_pairs_hook=unique)


def exclusive_file(path, data):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink()
        raise


def saved_content(session, quiz):
    manifest, key, saved, reviews = quiz._load_build(session)
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
    require(
        json.loads(saved["/questions.json"]) == visible,
        "Saved questions differ from frozen key",
    )
    questions = []
    summaries = {}
    for question, case_id in zip(key["questions"], CASE_IDS):
        questions.append(
            {
                "id": case_id,
                "stem": text(question["stem"], "stem", 2000),
                "options": [
                    {
                        "id": option["letter"],
                        "text": text(option["statement"], "option", 2000),
                    }
                    for option in question["options"]
                ],
                "correctOption": question["correct"],
            }
        )
        number = question["id"]
        data = saved[f"/summary-{number}.html"]
        # Check the original projection as well as the saved receipt; ship the saved bytes.
        require(
            quiz._blinded_report(reviews[f"/review/{number}"].decode("utf-8")).encode(
                "utf-8"
            )
            == data,
            f"Saved blinded summary differs from original report: {case_id}",
        )
        data.decode("utf-8")
        require(len(data) <= SUMMARY_LIMIT, f"Summary too large: {case_id}")
        summaries[f"summaries/{case_id}.html"] = data
    return manifest, key, questions, summaries


def package_content(
    session, quiz, evaluation_id, title, producer_version=PRODUCER_VERSION
):
    require(
        isinstance(evaluation_id, str)
        and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", evaluation_id),
        "Invalid evaluation ID",
    )
    text(title, "title", 200)
    text(producer_version, "producer version", 120)
    source, key, questions, files = saved_content(session, quiz)
    files["questions.json"] = json_bytes(questions)
    require(len(files["questions.json"]) <= 64 * 1024, "Questions too large")
    hashes = {name: digest(data) for name, data in files.items()}
    hashes["questions.json"] = digest(canonical(questions))
    manifest = {
        "schemaVersion": 1,
        "evaluationId": evaluation_id,
        "title": title,
        "caseIds": CASE_IDS,
        "producerVersion": producer_version,
        "files": hashes,
    }
    files["manifest.json"] = json_bytes(manifest)
    require(len(files["manifest.json"]) <= 16 * 1024, "Manifest too large")
    require(sum(map(len, files.values())) <= PACKAGE_LIMIT, "Package too large")
    return manifest, files, source, key


def export_package(session, quiz, repo_root, evaluation_id, title, out):
    """The CLI verifies frozen inputs before entering this operation."""
    session = safe_path(session)
    destination = outside_trees(out, repo_root)
    require(
        not destination.exists(), "Package destination already exists; never overwrite"
    )
    require(destination.parent.is_dir(), "Package parent directory must already exist")
    require(
        destination != session
        and session not in destination.parents
        and destination not in session.parents,
        "Package must be separate from private session provenance",
    )
    manifest, files, source, _ = package_content(session, quiz, evaluation_id, title)
    mapping_directory = safe_path(session / "hosted-exports")
    mapping_path = mapping_directory / f"{evaluation_id}.json"
    require(
        not mapping_path.exists(), "Evaluation ID already exported from this session"
    )
    provenance = {
        "schemaVersion": 1,
        "evaluationId": evaluation_id,
        "contentHash": digest(canonical(manifest)),
        "manifest": manifest,
        "packagePath": str(destination),
        "sessionId": source["id"],
        "sessionPath": str(session),
        "answerKeySha256": digest((session / "answer-key.json").read_bytes()),
        "quizBuildSha256": digest((session / "quiz-build.json").read_bytes()),
        "cases": source["cases"],
    }
    mapping_directory.mkdir(mode=0o700, exist_ok=True)
    destination.mkdir(mode=0o700)
    mapping_created = False
    try:
        (destination / "summaries").mkdir(mode=0o700)
        for name, data in files.items():
            exclusive_file(destination / name, data)
        exclusive_file(mapping_path, json_bytes(provenance))
        mapping_created = True
    except BaseException:
        # Only remove the fresh destination owned by this invocation.
        shutil.rmtree(destination)
        if mapping_created:
            mapping_path.unlink()
        raise
    return {
        "evaluationId": evaluation_id,
        "contentHash": provenance["contentHash"],
        "packagePath": str(destination),
        "privateMappingPath": str(mapping_path),
        "publicationAuthorized": False,
    }


def verify_package(session, quiz, repo_root, package):
    package = outside_trees(package, repo_root)
    require(package.is_dir(), "Package directory does not exist")
    manifest = read_json(package / "manifest.json")
    require(isinstance(manifest, dict), "Invalid package manifest")
    expected, data, source, key = package_content(
        session,
        quiz,
        manifest.get("evaluationId"),
        manifest.get("title"),
        manifest.get("producerVersion"),
    )
    require(
        type(manifest.get("schemaVersion")) is int and manifest == expected,
        "Package manifest does not match saved evidence",
    )
    found = set()
    for directory, dirs, names in os.walk(package, followlinks=False):
        for name in dirs:
            child = safe_path(Path(directory) / name)
            require(
                child.relative_to(package).as_posix() == "summaries",
                "Unexpected package directory",
            )
        for name in names:
            child = safe_path(Path(directory) / name)
            require(stat.S_ISREG(child.stat().st_mode), "Nonregular package entry")
            found.add(child.relative_to(package).as_posix())
    require(found == set(data), "Unexpected or missing package entries")
    for name, original in data.items():
        actual = (package / name).read_bytes()
        if name in ("manifest.json", "questions.json"):
            require(
                read_json(package / name) == json.loads(original),
                f"Package JSON differs: {name}",
            )
        else:
            require(actual == original, f"Package summary differs: {name}")
        require(
            len(actual)
            <= (
                SUMMARY_LIMIT
                if name.endswith(".html")
                else 64 * 1024
                if name == "questions.json"
                else 16 * 1024
            ),
            f"Oversize package entry: {name}",
        )
    require(
        sum((package / name).stat().st_size for name in data) <= PACKAGE_LIMIT,
        "Package too large",
    )
    mapping = read_json(
        safe_path(session) / "hosted-exports" / f"{expected['evaluationId']}.json"
    )
    require(
        mapping.get("sessionId") == source["id"]
        and mapping.get("manifest") == expected
        and mapping.get("contentHash") == digest(canonical(expected))
        and mapping.get("answerKeySha256")
        == digest((session / "answer-key.json").read_bytes())
        and mapping.get("quizBuildSha256")
        == digest((session / "quiz-build.json").read_bytes()),
        "Private export provenance does not match frozen session/package",
    )
    return expected, key


def timestamp(value, label):
    text(value, label, 80)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid {label}") from exc
    require(parsed.tzinfo is not None, f"{label} must include timezone")


def analyze_responses(session, quiz, repo_root, package, responses):
    """Recompute every raw response against the original saved key, without writes."""
    manifest, key = verify_package(session, quiz, repo_root, package)
    response_path = outside_trees(responses, repo_root)
    exported = read_json(response_path)
    fields = {
        "schemaVersion",
        "evaluationId",
        "contentHash",
        "manifest",
        "exportedAt",
        "responses",
    }
    require(
        isinstance(exported, dict) and set(exported) == fields,
        "Invalid hosted response export fields",
    )
    content_hash = digest(canonical(manifest))
    require(
        type(exported["schemaVersion"]) is int
        and exported["schemaVersion"] == 1
        and exported["evaluationId"] == manifest["evaluationId"]
        and exported["contentHash"] == content_hash
        and isinstance(exported["manifest"], dict)
        and type(exported["manifest"].get("schemaVersion")) is int
        and exported["manifest"] == manifest,
        "Hosted response export identity differs from frozen package",
    )
    timestamp(exported["exportedAt"], "export time")
    require(isinstance(exported["responses"], list), "Responses must be an array")
    results, uids, respondents = [], set(), {}
    submission_fields = {
        "schemaVersion",
        "evaluationId",
        "respondent",
        "contentHash",
        "siteBuild",
        "answers",
        "confidence",
        "insufficientEvidence",
        "notes",
        "clientScore",
        "submittedAt",
    }
    for response in exported["responses"]:
        require(
            isinstance(response, dict)
            and set(response) == {"uid", "submission", "recomputedScore"},
            "Invalid response record",
        )
        uid = text(response["uid"], "UID", 128)
        require(uid not in uids, "Duplicate UID in response export")
        uids.add(uid)
        submission = response["submission"]
        require(
            isinstance(submission, dict) and set(submission) == submission_fields,
            "Invalid submission fields",
        )
        require(
            type(submission["schemaVersion"]) is int
            and submission["schemaVersion"] == 1
            and submission["evaluationId"] == manifest["evaluationId"]
            and submission["contentHash"] == content_hash,
            "Submission identity differs from package",
        )
        respondent = text(submission["respondent"], "respondent", 200)
        require(respondent == respondent.strip(), "Respondent must be trimmed")
        text(submission["siteBuild"], "site build", 120)
        timestamp(submission["submittedAt"], "submission time")
        require(
            type(submission["clientScore"]) is int
            and 0 <= submission["clientScore"] <= 5,
            "Invalid client score",
        )
        require(
            type(response["recomputedScore"]) is int
            and 0 <= response["recomputedScore"] <= 5,
            "Invalid exported score",
        )
        for field in ("answers", "confidence", "insufficientEvidence", "notes"):
            require(
                isinstance(submission[field], dict)
                and set(submission[field]) == set(CASE_IDS),
                f"Incomplete {field} map",
            )
        local_answers = []
        for number, case_id in enumerate(CASE_IDS, 1):
            require(submission["answers"][case_id] in LETTERS, "Invalid option ID")
            require(
                submission["confidence"][case_id] in ("low", "medium", "high"),
                "Invalid confidence",
            )
            require(
                type(submission["insufficientEvidence"][case_id]) is bool,
                "Invalid evidence flag",
            )
            text(submission["notes"][case_id], "note", 2000, nonblank=False)
            local_answers.append(
                {
                    "id": number,
                    "letter": submission["answers"][case_id],
                    "confidence": submission["confidence"][case_id],
                    "insufficient": submission["insufficientEvidence"][case_id],
                    "note": submission["notes"][case_id],
                }
            )
        scored = quiz._score(
            key, {"session_id": key["session_id"], "answers": local_answers}
        )
        score = scored["score"]["correct"]
        results.append(
            {
                "uid": uid,
                "original": response,
                "keyedResult": scored,
                "clientScoreMatches": submission["clientScore"] == score,
                "exportedScoreMatches": response["recomputedScore"] == score,
                "insufficientEvidenceCount": sum(
                    submission["insufficientEvidence"].values()
                ),
            }
        )
        respondents.setdefault(respondent.casefold(), []).append(uid)
    return {
        "schemaVersion": 1,
        "evaluationId": manifest["evaluationId"],
        "contentHash": content_hash,
        "sourceExport": {
            "path": str(response_path),
            "sha256": digest(response_path.read_bytes()),
        },
        "responseCount": len(results),
        "responses": results,
        "duplicateRespondents": [
            {"respondent": name, "uids": sorted(group)}
            for name, group in sorted(respondents.items())
            if len(group) > 1
        ],
        "questionValidity": [
            {
                "id": case_id,
                "status": "not-assessed",
                "savedSummary": f"public/summary-{number}.html",
                "privateEvidence": f"case-{number}/",
                "requiredAssessment": ["observed contrast", "summary exposure"],
            }
            for number, case_id in enumerate(CASE_IDS, 1)
        ],
        "interpretation": "Original keyed scores are retained for every UID. Duplicate names are advisory, not verified identity; never merge. Independently assess all five cases against saved source sides, scenario, trials, and blinded summaries. Keep validity separate; never alter keys, exclude weak cases, or revise the denominator. Five cases do not estimate product accuracy.",
    }
