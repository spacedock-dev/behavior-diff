#!/usr/bin/env python3
"""Prototype: project fixed local evidence onto owner-confirmed, mutable goals."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    require(isinstance(value, str) and bool(value.strip()), "Expected nonblank text")
    return value


def goals(value):
    require(isinstance(value, list) and bool(value), "Supply at least one goal")
    result = []
    for goal in value:
        require(isinstance(goal, dict), "Expected goal object")
        require(
            set(goal) == {"id", "text", "basis", "reference", "next"},
            "Invalid goal fields",
        )
        require(goal["basis"] in ("explicit", "inferred"), "Invalid goal provenance")
        result.append({key: text(item) for key, item in goal.items()})
    require(len({g["id"] for g in result}) == len(result), "Duplicate goal id")
    return result


def citation(root, value):
    require(
        isinstance(value, dict) and set(value) == {"path", "start", "end"},
        "Invalid citation",
    )
    relative = Path(text(value["path"]))
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "Citation must stay inside case root",
    )
    path = (root / relative).resolve()
    require(path.is_relative_to(root) and path != root, "Citation escapes case root")
    start, end = value["start"], value["end"]
    require(
        type(start) is int and type(end) is int and 1 <= start <= end < start + 120,
        "Invalid line range (maximum 120)",
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    require(
        end <= len(lines),
        "Citation lines missing; supply an existing scoped coordinate",
    )
    excerpt = "\n".join(
        f"{index + 1}: {lines[index]}" for index in range(start - 1, end)
    )
    return {
        **value,
        "excerpt": excerpt,
        "digest": hashlib.sha256(excerpt.encode()).hexdigest(),
    }


def project(state, root):
    rows = []
    for goal in state["goals"]:
        row = {
            **goal,
            "status": "unverified",
            "reason": "No reviewed evidence for this exact goal",
            "citations": [],
        }
        binding = state["bindings"].get(goal["id"])
        if binding:
            try:
                for saved in binding["citations"]:
                    current = citation(
                        root, {key: saved[key] for key in ("path", "start", "end")}
                    )
                    require(
                        current["digest"] == saved["digest"],
                        "Cited evidence changed; review and rebind",
                    )
                row.update(binding)
            except (ValueError, OSError, UnicodeError) as error:
                row["reason"] = f"Evidence gap: {error}"
        rows.append(row)
    return {
        "revision": state["revision"],
        "mode": "fixed-evidence replay; no fresh execution",
        "goals": rows,
    }


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def apply(state, action, root):
    op = action.get("action")
    fields = {
        "init": {"goals"},
        "show": set(),
        "correct": {"id", "text"},
        "replace": {"goals"},
        "bind": {"id", "status", "origin", "reason", "scope", "citations"},
        "confirm": set(),
        "result": set(),
        "evidence": {"citation"},
        "decide": {"choice"},
    }
    require(op in fields, "Unknown action")
    expected = (
        {"action"} | fields[op] | (set() if op in ("init", "show") else {"revision"})
    )
    require(set(action) == expected, "Invalid action fields")
    if op == "init":
        require(state is None, "Session already exists")
        state = {
            "revision": 1,
            "root": str(root),
            "goals": goals(action["goals"]),
            "bindings": {},
            "confirmed": None,
            "result": None,
            "decision": None,
        }
    else:
        require(state is not None, "Initialize a private session first")
        require(state["root"] == str(root), "Case root differs from session")
        if op == "show":
            return state, state
        require(
            type(action["revision"]) is int and action["revision"] == state["revision"],
            "Stale revision; show current session before retrying",
        )
        if op in ("correct", "bind"):
            goal = next((g for g in state["goals"] if g["id"] == action["id"]), None)
            require(goal is not None, "Unknown goal id")
        if op == "correct":
            corrected = text(action["text"])
            if corrected != goal["text"]:
                goal.update(
                    text=corrected,
                    basis="explicit",
                    reference="Current conversation: owner correction",
                )
                state["bindings"].pop(goal["id"], None)
                state["revision"] += 1
                state.update(confirmed=None, result=None, decision=None)
        elif op == "replace":
            state.update(
                goals=goals(action["goals"]),
                bindings={},
                revision=state["revision"] + 1,
                confirmed=None,
                result=None,
                decision=None,
            )
        elif op == "bind":
            require(
                action["status"] in ("supported", "contradicted"),
                "Invalid observation status",
            )
            require(
                action["origin"] in ("reused", "synthetic"),
                "Evidence must be labeled reused or synthetic",
            )
            require(
                isinstance(action["citations"], list) and bool(action["citations"]),
                "Reviewed support requires citations",
            )
            sources = [citation(root, item) for item in action["citations"]]
            state["bindings"][goal["id"]] = {
                "status": action["status"],
                "origin": action["origin"],
                "reason": text(action["reason"]),
                "scope": text(action["scope"]),
                "citations": sources,
            }
            state.update(result=None, decision=None)
        elif op == "confirm":
            state["confirmed"] = state["revision"]
        elif op in ("result", "decide"):
            require(
                state["confirmed"] == state["revision"],
                "Confirm current goals before results",
            )
            result = project(state, root)
            if op == "result":
                state["result"] = fingerprint(result)
                return state, result
            require(
                state["result"] == fingerprint(result),
                "View current result before deciding",
            )
            require(
                action["choice"] in ("accept", "revise", "request-verification"),
                "Invalid decision",
            )
            state["decision"] = action["choice"]
        elif op == "evidence":
            return state, citation(root, action["citation"])
    return state, state


def private_state(path):
    require(not path.is_symlink(), "State must not be a symlink")
    parent = path.parent.resolve(strict=True)
    require(
        stat.S_IMODE(parent.stat().st_mode) == 0o700,
        "State directory must have mode 0700",
    )
    require(
        not any((item / ".git").exists() for item in (parent, *parent.parents)),
        "Keep state outside all Git trees",
    )
    require(
        not path.exists()
        or (stat.S_IMODE(path.stat().st_mode) == 0o600 and path.stat().st_nlink == 1),
        "State file must have mode 0600 and no hard links",
    )
    return parent / path.name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    try:
        path = private_state(args.state)
        root = args.root.resolve(strict=True)
        require(root.is_dir(), "Case root must be a directory")
        require(
            not path.is_relative_to(root),
            "State must stay outside the read-only case root",
        )
        action = json.load(sys.stdin)
        require(isinstance(action, dict), "Expected action object")
        state = json.loads(path.read_text()) if path.exists() else None
        state, result = apply(state, action, root)
        if action["action"] not in ("show", "evidence"):
            descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".replay-")
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    json.dump(state, stream, ensure_ascii=False, indent=2)
                    stream.write("\n")
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, UnicodeError, TypeError, KeyError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
