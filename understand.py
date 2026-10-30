"""
Understanding layer for Specora AI.

This module receives a product idea as text and asks an LLM to produce a
structured, reviewable software specification.

Specora receives a product idea and produces one specification draft:

    product idea -> specification draft

The module does not claim that the generated specification is validated. It
keeps assumptions and open questions visible so that a human can review them.
"""

import json
import os

from openai import OpenAI


# ---------------------------------------------------------------------------
# BLOCK 1 — Specora's generation instructions
# ---------------------------------------------------------------------------
#
# The model acts as a product-specification assistant. It must distinguish
# information stated by the user from information that it has inferred.
#
# The model is instructed to return the same language as the input idea and to
# keep unknown decisions in open_questions or assumptions instead of silently
# inventing them.

SYSTEM_PROMPT = """You are Specora AI, a product specification assistant.

Transform the user's product idea into a structured first-draft software
specification. This is a proposal for human review, not a final validation.

Return exactly the JSON structure requested by the schema. Do not add prose
outside the JSON object.

Write the result in the same language as the user's idea, unless the user
explicitly asks for another language.

Rules:
- Preserve the user's product intent.
- Do not invent business decisions, integrations, legal requirements, prices,
  roles, or technical constraints as facts.
- If information is missing, record it as an open question or an assumption.
- Make functional requirements concrete and testable.
- Give every requirement, user story, acceptance-criteria group,
  non-functional requirement, question, and assumption a unique identifier.
- Link each acceptance-criteria group to an existing user story using
  user_story_id.
- Acceptance criteria must be observable and verifiable.
- Use priority values must, should, could, or unknown when the idea does not
  establish a priority.
- For non-functional requirements, use relevant categories such as security,
  performance, accessibility, reliability, privacy, compatibility, or
  maintainability. Do not force irrelevant categories.
"""


# ---------------------------------------------------------------------------
# BLOCK 2 — Canonical JSON schema returned by the model
# ---------------------------------------------------------------------------
#
# This is the new Specora contract. The former schema had three alternative
# branches for task/content/summary. Specora needs one complete specification
# object containing its six product sections. The nested objects are explicit
# and have additionalProperties=False so that unexpected model fields are not
# silently accepted.
#
# Every field is required inside the structured-output schema. When the model
# does not know a value, it should use an empty array, "unknown", or a clearly
# labelled question/assumption instead of omitting the field.

_TARGET_USER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "name", "description"],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
    },
}

_SCOPE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["in_scope", "out_of_scope"],
    "properties": {
        "in_scope": {"type": "array", "items": {"type": "string"}},
        "out_of_scope": {"type": "array", "items": {"type": "string"}},
    },
}

_PROJECT_OVERVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "proposed_name",
        "summary",
        "problem_statement",
        "goals",
        "target_users",
        "scope",
    ],
    "properties": {
        "proposed_name": {"type": "string"},
        "summary": {"type": "string"},
        "problem_statement": {"type": "string"},
        "goals": {"type": "array", "items": {"type": "string"}},
        "target_users": {"type": "array", "items": _TARGET_USER_SCHEMA},
        "scope": _SCOPE_SCHEMA,
    },
}

_FUNCTIONAL_REQUIREMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "title", "description", "priority", "actor"],
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "priority": {
            "type": "string",
            "enum": ["must", "should", "could", "unknown"],
        },
        "actor": {"type": "string"},
    },
}

_USER_STORY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "id",
        "feature",
        "as_a",
        "i_want",
        "so_that",
        "related_requirement_ids",
    ],
    "properties": {
        "id": {"type": "string"},
        "feature": {"type": "string"},
        "as_a": {"type": "string"},
        "i_want": {"type": "string"},
        "so_that": {"type": "string"},
        "related_requirement_ids": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}

_ACCEPTANCE_CRITERIA_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "user_story_id", "criteria"],
    "properties": {
        "id": {"type": "string"},
        "user_story_id": {"type": "string"},
        "criteria": {"type": "array", "items": {"type": "string"}},
    },
}

_NON_FUNCTIONAL_REQUIREMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "category", "description", "priority"],
    "properties": {
        "id": {"type": "string"},
        "category": {"type": "string"},
        "description": {"type": "string"},
        "priority": {
            "type": "string",
            "enum": ["must", "should", "could", "unknown"],
        },
    },
}

_OPEN_QUESTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "question", "related_area"],
    "properties": {
        "id": {"type": "string"},
        "question": {"type": "string"},
        "related_area": {"type": "string"},
    },
}

_ASSUMPTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "statement", "needs_validation"],
    "properties": {
        "id": {"type": "string"},
        "statement": {"type": "string"},
        "needs_validation": {"type": "boolean"},
    },
}

SPECIFICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "project_overview",
        "functional_requirements",
        "user_stories",
        "acceptance_criteria",
        "non_functional_requirements",
        "open_questions",
        "assumptions",
    ],
    "properties": {
        "project_overview": _PROJECT_OVERVIEW_SCHEMA,
        "functional_requirements": {
            "type": "array",
            "items": _FUNCTIONAL_REQUIREMENT_SCHEMA,
        },
        "user_stories": {
            "type": "array",
            "items": _USER_STORY_SCHEMA,
        },
        "acceptance_criteria": {
            "type": "array",
            "items": _ACCEPTANCE_CRITERIA_SCHEMA,
        },
        "non_functional_requirements": {
            "type": "array",
            "items": _NON_FUNCTIONAL_REQUIREMENT_SCHEMA,
        },
        "open_questions": {
            "type": "array",
            "items": _OPEN_QUESTION_SCHEMA,
        },
        "assumptions": {
            "type": "array",
            "items": _ASSUMPTION_SCHEMA,
        },
    },
}

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "specora_specification",
        "strict": True,
        "schema": SPECIFICATION_SCHEMA,
    },
}


