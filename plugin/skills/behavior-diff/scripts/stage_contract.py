"""Terminal pipeline results and their local, versioned provenance records."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
TERMINAL_STATES = ("completed", "failed", "skipped", "blocked")


def canonical_bytes(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def content_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


@dataclass(frozen=True)
class StageResult:
    """Execution status, never a judgment of whether the experiment helped."""

    state: str
    output: Any = None
    error: str | None = None

    def __post_init__(self):
        if self.state not in TERMINAL_STATES:
            raise ValueError(f"invalid terminal stage state: {self.state}")
        if self.error is not None and not isinstance(self.error, str):
            raise ValueError("stage error must be text or None")
        if self.state == "completed" and self.error is not None:
            raise ValueError("completed stage cannot have an error")
        canonical_bytes(self.output)

    def to_dict(self):
        return {"state": self.state, "output": self.output, "error": self.error}


def artifact_reference(path):
    """Identify original bytes without interpreting the artifact's own schema."""
    path = Path(path)
    data = path.read_bytes()
    return {
        "path": str(path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
    }


def stage_record(name, result, producer, input_records, outputs):
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": name,
        "producer": producer,
        "input_hashes": {
            name: content_hash(record) for name, record in input_records.items()
        },
        "outputs": [
            artifact_reference(path)
            for path in outputs
            if path.is_file() and not path.is_symlink()
        ],
        **result.to_dict(),
    }
