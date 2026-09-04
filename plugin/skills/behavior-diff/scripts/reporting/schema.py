"""Immutable internal data model for Behavior Diff reports."""

import json
from dataclasses import asdict, dataclass
from typing import Dict, Optional, Tuple, Union

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class TrialData:
    name: str
    verdict: str
    actions: str
    commands: Tuple[str, ...]
    final: str
    outcome: Optional[str]


@dataclass(frozen=True)
class VariantData:
    label: str
    note: str
    passed: int
    blocked: int
    valid: int
    total: int
    count_text: str
    count_emphasized: bool
    trials: Tuple[TrialData, ...]


@dataclass(frozen=True)
class VariantsData:
    before: VariantData
    after: VariantData


@dataclass(frozen=True)
class FlowPathData:
    steps: Tuple[str, ...]
    count: int


@dataclass(frozen=True)
class FlowBranchData:
    prefix: Tuple[str, ...]
    paths: Tuple[FlowPathData, ...]
    total: int


@dataclass(frozen=True)
class CommandFlowData:
    enabled: bool
    same: bool
    shared: Tuple[str, ...]
    before: FlowBranchData
    after: FlowBranchData


@dataclass(frozen=True)
class DecisionChoiceData:
    choice: str
    count: int


@dataclass(frozen=True)
class DecisionRowData:
    decision: str
    topic: str
    anchor: Union[int, str]
    diverges: bool
    note: str
    before: Tuple[DecisionChoiceData, ...]
    after: Tuple[DecisionChoiceData, ...]


@dataclass(frozen=True)
class DecisionData:
    rows: Tuple[DecisionRowData, ...]
    fork: Optional[int]
    fork_note: str
    dropped: int
    extractor: str
    before_count: int
    after_count: int


@dataclass(frozen=True)
class MetadataData:
    model: str
    mode: str
    vocab: str
    trace_source: str
    target_file: str
    before_label: str
    after_label: str


@dataclass(frozen=True)
class ContentData:
    title: str
    subtitle: str
    observation: str
    scenario_heading: str
    scenario: str
    expected_heading: str
    expected: Optional[str]
    diff_heading: str
    decision_heading: str
    decision_blurb: str
    flow_heading: str
    result_heading: str
    boundary: str


@dataclass(frozen=True)
class ResultData:
    text: str
    kind: str


@dataclass(frozen=True)
class ReportData:
    schema_version: int
    metadata: MetadataData
    content: ContentData
    rule_diff: str
    result: ResultData
    variants: VariantsData
    command_flow: CommandFlowData
    decisions: DecisionData

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ReportData":
        version = data.get("schema_version")
        if version != SCHEMA_VERSION:
            raise ValueError("unsupported report-data schema version: {0}".format(version))

        metadata_data = data["metadata"]
        content_data = data["content"]
        result_data = data["result"]
        variants_data = data["variants"]
        command_flow_data = data["command_flow"]
        decisions_data = data["decisions"]

        def trial(raw):
            return TrialData(
                name=raw["name"],
                verdict=raw["verdict"],
                actions=raw["actions"],
                commands=tuple(raw["commands"]),
                final=raw["final"],
                outcome=raw["outcome"],
            )

        def variant(raw):
            return VariantData(
                label=raw["label"],
                note=raw["note"],
                passed=raw["passed"],
                blocked=raw["blocked"],
                valid=raw["valid"],
                total=raw["total"],
                count_text=raw["count_text"],
                count_emphasized=raw["count_emphasized"],
                trials=tuple(trial(item) for item in raw["trials"]),
            )

        def flow_path(raw):
            return FlowPathData(steps=tuple(raw["steps"]), count=raw["count"])

        def flow_branch(raw):
            return FlowBranchData(
                prefix=tuple(raw["prefix"]),
                paths=tuple(flow_path(item) for item in raw["paths"]),
                total=raw["total"],
            )

        def decision_choice(raw):
            return DecisionChoiceData(choice=raw["choice"], count=raw["count"])

        def decision_row(raw):
            return DecisionRowData(
                decision=raw["decision"],
                topic=raw["topic"],
                anchor=raw["anchor"],
                diverges=raw["diverges"],
                note=raw["note"],
                before=tuple(decision_choice(item) for item in raw["before"]),
                after=tuple(decision_choice(item) for item in raw["after"]),
            )

        return cls(
            schema_version=version,
            metadata=MetadataData(
                model=metadata_data["model"],
                mode=metadata_data["mode"],
                vocab=metadata_data["vocab"],
                trace_source=metadata_data["trace_source"],
                target_file=metadata_data["target_file"],
                before_label=metadata_data["before_label"],
                after_label=metadata_data["after_label"],
            ),
            content=ContentData(
                title=content_data["title"],
                subtitle=content_data["subtitle"],
                observation=content_data["observation"],
                scenario_heading=content_data["scenario_heading"],
                scenario=content_data["scenario"],
                expected_heading=content_data["expected_heading"],
                expected=content_data["expected"],
                diff_heading=content_data["diff_heading"],
                decision_heading=content_data["decision_heading"],
                decision_blurb=content_data["decision_blurb"],
                flow_heading=content_data["flow_heading"],
                result_heading=content_data["result_heading"],
                boundary=content_data["boundary"],
            ),
            rule_diff=data["rule_diff"],
            result=ResultData(text=result_data["text"], kind=result_data["kind"]),
            variants=VariantsData(
                before=variant(variants_data["before"]),
                after=variant(variants_data["after"]),
            ),
            command_flow=CommandFlowData(
                enabled=command_flow_data["enabled"],
                same=command_flow_data["same"],
                shared=tuple(command_flow_data["shared"]),
                before=flow_branch(command_flow_data["before"]),
                after=flow_branch(command_flow_data["after"]),
            ),
            decisions=DecisionData(
                rows=tuple(decision_row(item) for item in decisions_data["rows"]),
                fork=decisions_data["fork"],
                fork_note=decisions_data["fork_note"],
                dropped=decisions_data["dropped"],
                extractor=decisions_data["extractor"],
                before_count=decisions_data["before_count"],
                after_count=decisions_data["after_count"],
            ),
        )

    def to_dict(self):
        return _json_value(asdict(self))

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def _json_value(value):
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value
