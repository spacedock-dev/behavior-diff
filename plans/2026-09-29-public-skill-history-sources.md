# Public Skill History Sources for Behavior Diff

Survey date: 2026-09-29 (UTC).
Status: Source survey, not a validated benchmark or permission to run upstream code.
Tracking: A Verification issue in the Engram Linear project remains required, with the `behavior-diff` label.

## Purpose

Use public skill revisions as realistic inputs for Behavior Diff scenario replay.
The unit of interest is an instruction change with a reproducible decision moment,
not a repository download or a collection of current skill descriptions.

Public commits show what maintainers changed. They do not provide measured agent
behavior, a reliable expected result, or proof that the newer skill is better.
Every scenario below is a proposed experiment unless stated otherwise. No live
agent trials, upstream installations, deployments, or model evaluations ran for this survey.

This is a curated survey of popular and relevant sources, not an exhaustive index
of every public skill repository. Repository stars indicate visibility, not skill
adoption, safety, licensing permission, or historical data quality.

Source checks confirmed 97 cited file paths across 22 immutable repository snapshots.
All 24 candidate Before revisions match the cited After commit's first parent.
These checks establish source provenance, not behavioral validity or legal clearance.
Local document links and Markdown whitespace were also checked.

## Selection and evidence rules

Prefer canonical author repositories over mirrors and marketplace copies. Inspect
actual `SKILL.md` files, companion files, license terms, and noninitial commit patches.
Use the whole skill directory for history discovery because instructions can live
in references, templates, or scripts. A `SKILL.md`-only filter misses those changes.

Source links use recorded commit SHAs. A history link is a discovery aid, not a
frozen dataset. Example Before revisions are the first parent of the cited After
commit unless an entry states otherwise. A multi-file commit is not automatically
a clean instruction-only experiment.

Priorities describe proposed collection order:

- **Start:** bounded local scenarios with observable choices and promising history.
- **Extend:** useful sources that need more runtime setup or broader bundle support.
- **Hold:** license, service, or history constraints must be resolved before use.

Priorities are recommendations, not results from Behavior Diff.

## Survey at a glance

The catalog contains **18 repositories and 66 selected current skill entrypoints**,
plus a historical trigger-skill example. It includes **24 inspected commit pairs**.
Not every listed skill has its own inspected pair. Each repository has at least
one example, with the exact scope described below.

All 18 repositories were public, non-forks, and not GitHub-archived at observation.
All used `main` as the default branch. Those flags do not rule out deprecation or
exported mirrors. OpenAI and Remotion illustrate that distinction.