# ---------------------------------------------------------------------------
# BLOCK 3 — Backend selection
# ---------------------------------------------------------------------------
#
# The application can use OpenAI in the cloud or a local
# OpenAI-compatible server such as llama.cpp. The rest of the module does not
# need to know which provider is active.

def active_backend() -> str:
    return os.getenv("UNDERSTAND_BACKEND", "openai").strip().lower()


def _resolve_client() -> tuple[OpenAI, str]:
    """Return the configured LLM client and model name."""
    if active_backend() == "local":
        base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:8080/v1")
        model = os.getenv("LOCAL_LLM_MODEL", "qwen2.5-1.5b-instruct")
        return OpenAI(base_url=base_url, api_key="sk-local-noop"), model

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set — add it to your .env file.")
    return OpenAI(api_key=key), "gpt-4o"


# ---------------------------------------------------------------------------
# BLOCK 4 — Defensive validation after the model response
# ---------------------------------------------------------------------------
#
# OpenAI structured output validates the JSON shape when supported. A local
# OpenAI-compatible server may not enforce the same schema, so we also perform
# a small application-level validation. This catches missing top-level
# sections, duplicate IDs, and broken links between stories and criteria.
#
# This is intentionally not a second full JSON-schema engine. The canonical
# schema above remains the source of truth; these checks protect the domain
# relationships that are especially important to Specora.

_REQUIRED_SECTIONS = (
    "project_overview",
    "functional_requirements",
    "user_stories",
    "acceptance_criteria",
    "non_functional_requirements",
    "open_questions",
    "assumptions",
)


def _validate_specification(data: object) -> dict:
    """Validate the minimum Specora shape and cross-section references."""
    if not isinstance(data, dict):
        raise ValueError("Specification must be a JSON object.")

    missing = [section for section in _REQUIRED_SECTIONS if section not in data]
    if missing:
        raise ValueError(f"Missing specification sections: {', '.join(missing)}")

    for section in _REQUIRED_SECTIONS[1:]:
        if not isinstance(data[section], list):
            raise ValueError(f"Specification section '{section}' must be a list.")

    if not isinstance(data["project_overview"], dict):
        raise ValueError("project_overview must be an object.")

    known_ids: set[str] = set()
    for section in (
        "functional_requirements",
        "user_stories",
        "acceptance_criteria",
        "non_functional_requirements",
        "open_questions",
        "assumptions",
    ):
        for item in data[section]:
            if not isinstance(item, dict):
                raise ValueError(f"Items in '{section}' must be objects.")
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id.strip():
                raise ValueError(f"Each item in '{section}' needs a non-empty id.")
            if item_id in known_ids:
                raise ValueError(f"Duplicate specification id: {item_id}")
            known_ids.add(item_id)

    requirement_ids = {
        item["id"]
        for item in data["functional_requirements"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for story in data["user_stories"]:
        related_ids = story.get("related_requirement_ids")
        if not isinstance(related_ids, list):
            raise ValueError(
                f"User story {story.get('id')} has invalid related requirements."
            )
        unknown_ids = [item_id for item_id in related_ids if item_id not in requirement_ids]
        if unknown_ids:
            raise ValueError(
                f"User story {story.get('id')} references unknown requirements: "
                f"{', '.join(unknown_ids)}"
            )

    story_ids = {
        item["id"]
        for item in data["user_stories"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for criterion_group in data["acceptance_criteria"]:
        story_id = criterion_group.get("user_story_id")
        if story_id not in story_ids:
            raise ValueError(
                "Acceptance criteria reference an unknown user story: "
                f"{story_id}"
            )

    return data


# ---------------------------------------------------------------------------
# BLOCK 5 — Main Specora generation function
# ---------------------------------------------------------------------------
#
# The function accepts a raw product idea. It is deliberately independent from
# any input method: the idea may come from the HTML form, an API client, or a
# future audio-to-text adapter.
#
# The return contract is specific to Specora. Successful generation uses
# type="specification"; failures use type="error".

def understand(raw_idea: str) -> dict:
    """Generate a Specora specification from a product idea.

    Return:
        {"type": "specification", "data": {...}}
    or:
        {"type": "error", "error": "..."}
    """
    raw_idea = (raw_idea or "").strip()
    if not raw_idea:
        return {"type": "error", "error": "Empty product idea."}

    try:
        client, model = _resolve_client()
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format=RESPONSE_FORMAT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw_idea},
            ],
        )
    except Exception as exc:
        hint = ""
        if active_backend() == "local":
            hint = " (is the llama.cpp server running at LOCAL_LLM_BASE_URL?)"
        return {
            "type": "error",
            "error": f"[{active_backend()}] request failed: {exc}{hint}",
        }

    choice = response.choices[0]

    # Structured-output refusals are returned on a dedicated field by OpenAI.
    # Treat them as a normal application error and preserve the caller's
    # ability to render an error without crashing.
    refusal = getattr(choice.message, "refusal", None)
    if refusal:
        return {"type": "error", "error": f"Model refused: {refusal}"}

    raw_content = choice.message.content or ""
    try:
        specification = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        return {
            "type": "error",
            "error": f"Could not parse model JSON: {exc}",
            "raw": raw_content,
        }

    try:
        specification = _validate_specification(specification)
    except ValueError as exc:
        return {
            "type": "error",
            "error": f"Invalid Specora specification: {exc}",
            "raw": specification,
        }

    return {
        "type": "specification",
        "data": specification,
        "generation_metadata": {
            "backend": active_backend(),
            "model": model,
        },
    }
