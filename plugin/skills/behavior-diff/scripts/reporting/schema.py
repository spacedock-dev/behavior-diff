"""Immutable internal data model for Behavior Diff reports."""

import json
from dataclasses import asdict, dataclass
from typing import Dict, Optional, Tuple, Union

SCHEMA_VERSION = 3
RESULT_KINDS = ("good", "bad", "neutral")


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
    count_suffix: str
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
    kinds: Tuple[str, ...]
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
class EvidenceClaimData:
    text: str
    decisions: Tuple[int, ...]


@dataclass(frozen=True)
class DecisionData:
    rows: Tuple[DecisionRowData, ...]
    fork: Optional[int]
    fork_note: str
    dropped: int
    extractor: str
    before_count: int
    after_count: int
    outcome: Optional[int]
    implications: Tuple[EvidenceClaimData, ...]


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
    meta: Tuple[Tuple[str, str], ...]
    note: str
    limits_heading: str
    scenario_heading: str
    scenario: str
    expected_heading: str
    expected: Optional[str]
    diff_heading: str
    decision_heading: str
    decision_blurb: str
    tag_legend: Tuple[Tuple[str, str, str], ...]
    flow_heading: str
    flow_purpose: str
    result_heading: str
    boundary: str


@dataclass(frozen=True)
class ResultData:
    text: str
    kind: str
    summary: str
    outcome_heading: str
    behavior_heading: str
    outcomes: Tuple[int, ...]
    behavior: Tuple[int, ...]
    implications: Tuple[EvidenceClaimData, ...]
    limits: Tuple[str, ...]


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
        data = _expect_dict(data, "report-data")
        version = _expect_int(
            _field(data, "schema_version", "report-data"), "schema_version"
        )
        if version != SCHEMA_VERSION:
            raise ValueError(
                "unsupported report-data schema version: {0}".format(version)
            )

        decisions = _decisions(_field(data, "decisions", "report-data"), "decisions")
        result = _result(
            _field(data, "result", "report-data"), "result", len(decisions.rows)
        )
        return cls(
            schema_version=version,
            metadata=_metadata(_field(data, "metadata", "report-data"), "metadata"),
            content=_content(_field(data, "content", "report-data"), "content"),
            rule_diff=_expect_str(
                _field(data, "rule_diff", "report-data"), "rule_diff"
            ),
            result=result,
            variants=_variants(_field(data, "variants", "report-data"), "variants"),
            command_flow=_command_flow(
                _field(data, "command_flow", "report-data"), "command_flow"
            ),
            decisions=decisions,
        )

    def to_dict(self):
        return _json_value(asdict(self))

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def _metadata(value, path):
    value = _expect_dict(value, path)
    return MetadataData(
        model=_expect_str(_field(value, "model", path), path + ".model"),
        mode=_expect_str(_field(value, "mode", path), path + ".mode"),
        vocab=_expect_str(_field(value, "vocab", path), path + ".vocab"),
        trace_source=_expect_str(
            _field(value, "trace_source", path), path + ".trace_source"
        ),
        target_file=_expect_str(
            _field(value, "target_file", path), path + ".target_file"
        ),
        before_label=_expect_str(
            _field(value, "before_label", path), path + ".before_label"
        ),
        after_label=_expect_str(
            _field(value, "after_label", path), path + ".after_label"
        ),
    )


def _content(value, path):
    value = _expect_dict(value, path)
    return ContentData(
        title=_expect_str(_field(value, "title", path), path + ".title"),
        subtitle=_expect_str(_field(value, "subtitle", path), path + ".subtitle"),
        meta=_row_tuple(_field(value, "meta", path), path + ".meta", 2),
        note=_expect_str(_field(value, "note", path), path + ".note"),
        limits_heading=_expect_str(
            _field(value, "limits_heading", path), path + ".limits_heading"
        ),
        scenario_heading=_expect_str(
            _field(value, "scenario_heading", path), path + ".scenario_heading"
        ),
        scenario=_expect_str(_field(value, "scenario", path), path + ".scenario"),
        expected_heading=_expect_str(
            _field(value, "expected_heading", path), path + ".expected_heading"
        ),
        expected=_expect_optional_str(
            _field(value, "expected", path), path + ".expected"
        ),
        diff_heading=_expect_str(
            _field(value, "diff_heading", path), path + ".diff_heading"
        ),
        decision_heading=_expect_str(
            _field(value, "decision_heading", path), path + ".decision_heading"
        ),
        decision_blurb=_expect_str(
            _field(value, "decision_blurb", path), path + ".decision_blurb"
        ),
        tag_legend=_row_tuple(
            _field(value, "tag_legend", path), path + ".tag_legend", 3
        ),
        flow_heading=_expect_str(
            _field(value, "flow_heading", path), path + ".flow_heading"
        ),
        flow_purpose=_expect_str(
            _field(value, "flow_purpose", path), path + ".flow_purpose"
        ),
        result_heading=_expect_str(
            _field(value, "result_heading", path), path + ".result_heading"
        ),
        boundary=_expect_str(_field(value, "boundary", path), path + ".boundary"),
    )


