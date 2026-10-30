"""Small application actions used by the Specora API.

This module contains response shaping and section metadata only. Specora does
not dispatch tasks, captions, or summaries: its generated artifact is a
reviewable specification.
"""

from typing import Any


SPECIFICATION_SECTION_LABELS = {
    "project_overview": "Project Overview",
    "functional_requirements": "Functional Requirements",
    "user_stories": "User Stories",
    "acceptance_criteria": "Acceptance Criteria",
    "non_functional_requirements": "Non-Functional Requirements",
    "open_questions": "Open Questions",
    "assumptions": "Assumptions",
}


def build_specification_response(raw_idea: str, result: dict[str, Any]) -> dict[str, Any]:
    """Add the original idea to a successful generation response.

    Keeping this shaping step outside the LLM module leaves `understand.py`
    responsible only for generation and validation, while the API receives a
    complete artifact that can later be persisted or versioned.
    """
    if result.get("type") == "error":
        return result

    return {
        "type": "specification",
        "raw_idea": raw_idea,
        "data": result["data"],
        "generation_metadata": result.get("generation_metadata", {}),
    }
