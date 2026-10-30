const els = {
  ideaInput: document.getElementById("ideaInput"),
  generateBtn: document.getElementById("generateBtn"),
  recordBtn: document.getElementById("recordBtn"),
  recordLabel: document.getElementById("recordLabel"),
  recordTimer: document.getElementById("recordTimer"),
  status: document.getElementById("status"),
  samples: document.getElementById("samples"),
  emptyState: document.getElementById("emptyState"),
  resultContent: document.getElementById("resultContent"),
  healthDot: document.getElementById("healthDot"),
  healthText: document.getElementById("healthText"),
};

let lastSpecificationResponse = null;

const SAMPLES = [
  "I want to build a gym-room booking application. Customers should browse sessions, reserve a spot, pay for their subscription, and receive a confirmation. Managers should be able to manage sessions and bookings.",
  "I want a platform that helps small businesses track expenses, import invoices, and receive alerts when a budget is exceeded.",
  "I want to create a mobile app for organizing group activities, suggesting options, voting on a date, and reminding participants.",
];

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function list(items, empty = "No information generated.") {
  if (!Array.isArray(items) || items.length === 0) return `<span class="empty-list">${empty}</span>`;
  return `<ul class="list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function section(id, number, title, body) {
  return `<article id="${id}" class="spec-section">
    <div class="section-heading"><span class="section-number">${number}</span><h2>${title}</h2></div>
    ${body}
  </article>`;
}

function renderOverview(overview) {
  const users = (overview.target_users || []).map((user) => `
    <div class="item">
      <div class="item-title"><h3>${escapeHtml(user.name)}</h3><span class="pill green">${escapeHtml(user.id)}</span></div>
      <div class="muted">${escapeHtml(user.description)}</div>
    </div>`).join("");

  return `<div class="overview-grid">
    <div class="field"><div class="label">Proposed name</div><div class="value">${escapeHtml(overview.proposed_name)}</div></div>
    <div class="field"><div class="label">Summary</div><div class="value">${escapeHtml(overview.summary)}</div></div>
    <div class="field full"><div class="label">Problem statement</div><div class="value">${escapeHtml(overview.problem_statement)}</div></div>
    <div class="field"><div class="label">Goals</div>${list(overview.goals)}</div>
    <div class="field full"><div class="label">Target users</div><div class="cards">${users || '<span class="empty-list">No target users generated.</span>'}</div></div>
  </div>`;
}

function renderFunctionalRequirements(items) {
  if (!items?.length) return `<span class="empty-list">No functional requirements generated.</span>`;
  return `<div class="cards">${items.map((item) => `
    <div class="item">
      <div class="item-title"><h3>${escapeHtml(item.id)} · ${escapeHtml(item.title)}</h3><span class="pill">${escapeHtml(item.priority)}</span></div>
      <p>${escapeHtml(item.description)}</p>
      <div class="muted">Actor: ${escapeHtml(item.actor)}</div>
    </div>`).join("")}</div>`;
}

function renderUserStories(items) {
  if (!items?.length) return `<span class="empty-list">No user stories generated.</span>`;
  return `<div class="cards">${items.map((item) => `
    <div class="item">
      <div class="item-title"><h3>${escapeHtml(item.id)} · ${escapeHtml(item.feature)}</h3><span class="pill green">story</span></div>
      <div class="story-format"><b>As a</b> ${escapeHtml(item.as_a)}, <b>I want</b> ${escapeHtml(item.i_want)}, <b>so that</b> ${escapeHtml(item.so_that)}.</div>
      <div class="muted" style="margin-top:9px">Requirements: ${escapeHtml((item.related_requirement_ids || []).join(", ") || "none")}</div>
    </div>`).join("")}</div>`;
}

function renderAcceptanceCriteria(items) {
  if (!items?.length) return `<span class="empty-list">No acceptance criteria generated.</span>`;
  return `<div class="cards">${items.map((item) => `
    <div class="item">
      <div class="item-title"><h3>${escapeHtml(item.id)}</h3><span class="pill green">${escapeHtml(item.user_story_id)}</span></div>
      ${list(item.criteria)}
    </div>`).join("")}</div>`;
}

function renderNonFunctionalRequirements(items) {
  if (!items?.length) return `<span class="empty-list">No non-functional requirements generated.</span>`;
  return `<div class="cards">${items.map((item) => `
    <div class="item">
      <div class="item-title"><h3>${escapeHtml(item.id)} · ${escapeHtml(item.category)}</h3><span class="pill">${escapeHtml(item.priority)}</span></div>
      <p>${escapeHtml(item.description)}</p>
    </div>`).join("")}</div>`;
}

function renderQuestions(items) {
  if (!items?.length) return `<span class="empty-list">No open questions generated.</span>`;
  return `<div class="cards">${items.map((item) => `
    <div class="item">
      <div class="item-title"><h3>${escapeHtml(item.id)}</h3><span class="pill amber">${escapeHtml(item.related_area)}</span></div>
      <div>${escapeHtml(item.question)}</div>
    </div>`).join("")}</div>`;
}

function renderAssumptions(items) {
  if (!items?.length) return `<span class="empty-list">No assumptions generated.</span>`;
  return `<div class="cards">${items.map((item) => `
    <div class="item">
      <div class="item-title"><h3>${escapeHtml(item.id)}</h3><span class="pill amber">${item.needs_validation ? "Needs validation" : "Reviewed"}</span></div>
      <div>${escapeHtml(item.statement)}</div>
    </div>`).join("")}</div>`;
}

function renderSpecification(response) {
  const spec = response.data;
  const overview = spec.project_overview || {};
  const sectionLinks = [
    ["project-overview", "Overview"],
    ["functional-requirements", "Functional"],
    ["user-stories", "Stories"],
    ["acceptance-criteria", "Acceptance"],
    ["non-functional-requirements", "Non-functional"],
    ["open-questions", "Questions"],
    ["assumptions", "Assumptions"],
  ];

  els.resultContent.innerHTML = `
    <div class="result-head">
      <div><p class="eyebrow">Specification draft</p><h2>${escapeHtml(overview.proposed_name || "Untitled project")}</h2><p class="muted">Review the generated content before using it for development.</p></div>
      <button id="exportBtn" class="btn export" type="button">Export HTML / PDF</button>
    </div>
    <nav class="section-nav">${sectionLinks.map(([id, label]) => `<a href="#${id}">${label}</a>`).join("")}</nav>
    ${section("project-overview", "1", "Project Overview", renderOverview(overview))}
    ${section("functional-requirements", "2", "Functional Requirements", renderFunctionalRequirements(spec.functional_requirements))}
    ${section("user-stories", "3", "User Stories", renderUserStories(spec.user_stories))}
    ${section("acceptance-criteria", "4", "Acceptance Criteria", renderAcceptanceCriteria(spec.acceptance_criteria))}
    ${section("non-functional-requirements", "5", "Non-Functional Requirements", renderNonFunctionalRequirements(spec.non_functional_requirements))}
    ${section("open-questions", "6", "Open Questions", renderQuestions(spec.open_questions))}
    ${section("assumptions", "A", "Assumptions", renderAssumptions(spec.assumptions))}
  `;
  els.emptyState.hidden = true;
  els.resultContent.hidden = false;
  document.getElementById("exportBtn").addEventListener("click", exportSpecification);
}

async function exportSpecification() {
  if (!lastSpecificationResponse) return;
  const exportWindow = window.open("about:blank", "_blank");
  if (!exportWindow) {
    setStatus("Allow pop-ups to open the export document.", true);
    return;
  }

  const button = document.getElementById("exportBtn");
  if (button) button.disabled = true;
  setStatus("Preparing the export…");
  try {
    const response = await fetch("/api/specifications/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        raw_idea: lastSpecificationResponse.raw_idea,
        data: lastSpecificationResponse.data,
        generation_metadata: lastSpecificationResponse.generation_metadata || {},
      }),
    });
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.error || "Export failed.");
    }
    exportWindow.document.open();
    exportWindow.document.write(await response.text());
    exportWindow.document.close();
    setStatus("Export ready. Use Print / Save as PDF in the new tab.");
  } catch (error) {
    exportWindow.close();
    setStatus(error.message, true);
  } finally {
    if (button) button.disabled = false;
  }
}

function setStatus(message, isError = false) {
  els.status.textContent = message;
  els.status.classList.toggle("error", isError);
}

async function generateSpecification() {
  const rawIdea = els.ideaInput.value.trim();
  if (!rawIdea) {
    setStatus("Write a product idea first.", true);
    els.ideaInput.focus();
    return;
  }

  els.generateBtn.disabled = true;
  setStatus("Generating your specification…");
  try {
    const response = await fetch("/api/specifications/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_idea: rawIdea }),
    });
    const payload = await response.json();
    if (!response.ok || payload.type === "error") {
      throw new Error(payload.error || "Specification generation failed.");
    }
    lastSpecificationResponse = payload;
    renderSpecification(payload);
    setStatus("Specification generated. Review the questions and assumptions.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    els.generateBtn.disabled = false;
  }
}

function renderSamples() {
  els.samples.innerHTML = SAMPLES.map((sample, index) =>
    `<button class="sample" data-sample="${index}">Sample ${index + 1}<br /><span>${escapeHtml(sample)}</span></button>`
  ).join("");
  els.samples.querySelectorAll("[data-sample]").forEach((button) => {
    button.addEventListener("click", () => {
      els.ideaInput.value = SAMPLES[Number(button.dataset.sample)];
      setStatus("Example loaded. You can edit it or generate it now.");
      els.ideaInput.focus();
    });
  });
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    els.healthDot.className = `health-dot ${health.ok ? "ok" : "bad"}`;
    els.healthText.textContent = health.llm_configured
      ? `API ready · ${health.llm_backend}`
      : `API ready · configure ${health.llm_backend}`;
  } catch (error) {
    els.healthDot.className = "health-dot bad";
    els.healthText.textContent = "API unavailable";
  }
}

let mediaRecorder = null;
let recordedChunks = [];
let recordingTimer = null;
let recordingStartedAt = null;

function formatRecordingTime(seconds) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  const remainder = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${remainder}`;
}

