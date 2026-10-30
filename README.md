# Specora AI

From idea to development-ready specifications.

## Vision

Specora AI helps a client, Product Owner, or development team turn a rough
product idea into a structured specification that can be reviewed before
development starts.

For example, a user might write:

> I want to build a gym-room booking application. Customers should be able to
> see sessions, book a place, pay for a subscription, and receive a
> confirmation. Managers should be able to manage sessions and bookings.

This description is a useful starting point, but it is not yet precise enough
for a development team. Specora AI uses an LLM to propose a first structured
draft, then lets the user inspect, correct, complete, save, and export it.

Specora AI is an assistant for product discovery and specification writing. It
does not replace a Product Owner and does not claim that an LLM-generated draft
is automatically complete or validated.

## What Specora generates

Every project produces six main sections:

### 1. Project Overview

Proposed name, concise summary, problem statement, goals, target users, and
scope boundaries.

### 2. Functional Requirements

The capabilities the product must provide, written as identifiable and
testable requirements.

### 3. User Stories

Stories organized by feature or user journey, with an actor, an intention, and a
desired outcome.

### 4. Acceptance Criteria

Observable conditions linked to each relevant user story. Criteria should be
specific enough to guide implementation and testing.

### 5. Non-Functional Requirements

Relevant quality attributes such as security, performance, accessibility,
reliability, privacy, compatibility, and maintainability. Unknown items should
be marked as unknown instead of invented.

### 6. Open Questions & Assumptions

Information that still needs a decision, plus assumptions made to produce the
draft. This section is central to the human review step.

## Core workflow

```text
User idea
   ↓
Project creation
   ↓
LLM analysis with a versioned structured schema
   ↓
Six-section specification draft
   ↓
Human review and edits
   ↓
Section regeneration when needed
   ↓
Local save and Markdown/HTML export
```

The original idea is always preserved. Regenerating one section must not
silently overwrite user edits in unrelated sections.

## MVP goals

The first version should allow a user to:

- create a project from a free-form idea;
- choose or detect the output language;
- generate a structured specification with an LLM;
- review and edit each section;
- regenerate one section while preserving the rest;
- see assumptions and open questions clearly;
- save and reopen projects locally;
- export a project as Markdown or HTML;
- continue editing if the LLM is unavailable.

## Non-goals for the MVP

Specora is not initially intended to:

- generate a complete application automatically;
- replace product discovery or stakeholder validation;
- manage developer tasks or project execution;
- provide multi-user collaboration and permissions;
- require a cloud database;
- make voice transcription part of the core workflow.

Voice input can be added later as an input method, but the central domain is
idea-to-specification rather than speech-to-intent classification.

## Target architecture

### Frontend

Plain HTML, CSS, and JavaScript. The first interface should prioritize a clear
writing and review experience over a complex dashboard:

- idea input;
- generation state and errors;
- section navigation;
- editable specification content;
- visible assumptions and questions;
- save, reopen, and export actions.

### Backend

FastAPI provides the HTTP API and coordinates the domain services:

- project and specification models;
- input validation;
- LLM orchestration;
- local persistence;
- partial regeneration;
- Markdown and HTML export.

The LLM provider must be isolated behind an adapter so that a cloud provider or
a local model can be selected through configuration without changing the API
contract.

### Local storage

The default target is a local SQLite database containing projects and versioned
specification drafts. JSON is useful for fixtures, import/export, and backups.
Database files, generated exports, and secrets must remain outside version
control.

## Canonical specification shape

The backend should own one versioned schema shared by the API, LLM validation,
storage, and exporters. A project should include at least:

```json
{
  "id": "local-project-id",
  "title": "Proposed project name",
  "raw_idea": "Original idea written by the user",
  "language": "en",
  "status": "review",
  "sections": {
    "project_overview": {},
    "functional_requirements": [],
    "user_stories": [],
    "acceptance_criteria": [],
    "non_functional_requirements": [],
    "open_questions_assumptions": {}
  },
  "generation_metadata": {
    "model": "configured-model",
    "schema_version": "1.0",
    "generated_at": "2026-01-01T00:00:00Z"
  }
}
```

This is an illustrative shape, not a final implementation contract. The exact
schema should be formalized before building the generation endpoint.

## Suggested API surface

The initial API can expose:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/projects` | Create a project from an idea |
| `GET` | `/api/projects` | List local projects |
| `GET` | `/api/projects/{project_id}` | Read a project |
| `PATCH` | `/api/projects/{project_id}` | Save user edits |
| `POST` | `/api/projects/{project_id}/generate` | Generate or regenerate a draft |
| `POST` | `/api/projects/{project_id}/sections/{section}/regenerate` | Regenerate one section |
| `GET` | `/api/projects/{project_id}/export?format=markdown` | Export Markdown or HTML |

The API is provisional and may be adjusted during implementation, but full
generation and partial regeneration should remain separate operations.

## LLM behavior requirements

The generation layer should:

- return structured JSON validated against the canonical schema;
- preserve uncertainty as assumptions or open questions;
- produce traceable identifiers for requirements and user stories;
- generate acceptance criteria that are observable and testable;
- avoid inventing business decisions without marking them as assumptions;
- record model, prompt/schema version, timestamp, and failures;
- preserve the last valid draft if a request fails.

## Repository status

This repository started from an earlier Voice Insight project. Existing files
such as speech-to-text or voice-understanding modules are considered legacy
material while Specora is being rebuilt. They should only be reused when their
behavior fits the Specora domain and after the relevant boundaries are defined.

The product documentation in this README and the rules in `AGENTS.md` describe
the intended Specora direction independently of that inherited code.

## Development roadmap

### Phase 1 — Foundation

- define the canonical Pydantic/domain schema;
- create the FastAPI application boundary;
- add local SQLite persistence;
- add health and project CRUD endpoints;
- create the minimal HTML review interface.

### Phase 2 — Specification generation

- version the system prompt and JSON schema;
- implement the LLM adapter;
- validate and persist generated drafts;
- expose generation progress and errors;
- add section-level regeneration.

### Phase 3 — Review and export

- improve editing and traceability in the UI;
- distinguish generated content from user edits where practical;
- implement Markdown and HTML exporters;
- add project version history and recovery of the last valid draft.

### Phase 4 — Hardening

- add automated tests for generation failures and malformed output;
- improve accessibility and responsive layout;
- add import/export fixtures;
- evaluate optional local LLM support;
- assess future voice input without coupling it to the core domain.

## Definition of done for an MVP draft

A generated project is usable when its goals and target users are explicit,
requirements are identifiable, user stories are linked to verifiable acceptance
criteria, relevant non-functional concerns are present or marked unknown, and
assumptions and open questions are visible. The user must be able to edit, save,
reopen, and export the result.

## License and status

Specora AI is an early-stage project. Product decisions, the schema, and the API
may evolve as the review workflow is tested with real product ideas.
