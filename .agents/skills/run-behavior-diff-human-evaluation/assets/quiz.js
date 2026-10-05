"use strict";

const byId = (id) => document.getElementById(id);
let sessionId;
let questions;
let storageKey;
let submitted = false;
const frames = new Map();

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

async function request(path, options) {
  const response = await fetch(path, { credentials: "same-origin", ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "The local server rejected this request.");
  return data;
}

function fitFrame(frame) {
  try {
    const doc = frame.contentDocument;
    if (!doc || !doc.body) return;
    // Measure content without changing the viewport inside ResizeObserver.
    const style = frame.contentWindow.getComputedStyle(doc.body);
    const margins = (parseFloat(style.marginTop) || 0) + (parseFloat(style.marginBottom) || 0);
    const height = Math.ceil(doc.body.getBoundingClientRect().height + margins) + 24;
    if (Math.abs((parseFloat(frame.style.height) || 0) - height) > 2) frame.style.height = `${height}px`;
  } catch (_) {
    // Full reports remain accessible through their separate post-submit link.
  }
}

function reportFrame(path, title, full = false) {
  const frame = element("iframe");
  frame.title = title;
  frame.src = path;
  frame.setAttribute("sandbox", full ? "allow-scripts allow-same-origin" : "allow-same-origin");
  frame.addEventListener("load", () => {
    fitFrame(frame);
    const doc = frame.contentDocument;
    if (!doc) return;
    doc.addEventListener("toggle", () => requestAnimationFrame(() => fitFrame(frame)), true);
    doc.addEventListener("click", () => setTimeout(() => fitFrame(frame), 40));
    if (window.ResizeObserver) {
      const observer = new ResizeObserver(() => fitFrame(frame));
      observer.observe(doc.body);
      frames.set(frame, observer);
    }
  });
  return frame;
}

function answerFor(question) {
  const id = question.id;
  const selected = document.querySelector(`input[name="choice-${id}"]:checked`);
  const confidence = byId(`confidence-${id}`).value;
  return { id, letter: selected ? selected.value : "", confidence,
    insufficient: byId(`insufficient-${id}`).checked, note: byId(`note-${id}`).value };
}

function saveDraft() {
  if (submitted) return;
  const answers = questions.map(answerFor);
  try { localStorage.setItem(storageKey, JSON.stringify({ session_id: sessionId, answers })); } catch (_) { /* Storage is optional. */ }
  const complete = answers.filter((answer) => answer.letter && answer.confidence).length;
  byId("progress").textContent = `${complete} of ${questions.length} complete`;
}

function restoreDraft() {
  try {
    const draft = JSON.parse(localStorage.getItem(storageKey));
    if (!draft || draft.session_id !== sessionId || !Array.isArray(draft.answers)) return;
    for (const answer of draft.answers) {
      if (!questions.some((question) => question.id === answer.id)) continue;
      const choice = document.querySelector(`input[name="choice-${answer.id}"][value="${["A", "B", "C", "D"].includes(answer.letter) ? answer.letter : ""}"]`);
      if (choice) choice.checked = true;
      if (["low", "medium", "high"].includes(answer.confidence)) byId(`confidence-${answer.id}`).value = answer.confidence;
      byId(`insufficient-${answer.id}`).checked = answer.insufficient === true;
      if (typeof answer.note === "string") byId(`note-${answer.id}`).value = answer.note.slice(0, 2000);
    }
  } catch (_) { /* Ignore malformed or unavailable browser drafts. */ }
}

function renderQuestions() {
  for (const question of questions) {
    const section = element("section", undefined, "case");
    section.append(element("h2", `Case ${question.id}`));
    section.append(reportFrame(`/summary-${question.id}.html`, `Blinded summary for case ${question.id}`));
    const fieldset = element("fieldset");
    fieldset.append(element("legend", question.stem));
    for (const option of question.options) {
      const label = element("label", undefined, "option");
      const input = element("input");
      input.type = "radio"; input.name = `choice-${question.id}`; input.value = option.letter; input.required = true;
      label.append(input, element("span", `${option.letter}. ${option.statement}`));
      fieldset.append(label);
    }
    section.append(fieldset);
    const confidenceLabel = element("label", "Confidence ");
    const confidence = element("select");
    confidence.id = `confidence-${question.id}`; confidence.required = true;
    for (const [value, label] of [["", "Choose confidence"], ["low", "Low"], ["medium", "Medium"], ["high", "High"]]) {
      const option = element("option", label); option.value = value; confidence.append(option);
    }
    confidenceLabel.append(confidence);
    const insufficientLabel = element("label", undefined, "sufficiency");
    const insufficient = element("input");
    insufficient.type = "checkbox"; insufficient.id = `insufficient-${question.id}`;
    insufficientLabel.append(insufficient, element("span", "The summary provides insufficient evidence to choose confidently."));
    const noteLabel = element("label", "Optional note");
    const note = element("textarea");
    note.id = `note-${question.id}`; note.maxLength = 2000; note.rows = 3;
    noteLabel.append(note);
    section.append(confidenceLabel, insufficientLabel, noteLabel);
    byId("cases").append(section);
  }
  restoreDraft();
  byId("quiz").addEventListener("input", saveDraft);
  byId("quiz").addEventListener("change", saveDraft);
  saveDraft();
  byId("quiz").hidden = false;
}

function renderResults(data) {
  submitted = true;
  byId("quiz").hidden = true;
  byId("results").hidden = false;
  byId("status").textContent = "First complete submission saved. You can now inspect the answer key and full reports.";
  byId("score").replaceChildren(element("p", `${data.score.correct} of ${data.score.total} answers correct.`, "score"), element("p", data.interpretation));
  byId("reviews").replaceChildren();
  for (const answer of data.answers) {
    const review = element("article", undefined, "case");
    review.append(element("h3", `Case ${answer.id}: ${answer.correct ? "correct" : "incorrect"}`));
    review.append(element("p", `Your answer: ${answer.letter}. Correct answer: ${answer.correct_letter}. Confidence: ${answer.confidence}. Insufficient evidence flagged: ${answer.insufficient ? "yes" : "no"}.`));
    review.append(element("p", `Question scope: ${answer.scope}`));
    const reasons = element("ul");
    for (const option of answer.options) {
      const reason = element("li");
      reason.append(element("strong", `${option.letter}. ${option.statement}${option.correct ? " (correct)" : ""}`), element("p", option.rationale));
      reasons.append(reason);
    }
    review.append(reasons);
    if (answer.note) review.append(element("p", `Your note: ${answer.note}`));
    const links = element("p", undefined, "links");
    for (const [url, label] of [[answer.source_url, "Source commit"], [answer.before_source_url, "Before commit"], [answer.review_url, "Open full report"]]) {
      const link = element("a", label); link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer"; links.append(link);
    }
    review.append(links);
    const details = element("details");
    details.append(element("summary", "Full original Behavior Diff report"));
    details.addEventListener("toggle", () => {
      if (details.open && !details.querySelector("iframe")) details.append(reportFrame(answer.review_url, `Full report for case ${answer.id}`, true));
      else if (details.open) fitFrame(details.querySelector("iframe"));
    });
    review.append(details);
    byId("reviews").append(review);
  }
}

byId("quiz").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (submitted || !byId("quiz").reportValidity()) return;
  byId("submit").disabled = true;
  byId("status").textContent = "Saving your first complete submission…";
  try {
    renderResults(await request("/submit", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, answers: questions.map(answerFor) }) }));
  } catch (error) {
    byId("status").textContent = error.message;
    byId("submit").disabled = false;
  }
});

window.addEventListener("resize", () => { for (const frame of document.querySelectorAll("iframe")) fitFrame(frame); });

(async () => {
  try {
    const session = await request("/session-public.json");
    sessionId = session.session_id;
    storageKey = `behavior-diff-human-evaluation:${sessionId}`;
    // Server persistence, not browser storage, is authoritative about submission.
    const response = await fetch("/results", { credentials: "same-origin" });
    if (response.ok) { renderResults(await response.json()); return; }
    if (response.status !== 403) throw new Error("Unable to read this session's submission state.");
    questions = await request("/questions.json");
    renderQuestions();
    byId("status").textContent = "Read all five summaries before submitting. Your draft is private to this session.";
  } catch (error) {
    byId("status").textContent = error.message;
  }
})();
