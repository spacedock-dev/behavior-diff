// Source-history snapshot. Update deliberately after auditing new commits.
window.behaviorDiffHistory = {
  "repository": "https://github.com/spacedock-dev/behavior-diff",
  "head": "b561e35b373d6f878f4c7bb515209123bdba01fa",
  "entries": [
    {
      "sha": "ba6c2addcb2b053ef604ddf8957840f19f5ef3af",
      "date": "2026-09-02",
      "title": "Bring Behavior Diff into its own repository",
      "category": "Maintenance",
      "why": "The commit separates Behavior Diff from Engram.",
      "whyBasis": "commit",
      "what": "The existing standard and live comparison skills become the repository baseline.",
      "how": "It imports the skill instructions, sandbox and trial scripts, model-backed decision extraction, and report renderer from the named Engram revision.",
      "role": "The host prepares a task and requests approval; the existing extractor compares choices without being shown the instruction diff.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff-live/SKILL.md",
        "plugin/skills/behavior-diff/scripts/behavior-diff.sh",
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/render.py",
        "plugin/skills/behavior-diff/scripts/run-trial.sh"
      ]
    },
    {
      "sha": "588f6aba21f3dd601536dff3b0b0ccc902a5e373",
      "date": "2026-09-02",
      "title": "Give Behavior Diff its own name",
      "category": "Maintenance",
      "why": "The project needed a standalone identity after the split.",
      "whyBasis": "inferred",
      "what": "Documentation and report wording stop calling the project an Engram proof of concept.",
      "how": "Skill instructions, comments, docstrings, and the report footer use the Behavior Diff name.",
      "role": "The pipeline still presents evidence for the user to judge.",
      "files": [
        "plugin/skills/behavior-diff-live/SKILL.md",
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/references/spacedock-duo.md",
        "plugin/skills/behavior-diff/scripts/render.py"
      ]
    },
    {
      "sha": "9e422c9edd5f2e518561da5531dab25533b5b927",
      "date": "2026-09-02",
      "title": "Normalize script formatting",
      "category": "Maintenance",
      "why": "Consistent formatting makes shell and Python scripts easier to maintain.",
      "whyBasis": "inferred",
      "what": "The existing scripts are reformatted.",
      "how": "Shell case branches and Python layout are expanded and normalized.",
      "role": "The scripts retain their trial, extraction, and reporting responsibilities.",
      "files": [
        "plugin/skills/behavior-diff/scripts/behavior-diff.sh",
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/make-capsule.sh",
        "plugin/skills/behavior-diff/scripts/render.py",
        "plugin/skills/behavior-diff/scripts/run-trial.sh"
      ]
    },
    {
      "sha": "afc28eeef9fce2a92e51bbbcbd1b860a008ad56d",
      "date": "2026-09-02",
      "title": "Show decision self-check progress",
      "category": "Maintenance",
      "why": "Detailed progress makes unit checks easier to follow.",
      "whyBasis": "inferred",
      "what": "The decision extractor's self-check prints its current phase.",
      "how": "A flushing progress helper labels normalization, synthetic traces, provenance, errors, ingestion, and incomplete-trial checks.",
      "role": "Only self-check output changes; decision extraction keeps its existing role.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py"
      ]
    },
    {
      "sha": "e60fe022bac82b9099717752c3b059a7a962c63f",
      "date": "2026-09-02",
      "title": "Start without a run-mode confirmation",
      "category": "Preparation",
      "why": "Removing the mode prompt simplifies the run experience.",
      "whyBasis": "inferred",
      "what": "The standard skill stops asking for confirmation of file, task, cost, or run mode and starts once the task is known.",
      "how": "It preserves the current host and uses the regular run unless the user explicitly requests fast mode.",
      "role": "The host prepares the task and launches the runner without the previous approval step.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md"
      ]
    },
    {
      "sha": "03ccd6d7c9403ca0274403abfaeb8d5cfa94f9af",
      "date": "2026-09-02",
      "title": "Clarify Spacedock fixtures",
      "category": "Preparation",
      "why": "The fixture guidance needed clearer terminology and instructions.",
      "whyBasis": "inferred",
      "what": "The skills clarify how to prepare isolated Spacedock comparison fixtures.",
      "how": "They direct the host to the renamed make-spacedock-fixtures.sh and require the real Spacedock binary to create workflow state rather than hand editing it.",
      "role": "The skills guide fixture preparation; Spacedock creates the fixture state.",
      "files": [
        "plugin/skills/behavior-diff-live/SKILL.md",
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/references/spacedock-duo.md",
        "plugin/skills/behavior-diff/scripts/make-spacedock-fixtures.sh"
      ]
    },
    {
      "sha": "9203d4051632e6ae57d40a51996c357050da1084",
      "date": "2026-09-03",
      "title": "Accept Pi and OMP trial stacks",
      "category": "Execution",
      "why": "Comparisons needed to accept Pi and OMP as trial stacks.",
      "whyBasis": "inferred",
      "what": "The comparison entry point accepts Pi and OMP trials.",
      "how": "It validates the new stack names, requires their exact model IDs, and initially defaults extraction to the same stack and model.",
      "role": "The entry point selects and coordinates the trial and extraction stacks.",
      "files": [
        "plugin/skills/behavior-diff/scripts/behavior-diff.sh"
      ]
    },
    {
      "sha": "ed3dcad1369f039327d183cb34819f17e791f666",
      "date": "2026-09-03",
      "title": "Normalize Pi and OMP trial traces",
      "category": "Execution",
      "why": "Different trial stacks produce traces that need a common representation.",
      "whyBasis": "inferred",
      "what": "Pi and OMP trials feed the existing comparison pipeline.",
      "how": "The runner launches each host in JSON mode and converts tool-start events and the final assistant message into the shared trace.jsonl shape.",
      "role": "The runner collects and normalizes evidence for later assessment.",
      "files": [
        "plugin/skills/behavior-diff/scripts/run-trial.sh"
      ]
    },
    {
      "sha": "c6d266be232fa1ccd48ada697473917d7d66dcf0",
      "date": "2026-09-03",
      "title": "Extract decisions with Pi and OMP",
      "category": "Assessment",
      "why": "Decision extraction needed to support the additional stacks.",
      "whyBasis": "inferred",
      "what": "The existing decision extractor can use Pi or OMP.",
      "how": "It adds no-tools, no-session CLI calls with explicit model IDs and keeps explicit extractor selection pinned without cross-fallback.",
      "role": "The extractor continues to assess choices; model-backed extraction existed before this commit.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py"
      ]
    },
    {
      "sha": "c4f551d585df43e7740ef30962a2f8445f890777",
      "date": "2026-09-03",
      "title": "Define trial stack ownership",
      "category": "Preparation",
      "why": "The responsibilities around trial stacks and host dispatch needed clearer documentation.",
      "whyBasis": "inferred",
      "what": "The skills define who chooses the stack and how live trials run on different hosts.",
      "how": "The standard skill assigns judgment to the skill and mechanics to scripts; the live skill describes Claude and OMP dispatch and Pi and Codex alternatives.",
      "role": "The skill owns task and stack judgment; scripts own repeatable trial, extraction, and reporting mechanics.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff-live/SKILL.md"
      ]
    },
    {
      "sha": "94c4c8774df95af7fe31cf20fc77b45bb2b63a19",
      "date": "2026-09-03",
      "title": "Preserve extraction contracts across hosts",
      "category": "Assessment",
      "why": "Pi and OMP extraction contracts needed to be preserved.",
      "whyBasis": "commit",
      "what": "The runner and live skill correct extraction handling for these host paths.",
      "how": "The live skill skips extraction rather than launching another CLI when Codex has no subagent dispatch; the runner also changes extraction selection handling.",
      "role": "The live host reports raw trial evidence when its required extraction dispatch is unavailable rather than inventing a decision diff.",
      "files": [
        "plugin/skills/behavior-diff/scripts/behavior-diff.sh",
        "plugin/skills/behavior-diff-live/SKILL.md"
      ]
    },
    {
      "sha": "1ef39045a3b2f2d54fea0b8fb177cfaf3f4f555b",
      "date": "2026-09-04",
      "title": "Separate report rendering into modules",
      "category": "Maintenance",
      "why": "The report renderer was reorganized into clearer internal responsibilities.",
      "whyBasis": "inferred",
      "what": "Report data assembly, schema, Markdown, HTML, and styles are separated.",
      "how": "A reporting package holds dedicated loading, content, validation, and rendering modules while the main renderer becomes the entry point.",
      "role": "Report rendering is split internally while it continues to produce reports from comparison evidence.",
      "files": [
        "plugin/skills/behavior-diff/scripts/render.py",
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/load.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py",
        "plugin/skills/behavior-diff/scripts/reporting/schema.py"
      ]
    },
    {
      "sha": "8296326bc15909f15d3e3ecf70cd21eac1d0458c",
      "date": "2026-09-22",
      "title": "Show file writes without inventing an order",
      "category": "Reporting",
      "why": "The flow diff hid file writes, misclassified redirected writes as reads, omitted empty groups, and implied an order the classifier did not preserve.",
      "whyBasis": "commit",
      "what": "The flow report includes writes and empty groups without presenting command kinds as a sequence.",
      "how": "It adds a write kind, keeps the no-command group, lists kinds, and removes arrows and claims of command order.",
      "role": "The report describes observed command kinds rather than claiming an ordered execution path.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/load.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py",
        "plugin/skills/behavior-diff/scripts/reporting/schema.py"
      ]
    },
    {
      "sha": "a27c77ac646932eab60012739c929e5b59ffbc77",
      "date": "2026-09-22",
      "title": "Put the actual run facts at the top",
      "category": "Reporting",
      "why": "The old header did not identify the two things being compared.",
      "whyBasis": "commit",
      "what": "Reports lead with before, after, model, trials, and evidence facts.",
      "how": "The runner records actual paths or the relevant commit, and HTML and Markdown render those labels.",
      "role": "The runner supplies comparison identity while the report makes it visible.",
      "files": [
        "plugin/skills/behavior-diff/scripts/behavior-diff.sh",
        "plugin/skills/behavior-diff/scripts/reporting/load.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py"
      ]
    },
    {
      "sha": "9ec20f8798366a4f9301cd4979a30eb555a8d19a",
      "date": "2026-09-22",
      "title": "Explain the report to a new reader",
      "category": "Reporting",
      "why": "Readers could not tell what tags, model-written text, or sections meant.",
      "whyBasis": "commit",
      "what": "The report explains sections and labels decisions with their questions.",
      "how": "It adds a tag key and section descriptions, aligns the headline as plain text, collapses the instruction diff, and removes a narrow width cap.",
      "role": "The report explains evidence more clearly without assigning the final judgment to the model.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py",
        "plugin/skills/behavior-diff/scripts/reporting/report.css"
      ]
    },
    {
      "sha": "c15467053236cb396877f326fb838ca1a9e490a6",
      "date": "2026-09-23",
      "title": "Organize the HTML report into tabs",
      "category": "Reporting",
      "why": "The long report made it hard to keep place while comparing paired trials.",
      "whyBasis": "commit",
      "what": "The HTML report separates summary, decision, flow, and trial results into tabs.",
      "how": "Radio inputs switch panels without JavaScript; paired trial cards sit side by side, and printing shows all panels.",
      "role": "HTML presentation changes while the Markdown report remains unchanged.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/report.css"
      ]
    },
    {
      "sha": "2c4dc660dea7763f90ea48350bb7078c8cb160b9",
      "date": "2026-09-23",
      "title": "Lead with outcomes and link the evidence",
      "category": "Reporting",
      "why": "Readers needed a direct summary connected to supporting evidence.",
      "whyBasis": "inferred",
      "what": "Reports show outcome-first summaries with linked evidence.",
      "how": "The extractor identifies a primary outcome and supported implications with decision references; normalization validates and remaps those references as rows are sorted or dropped.",
      "role": "The extractor proposes evidence-backed interpretations and the report links them to the underlying comparisons.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/load.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py",
        "plugin/skills/behavior-diff/scripts/reporting/schema.py"
      ]
    },
    {
      "sha": "bc03ddfaae6834d9e714c7eb4671b57bf2156deb",
      "date": "2026-09-24",
      "title": "Separate results from behavior changes",
      "category": "Reporting",
      "why": "Results and action comparisons needed clearer labels without losing uncertainty.",
      "whyBasis": "commit",
      "what": "The summary distinguishes final results from behavior changes in both report formats.",
      "how": "The extraction prompt treats links between differences as possible explanations rather than proven causes; report content, renderers, and schema simplify evidence labels.",
      "role": "The report presents outcomes separately from actions and preserves uncertainty about explanations.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py",
        "plugin/skills/behavior-diff/scripts/reporting/schema.py"
      ]
    },
    {
      "sha": "13a69279f34ca614b97f9edf7b6cd005c96276c6",
      "date": "2026-09-24",
      "title": "Clarify decisions and recorded flow",
      "category": "Reporting",
      "why": "Decision comparisons and recorded flow paths needed clearer presentation.",
      "whyBasis": "inferred",
      "what": "The report distinguishes model-extracted decision comparisons from recorded command sequences.",
      "how": "It groups identical complete recorded command sequences, preserves repeats and order, and warns that independent trials and incomplete records do not prove causation or successful execution.",
      "role": "The report presents recorded flow and model interpretation as different kinds of evidence.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py",
        "plugin/skills/behavior-diff/scripts/reporting/report.css"
      ]
    },
    {
      "sha": "d2d2e2af5220817cab949f9c0d94d6d42a434192",
      "date": "2026-09-26",
      "title": "Align report terms and evidence",
      "category": "Reporting",
      "why": "Terminology and evidence presentation needed to be consistent.",
      "whyBasis": "inferred",
      "what": "Decision and report wording and evidence presentation are aligned.",
      "how": "Shared report content, renderers, styling, and decision self-check assertions are updated.",
      "role": "Extraction and reporting retain their roles while using more consistent presentation.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py",
        "plugin/skills/behavior-diff/scripts/reporting/report.css"
      ]
    },
    {
      "sha": "70bb949110a5350ae85c7d7a31c8f017b5ad41ba",
      "date": "2026-09-30",
      "title": "Show instruction edits beside related behavior",
      "category": "Reporting",
      "why": "Readers needed to see instruction edits and related behavior together.",
      "whyBasis": "inferred",
      "what": "The report surfaces instruction changes and interpreted links to observed behavior.",
      "how": "A new instruction-reporting module parses numbered diff hunks; the extractor now receives those hunks as untrusted evidence after identifying trial choices.",
      "role": "Extraction is no longer blind to the instruction diff; it interprets links without treating them as proof of causality or author intent.",
      "files": [
        "plugin/skills/behavior-diff-live/SKILL.md",
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/instruction.py",
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/load.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py",
        "plugin/skills/behavior-diff/scripts/reporting/schema.py"
      ]
    },
    {
      "sha": "23431ed56e62afdf6b0cd219c42565cce93fae4a",
      "date": "2026-09-30",
      "title": "Order decisions and color their labels",
      "category": "Reporting",
      "why": "Ordered decisions and meaningful label colors make comparisons easier to read.",
      "whyBasis": "inferred",
      "what": "Reports display decisions in extracted order with semantic label colors.",
      "how": "The HTML progression aligns before and after choices at each decision and labels result, action, detail, and evidence source; the report warns this is not a recorded or causal path.",
      "role": "The report clarifies decision presentation without claiming a complete trial path.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py",
        "plugin/skills/behavior-diff/scripts/reporting/report.css"
      ]
    },
    {
      "sha": "66df56a4464a0609e859281c53e12ce644634c5b",
      "date": "2026-09-30",
      "title": "Separate trial and extraction model defaults",
      "category": "Execution",
      "why": "Trial execution and decision extraction needed separate model defaults.",
      "whyBasis": "inferred",
      "what": "Trial and extraction model selection are separated.",
      "how": "Claude trials default to Opus and extraction to Sonnet; Codex resolves stable Sol for trials and Luna for extraction from its model catalog, with explicit overrides and no silent model substitution on discovery failure.",
      "role": "Trial agents perform the task; the extractor separately assesses decisions using its own model selection.",
      "files": [
        "plugin/skills/behavior-diff-live/SKILL.md",
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/scripts/behavior-diff.sh",
        "plugin/skills/behavior-diff/scripts/codex_model.py",
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/run-trial.sh"
      ]
    },
    {
      "sha": "699bcdceca81b75d7344429c294b8ddc4837a004",
      "date": "2026-10-01",
      "title": "Add a visual Before and After summary",
      "category": "Reporting",
      "why": "Make the observed comparison easier to understand at a glance.",
      "whyBasis": "inferred",
      "what": "Added a visual summary of the leading observed behavior.",
      "how": "Extracts a cited narrative with all choices, validates it against decision rows, and renders illustrated Before and After cards.",
      "role": "The reporting pipeline now selects and presents a narrative while preserving underlying evidence.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/summary.py",
        "plugin/skills/behavior-diff/scripts/reporting/illustrations.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py"
      ]
    },
    {
      "sha": "10dddefc360a9c2efc21398b2474ef4eddf4ceba",
      "date": "2026-10-01",
      "title": "Explain the instruction edit's aim",
      "category": "Reporting",
      "why": "Connect the short summary to what the instruction edit appears to encourage.",
      "whyBasis": "commit",
      "what": "Added an interpretation of the edit's intended behavior to the report.",
      "how": "Extracts an optional plain-language aim citing changed instruction hunks, separately from trial results, without claiming author intent or causality.",
      "role": "The extractor now interprets the edit as well as observed trial behavior.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/summary.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py"
      ]
    },
    {
      "sha": "c6838f1b3a2c83203fc6eafd54bb1af9667686c6",
      "date": "2026-10-02",
      "title": "Keep mixed result headlines",
      "category": "Reporting",
      "why": "Avoid losing a supported headline when primary results are mixed.",
      "whyBasis": "commit",
      "what": "Preserved eligible mixed primary-result summaries.",
      "how": "Allows a changed mixed primary row to lead when the validated narrative selects it.",
      "role": "The summary selector still presents existing evidence; its selection rules changed.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/summary.py"
      ]
    },
    {
      "sha": "717f57ba44daba0e082c2d6f90e4a002bc69bb78",
      "date": "2026-10-02",
      "title": "Keep valid non-result headlines",
      "category": "Reporting",
      "why": "Avoid discarding a validated headline about a behavior other than the primary result.",
      "whyBasis": "commit",
      "what": "Preserved supported non-outcome narrative selections.",
      "how": "Separates fallback row ranking from validation of a selected narrative and rejects unsupported selections.",
      "role": "The report selector remains responsible for choosing a defensible lead.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/summary.py"
      ]
    },
    {
      "sha": "01d4c0b537e37247d5a6ceee37840db464e3b658",
      "date": "2026-10-05",
      "title": "Call observed choices behaviors",
      "category": "Reporting",
      "why": "Make report terminology describe behavior in plain language.",
      "whyBasis": "inferred",
      "what": "Changed reader-facing choice terminology to behavior.",
      "how": "Rewords report labels, missing-evidence text, and explanations of trial variation.",
      "role": "Reporting wording changed; responsibility for extracting behavior did not.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/content.py"
      ]
    },
    {
      "sha": "f5fbce1f857cad75c4c030818dda3e910678479b",
      "date": "2026-10-05",
      "title": "Add a guided story and trial summaries",
      "category": "Reporting",
      "why": "Make the comparison and individual trial evidence easier to follow.",
      "whyBasis": "inferred",
      "what": "Added a guided report story and readable summaries of trial groups.",
      "how": "The existing extraction call produces named Before and After trial summaries with takeaways and caveats, which are validated and rendered.",
      "role": "The extractor and report now explain individual trial groups as well as aggregate decisions.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/trial_summary.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py"
      ]
    },
    {
      "sha": "c3ecb5b614884972cb44f0a1176f83e9c3d39b1f",
      "date": "2026-10-05",
      "title": "Clarify Before and After comparisons",
      "category": "Reporting",
      "why": "Keep primary results visible and make comparisons consistent.",
      "whyBasis": "commit",
      "what": "Clarified summaries and their comparison destination.",
      "how": "Assigns exact completed trial names to each decision branch and derives counts from those assignments rather than model-supplied counts.",
      "role": "Extraction must now account for each completed trial in each decision row.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py"
      ]
    },
    {
      "sha": "fa4f2ee2659e1fec2f7e24fb7894fc3718e401fa",
      "date": "2026-10-05",
      "title": "Highlight the operative rule",
      "category": "Reporting",
      "why": "Explain a meaningful change in how an agent acts rather than only its downstream result.",
      "whyBasis": "commit",
      "what": "Changed the preferred lead for behavior summaries.",
      "how": "Instructs extraction to select an evidenced change in condition, timing, scope, or prerequisite before falling back to other results.",
      "role": "The extractor prioritizes the decision rule while still reporting primary outcomes.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py"
      ]
    },
    {
      "sha": "8d1d95df42f2dcc73e45930d6c63d2d95b9c3e53",
      "date": "2026-10-06",
      "title": "Restore the approved wrench illustration",
      "category": "Reporting",
      "why": "Replace the broken summary-card wrench with the approved slim design.",
      "whyBasis": "commit",
      "what": "Changed a decorative summary illustration.",
      "how": "Replaces the wrench SVG while retaining the existing palette and other icons.",
      "role": "Report illustration only; comparison and assessment responsibilities did not change.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/illustrations.py"
      ]
    },
    {
      "sha": "89cc813af93b03c084c753bc71dbda5412388d4f",
      "date": "2026-10-06",
      "title": "Explain changes with supporting evidence",
      "category": "Reporting",
      "why": "Give readers a structured explanation of the observed change.",
      "whyBasis": "commit",
      "what": "Added an Understand the change report section.",
      "how": "Extracts and validates explanations that cite decision rows and displays them in HTML and Markdown.",
      "role": "The reporting pipeline now explains the practical meaning of supported distinctions.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/explanation.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py"
      ]
    },
    {
      "sha": "a2f4d544c3f2a88e8363e76577a9970e2a5020af",
      "date": "2026-10-07",
      "title": "Add visual attention and deeper explanations",
      "category": "Reporting",
      "why": "Make important findings easier to notice and explore.",
      "whyBasis": "inferred",
      "what": "Added picture-first attention and expanded evidence explanations.",
      "how": "Extracts structured attention data, validates it, and renders illustrations and deeper evidence in both report formats.",
      "role": "Reporting takes on a richer visual and explanatory presentation of existing evidence.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/attention.py",
        "plugin/skills/behavior-diff/scripts/reporting/illustrations.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py"
      ]
    },
    {
      "sha": "da605e2efbb165883fe406cf15d223b8f6dc7f79",
      "date": "2026-10-07",
      "title": "Use optional Humanizer prose guidance",
      "category": "Reporting",
      "why": "Improve the naturalness of report prose without adding a model call.",
      "whyBasis": "commit",
      "what": "Allowed installed Humanizer guidance to inform report narrative.",
      "how": "Reads available guidance into the existing extraction prompt; otherwise uses concise prose, without installing or invoking the skill.",
      "role": "The extractor gains optional prose guidance; deterministic report assembly remains unchanged.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/scripts/decisions.py"
      ]
    },
    {
      "sha": "6cb2663959c6804de6e4707bd4c454ea51ea1b9f",
      "date": "2026-10-07",
      "title": "Keep compared instructions out of prose guidance",
      "category": "Reporting",
      "why": "Prevent live comparison sources from being treated as Humanizer guidance.",
      "whyBasis": "commit",
      "what": "Excluded compared source paths when selecting optional prose guidance.",
      "how": "Records resolved original and scratch comparison paths in live provenance and checks them during guidance discovery.",
      "role": "The live skill now supplies source provenance to protect the extractor's guidance boundary.",
      "files": [
        "plugin/skills/behavior-diff-live/SKILL.md",
        "plugin/skills/behavior-diff/scripts/decisions.py"
      ]
    },
    {
      "sha": "e3158d30bcdefb76caacf30323e79ec39e928550",
      "date": "2026-10-07",
      "title": "Give explanations context and evidence",
      "category": "Reporting",
      "why": "Help readers understand the task and avoid unsupported claims.",
      "whyBasis": "commit",
      "what": "Expanded guidance for report and conversation explanations.",
      "how": "Requires practical context, minority and unchanged behavior, evidence limits, and separation of plans from completed actions.",
      "role": "Both skills now have clearer responsibility for contextual, evidence-grounded presentation.",
      "files": [
        "plugin/skills/behavior-diff-live/SKILL.md",
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/scripts/decisions.py"
      ]
    },
    {
      "sha": "843d021e39a1ec9f7312fb8d51f310fb1dee08f3",
      "date": "2026-10-07",
      "title": "Explain unchanged behavior honestly",
      "category": "Assessment",
      "why": "Avoid assuming that unchanged behavior means a scenario was missed.",
      "whyBasis": "commit",
      "what": "Clarified how to discuss unchanged trial flows.",
      "how": "Allows no divergence and directs both workflows to describe unchanged results and evidence limitations without assuming a cause.",
      "role": "Both skills remain responsible for interpreting results, now including unchanged flows explicitly.",
      "files": [
        "plugin/skills/behavior-diff-live/SKILL.md",
        "plugin/skills/behavior-diff/SKILL.md"
      ]
    },
    {
      "sha": "394a699b89f198a4ef4d53d76bfbd1ce817adf5c",
      "date": "2026-10-08",
      "title": "Compare results with the change's goals",
      "category": "Assessment",
      "why": "Connect report conclusions to the purpose of the skill change.",
      "whyBasis": "commit",
      "what": "Added purpose-aware conclusions and supporting evidence.",
      "how": "Freezes change goals, gathers trial evidence, and links goal assessments and report conclusions to supported observations.",
      "role": "The skill moves beyond describing differences to assessing evidence against frozen change goals.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff-live/SKILL.md",
        "plugin/skills/behavior-diff/scripts/purpose.py",
        "plugin/skills/behavior-diff/scripts/reporting/evidence.py",
        "plugin/skills/behavior-diff/scripts/reporting/target.py"
      ]
    },
    {
      "sha": "7f3788525c950968a8cca218ac2f79713b31a893",
      "date": "2026-10-12",
      "title": "Explain the skill change in the summary",
      "category": "Reporting",
      "why": "Make the summary relate observed results to the instruction change.",
      "whyBasis": "commit",
      "what": "Refined the report's summary of the change and its observed effects.",
      "how": "Adds evidence-linked context and revised summary structures and renders them in HTML and Markdown.",
      "role": "Reporting takes more responsibility for explaining the relationship between the edit and observed behavior.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/summary.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py"
      ]
    },
    {
      "sha": "2801a8d79b607179d7bcac3cd41225875e781fb2",
      "date": "2026-10-12",
      "title": "Keep the short intent and full goals",
      "category": "Reporting",
      "why": "Keep the summary concise without losing the full frozen goals.",
      "whyBasis": "commit",
      "what": "Added a concise purpose paraphrase while retaining detailed goals.",
      "how": "The existing extraction call paraphrases frozen goals for the summary and the report keeps the originals in detail.",
      "role": "Reporting presents both a short explanation and the authoritative prepared goals.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/summary.py"
      ]
    },
    {
      "sha": "a102422c8d3e4c231ec127e02f82f0e1e549e850",
      "date": "2026-10-12",
      "title": "Simplify summary navigation",
      "category": "Reporting",
      "why": "Make Before and After prose and navigation easier to distinguish.",
      "whyBasis": "commit",
      "what": "Refined report navigation and version styling.",
      "how": "Adds version-name rendering and revises the HTML summary and supporting-detail presentation.",
      "role": "Presentation changed; trial execution and assessment ownership stayed the same.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/report.css",
        "plugin/skills/behavior-diff/scripts/reporting/version_names.py"
      ]
    },
    {
      "sha": "7ee50c473af429f0a46ba8e45fdc7e9dfdfe572a",
      "date": "2026-10-13",
      "title": "Monitor background comparisons",
      "category": "Execution",
      "why": "Let users follow a running comparison without blocking other work.",
      "whyBasis": "commit",
      "what": "Added progress recording and status monitoring for background runs.",
      "how": "The runner records progress by run directory and provides status, active-list, JSON, and watch commands.",
      "role": "The runner and skill now own progress visibility in addition to executing trials.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/scripts/behavior-diff.sh",
        "plugin/skills/behavior-diff/scripts/progress.py",
        "plugin/skills/behavior-diff/scripts/status.py",
        "plugin/skills/behavior-diff/scripts/run-trial.sh"
      ]
    },
    {
      "sha": "a3793ac4eed504b3a64d04a4945b7d21bddbb105",
      "date": "2026-10-13",
      "title": "Link historical reports to their sources",
      "category": "Reporting",
      "why": "Show where historical instruction versions came from.",
      "whyBasis": "commit",
      "what": "Added repository and revision links to historical reports.",
      "how": "Captures verified original-repository provenance and renders source links without claiming the whole pull request was tested.",
      "role": "Preparation records historical provenance; reporting displays it without changing trial evidence.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/scripts/source.py",
        "plugin/skills/behavior-diff/scripts/reporting/provenance.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py"
      ]
    },
    {
      "sha": "a5dacb04b26b6562cff6759004251888f7250ef5",
      "date": "2026-10-13",
      "title": "Add automatic CI report context",
      "category": "Reporting",
      "why": "Show the repository and pull request context available in CI.",
      "whyBasis": "commit",
      "what": "Added automatic CI repository and PR or MR links to reports.",
      "how": "Reads predefined GitHub Actions or GitLab variables and event metadata; explicit historical source metadata takes precedence.",
      "role": "The runner supplies display context, not evidence of which revisions were compared.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/scripts/ci_context.py",
        "plugin/skills/behavior-diff/scripts/reporting/provenance.py"
      ]
    },
    {
      "sha": "8cccfec08faa84eddbd3905e7827696328f0f2fc",
      "date": "2026-10-19",
      "title": "Deliver shared data to both snapshots",
      "category": "Preparation",
      "why": "Give Before and After the same frozen inputs while preserving isolation and baseline semantics.",
      "whyBasis": "commit",
      "what": "Added preparation and delivery of shared trial data.",
      "how": "Stages and verifies reviewed inputs, delivers them into both snapshots, and isolates nested trial storage.",
      "role": "The skill reviews shared data; scripts stage and verify it before trials.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/references/scenario-and-test-data.md",
        "plugin/skills/behavior-diff/scripts/prepare_shared.py",
        "plugin/skills/behavior-diff/scripts/run-trial.sh"
      ]
    },
    {
      "sha": "c4c2c001d491ef4599b385965d46ebaf16d446cd",
      "date": "2026-10-19",
      "title": "Prepare scenarios from change intent",
      "category": "Preparation",
      "why": "Evaluate the intended change using prepared scenarios and private criteria.",
      "whyBasis": "commit",
      "what": "Made scenario, shared-data, and assessment preparation an explicit skill responsibility.",
      "how": "The skill derives cases from frozen intent, preflights and freezes inputs, and assesses raw evidence; scripts do not generate scenarios or data.",
      "role": "The skill expands from drafting a task to owning scenario design, private criteria, and evidence assessment.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/references/scenario-and-test-data.md",
        "plugin/skills/behavior-diff/scripts/decisions.py"
      ]
    },
    {
      "sha": "4ff0321c9efc9ce78f4d98ebef713a941845b3bf",
      "date": "2026-10-20",
      "title": "Report assumptions alongside evidence",
      "category": "Reporting",
      "why": "Make instruction assumptions and their supporting evidence visible in summaries.",
      "whyBasis": "commit",
      "what": "Added evidence-backed reporting of instruction assumptions.",
      "how": "Extends extraction, evidence loading and summary rendering, including handling interrupted trials.",
      "role": "Reporting now relates instruction assumptions to trial evidence and its limits.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/reporting/evidence.py",
        "plugin/skills/behavior-diff/scripts/reporting/summary.py",
        "plugin/skills/behavior-diff/scripts/reporting/target.py"
      ]
    },
    {
      "sha": "810367396254ed543ba3b682b6a1b47fed76d368",
      "date": "2026-10-20",
      "title": "Keep detailed evidence in summaries",
      "category": "Reporting",
      "why": "Preserve supporting detail in the refined report summary.",
      "whyBasis": "commit",
      "what": "Expanded the summary's evidence details.",
      "how": "Builds and renders detailed check, goal, and evidence information in HTML and Markdown.",
      "role": "Reporting retains more detail; responsibility for judging the evidence remains separate.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py"
      ]
    },
    {
      "sha": "cac7425399436a82d3399c4cf97b83cd2fcb5233",
      "date": "2026-10-20",
      "title": "Focus summaries on observations and open goals",
      "category": "Reporting",
      "why": "Make observed changes and goals still needing evidence prominent.",
      "whyBasis": "commit",
      "what": "Reorganized summary content around observations and open goals.",
      "how": "Uses effective purpose and check information to select report content and updates HTML and Markdown rendering.",
      "role": "The report prioritizes observed behavior and unresolved goals rather than introducing a new evaluator.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py"
      ]
    },
    {
      "sha": "ed9aaef00435f498fc2943971e3c442dc3751108",
      "date": "2026-10-20",
      "title": "Carry frozen checks into assessment",
      "category": "Assessment",
      "why": "Ensure prepared scenario checks reach assessment reports.",
      "whyBasis": "commit",
      "what": "Connected frozen scenario checks to extraction and reporting.",
      "how": "Adds scenario loading and validation, passes the frozen checks through the runner, and renders assessment results.",
      "role": "The skill prepares checks and the assessment pipeline now carries them into the report.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/references/scenario-and-test-data.md",
        "plugin/skills/behavior-diff/scripts/scenario.py",
        "plugin/skills/behavior-diff/scripts/reporting/scenario.py",
        "plugin/skills/behavior-diff/scripts/decisions.py"
      ]
    },
    {
      "sha": "8fd14adc716c66e4e1b069e4fc9c0b1b268a165c",
      "date": "2026-10-20",
      "title": "Keep independently validated findings",
      "category": "Assessment",
      "why": "Avoid losing assessment findings that have independent evidence.",
      "whyBasis": "commit",
      "what": "Reworked assessment validation and evidence sourcing.",
      "how": "Validates findings against source evidence independently and retains supported results while reporting rejected or unresolved material.",
      "role": "Assessment takes responsibility for evaluating individual findings against their sources rather than treating all findings as one bundle.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/scripts/reporting/evidence.py",
        "plugin/skills/behavior-diff/scripts/reporting/sources.py",
        "plugin/skills/behavior-diff/scripts/reporting/target.py"
      ]
    },
    {
      "sha": "01a3b9173b34944b07caa9c5143aba61dda2b12b",
      "date": "2026-10-21",
      "title": "Refine the observed-behavior summary",
      "category": "Reporting",
      "why": "Center the report on what the tests actually establish.",
      "whyBasis": "commit",
      "what": "Simplified and renamed summary sections around observed Before and After behavior.",
      "how": "Reorganizes summary headings, check details, context and HTML and Markdown presentation.",
      "role": "Report presentation changed; preparation and trial execution responsibilities stayed the same.",
      "files": [
        "plugin/skills/behavior-diff/scripts/reporting/content.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_html.py",
        "plugin/skills/behavior-diff/scripts/reporting/render_markdown.py"
      ]
    },
    {
      "sha": "9e807d2139f689d494b7e68ccc521bdfff8a1aad",
      "date": "2026-10-23",
      "title": "Offer optional Jev judgment advice",
      "category": "Assessment",
      "why": "Assist semantic judgments when Jev is configured and approved.",
      "whyBasis": "commit",
      "what": "Added optional Jev assistance to both skill workflows.",
      "how": "A shared helper and reference constrain use to approved provider, data, and cost; advice stays outside trials, extraction, and saved reports.",
      "role": "The outer skill can request semantic advice while retaining responsibility for the final assessment.",
      "files": [
        "plugin/skills/behavior-diff-live/SKILL.md",
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/references/jev.md",
        "plugin/skills/behavior-diff/scripts/jev.py"
      ]
    },
    {
      "sha": "83fafb201ce4348db23bace45ea0f94ae08ba89e",
      "date": "2026-10-27",
      "title": "Disable inherited advisors during extraction",
      "category": "Execution",
      "why": "Keep OMP extraction to one model call rather than an inherited advisor review.",
      "whyBasis": "commit",
      "what": "Isolated OMP extraction from inherited advisor configuration.",
      "how": "Passes a bundled OMP configuration explicitly to the extraction process.",
      "role": "The extractor remains a single-call operation and now controls its advisor configuration.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/omp-extraction.json"
      ]
    },
    {
      "sha": "2e3d915542233a263c13d7f9d72c378452c20e01",
      "date": "2026-10-27",
      "title": "Isolate OMP trials from advisors",
      "category": "Execution",
      "why": "Prevent inherited advisors from changing trial execution.",
      "whyBasis": "commit",
      "what": "Extended OMP advisor isolation from extraction to trials.",
      "how": "Renames the shared isolation configuration and passes it to trial execution as well as extraction.",
      "role": "Both the trial runner and extractor now control inherited advisor settings.",
      "files": [
        "plugin/skills/behavior-diff/scripts/decisions.py",
        "plugin/skills/behavior-diff/scripts/omp-isolation.json",
        "plugin/skills/behavior-diff/scripts/run-trial.sh"
      ]
    },
    {
      "sha": "c090d028b9bf2c565dbf227d5b6eecbd443cca24",
      "date": "2026-10-27",
      "title": "Freeze complete handoffs and index original evidence",
      "category": "Preparation",
      "why": "Keep prepared inputs complete and make original trial evidence traceable.",
      "whyBasis": "commit",
      "what": "Added complete skill handoffs and an original-evidence index.",
      "how": "Expands shared-input preparation to validate and freeze a handoff and adds an evidence-audit script for original trial artifacts.",
      "role": "The skill owns a complete prepared handoff; scripts freeze it and index original evidence for assessment.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/references/scenario-and-test-data.md",
        "plugin/skills/behavior-diff/scripts/prepare_shared.py",
        "plugin/skills/behavior-diff/scripts/audit_evidence.py"
      ]
    },
    {
      "sha": "23c350837d92cc9865298dcffa10b3a89756d90c",
      "date": "2026-10-27",
      "title": "Reject empty scenarios in complete handoffs",
      "category": "Preparation",
      "why": "Prevent a handoff with a non-null purpose from accepting a null scenario.",
      "whyBasis": "commit",
      "what": "Tightened complete-handoff scenario validation and adjusted evidence hashing.",
      "how": "Reads the scenario value before requiring it for a non-null purpose and hashes evidence in blocks.",
      "role": "Preparation still validates handoffs; it now rejects a missing or null reviewed scenario.",
      "files": [
        "plugin/skills/behavior-diff/scripts/prepare_shared.py",
        "plugin/skills/behavior-diff/scripts/audit_evidence.py"
      ]
    },
    {
      "sha": "b561e35b373d6f878f4c7bb515209123bdba01fa",
      "date": "2026-10-28",
      "title": "Select committed comparison inputs correctly",
      "category": "Preparation",
      "why": "Support committed comparisons without treating them as uncommitted edits.",
      "whyBasis": "commit",
      "what": "Clarified selection of local, PR, revision, and explicit Before and After inputs.",
      "how": "Updates skill and preparation instructions to select the requested source and preserve the user's checkout.",
      "role": "The skill's input-selection responsibility explicitly includes committed and file-based comparisons.",
      "files": [
        "plugin/skills/behavior-diff/SKILL.md",
        "plugin/skills/behavior-diff/references/scenario-and-test-data.md"
      ]
    }
  ]
};
