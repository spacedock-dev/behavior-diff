"""Report header provenance: caller-supplied Git history or CI run context."""

from dataclasses import dataclass
from typing import Optional, Tuple
from urllib.parse import urlsplit

from ci_context import parse_ci_context
from source import parse_source

SHORT_COMMIT_LENGTH = 8
_SIDE_ORDER = {"before": 0, "both": 1, "after": 2}


@dataclass(frozen=True)
class PullRequestData:
    number: int
    title: str
    url: str
    applies_to: str


@dataclass(frozen=True)
class SourceData:
    forge: str
    repository_url: str
    before_commit: str
    after_commit: str
    pull_requests: Tuple[PullRequestData, ...]


@dataclass(frozen=True)
class CiPullRequestData:
    number: int
    title: Optional[str]
    url: str


@dataclass(frozen=True)
class CiContextData:
    """Repository and PR/MR of the CI workflow run; never Before/After history."""

    forge: str
    repository_url: str
    pull_request: Optional[CiPullRequestData]


@dataclass(frozen=True)
class SourceLinkData:
    label: str
    text: str
    url: str
    title: str = ""


def _data(normalized) -> SourceData:
    return SourceData(
        forge=normalized["forge"],
        repository_url=normalized["repository_url"],
        before_commit=normalized["before_commit"],
        after_commit=normalized["after_commit"],
        pull_requests=tuple(
            PullRequestData(
                number=request["number"],
                title=request["title"],
                url=request["url"],
                applies_to=request["applies_to"],
            )
            for request in normalized["pull_requests"]
        ),
    )


def config_source(value) -> Optional[SourceData]:
    """Normalize the optional `source` object from a run config."""
    try:
        normalized = parse_source(value)
    except ValueError as error:
        raise SystemExit("invalid config source: {0}".format(error))
    return None if normalized is None else _data(normalized)


def report_source(value, path) -> Optional[SourceData]:
    """Accept serialized provenance only in its already-normalized form."""
    try:
        normalized = parse_source(value)
    except ValueError as error:
        raise ValueError("invalid report-data field {0}: {1}".format(path, error))
    if normalized != value:
        raise ValueError(
            "invalid report-data field {0}: expected normalized source".format(path)
        )
    return None if normalized is None else _data(normalized)


def _ci_data(normalized) -> CiContextData:
    request = normalized["pull_request"]
    return CiContextData(
        forge=normalized["forge"],
        repository_url=normalized["repository_url"],
        pull_request=None
        if request is None
        else CiPullRequestData(
            number=request["number"], title=request["title"], url=request["url"]
        ),
    )


def config_ci_context(value) -> Optional[CiContextData]:
    """Normalize the optional `ci_context` object captured at run creation."""
    try:
        normalized = parse_ci_context(value)
    except ValueError as error:
        raise SystemExit("invalid config ci_context: {0}".format(error))
    return None if normalized is None else _ci_data(normalized)


def report_ci_context(value, path) -> Optional[CiContextData]:
    """Accept serialized CI context only in its already-normalized form."""
    try:
        normalized = parse_ci_context(value)
    except ValueError as error:
        raise ValueError("invalid report-data field {0}: {1}".format(path, error))
    if normalized != value:
        raise ValueError(
            "invalid report-data field {0}: expected normalized ci_context".format(path)
        )
    return None if normalized is None else _ci_data(normalized)


def repository_name(source) -> str:
    return urlsplit(source.repository_url).path.strip("/")


def request_noun(source) -> str:
    return "MR" if source.forge == "gitlab" else "PR"


def commit_links(source: SourceData) -> Tuple[SourceLinkData, SourceLinkData]:
    separator = "/-/commit/" if source.forge == "gitlab" else "/commit/"
    return tuple(
        SourceLinkData(
            label=label,
            text=commit[:SHORT_COMMIT_LENGTH],
            url=source.repository_url + separator + commit,
            title=commit,
        )
        for label, commit in (
            ("Before", source.before_commit),
            ("After", source.after_commit),
        )
    )


def header_links(source: SourceData) -> Tuple[SourceLinkData, ...]:
    """Repository and related PR/MR links, in reading order."""
    noun = request_noun(source)
    marker = "!" if source.forge == "gitlab" else "#"
    sided = any(request.applies_to != "both" for request in source.pull_requests)
    requests = sorted(
        source.pull_requests, key=lambda request: _SIDE_ORDER[request.applies_to]
    )
    links = [
        SourceLinkData("Repository", repository_name(source), source.repository_url)
    ]
    for request in requests:
        side = request.applies_to
        label = (
            "{0} {1}".format(side.capitalize(), noun)
            if sided and side != "both"
            else "Related " + noun
        )
        links.append(
            SourceLinkData(
                label,
                "{0}{1} — {2}".format(marker, request.number, request.title),
                request.url,
            )
        )
    return tuple(links)


def ci_header_links(context: CiContextData) -> Tuple[SourceLinkData, ...]:
    """Repository and workflow PR/MR links; labelled as run context, not history."""
    links = [
        SourceLinkData("Repository", repository_name(context), context.repository_url)
    ]
    request = context.pull_request
    if request is not None:
        marker = "!" if context.forge == "gitlab" else "#"
        text = "{0}{1}".format(marker, request.number)
        if request.title:
            text += " — " + request.title
        links.append(
            SourceLinkData("Workflow " + request_noun(context), text, request.url)
        )
    return tuple(links)