def _result(value, path, row_count):
    value = _expect_dict(value, path)
    kind = _expect_str(_field(value, "kind", path), path + ".kind")
    if kind not in RESULT_KINDS:
        _invalid(path + ".kind", "one of " + ", ".join(RESULT_KINDS))
    return ResultData(
        text=_expect_str(_field(value, "text", path), path + ".text"),
        kind=kind,
        summary=_expect_str(_field(value, "summary", path), path + ".summary"),
        outcome_heading=_expect_str(
            _field(value, "outcome_heading", path), path + ".outcome_heading"
        ),
        behavior_heading=_expect_str(
            _field(value, "behavior_heading", path), path + ".behavior_heading"
        ),
        outcomes=_references(
            _field(value, "outcomes", path), path + ".outcomes", row_count
        ),
        behavior=_references(
            _field(value, "behavior", path), path + ".behavior", row_count
        ),
        implications=_claims(
            _field(value, "implications", path), path + ".implications", row_count
        ),
        limits=_string_tuple(_field(value, "limits", path), path + ".limits"),
    )


def _variants(value, path):
    value = _expect_dict(value, path)
    return VariantsData(
        before=_variant(_field(value, "before", path), path + ".before"),
        after=_variant(_field(value, "after", path), path + ".after"),
    )


def _variant(value, path):
    value = _expect_dict(value, path)
    trials = _expect_list(_field(value, "trials", path), path + ".trials")
    return VariantData(
        label=_expect_str(_field(value, "label", path), path + ".label"),
        note=_expect_str(_field(value, "note", path), path + ".note"),
        passed=_expect_int(_field(value, "passed", path), path + ".passed"),
        blocked=_expect_int(_field(value, "blocked", path), path + ".blocked"),
        valid=_expect_int(_field(value, "valid", path), path + ".valid"),
        total=_expect_int(_field(value, "total", path), path + ".total"),
        count_text=_expect_str(_field(value, "count_text", path), path + ".count_text"),
        count_suffix=_expect_str(
            _field(value, "count_suffix", path), path + ".count_suffix"
        ),
        count_emphasized=_expect_bool(
            _field(value, "count_emphasized", path), path + ".count_emphasized"
        ),
        trials=tuple(
            _trial(item, "{0}.trials[{1}]".format(path, index))
            for index, item in enumerate(trials)
        ),
    )


def _trial(value, path):
    value = _expect_dict(value, path)
    return TrialData(
        name=_expect_str(_field(value, "name", path), path + ".name"),
        verdict=_expect_str(_field(value, "verdict", path), path + ".verdict"),
        actions=_expect_str(_field(value, "actions", path), path + ".actions"),
        commands=_string_tuple(_field(value, "commands", path), path + ".commands"),
        final=_expect_str(_field(value, "final", path), path + ".final"),
        outcome=_expect_optional_str(_field(value, "outcome", path), path + ".outcome"),
    )


def _command_flow(value, path):
    value = _expect_dict(value, path)
    return CommandFlowData(
        enabled=_expect_bool(_field(value, "enabled", path), path + ".enabled"),
        same=_expect_bool(_field(value, "same", path), path + ".same"),
        kinds=(
            ()
            if value.get("kinds") is None
            else _string_tuple(value["kinds"], path + ".kinds")
        ),
        shared=_string_tuple(_field(value, "shared", path), path + ".shared"),
        before=_flow_branch(_field(value, "before", path), path + ".before"),
        after=_flow_branch(_field(value, "after", path), path + ".after"),
    )


def _flow_branch(value, path):
    value = _expect_dict(value, path)
    paths = _expect_list(_field(value, "paths", path), path + ".paths")
    return FlowBranchData(
        prefix=_string_tuple(_field(value, "prefix", path), path + ".prefix"),
        paths=tuple(
            _flow_path(item, "{0}.paths[{1}]".format(path, index))
            for index, item in enumerate(paths)
        ),
        total=_expect_int(_field(value, "total", path), path + ".total"),
    )


def _flow_path(value, path):
    value = _expect_dict(value, path)
    return FlowPathData(
        steps=_string_tuple(_field(value, "steps", path), path + ".steps"),
        count=_expect_int(_field(value, "count", path), path + ".count"),
    )