function setRecordingState(isRecording) {
  els.recordBtn.classList.toggle("is-recording", isRecording);
  els.recordBtn.setAttribute("aria-pressed", String(isRecording));
  els.recordLabel.textContent = isRecording ? "Stop recording" : "Record idea";
  els.recordTimer.hidden = !isRecording;
  if (!isRecording) {
    window.clearInterval(recordingTimer);
    recordingTimer = null;
    recordingStartedAt = null;
    els.recordTimer.textContent = "00:00";
  }
}

function updateRecordingTimer() {
  if (recordingStartedAt === null) return;
  const elapsed = (Date.now() - recordingStartedAt) / 1000;
  els.recordTimer.textContent = formatRecordingTime(elapsed);
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size) recordedChunks.push(event.data);
    };
    mediaRecorder.onstop = () => {
      setRecordingState(false);
      uploadRecording(stream);
    };
    mediaRecorder.start();
    recordingStartedAt = Date.now();
    recordingTimer = window.setInterval(updateRecordingTimer, 500);
    setRecordingState(true);
    setStatus("Recording… click Stop recording when the idea is complete.");
  } catch (error) {
    setRecordingState(false);
    setStatus(`Microphone unavailable: ${error.message}`, true);
  }
}

async function uploadRecording(stream) {
  stream.getTracks().forEach((track) => track.stop());
  setStatus("Transcribing recording…");
  const blob = new Blob(recordedChunks, { type: mediaRecorder.mimeType || "audio/webm" });
  const form = new FormData();
  form.append("audio", blob, "idea.webm");
  try {
    const response = await fetch("/api/transcribe", { method: "POST", body: form });
    const payload = await response.json();
    if (!response.ok || payload.type === "error") throw new Error(payload.error || "Transcription failed.");
    els.ideaInput.value = payload.transcript || "";
    setStatus("Transcription complete. Review the text, then generate the specification.");
  } catch (error) {
    setStatus(error.message, true);
  }
}

els.generateBtn.addEventListener("click", generateSpecification);
els.ideaInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") generateSpecification();
});
els.recordBtn.addEventListener("click", () => {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    return;
  }
  startRecording();
});

renderSamples();
checkHealth();