| Repository | Observed stars | Main collection value | Key caution |
| --- | ---: | --- | --- |
| [obra/superpowers](https://github.com/obra/superpowers) | 292,590 | Verification, debugging, and trigger changes | Cross-skill dependencies and host hooks |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 271,478 | Evidence contracts and clarification | In-progress skills and derived material |
| [anthropics/skills](https://github.com/anthropics/skills) | 178,876 | Authoring/evaluation workflow changes | Custom-restricted document skills |
| [garrytan/gstack](https://github.com/garrytan/gstack) | 134,438 | Context-aware planning | Generated files and runtime coupling |
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | 51,836 | Evidence calibration and context reuse | External empirical claims are not ground truth |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 47,036 | Bounded analysis and data-handling constraints | Per-skill licenses and mixed code/prose changes |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | 31,691 | Framework choices and reference changes | Generated copies and runtime-version sensitivity |
| [openai/skills](https://github.com/openai/skills) | 27,797 | Small historical workflow changes | Deprecated catalog and per-skill licensing |
| [huggingface/skills](https://github.com/huggingface/skills) | 11,113 | Privacy defaults and command routing | Remote writes, generated CLI content, paid jobs |
| [trailofbits/skills](https://github.com/trailofbits/skills) | 7,282 | Security reasoning and coverage honesty | CC-BY-SA obligations and scanner coupling |
| [czlonkowski/n8n-skills](https://github.com/czlonkowski/n8n-skills) | 6,346 | Expressions and false-success diagnosis | Runtime-specific semantics and MCP dependencies |
| [remotion-dev/skills](https://github.com/remotion-dev/skills) | 4,759 | Concrete animation/API changes | Rights hold and exported/duplicated content |
| [microsoft/skills](https://github.com/microsoft/skills) | 3,063 | Local Python correctness and upstream scenario leads | Broad multi-skill commits and weak pattern graders |
| [cloudflare/skills](https://github.com/cloudflare/skills) | 2,935 | Concrete Worker review decisions | Retrieved documentation and remote bindings |
| [supabase/agent-skills](https://github.com/supabase/agent-skills) | 2,659 | SQL authorization and scoped credentials | Privilege changes need execution-based checking |
| [expo/skills](https://github.com/expo/skills) | 2,635 | Mobile-state handling and recovery commands | Native runtime or paid EAS for full execution |
| [getsentry/skills](https://github.com/getsentry/skills) | 1,023 | Review policy and false-positive control | Mixed-license security references |
| [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills) | 878 | Version-aware local policy validation | MPL terms and provisioned provider schemas |

Smaller vendor-maintained sources are included for relevant, inspectable changes,
not because every entry meets a common popularity threshold. Counts are a dated
snapshot, not a live ranking. Exact source and license links appear in each section.

## Recommended first collection

Start with the first five cases. They have small instruction changes or bounded
instruction projections. Then add reference-bundle and runtime-sensitive cases.
This order prioritizes interpretable evidence over star count.

| Order | Skill / After commit prefix | Comparison scope | Primary observation |
| ---: | --- | --- | --- |
| 1 | OpenAI `skill-installer` / `49f948f` | One instruction file | User must restart versus can use the skill next turn |
| 2 | Cloudflare `workers-best-practices` / `42839d0` | One instruction file | Concrete unsafe patterns identified in a fixed Worker fixture |
| 3 | Hugging Face `huggingface-datasets` / `b3df145` | One instruction file, plan only | Private trace-storage default and scoped command plan |
| 4 | Matt Pocock `pr` / `35f5926` | One instruction file, draft only | Specific supported evidence without fabricated proof |
| 5 | Microsoft `fastapi-router-py` / `8ae5031` | Projected single-skill instruction change | Blocking dependency handled without blocking an async handler |
| 6 | Sentry `gha-security-review` / `7e127fe` | Two-file instruction bundle | Privileged third-party tags separated from other trust questions |
| 7 | Superpowers `systematic-debugging` / `af67e03` | One instruction file, fixed dependency skill | Verification before completion after guidance moves to its use site |
| 8 | Supabase Postgres / `133f43e` | Projected reference bundle | Unauthorized denial and intended-user access both preserved |
| 9 | n8n expressions / `470e9aa` | Projected skill/reference bundle | Correct output values, not merely a green execution indicator |
| 10 | Expo `eas-simulator` / `efa52f0` | Reference-only projection, command plan | Headless boot with the variable on the correct client |

Full SHAs and observed patch details appear in the corresponding source sections.
“Offline” means no task-side external service. Future agent trials still require
model access and approval. A supplied tool-result fixture is synthetic input, not
evidence that an upstream installation, scan, deployment, or recovery succeeded.

## Repository and skill catalog

### Anthropic — skill authoring, browser work, and document holds

Repository: [anthropics/skills](https://github.com/anthropics/skills).
Observed stars: **178,876**. Snapshot/default branch:
[`8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4`](https://github.com/anthropics/skills/commit/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4), `main`.
**Mixed licenses:** the three selected authoring/web skills use Apache-2.0,
including [skill-creator's license](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/skill-creator/LICENSE.txt).
The [README](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/README.md)
calls DOCX, PDF, PPTX, and XLSX source-available, not open source.
Their custom terms restrict copying and use outside the defined Services.
Hold those document bundles pending permission review. Preserve third-party notices and asset licenses.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [skill-creator](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/skill-creator/SKILL.md) | Extend | Improve a small CSV-normalization skill. Compare baseline preservation, discriminating cases, and human-review ordering. | Start with a plan only. Full workflow invokes scripts, a viewer, and nested model trials. |
| [webapp-testing](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/webapp-testing/SKILL.md) | Extend | Check a delayed-render local form. Observe rendered-selector discovery and browser/server cleanup. | Python Playwright, Chromium, and pinned helper scripts. |
| [web-artifacts-builder](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/web-artifacts-builder/SKILL.md) | Extend | Build a small stateful dashboard as self-contained HTML. Check deliverable dependencies and artifact completeness. | Preprovision the React/build stack. Do not run arbitrary initialization downloads. |
| [docx](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/docx/SKILL.md) | Hold | After permission, edit a sentence split across XML runs while preserving formatting. | [Custom license](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/docx/LICENSE.txt), XML/archive tools, LibreOffice/Poppler, and visual checks. |
| [xlsx](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/xlsx/SKILL.md) | Hold | After permission, update designated inputs without losing formulas. Check recalculation errors rather than exit status alone. | [Custom license](https://github.com/anthropics/skills/blob/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/xlsx/LICENSE.txt), spreadsheet libraries and recalculation runtime. |

**Observed pair A:** Before `a5bcdd7e58cdff48566bf876f0a72a2008dcefbc` →
After [`1ed29a03dc852d30fa6ef2ca53a67dc2c2c2c563`](https://github.com/anthropics/skills/commit/1ed29a03dc852d30fa6ef2ca53a67dc2c2c2c563),
2026-02-06, “Update skill-creator and make scripts executable.”
Creator instructions and validation gain optional `compatibility` metadata.
Initializer help changes its stated name-length limit. Do not mislabel that help
change as a new validator limit. Use a short and an overlong environment requirement
to distinguish authoring choices from deterministic helper behavior.

**Observed pair B:** Before `1ed29a03dc852d30fa6ef2ca53a67dc2c2c2c563` →
After [`3d59511518591fa82e6cfcf0438d68dd5dad3e76`](https://github.com/anthropics/skills/commit/3d59511518591fa82e6cfcf0438d68dd5dad3e76),
2026-02-25, “chore: export latest skills.”
The creator workflow gains paired trials, old-skill baselines, assertions,
benchmark aggregation, and human review. Scripts, agents, schemas, and viewer files
also change. Isolate the Apache creator bundle because the commit includes DOCX changes.
[Creator history](https://github.com/anthropics/skills/commits/main/skills/skill-creator).
Earlier skills moved into `skills/`, so current-path history is incomplete without renames.

### OpenAI — historical Codex skills

Repository: [openai/skills](https://github.com/openai/skills).
Observed stars: **27,797**. Snapshot/default branch:
[`49f948faa9258a0c61caceaf225e179651397431`](https://github.com/openai/skills/commit/49f948faa9258a0c61caceaf225e179651397431), `main`.
The [README](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/README.md)
deprecates this repository in favor of `openai/plugins`. GitHub does not mark it archived.
It remains useful for historical pairs, not as a claim about current supported installation.

Licensing is per skill. The selected system and curated skills have Apache-2.0
licenses: [creator](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.system/skill-creator/LICENSE.txt)
and [PDF](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/pdf/LICENSE.txt)
are representative inspected texts. Figma bundles have custom terms and are not
approved by that conclusion. Anthropic's document-license restrictions do not
automatically apply to OpenAI's separately licensed PDF skill.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [skill-creator](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.system/skill-creator/SKILL.md) | Start | Finish a complete local skill folder. Compare folder validation against obsolete ZIP packaging. | Pin historical helpers and references. Do not restore a deleted helper with a compatibility shim. |
| [skill-installer](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.system/skill-installer/SKILL.md) | Start | Provide the same successful-install result and request the next step. Compare restart requirements with next-turn availability. | Recorded-tool-result boundary only. No installation or network needed. |
| [pdf](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/pdf/SKILL.md) | Extend | Review a PDF with a clipped table but correct extracted text. Check whether visual evidence informs readiness. | Poppler, local PDF libraries, fonts, and a visual inspection surface. |
| [jupyter-notebook](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/jupyter-notebook/SKILL.md) | Extend | Produce a small tutorial notebook when execution is unavailable. Check mode, cell structure, and honest execution status. | Pin templates. An unexecuted notebook must not be reported as tested. |
| [security-best-practices](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/security-best-practices/SKILL.md) | Extend | Review a local Flask/JS fixture, then use a general-review negative trigger. Check scoped findings and no unsolicited mutations. | Pin language/framework references. Unsupported frameworks need explicit limits. |

**Observed pair A:** Before `8447091cbb995cb4deeea8910f0d26579876267b` →
After [`f1994cce0af236f6d0fa6548e5d5ea59376311aa`](https://github.com/openai/skills/commit/f1994cce0af236f6d0fa6548e5d5ea59376311aa),
2026-02-01, “Remove zipped .skill packaging from skill-creator.”
The instructions switch to `quick_validate.py` and folder delivery. The packaging
script is deleted. This is a two-file workflow/resource change.

**Observed pair B:** Before `778b0e6129cf18cbaee3bf11479f583fadae8d03` →
After [`49f948faa9258a0c61caceaf225e179651397431`](https://github.com/openai/skills/commit/49f948faa9258a0c61caceaf225e179651397431),
2026-06-24, “Update skill installer post-install guidance.”
One instruction changes the required user action from restart to next-turn use.
Grade the semantic requirement, not an exact phrase.
[Installer history](https://github.com/openai/skills/commits/main/skills/.system/skill-installer/SKILL.md).
Competing README guidance and globally installed system skills must not leak into the fixture.

### Superpowers — debugging, evidence, and workflow selection

Repository: [obra/superpowers](https://github.com/obra/superpowers).
Observed stars: **292,590**. Snapshot/default branch:
[`8ca22dba9a94f28898bbce59f2537ff4d87c747d`](https://github.com/obra/superpowers/commit/8ca22dba9a94f28898bbce59f2537ff4d87c747d), `main`.
License: [MIT](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/LICENSE).
Freeze cross-skill dependencies and host adapters instead of installing the latest full plugin.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [systematic-debugging](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/systematic-debugging/SKILL.md) | Start | Present a deterministic configuration failure under pressure to patch immediately. Check reproduction, diagnosis, and verification order. | Local fixture and pinned referenced skills. |
| [verification-before-completion](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/verification-before-completion/SKILL.md) | Start | Provide an old passing log followed by an edit. Check fresh evidence or a qualified completion claim. | A current local check must be available for the positive case. |
| [receiving-code-review](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/receiving-code-review/SKILL.md) | Extend | Mix valid, incompatible, and ambiguous reviewer requests. Check clarification and technical pushback. | Judge technical choices, not courtesy phrases. |
| [writing-plans](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/writing-plans/SKILL.md) | Extend | Plan a bounded change with explicit naming/version constraints. Check exact interfaces and no premature implementation. | Disable commits and implementation dispatch for this plan-only fixture. |
| [writing-skills](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/writing-skills/SKILL.md) | Extend | Revise a trigger description using supplied baseline evidence. Check trigger precision and evidence-backed claims. | Initial replay uses synthetic evidence, not nested model trials. |

**Observed pair A:** Before `2a19be0b7824ade92420e496f9127e8ad7ed19ba` →
After [`030a222af19c1f3a93c6eb876a7422d8e4fc0162`](https://github.com/obra/superpowers/commit/030a222af19c1f3a93c6eb876a7422d8e4fc0162),
committed 2025-12-18, “Fix skill descriptions: remove workflow summaries that override flowcharts.”
Seven description lines change. The historical
[`dispatching-parallel-agents`](https://github.com/obra/superpowers/blob/030a222af19c1f3a93c6eb876a7422d8e4fc0162/skills/dispatching-parallel-agents/SKILL.md)
trigger changes from three independent failures to two independent tasks.
This is selection behavior, not cosmetic metadata. Expose historical discovery
descriptions and use exactly two independent tasks to test that threshold.

**Observed pair B:** Before `03147d23992d0ae80b04fc24af67063607dfac3b` →
After [`af67e03f85baace34c5564c3bf934f45e3c2d36d`](https://github.com/obra/superpowers/commit/af67e03f85baace34c5564c3bf934f45e3c2d36d),
committed 2026-07-24, “fold systematic-debugging Related-skills block into Phase 4.”
One file moves the verification instruction to the point of use. Verification was
already required. This tests placement sensitivity, not a newly introduced requirement.

**Optional sensitivity pair:** Before `c74782ead66b8ded584d9b9cf64dcba95457f320` →
After [`3be5aad3dd2400ef23b15680969f4bcd3b6d7b8b`](https://github.com/obra/superpowers/commit/3be5aad3dd2400ef23b15680969f4bcd3b6d7b8b),
committed 2026-07-24. Nineteen persuasion/testimonial lines disappear from the
verification skill while the evidence gate remains. No difference is a valid outcome.
[Verification history](https://github.com/obra/superpowers/commits/main/skills/verification-before-completion/SKILL.md).

### Vercel — React and application behavior

Repository: [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills).
Observed stars: **31,691**. Snapshot/default branch:
[`063bee94c3f4df8453406c830b0a7df0f2860278`](https://github.com/vercel-labs/agent-skills/commit/063bee94c3f4df8453406c830b0a7df0f2860278), `main`.
The [README](https://github.com/vercel-labs/agent-skills/blob/063bee94c3f4df8453406c830b0a7df0f2860278/README.md)
and selected skill frontmatter declare MIT. No standalone license file was found.
Confirm the license text and attribution before copying bundles.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [react-best-practices](https://github.com/vercel-labs/agent-skills/blob/063bee94c3f4df8453406c830b0a7df0f2860278/skills/react-best-practices/SKILL.md) | Start | Refactor independent sequential fetches alongside one dependent fetch. Check parallelism without changing response behavior. | Local data and pinned React/Next.js. Include rule files. |
| [composition-patterns](https://github.com/vercel-labs/agent-skills/blob/063bee94c3f4df8453406c830b0a7df0f2860278/skills/composition-patterns/SKILL.md) | Extend | Refactor conflicting boolean component variants. Check state ownership and preserved consumer behavior. | Distinguish React 18 and 19 APIs. |
| [react-native-skills](https://github.com/vercel-labs/agent-skills/blob/063bee94c3f4df8453406c830b0a7df0f2860278/skills/react-native-skills/SKILL.md) | Extend | Repair a long heterogeneous list and a numeric conditional-render branch. Check virtualization and the zero-item state. | Static review is bounded. Performance claims need a device/emulator and measurements. |
| [react-view-transitions](https://github.com/vercel-labs/agent-skills/blob/063bee94c3f4df8453406c830b0a7df0f2860278/skills/react-view-transitions/SKILL.md) | Extend | Add a local Suspense crossfade. Compare CSS selection, blur, boundary placement, and obsolete configuration flags. | Pin framework/browser versions and bundled reference documents. |

**Observed pair:** Before `20e89cc4bb256eb7b1fcbdc68f7175284709a847` →
After [`063bee94c3f4df8453406c830b0a7df0f2860278`](https://github.com/vercel-labs/agent-skills/commit/063bee94c3f4df8453406c830b0a7df0f2860278),
2026-08-28, merge of the React View Transitions guidance update.
The patch removes blur from shared fade keyframes, narrows copied CSS to applicable
recipes, and removes advice to add an obsolete Next.js experimental flag.
It changes `SKILL.md`, references, and a compiled instruction copy. Troubleshooting
also moves between files. Compare the relevant source bundle, not generated-file
churn or the whole repository.
[Bundle history](https://github.com/vercel-labs/agent-skills/commits/main/skills/react-view-transitions).

### Expo — mobile development and recovery decisions

Repository: [expo/skills](https://github.com/expo/skills).
Observed stars: **2,635**. Snapshot/default branch:
[`c0dadf355d4caa4e1720de372f0f8766df1a8978`](https://github.com/expo/skills/commit/c0dadf355d4caa4e1720de372f0f8766df1a8978), `main`.
License: [MIT](https://github.com/expo/skills/blob/c0dadf355d4caa4e1720de372f0f8766df1a8978/LICENSE).
Some other skills contain separately attributed MIT material.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [expo-router](https://github.com/expo/skills/blob/c0dadf355d4caa4e1720de372f0f8766df1a8978/plugins/expo/skills/expo-router/SKILL.md) | Extend | Move a detail route into grouped tabs. Check preserved URLs, route-only directories, and version-appropriate imports. | Pin Expo SDK. Native visual claims require a simulator/device. |
| [expo-data-fetching](https://github.com/expo/skills/blob/c0dadf355d4caa4e1720de372f0f8766df1a8978/plugins/expo/skills/expo-data-fetching/SKILL.md) | Extend | Simulate a refresh error after cached data and a failed mutation. Check retained content, draft state, and nonblocking errors. | Local deterministic responses and pinned TanStack Query/Expo. |
| [expo-upgrade](https://github.com/expo/skills/blob/c0dadf355d4caa4e1720de372f0f8766df1a8978/plugins/expo/skills/expo-upgrade/SKILL.md) | Extend | Review an SDK upgrade with frozen peer manifests and a bare native project. Check dependency retention and destructive-command avoidance. | Planning can be offline. Builds need cached packages and native toolchains. |
| [eas-simulator](https://github.com/expo/skills/blob/c0dadf355d4caa4e1720de372f0f8766df1a8978/plugins/expo/skills/eas-simulator/SKILL.md) | Start for command-plan replay | Given a recorded Linux emulator timeout, select the next recovery command. Check headless boot and environment-variable placement. | Offline next-action evidence only. Actual EAS sessions require credentials and a paid-service budget. |

**Observed pair:** Before `cd752143d19e5a9aa71b4aaaf1cfc59226c77d6a` →
After [`efa52f0a9d2176db75992736281c77da1b714fa3`](https://github.com/expo/skills/commit/efa52f0a9d2176db75992736281c77da1b714fa3),
2026-09-24, “Boot the Android emulator headless with agent-device (#207).”
The behavior-bearing change is a row in
[`references/troubleshooting.md`](https://github.com/expo/skills/blob/efa52f0a9d2176db75992736281c77da1b714fa3/plugins/expo/skills/eas-simulator/references/troubleshooting.md).
It adds headless boot guidance and places `AGENT_DEVICE_HEADLESS` in the local
client environment. Four manifest versions also change. `SKILL.md` does not change.
[Bundle history](https://github.com/expo/skills/commits/main/plugins/expo/skills/eas-simulator).

Freeze CLI help and documentation rather than following `@latest`. Do not enable
feedback submission or create paid sessions during an offline recovery experiment.

### Remotion — animation and media workflows, rights hold

Repository: [remotion-dev/skills](https://github.com/remotion-dev/skills).
Observed stars: **4,759**. Snapshot/default branch:
[`cf49eff5d4463b33966b6618c83f7295797dd028`](https://github.com/remotion-dev/skills/commit/cf49eff5d4463b33966b6618c83f7295797dd028), `main`.
**License hold:** no license grant was found in the inspected tree, README,
package metadata, or selected entrypoints.
The [package metadata](https://github.com/remotion-dev/skills/blob/cf49eff5d4463b33966b6618c83f7295797dd028/package.json)
identifies `remotion-dev/remotion/packages/skills` as its source.
Resolve source provenance and reuse rights before ingestion. The runtime's license
does not automatically establish rights for the skill distribution.

| Specific skill and exact source | Priority | Proposed replay after rights clearance | Requirements and limits |
| --- | --- | --- | --- |
| [remotion-markup](https://github.com/remotion-dev/skills/blob/cf49eff5d4463b33966b6618c83f7295797dd028/skills/remotion-markup/SKILL.md) | Hold | Animate a local title card with motion blur. Check API choice, frame sampling, and child placement. | Pin Remotion and browser. Use local media. |
| [remotion-interactivity](https://github.com/remotion-dev/skills/blob/cf49eff5d4463b33966b6618c83f7295797dd028/skills/remotion-interactivity/SKILL.md) | Hold | Make SVG path keyframes editable. Check `Interactive.Path` and inline interpolation. | Actual editability requires Studio interaction, not only rendered output. |
| [remotion-captions](https://github.com/remotion-dev/skills/blob/cf49eff5d4463b33966b6618c83f7295797dd028/skills/remotion-captions/SKILL.md) | Hold | Import a local SRT. Check timing units and render-delay completion/error handling. | Avoid transcription services and model downloads. |
| [remotion-render](https://github.com/remotion-dev/skills/blob/cf49eff5d4463b33966b6618c83f7295797dd028/skills/remotion-render/SKILL.md) | Hold | Request selected frames as PNG. Compare still/frame export against an unnecessary full video render. | Installed CLI, browser, codecs, fonts, and local media for execution. |

**Observed pair:** Before `41b22eec767aa77eb31df62ccb3bacf52ed771fb` →
After [`cf49eff5d4463b33966b6618c83f7295797dd028`](https://github.com/remotion-dev/skills/commit/cf49eff5d4463b33966b6618c83f7295797dd028),
2026-09-25, “Update template.”
Despite the generic title, the patch adds SVG-editability instructions and a
motion-blur reference. It also updates versions and duplicate umbrella references.
The new motion-blur API requires Remotion 4.0.529 according to the source. Hold that
runtime constant across both instruction versions.
[Markup history](https://github.com/remotion-dev/skills/commits/main/skills/remotion-markup).

Deduplicate the exported repository, monorepo source, and umbrella `REFERENCE.md`
copies. They are not independent examples.

### Supabase — SQL security and platform authentication

Repository: [supabase/agent-skills](https://github.com/supabase/agent-skills).
Observed stars: **2,659**. Snapshot/default branch:
[`544bfc56c89afe2b87b20017a59b2c6e9502a1fb`](https://github.com/supabase/agent-skills/commit/544bfc56c89afe2b87b20017a59b2c6e9502a1fb), `main`.
License: [MIT](https://github.com/supabase/agent-skills/blob/544bfc56c89afe2b87b20017a59b2c6e9502a1fb/LICENSE).
The inspected tree contains two `SKILL.md` entrypoints. Both are listed here.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [supabase-postgres-best-practices](https://github.com/supabase/agent-skills/blob/544bfc56c89afe2b87b20017a59b2c6e9502a1fb/skills/supabase-postgres-best-practices/SKILL.md) | Start | Review an RLS membership helper. Check ownership predicates, function placement, privilege reasoning, and executable authorization behavior. | Disposable Postgres with representative roles/auth functions. References also cover pagination and composite indexes. |
| [supabase](https://github.com/supabase/agent-skills/blob/544bfc56c89afe2b87b20017a59b2c6e9502a1fb/skills/supabase/SKILL.md) | Extend | Plan browserless CLI/MCP authentication using frozen permission documentation. Check scoped credentials and environment-token precedence. | Offline plan assessment does not prove actual token permissions or remote migrations. |

**Observed pair A:** Before `daaed4afe2c78cbdbf92a98f43540cb0293b512d` →
After [`133f43e8c2ffc48823ff0630c692cabecea3e3a3`](https://github.com/supabase/agent-skills/commit/133f43e8c2ffc48823ff0630c692cabecea3e3a3),
2026-05-19, “cover SECURITY DEFINER, auth.role() deprecation, and BOLA.”
The two-file patch changes the platform checklist and
[`security-rls-performance.md`](https://github.com/supabase/agent-skills/blob/133f43e8c2ffc48823ff0630c692cabecea3e3a3/skills/supabase-postgres-best-practices/references/security-rls-performance.md).
It moves a helper to `private`, adds privilege revocation, and warns against
permission-error workarounds. Check both unauthorized denial and intended-user
access. Do not assume that the newer privilege guidance preserves functionality.

**Observed pair B:** Before `8331f910845103c08d51f6ca1d86ebb7d1f745e3` →
After [`551274ed2fe97c8fea1325f7ceb05803a542f8df`](https://github.com/supabase/agent-skills/commit/551274ed2fe97c8fea1325f7ceb05803a542f8df),
2026-09-24, “recommend scoped personal access tokens for the Management API, CLI, and MCP.”
Six added lines prefer scoped tokens and explain login, environment precedence,
and permission diagnosis. This is a small instruction-only candidate.
[Platform history](https://github.com/supabase/agent-skills/commits/main/skills/supabase).

### Trail of Bits — security reasoning and coverage honesty

Repository: [trailofbits/skills](https://github.com/trailofbits/skills).
Observed stars: **7,282**. Snapshot/default branch:
[`82fe8226252622fa807643bdca1710901198553a`](https://github.com/trailofbits/skills/commit/82fe8226252622fa807643bdca1710901198553a), `main`.
License: [CC-BY-SA-4.0](https://github.com/trailofbits/skills/blob/82fe8226252622fa807643bdca1710901198553a/LICENSE).
Preserve attribution, change notices, and applicable share-alike obligations.
Test-fixture skills inside this repository are not additional production-skill sources.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [differential-review](https://github.com/trailofbits/skills/blob/82fe8226252622fa807643bdca1710901198553a/plugins/differential-review/skills/differential-review/SKILL.md) | Start | Remove an ownership check in a small Git fixture. Check historical regression analysis, callers, and scoped coverage claims. | Local Git history and pinned methodology/reporting references. |
| [sharp-edges](https://github.com/trailofbits/skills/blob/82fe8226252622fa807643bdca1710901198553a/plugins/sharp-edges/skills/sharp-edges/SKILL.md) | Start | Review an OTP API where zero disables expiry. Distinguish a dangerous default from an invented implementation vulnerability. | Read-only fixture. No scanner required. |
| [property-based-testing](https://github.com/trailofbits/skills/blob/82fe8226252622fa807643bdca1710901198553a/plugins/property-based-testing/skills/property-based-testing/SKILL.md) | Extend | Repair a vacuous canonicalizer property test. Check meaningful invariants and valid-input generation. | Preinstalled bounded PBT runtime. Do not install a dependency without authorization. |
| [semgrep](https://github.com/trailofbits/skills/blob/82fe8226252622fa807643bdca1710901198553a/plugins/static-analysis/skills/semgrep/SKILL.md) | Start for report-only replay | Supply zero findings plus a nonempty oversized-files list. Check that skipped files remain coverage gaps. | Full scanning needs Semgrep, cached rules, and helpers. Pro scanning is optional and credentialed. |

**Observed pair:** Before `ed01a6bca3361fd937cd7d5f05a58cb1abffe509` →
After [`82fe8226252622fa807643bdca1710901198553a`](https://github.com/trailofbits/skills/commit/82fe8226252622fa807643bdca1710901198553a),
2026-09-28, “Scan files over 1 MB, and report the ones still skipped.”
Nine files change. Instructions require reporting oversized files, while scanner
code also changes the size limit and emits new fields. For an instruction experiment,
hold recorded scanner outputs and executable tools constant. For historical bundle
replay, retain the code change and do not attribute its effects only to prose.
[Semgrep history](https://github.com/trailofbits/skills/commits/main/plugins/static-analysis/skills/semgrep).

### Sentry — review policy and false-positive control

Repository: [getsentry/skills](https://github.com/getsentry/skills).
Observed stars: **1,023**. Snapshot/default branch:
[`8ca687957041ab9ece4562aad2b399b8dc8e4cae`](https://github.com/getsentry/skills/commit/8ca687957041ab9ece4562aad2b399b8dc8e4cae), `main`.
Root license: [Apache-2.0](https://github.com/getsentry/skills/blob/8ca687957041ab9ece4562aad2b399b8dc8e4cae/LICENSE).
The [security-review license](https://github.com/getsentry/skills/blob/8ca687957041ab9ece4562aad2b399b8dc8e4cae/skills/security-review/LICENSE)
identifies OWASP-derived CC-BY-SA material. The Django access skill declares related
terms but lacks the referenced local license file in the inspected tree.
Resolve those bundle terms before copying them.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [gha-security-review](https://github.com/getsentry/skills/blob/8ca687957041ab9ece4562aad2b399b8dc8e4cae/skills/gha-security-review/SKILL.md) | Start | Compare official actions, privileged third-party tags, read-only jobs, and untrusted local actions. Check policy classification and trust-boundary reasoning. | Static YAML plus pinned references. Never run the workflows. |
| [find-bugs](https://github.com/getsentry/skills/blob/8ca687957041ab9ece4562aad2b399b8dc8e4cae/skills/find-bugs/SKILL.md) | Extend | Provide an initially truncated diff and readable changed files. Check complete evidence gathering, middleware consideration, and no edits. | Freeze default-branch metadata rather than allowing live `gh` discovery. |
| [code-simplifier](https://github.com/getsentry/skills/blob/8ca687957041ab9ece4562aad2b399b8dc8e4cae/skills/code-simplifier/SKILL.md) | Extend | Simplify one changed function without touching its neighbor. Check all state combinations. | Anthropic-derived lineage. Deduplicate and preserve provenance. |
| [security-review](https://github.com/getsentry/skills/blob/8ca687957041ab9ece4562aad2b399b8dc8e4cae/skills/security-review/SKILL.md) | Hold for bundle licensing | Compare server-configured and user-controlled outbound URLs. Check source tracing instead of labeling both SSRF. | Mixed OWASP-derived reference terms need curation. |
| [django-access-review](https://github.com/getsentry/skills/blob/8ca687957041ab9ece4562aad2b399b8dc8e4cae/skills/django-access-review/SKILL.md) | Hold for bundle licensing | Compare tenant-scoped and global object lookups. Check object authorization rather than authentication alone. | Local Django fixture. Resolve the missing license reference. |

**Observed pair:** Before `e7a87fa72645158f9b5e722cbb1c7e09266f48f1` →
After [`7e127fe8a5d16a6800a80f9cf50f96a7324eac0e`](https://github.com/getsentry/skills/commit/7e127fe8a5d16a6800a80f9cf50f96a7324eac0e),
2026-08-08, “Pin third-party actions only.”
The Actions skill and its supply-chain reference narrow mutable-reference findings
to third-party actions in privileged jobs. They exclude first-party tags from that
specific policy. Compare both instruction files together. A local action loaded
from an untrusted PR remains a separate trust-boundary question.
[Actions skill history](https://github.com/getsentry/skills/commits/main/skills/gha-security-review).
Earlier plugin-local paths moved to root `skills/`. The `.agents/skills` symlink
does not create another independent corpus.

### Hugging Face — data handling and command planning

Repository: [huggingface/skills](https://github.com/huggingface/skills).
Observed stars: **11,113**. Snapshot/default branch:
[`80f9fa530e46f4ae642fcb9e1725bad0e1979395`](https://github.com/huggingface/skills/commit/80f9fa530e46f4ae642fcb9e1725bad0e1979395), `main`.
License: [Apache-2.0](https://github.com/huggingface/skills/blob/80f9fa530e46f4ae642fcb9e1725bad0e1979395/LICENSE).
Models, datasets, and runtime packages have separate licenses.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [huggingface-datasets](https://github.com/huggingface/skills/blob/80f9fa530e46f4ae642fcb9e1725bad0e1979395/skills/huggingface-datasets/SKILL.md) | Start for plan-only replay | Plan storage of synthetic trace JSONL. Check private visibility, project separation, and command selection. | No real home-directory traces or uploads. Freeze CLI help/API schemas. |
| [huggingface-tool-builder](https://github.com/huggingface/skills/blob/80f9fa530e46f4ae642fcb9e1725bad0e1979395/skills/huggingface-tool-builder/SKILL.md) | Extend | Build a local metadata-to-NDJSON tool with missing optional fields. Check schema handling, help, and credential hygiene. | Use fixed API response fixtures instead of live authenticated requests. |
| [hf-cli](https://github.com/huggingface/skills/blob/80f9fa530e46f4ae642fcb9e1725bad0e1979395/skills/hf-cli/SKILL.md) | Extend | Plan inspection and dry-run cleanup of a disposable cache. Check supported syntax and scope. | Generated from CLI versions. Full skill includes token display, deletes, uploads, and paid jobs. |
| [huggingface-community-evals](https://github.com/huggingface/skills/blob/80f9fa530e46f4ae642fcb9e1725bad0e1979395/skills/huggingface-community-evals/SKILL.md) | Hold for execution | Given no CUDA GPU, request a bounded evaluation plan. Check resource-gap disclosure and no unauthorized provider use. | Actual evaluation needs model downloads/GPU or credentialed inference. No nested evaluation runs in the first corpus. |

**Observed pair:** Before `acd2bf5a7126994e15143bec061fe87a882811f3` →
After [`b3df145a3a5a3e64ac075d781c625896d9d2bfcd`](https://github.com/huggingface/skills/commit/b3df145a3a5a3e64ac075d781c625896d9d2bfcd),
committed 2026-04-30, “update dataset skill guidance.”
One skill file replaces a Parquet workflow with `hf` CLI guidance and adds private
trace-dataset defaults with project/cwd nesting. It is a clean instruction-only
candidate for command-plan comparison. Never upload the synthetic fixture as part
of this first experiment.
[Dataset history](https://github.com/huggingface/skills/commits/main/skills/huggingface-datasets/SKILL.md).
Follow earlier skill renames. Generated fallback bundles are not separate sources.

### Cloudflare — Worker review and local/remote boundaries

Repository: [cloudflare/skills](https://github.com/cloudflare/skills).
Observed stars: **2,935**. Snapshot/default branch:
[`626547c06881a20b3322bdc2ed6e6451b33a4fb6`](https://github.com/cloudflare/skills/commit/626547c06881a20b3322bdc2ed6e6451b33a4fb6), `main`.
License: [Apache-2.0](https://github.com/cloudflare/skills/blob/626547c06881a20b3322bdc2ed6e6451b33a4fb6/LICENSE).

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [workers-best-practices](https://github.com/cloudflare/skills/blob/626547c06881a20b3322bdc2ed6e6451b33a4fb6/skills/workers-best-practices/SKILL.md) | Start | Review a local Worker with insecure token generation and request-state leakage. Check concrete findings against safe counterexamples. | Pin types, compatibility date, and retrieved references. No deployment needed. |
| [durable-objects](https://github.com/cloudflare/skills/blob/626547c06881a20b3322bdc2ed6e6451b33a4fb6/skills/durable-objects/SKILL.md) | Extend | Review initialization and a missing SQLite-class migration in a local counter. Check fixes and relevant local tests. | Runtime proof needs local Workers tooling and explicit local bindings. |
| [wrangler](https://github.com/cloudflare/skills/blob/626547c06881a20b3322bdc2ed6e6451b33a4fb6/skills/wrangler/SKILL.md) | Extend | Request a local-only test plan with a remote D1 binding present. Check remote-write risk and project-local version choice. | No credentials or deploys. Local mode alone does not guarantee local bindings. |

**Observed pair:** Before `59b74b9f5362052f0d21ae47614b83b4021cd9af` →
After [`42839d0d791a58bcccb1fa44b201a4468ba6ab10`](https://github.com/cloudflare/skills/commit/42839d0d791a58bcccb1fa44b201a4468ba6ab10),
2026-09-05, “Restore concrete Workers anti-patterns in skill entrypoint.”
One file replaces generic pitfalls with explicit checks, including security-token
randomness, hardcoded secrets, and destructured context methods. No executable
companion changes. This is a strong instruction-only review candidate.
[Workers history](https://github.com/cloudflare/skills/commits/main/skills/workers-best-practices/SKILL.md).
Historical references have different filenames from current ones. Pin the historical
bundle and the clock used for compatibility-date advice.

### Microsoft — Python SDK and application patterns

Repository: [microsoft/skills](https://github.com/microsoft/skills).
Observed stars: **3,063**. Default branch: `main`. Public, non-fork, not archived.
Snapshot: [`23d0dac5f83f268166a17f0bc7dc6c73dc348a33`](https://github.com/microsoft/skills/commit/23d0dac5f83f268166a17f0bc7dc6c73dc348a33).
License: [MIT](https://github.com/microsoft/skills/blob/23d0dac5f83f268166a17f0bc7dc6c73dc348a33/LICENSE).
The three selected skills also declare MIT in their frontmatter. Other plugin
bundles have their own license files, so this is not blanket clearance for the repository.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [fastapi-router-py](https://github.com/microsoft/skills/blob/23d0dac5f83f268166a17f0bc7dc6c73dc348a33/.github/plugins/azure-sdk-python/skills/fastapi-router-py/SKILL.md) | Start | Give an endpoint a synchronous blocking dependency. Compare handler choice, blocking calls inside async handlers, and resource lifetime management. | Pin Python and FastAPI. Use a local dependency, not Azure. |
| [pydantic-models-py](https://github.com/microsoft/skills/blob/23d0dac5f83f268166a17f0bc7dc6c73dc348a33/.github/plugins/azure-sdk-python/skills/pydantic-models-py/SKILL.md) | Extend | Generate a small request/update/response model set. Check alias acceptance, optional update fields, and importable output with runtime assertions. | Pin Pydantic v2. Include the referenced template in bundle comparisons. |
| [azure-identity-py](https://github.com/microsoft/skills/blob/23d0dac5f83f268166a17f0bc7dc6c73dc348a33/.github/plugins/azure-sdk-python/skills/azure-identity-py/SKILL.md) | Extend | Review an async client with a sync credential and missing cleanup. Compare credential selection and context-manager use. | Static or local SDK checks can avoid credentials. Actual Azure authentication needs a separate authorized environment. |

**Observed history examples:**

- **2026-04-24:** [`8ae5031f98413bcb3a8e17d0a87c655e51c23b96`](https://github.com/microsoft/skills/commit/8ae5031f98413bcb3a8e17d0a87c655e51c23b96),
  “add python best practice and update python skills accordingly.”
  Before: `7d736cbd13e586462eac0c22d6eada4f7a0e435a`.
  The FastAPI patch adds sync/async selection and lifespan/dependency guidance.
  The full commit touches 43 files. Projecting only this skill's instruction patch
  is a proposed controlled comparison, not replaying the full repository change.
- **2026-07-28:** [`4a2873faffc1b101a33a0b59c24713d4ed78142f`](https://github.com/microsoft/skills/commit/4a2873faffc1b101a33a0b59c24713d4ed78142f),
  “Add Vally skill-effectiveness experiments and Python test scenarios (#383).”
  Before: `0ba2f485864a8c53f1d5a2a02615c027da4fb33d`.
  The Pydantic patch replaces nested configuration examples with `ConfigDict` and
  adds imports. The template also changes. This 187-file commit is a mixed bundle
  and evaluation change, not a clean single-file baseline.

[FastAPI history](https://github.com/microsoft/skills/commits/main/.github/plugins/azure-sdk-python/skills/fastapi-router-py/SKILL.md)
contains five path entries in the inspected history. The oldest entry reorganizes
skills, so earlier history needs rename-aware discovery.

**Useful upstream scenario leads, not trusted grading data:**
[FastAPI scenarios](https://github.com/microsoft/skills/blob/4a2873faffc1b101a33a0b59c24713d4ed78142f/tests/scenarios/fastapi-router-py/scenarios.yaml)
and [Pydantic scenarios](https://github.com/microsoft/skills/blob/4a2873faffc1b101a33a0b59c24713d4ed78142f/tests/scenarios/pydantic-models-py/scenarios.yaml).
They contain prompts, expected patterns, and `mock_response` fields. Some prompts
explicitly request the target pattern. Some Pydantic patterns still expect nested
`Config` despite the skill's `ConfigDict` change. These examples need independent
curation and runtime checks. Their mock answers are not real trial evidence.

### Matt Pocock — clarification, debugging, and evidence contracts

Repository: [mattpocock/skills](https://github.com/mattpocock/skills).
Observed stars: **271,478**. Snapshot/default branch:
[`c55ee46073ed923f86ce59a5eb3b6d895095d1b7`](https://github.com/mattpocock/skills/commit/c55ee46073ed923f86ce59a5eb3b6d895095d1b7), `main`.
License: [MIT](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/LICENSE).
The PR skill credits HumanLayer's `show-me`. Preserve that provenance and notices.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [pr](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/in-progress/pr/SKILL.md) | Start | Draft a PR body from a small diff and recorded test evidence. Check specific proof and no invented failing-before results. | Text-only, no PR creation. Upstream marks the skill in-progress. |
| [grilling](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/productivity/grilling/SKILL.md) | Extend | Present two independent decisions and one dependent decision. Check question batching and waiting across two scripted rounds. | Requires a controlled interview/tool surface. `grill-me` is a wrapper, not another independent implementation. |
| [diagnosing-bugs](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/diagnosing-bugs/SKILL.md) | Extend | Reproduce a local parser failure from a synthetic log containing a fake token. Check diagnosis order and artifact redaction. | Bounded local commands. No production instrumentation. |

**Observed pair:** Before `73a3e94e6a51b041948fbdcae01128f7fdbd1ac4` →
After [`35f592643946a5dce0ce8d7773afaa232a2eb13d`](https://github.com/mattpocock/skills/commit/35f592643946a5dce0ce8d7773afaa232a2eb13d),
2026-09-17, “update execution evidence description to include pseudocode of test steps.”
Only the PR skill changes. It replaces generic steps/outcomes guidance with a
specific failing/passing-test explanation. Grade evidential support and specificity,
not a required Markdown phrase or invented proof.
[PR skill history](https://github.com/mattpocock/skills/commits/main/skills/in-progress/pr/SKILL.md).

### gstack — context-aware planning, with runtime dependencies

Repository: [garrytan/gstack](https://github.com/garrytan/gstack).
Observed stars: **134,438**. Snapshot/default branch:
[`65bfb0ce49da807698359ca033a05709e342c684`](https://github.com/garrytan/gstack/commit/65bfb0ce49da807698359ca033a05709e342c684), `main`.
License: [MIT](https://github.com/garrytan/gstack/blob/65bfb0ce49da807698359ca033a05709e342c684/LICENSE),
with [third-party notices](https://github.com/garrytan/gstack/blob/65bfb0ce49da807698359ca033a05709e342c684/NOTICE.md)
for Apache-derived material elsewhere in the repository.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [office-hours](https://github.com/garrytan/gstack/blob/65bfb0ce49da807698359ca033a05709e342c684/office-hours/SKILL.md) | Extend | Supply known product facts but missing demand evidence. Check whether the first question targets missing information. | Fixed preflight outputs and scripted answers. No live brain service or onboarding. |
| [plan-ceo-review](https://github.com/garrytan/gstack/blob/65bfb0ce49da807698359ca033a05709e342c684/plan-ceo-review/SKILL.md) | Extend | Review a small export plan with HOLD SCOPE and a prior no-cloud-sync decision. Check scope and conflict handling. | Pin goals/context and stop before external research or roadmap writes. |
| [plan-eng-review](https://github.com/garrytan/gstack/blob/65bfb0ce49da807698359ca033a05709e342c684/plan-eng-review/SKILL.md) | Extend | Present an ambiguous review request with both a diff and unrelated plan. Check target selection before tools. | Pin genuine host metadata. Text claiming “plan mode” is not host metadata. |

**Observed pair:** Before `ce5fbfa99ffb82fe445cae23a398a130dd643952` →
After [`070722ace3989d5db9c66620c56504783ae64a07`](https://github.com/garrytan/gstack/commit/070722ace3989d5db9c66620c56504783ae64a07),
2026-05-29, “brain-aware planning — 5 skills read structured gbrain context before asking.”
Generated instructions add preflight context, skip answered questions, and surface
conflicting prior decisions. This 44-file commit also changes runtime code and tests.
For a bounded instruction projection, supply fixed context-tool results and stop
after the first interview question. That does not validate the brain implementation.
[Office-hours history](https://github.com/garrytan/gstack/commits/main/office-hours/SKILL.md).

These `SKILL.md` files are generated from templates and sections. Preserve the
consumed output and generation provenance. Do not count generated/source copies twice.
Full skills include helper commands and external integrations, so a complete install
is not equivalent to the proposed bounded replay.

### Marketing Skills — context reuse and evidence calibration

Repository: [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills).
Observed stars: **51,836**. Snapshot/default branch:
[`5b2c0007766c6a1cf1d53fd8fc73e979e0821022`](https://github.com/coreyhaines31/marketingskills/commit/5b2c0007766c6a1cf1d53fd8fc73e979e0821022), `main`.
License: [MIT](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/LICENSE).
Linked studies have separate provenance and are not verified by this survey.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [ai-seo](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/ai-seo/SKILL.md) | Start for planning replay | Prioritize six pages from a fictional backlog and one recorded AI answer. Check uncertainty, sample-size awareness, and qualified recommendations. | Freeze reference bundle and product context. No live search or nested model sampling. |
| [seo-audit](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/seo-audit/SKILL.md) | Extend | Supply static HTML extraction and rendered JSON-LD evidence. Check that missing script tags in extraction do not prove missing schema. | Local pages/browser evidence. No Search Console or live crawling. |
| [copywriting](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/copywriting/SKILL.md) | Extend | Draft a hero section from existing product context without quantified savings. Check context reuse and no fabricated testimonials. | Text-only synthetic context. No ads, posting, or marketing accounts. |

**Observed pair:** Before `5cd4a7eae3a9a7b5d2aceb0613f7d1f7c4b65968` →
After [`5b2c0007766c6a1cf1d53fd8fc73e979e0821022`](https://github.com/coreyhaines31/marketingskills/commit/5b2c0007766c6a1cf1d53fd8fc73e979e0821022),
2026-09-05 UTC, “ai-seo 2.5.0 — ChatGPT 5.6 format-volatility guidance.”
The skill and a new reference qualify format claims by platform/date and recommend
repeated observations with reported sample sizes. Six files also include version
and evaluation changes. Compare the instruction/reference bundle, not those eval answers.
Treat external performance statistics as upstream claims, not established facts.
[AI-SEO history](https://github.com/coreyhaines31/marketingskills/commits/main/skills/ai-seo).

### HashiCorp — local Terraform and policy validation

Repository: [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills).
Observed stars: **878**. Snapshot/default branch:
[`f706481af9b8fedb66de909f6243ad29601afa0c`](https://github.com/hashicorp/agent-skills/commit/f706481af9b8fedb66de909f6243ad29601afa0c), `main`.
License: [MPL-2.0](https://github.com/hashicorp/agent-skills/blob/f706481af9b8fedb66de909f6243ad29601afa0c/LICENSE).
Preserve covered-file notices and applicable distribution obligations. Product
licensing must not be substituted for this repository's actual license.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [terraform-test](https://github.com/hashicorp/agent-skills/blob/f706481af9b8fedb66de909f6243ad29601afa0c/plugins/terraform/skills/terraform-test/SKILL.md) | Extend | Test a provider-free locals/outputs module in plan mode. Check assertions and expected validation failures. | Pin Terraform. Default apply can create resources. Mocks still need provisioned schemas. |
| [terraform-style-guide](https://github.com/hashicorp/agent-skills/blob/f706481af9b8fedb66de909f6243ad29601afa0c/plugins/terraform/skills/terraform-style-guide/SKILL.md) | Extend | Repair typed inputs, descriptions, and formatting in a local HCL module. Check with local formatting/validation tools. | No backend, cloud provider, or apply operation. |
| [terraform-policy](https://github.com/hashicorp/agent-skills/blob/f706481af9b8fedb66de909f6243ad29601afa0c/plugins/terraform/skills/terraform-policy/SKILL.md) | Extend | Repair an empty mock state that skips a policy test. Check that a real assertion executes. | Pin tfpolicy 0.3.x and cached provider/schema dependencies, not just Terraform. |

**Observed pair:** Before `c2d65dfe492f74d360d35b859b88932222470bd8` →
After [`516354c484b43fa5469567485113dd0c769c3d24`](https://github.com/hashicorp/agent-skills/commit/516354c484b43fa5469567485113dd0c769c3d24),
2026-09-24, “update terraform policy skill for tfpolicy 0.3.”
Five files in the policy bundle change. Guidance adds explicit mock state,
schema-failure handling, provider declaration placement, and updated functions.
Compare the whole instruction/reference bundle against the same pinned 0.3.x tool.
[Policy history](https://github.com/hashicorp/agent-skills/commits/main/plugins/terraform/skills/terraform-policy).
This smaller official repository is included for domain coverage, not a claim of top-tier popularity.

### n8n — expression correctness and false-success detection

Repository: [czlonkowski/n8n-skills](https://github.com/czlonkowski/n8n-skills).
Observed stars: **6,346**. Snapshot/default branch:
[`19cd793f4789e3ef9c657ccf26e097f641a77df0`](https://github.com/czlonkowski/n8n-skills/commit/19cd793f4789e3ef9c657ccf26e097f641a77df0), `main`.
License: [MIT](https://github.com/czlonkowski/n8n-skills/blob/19cd793f4789e3ef9c657ccf26e097f641a77df0/LICENSE),
with [Apache-derived hook notices](https://github.com/czlonkowski/n8n-skills/blob/19cd793f4789e3ef9c657ccf26e097f641a77df0/NOTICES).
The n8n runtime has separate licensing.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [n8n-expression-syntax](https://github.com/czlonkowski/n8n-skills/blob/19cd793f4789e3ef9c657ccf26e097f641a77df0/skills/n8n-expression-syntax/SKILL.md) | Start with pinned runtime | Diagnose an empty result despite a known matching JSON record. Check literal quoting, argument order, and item wrappers. | Actual n8n runtime is needed to prove swallowed-error behavior. Plain JavaScript is insufficient. |
| [n8n-validation-expert](https://github.com/czlonkowski/n8n-skills/blob/19cd793f4789e3ef9c657ccf26e097f641a77df0/skills/n8n-validation-expert/SKILL.md) | Extend | Interpret a validator warning without breaking a valid webhook response route. Check real errors versus false positives. | Fixed diagnostics for reasoning. Actual validation needs compatible n8n-mcp. |
| [n8n-code-javascript](https://github.com/czlonkowski/n8n-skills/blob/19cd793f4789e3ef9c657ccf26e097f641a77df0/skills/n8n-code-javascript/SKILL.md) | Extend | Aggregate local JSON with missing and zero values. Check All Items mode and returned item wrappers. | Pin the Code-node runtime. No HTTP nodes or external credentials. |

**Observed pair:** Before `3b3d6a758472b1822f70acff2f5f4dc361e1a43f` →
After [`470e9aa25bb36c03df6bfeb0d04f3610fe9b303a`](https://github.com/czlonkowski/n8n-skills/commit/470e9aa25bb36c03df6bfeb0d04f3610fe9b303a),
2026-09-16, “$jmespath, silent-null expression errors, error-output blind spots, validator false positives.”
The patch adds literal-string quoting, wrapper access, and green-execution/null-output
diagnostics. Fifteen files span several skills and new evals. Project the expression
skill directory, or explicitly isolate its changed `SKILL.md`. Keep expected eval
answers outside the trial workspace.
[Expression history](https://github.com/czlonkowski/n8n-skills/commits/main/skills/n8n-expression-syntax).
The commit's observations refer to n8n 2.38.5. They were not reproduced in this survey.

### K-Dense — bounded scientific data analysis

Repository: [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills).
Observed stars: **47,036**. Snapshot/default branch:
[`065b734670d7d990627dbc06a05b5a99be33f1f1`](https://github.com/K-Dense-AI/scientific-agent-skills/commit/065b734670d7d990627dbc06a05b5a99be33f1f1), `main`.
The former `claude-scientific-skills` URL redirects here. Treat both names as one lineage.
Root license: [MIT](https://github.com/K-Dense-AI/scientific-agent-skills/blob/065b734670d7d990627dbc06a05b5a99be33f1f1/LICENSE.md).
Individual skills can differ. EDA declares MIT, NetworkX declares BSD-3-Clause,
and Matplotlib points to external project license material that needs separate review.
No repository license grants rights to external scientific datasets.

| Specific skill and exact source | Priority | Proposed replay and observable evidence | Requirements and limits |
| --- | --- | --- | --- |
| [exploratory-data-analysis](https://github.com/K-Dense-AI/scientific-agent-skills/blob/065b734670d7d990627dbc06a05b5a99be33f1f1/skills/exploratory-data-analysis/SKILL.md) | Extend | Profile a tiny synthetic CSV with missing values, repeated entities, and a data-embedded instruction. Check leakage warnings, data preservation, and bounded claims. | Python standard-library core, local approved root. Bundle code changes complicate instruction attribution. |
| [matplotlib](https://github.com/K-Dense-AI/scientific-agent-skills/blob/065b734670d7d990627dbc06a05b5a99be33f1f1/skills/matplotlib/SKILL.md) | Hold for license capture | Plot supplied arrays with units and two axes. Check data/labels and rendered output, not exact image bytes. | Review referenced license. Pin Matplotlib/NumPy and headless Agg. |
| [networkx](https://github.com/K-Dense-AI/scientific-agent-skills/blob/065b734670d7d990627dbc06a05b5a99be33f1f1/skills/networkx/SKILL.md) | Extend | Analyze a ten-edge weighted directed graph. Check weighted paths and disconnected-component semantics. | Pin Python/NetworkX and preserve BSD terms. No downloaded networks or GPU. |

**Observed pair:** Before `025a3a627c56a425954c4ddb2a4aceb70efeb566` →
After [`cadf380493b3768e358b9cd6b45aa0441e23348b`](https://github.com/K-Dense-AI/scientific-agent-skills/commit/cadf380493b3768e358b9cd6b45aa0441e23348b),
2026-07-24 UTC, “Update exploratory data analysis workflows.”
The rewrite narrows supported formats, adds a network-free core, treats input as
untrusted data, and prohibits automatic imputation/removal and unsupported causal claims.
Twenty-four files include scripts, references, templates, and tests. Use a faithful
EDA bundle comparison for execution, or label an instruction-only projection with
a fixed independent tool layer. Do not silently mix old prose with new helpers.
[EDA history](https://github.com/K-Dense-AI/scientific-agent-skills/commits/main/skills/exploratory-data-analysis).

## Turning a candidate into replay data

1. Record the canonical repository, source license, skill path, and bundle boundaries.
2. Select a behavior-relevant noninitial commit and its exact parent.
3. Read the patch and any linked PR rationale. Separate observed changes from inferred intent.
4. Follow renames and inspect companion files before declaring a single-file experiment.
5. Choose instruction-only or whole-bundle comparison explicitly. Keep unrelated project context identical.
6. Recreate the decision moment with a small synthetic or sanitized fixture.
7. Keep expected outcomes and the patch rationale out of the trial prompt.
8. Check that each host loads the intended skill revision, not a cached or globally installed copy.
9. Run fresh repeated trials only after approval of model cost and data access.
10. Preserve blocked and inconclusive results rather than converting them into failures or successes.

For every admitted case, retain:

- Repository, skill identity, Before/After commit SHAs, and Before/After paths.
- License and attribution evidence for both revisions and any bundled assets.
- Changed-file list and the exact bundle or projected instruction patch under test.
- Fixture revision, prompt, expected observable behavior, and a human-reviewed rationale.
- Agent host, model, tool permissions, dependency versions, and skill-loading method.
- Trial counts, raw evidence provenance, blocked reasons, and report location.

A skill repository is often not the task workspace. Install the pinned skill into
a separate fixture project with the same loading method on both sides. Do not
assume that cloning a skill catalog causes Claude Code or Codex to discover it.

Check **selection** and **execution** separately. A normal request tests whether a
host chooses the skill. An explicit invocation tests its workflow after selection.
Forcing a skill to load cannot establish that its trigger description works.

Include an unchanged-skill A/A comparison to estimate trial variability. Add an
unaffected task and a negative-trigger task. Three trials per side can expose
patterns, but do not establish statistical significance or causal certainty.

## Exclusions and safeguards

- Use [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills)
  and [skills.sh](https://skills.sh/) for discovery, not as canonical revision histories.
- Do not count marketplace mirrors, generated copies, or repeated imports as independent cases.
- Skip initial additions, bulk moves, packaging-only changes, and cosmetic edits
  for the first behavioral dataset. Metadata changes can affect selection, so they
  need a selection experiment rather than an automatic “no effect” label.
- Treat custom, mixed, or missing licenses as collection holds until the specific
  reuse is approved. Public readability is not redistribution permission.
- Review scripts and hooks as untrusted code. Do not expose credentials, production
  services, paid training jobs, live deployments, publishing accounts, or destructive tools.
- External documents can change without a Git commit. Pin required reference
  material where permitted, or record that the case is not reproducible offline.
- Keep train/development and held-out cases separated by skill lineage or repository.
  Near-duplicate forks and adjacent revisions can leak the same rule across splits.
- Do not use a model's explanation as the sole grading oracle. Prefer executable
  fixture checks and captured actions, with a human rubric for subjective outcomes.
- Do not commit real runs or transcripts. Future model-backed replay remains manual,
  not part of this repository's deterministic CI.
