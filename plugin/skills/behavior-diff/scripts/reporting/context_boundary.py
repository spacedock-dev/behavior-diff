"""Sanitized shared filesystem-boundary eligibility, never raw private paths."""

import json
from pathlib import Path


def boundary_status(trial_dir):
    trial_dir = Path(trial_dir)
    config_path = trial_dir.parent / "config.json"
    if config_path.is_symlink():
        return "unavailable"
    try:
        config = json.loads(config_path.read_text())
    except FileNotFoundError:
        config = {}
    except (OSError, ValueError):
        return "unavailable"
    if not isinstance(config, dict):
        return "unavailable"
    if (
        "context_boundary_required" in config
        and type(config["context_boundary_required"]) is not bool
    ):
        return "unavailable"
    required = config.get("context_boundary_required") is True
    marker = trial_dir / "context-boundary.json"
    if not marker.exists():
        return "unavailable" if required else None
    try:
        if marker.is_symlink():
            return "unavailable"
        value = json.loads(marker.read_text())
    except (OSError, ValueError):
        return "unavailable"
    if not isinstance(value, dict) or value.get("version") != 1:
        return "unavailable"
    status = value.get("status")
    if status == "violation":
        return status
    if (
        status != "enforced"
        or value.get("scope") != "codex-local-filesystem"
        or value.get("clean_context_proven") is not False
    ):
        return "unavailable"
    if value.get("observation") != "not_observed":
        return "unavailable"
    return "enforced"


def boundary_exclusion(trial_dir):
    status = boundary_status(trial_dir)
    if status == "violation":
        return (
            "recorded filesystem context boundary violation; private evidence excluded"
        )
    if status == "unavailable":
        return "required filesystem context boundary unavailable; private evidence excluded"
    return None
