# AGENTS.md — Specora AI

## 1. Purpose of this file

This file defines the product and engineering rules for Specora AI. It is the
source of truth for agents and contributors working in this repository.

Specora AI is a local-first application that transforms an unstructured product
idea into a reviewable, development-ready specification with the assistance of
an LLM. The result is a draft to be reviewed by a human Product Owner, not an
automatically validated specification.

## 2. Product principles

- Human review is mandatory. The LLM proposes; the user validates, edits, and
  approves.
- Traceability matters. Functional requirements, user stories, and acceptance
  criteria must remain linked and easy to inspect.
- Structured output comes first. The canonical specification is data with a
  stable schema; rendered Markdown or HTML is a view of that data.
- Local-first is the default. Projects and drafts should be usable without a
  remote database. External LLM access must be explicit and configurable.
- Assumptions must be visible. Missing information should become an open
  question or a clearly labelled assumption, never an invisible invention.
- The application should remain useful when the LLM is unavailable. Users must
  be able to create, edit, save, and export a specification manually.
- Prefer small, reversible changes. Preserve user-authored content when
  regenerating any section.

## 3. Product scope

### MVP must support

1. Creating a project from a free-form idea.
2. Sending the idea and relevant project context to an LLM.
3. Generating six specification sections:
   - Project Overview
   - Functional Requirements
   - User Stories
   - Acceptance Criteria
   - Non-Functional Requirements
   - Open Questions & Assumptions
4. Reviewing and editing generated content section by section.
5. Regenerating a selected section without silently replacing the rest.
6. Saving and reopening projects locally.
7. Exporting a specification as Markdown and a readable HTML document.
8. Displaying generation errors and preserving the last valid draft.

### Explicitly out of scope for the first version

- Automatic project management or task execution.
- Automatic coding or repository generation.
- Claims that the specification is complete, correct, or formally validated.
- Multi-user collaboration, permissions, billing, and enterprise tenancy.
- A mandatory cloud database.
- Voice transcription as a core requirement. Voice input may be added later as
  an input adapter, but Specora's core domain is idea-to-specification.

## 4. Canonical domain model

The backend should work with a versioned specification object. At minimum it
should contain:

- `id`: stable local project identifier.
- `title`: project name.
- `raw_idea`: original user input, preserved verbatim.
- `language`: requested or detected output language.
- `status`: `draft`, `review`, or `approved`.
- `sections`: the six generated sections.
- `assumptions`: explicit assumptions with review state.
- `open_questions`: questions requiring clarification.
- `generation_metadata`: model, timestamp, prompt/schema version, and errors.
- `created_at` and `updated_at`.

Generated content should use stable identifiers for requirements and user
stories so that acceptance criteria remain traceable after edits or partial
regeneration.

The exact JSON schema must be defined in one backend module and reused for:

- LLM structured-output validation.
- API request/response validation.
- Local persistence.
- Export rendering.
- Tests and fixtures.

Do not maintain separate, drifting schemas in the frontend and backend.

## 5. Target architecture

### Frontend

Use plain HTML, CSS, and JavaScript for the first version. Keep the interface
focused on:

- entering the initial idea;
- viewing generation progress and errors;
- navigating the six sections;
- editing content;
- identifying assumptions and unanswered questions;
- saving, reopening, and exporting a project.

Avoid introducing a frontend framework unless the interaction complexity makes
plain JavaScript unreasonable and the change is explicitly justified.

### Backend

Use FastAPI as the application boundary. The backend should separate:

- HTTP routes and serialization;
- domain models and validation;
- LLM provider integration;
- prompt and schema versioning;
- local persistence;
- Markdown/HTML export.

Routes should be resource-oriented. A likely MVP surface is:

- `POST /api/projects` — create a project from an idea.
- `GET /api/projects` — list saved projects.
- `GET /api/projects/{project_id}` — read a project.
- `PATCH /api/projects/{project_id}` — edit project content.
- `POST /api/projects/{project_id}/generate` — generate or regenerate content.
- `POST /api/projects/{project_id}/sections/{section}/regenerate` — regenerate
  one section while preserving the others.
- `GET /api/projects/{project_id}/export?format=markdown|html` — export.

Routes may evolve, but the distinction between full generation and partial
regeneration must remain explicit.

### LLM integration

The LLM adapter must:

- request structured JSON rather than unconstrained prose;
- validate the response against the canonical schema;
- identify the model and prompt/schema version in metadata;
- return actionable errors without destroying the previous draft;
- keep provider-specific code outside route handlers;
- make provider/model configuration environment-driven.

Prompts must instruct the model to distinguish facts from assumptions and to
generate testable acceptance criteria. They must not encourage the model to
hide uncertainty.

### Local storage

The default persistence target is a local SQLite database for project metadata
and versioned specification documents. JSON snapshots may be used for import,
export, fixtures, or backups. Storage paths must be configurable and must not
be committed to the repository.

## 6. Quality rules

- Python code should be typed where practical and formatted consistently.
- Validate all external input at the API boundary.
- Never trust raw LLM output before schema validation.
- Never log API keys, full user secrets, or private project content by default.
- Use deterministic fixtures for domain and export tests.
- Test the happy path, empty input, malformed LLM output, provider failure,
  partial regeneration, persistence, and export.
- Keep user edits distinguishable from generated text when the UI supports it.
- Every generated acceptance criterion should be observable or verifiable; avoid
  vague wording such as “works well” or “is user-friendly”.
- Maintain backward-compatible migrations for persisted project data.

## 7. Change workflow for agents

Before changing code:

1. Read this file and `README.md`.
2. Inspect the relevant files and confirm how they fit the Specora domain.
3. State the smallest coherent change that satisfies the request.
4. Preserve unrelated user changes.

While changing code:

1. Keep domain logic independent from HTTP and UI details.
2. Update the canonical schema before updating consumers.
3. Add or update tests for behavior that can regress.
4. Do not silently broaden the product scope.

Before handing off:

1. Run the relevant tests or validation commands.
2. Check that the application still starts.
3. Check that a saved project can be reopened.
4. Report known limitations, especially LLM/provider limitations.

## 8. Definition of done for a generated specification

A specification draft is considered usable when:

- the project goal and target users are explicit;
- functional requirements are uniquely identifiable;
- each important capability has at least one user story;
- user stories have verifiable acceptance criteria;
- relevant non-functional requirements are present or marked unknown;
- assumptions and open questions are visible;
- no generated section contradicts another section without being flagged;
- the user can edit, save, and export the result.