def _decisions(value, path):
    value = _expect_dict(value, path)
    rows = _expect_list(_field(value, "rows", path), path + ".rows")
    return DecisionData(
        rows=tuple(
            _decision_row(item, "{0}.rows[{1}]".format(path, index))
            for index, item in enumerate(rows)
        ),
        fork=_optional_reference(
            _field(value, "fork", path), path + ".fork", len(rows)
        ),
        fork_note=_expect_str(_field(value, "fork_note", path), path + ".fork_note"),
        dropped=_expect_int(_field(value, "dropped", path), path + ".dropped"),
        extractor=_expect_str(_field(value, "extractor", path), path + ".extractor"),
        before_count=_expect_int(
            _field(value, "before_count", path), path + ".before_count"
        ),
        after_count=_expect_int(
            _field(value, "after_count", path), path + ".after_count"
        ),
        outcome=_optional_reference(
            _field(value, "outcome", path), path + ".outcome", len(rows)
        ),
        implications=_claims(
            _field(value, "implications", path), path + ".implications", len(rows)
        ),
    )


def _decision_row(value, path):
    value = _expect_dict(value, path)
    before = _expect_list(_field(value, "before", path), path + ".before")
    after = _expect_list(_field(value, "after", path), path + ".after")
    return DecisionRowData(
        decision=_expect_str(_field(value, "decision", path), path + ".decision"),
        topic=_expect_str(_field(value, "topic", path), path + ".topic"),
        anchor=_expect_anchor(_field(value, "anchor", path), path + ".anchor"),
        diverges=_expect_bool(_field(value, "diverges", path), path + ".diverges"),
        note=_expect_str(_field(value, "note", path), path + ".note"),
        before=tuple(
            _decision_choice(item, "{0}.before[{1}]".format(path, index))
            for index, item in enumerate(before)
        ),
        after=tuple(
            _decision_choice(item, "{0}.after[{1}]".format(path, index))
            for index, item in enumerate(after)
        ),
    )


def _decision_choice(value, path):
    value = _expect_dict(value, path)
    return DecisionChoiceData(
        choice=_expect_str(_field(value, "choice", path), path + ".choice"),
        count=_expect_int(_field(value, "count", path), path + ".count"),
    )


def _optional_reference(value, path, row_count):
    if value is None:
        return None
    return _reference(value, path, row_count)


def _reference(value, path, row_count):
    value = _expect_int(value, path)
    if not 1 <= value <= row_count:
        _invalid(path, "1-based decision row index")
    return value


def _references(value, path, row_count):
    values = _expect_list(value, path)
    references = tuple(
        _reference(item, "{0}[{1}]".format(path, index), row_count)
        for index, item in enumerate(values)
    )
    if len(set(references)) != len(references):
        _invalid(path, "unique decision row indexes")
    return references


def _claims(value, path, row_count):
    claims = []
    for index, item in enumerate(_expect_list(value, path)):
        item_path = "{0}[{1}]".format(path, index)
        item = _expect_dict(item, item_path)
        text = _expect_str(_field(item, "text", item_path), item_path + ".text")
        if not text.strip():
            _invalid(item_path + ".text", "nonblank string")
        references = _references(
            _field(item, "decisions", item_path), item_path + ".decisions", row_count
        )
        if not references:
            _invalid(item_path + ".decisions", "nonempty decision row indexes")
        claims.append(EvidenceClaimData(text, references))
    return tuple(claims)


def _field(value, name, path):
    try:
        return value[name]
    except KeyError:
        _invalid(path + "." + name, "present field")


def _expect_dict(value, path):
    if type(value) is not dict:
        _invalid(path, "dict")
    return value


def _expect_list(value, path):
    if type(value) is not list:
        _invalid(path, "list")
    return value


def _expect_str(value, path):
    if type(value) is not str:
        _invalid(path, "string")
    return value


def _expect_bool(value, path):
    if type(value) is not bool:
        _invalid(path, "boolean")
    return value


def _expect_int(value, path):
    if type(value) is not int:
        _invalid(path, "integer")
    return value


def _expect_optional_str(value, path):
    if value is None:
        return None
    return _expect_str(value, path)


def _expect_anchor(value, path):
    if type(value) is int or type(value) is str:
        return value
    _invalid(path, "integer or string")


def _row_tuple(value, path, width):
    items = _expect_list(value, path)
    rows = []
    for index, item in enumerate(items):
        item_path = "{0}[{1}]".format(path, index)
        row = _expect_list(item, item_path)
        if len(row) != width:
            _invalid(item_path, "{0} strings".format(width))
        rows.append(
            tuple(
                _expect_str(row[position], "{0}[{1}]".format(item_path, position))
                for position in range(width)
            )
        )
    return tuple(rows)


def _string_tuple(value, path):
    value = _expect_list(value, path)
    return tuple(
        _expect_str(item, "{0}[{1}]".format(path, index))
        for index, item in enumerate(value)
    )


def _invalid(path, expected):
    raise ValueError(
        "invalid report-data field {0}: expected {1}".format(path, expected)
    )


def _json_value(value):
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value
