"""Small in-code dependency coordinator; model and trial behavior live in handlers."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import os
from pathlib import Path
import re
import tempfile
from types import MappingProxyType

from stage_contract import StageResult, canonical_bytes, stage_record


@dataclass(frozen=True)
class Stage:
    name: str
    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    run: Callable[[Mapping[str, StageResult]], StageResult] | None = None


class Pipeline:
    def __init__(self, stages, record_dir, outputs=None, producer="behavior-diff"):
        self.stages = tuple(stages)
        self.record_dir = Path(record_dir)
        self.producer = producer
        self.registry = {}
        for stage in self.stages:
            if not re.fullmatch(r"[a-z][a-z0-9_-]*", stage.name):
                raise ValueError(f"invalid stage name: {stage.name}")
            if stage.name in self.registry:
                raise ValueError(f"duplicate stage: {stage.name}")
            if not callable(stage.run):
                raise ValueError(f"stage has no run callback: {stage.name}")
            self.registry[stage.name] = stage
        self.outputs = {
            name: tuple(Path(path).absolute() for path in paths)
            for name, paths in (outputs or {}).items()
        }
        unknown = self.outputs.keys() - self.registry.keys()
        if unknown:
            raise ValueError(f"unknown output owner: {sorted(unknown)}")
        owners = {}
        record_paths = {
            (self.record_dir / f"{stage.name}.json").resolve() for stage in self.stages
        }
        for name, paths in self.outputs.items():
            for path in paths:
                resolved = path.resolve()
                if resolved in owners or resolved in record_paths:
                    raise ValueError(f"duplicate output ownership: {path}")
                owners[resolved] = name
        self.order = []
        visiting = set()
        visited = set()

        def visit(name):
            if name not in self.registry:
                raise ValueError(f"unknown dependency: {name}")
            if name in visiting:
                raise ValueError(f"dependency cycle at: {name}")
            if name in visited:
                return
            visiting.add(name)
            stage = self.registry[name]
            dependencies = stage.required + stage.optional
            if len(set(dependencies)) != len(dependencies):
                raise ValueError(f"duplicate dependency for: {name}")
            for dependency in dependencies:
                visit(dependency)
            visiting.remove(name)
            visited.add(name)
            self.order.append(stage)

        for stage in self.stages:
            visit(stage.name)

    def _preflight(self):
        for stage in self.order:
            path = self.record_dir / f"{stage.name}.json"
            if path.exists() or path.is_symlink():
                raise FileExistsError(f"stage record already exists: {path}")
            for output in self.outputs.get(stage.name, ()):
                if output.exists() or output.is_symlink():
                    raise FileExistsError(f"stage output already exists: {output}")

    def _execute(self, stage, dependencies):
        failed = [
            name for name in stage.required if dependencies[name].state != "completed"
        ]
        if failed:
            return StageResult(
                "blocked", error="required inputs unavailable: " + ", ".join(failed)
            )
        try:
            result = stage.run(MappingProxyType(dependencies))
            if not isinstance(result, StageResult):
                raise TypeError("stage callback must return StageResult")
            if result.state == "completed":
                for output in self.outputs.get(stage.name, ()):
                    if not output.is_file() or output.is_symlink():
                        raise ValueError(
                            f"completed stage output is missing or not a regular file: {output}"
                        )
            return result
        except Exception as error:
            return StageResult("failed", error=f"{type(error).__name__}: {error}")

    def run(self):
        """Run once, refusing all existing stage records and declared outputs.

        Required failures block only their consumers. Optional inputs are still
        delivered with their terminal state, allowing an evidence-only report.
        """
        self._preflight()
        self.record_dir.mkdir(parents=True, exist_ok=True)
        results = {}
        records = {}
        for stage in self.order:
            path = self.record_dir / f"{stage.name}.json"
            # Each stage reserves only its own writer slot. No producer mutates
            # another stage's record or a shared aggregate status document.
            writer_path = self.record_dir / f".{stage.name}.writer"
            with writer_path.open("x", encoding="utf-8"):
                pass
            temporary = None
            try:
                if path.exists() or path.is_symlink():
                    raise FileExistsError(f"stage record already exists: {path}")
                for output in self.outputs.get(stage.name, ()):
                    if output.exists() or output.is_symlink():
                        raise FileExistsError(f"stage output already exists: {output}")
                dependencies = {
                    name: results[name] for name in stage.required + stage.optional
                }
                result = self._execute(stage, dependencies)
                record = stage_record(
                    stage.name,
                    result,
                    self.producer,
                    {name: records[name] for name in dependencies},
                    self.outputs.get(stage.name, ()),
                )
                descriptor, temporary = tempfile.mkstemp(
                    prefix=f".{stage.name}.", dir=self.record_dir
                )
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(canonical_bytes(record) + b"\n")
                os.link(temporary, path)
                results[stage.name] = result
                records[stage.name] = record
            finally:
                if temporary is not None:
                    Path(temporary).unlink(missing_ok=True)
                writer_path.unlink()
        return results
