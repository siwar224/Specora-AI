"""HTML export rendering for Specora specification drafts.

The export is intentionally a view of the canonical specification data.  It
does not reshape or regenerate the document, and it never renders the overview
scope fields.  The relationships owned by the canonical schema remain visible
through linked IDs between requirements, user stories, and acceptance criteria.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any, Iterable


TEMPLATE_PATH = Path(__file__).with_name("static") / "specification-export.html"


def _escape(value: Any, fallback: str = "Not specified") -> str:
    """Return safe text for an HTML text or attribute context."""
    if value is None or value == "":
        value = fallback
    return html.escape(str(value), quote=True)


def _slug(value: Any) -> str:
    """Create a stable, readable fragment for an export anchor."""
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value).strip()).strip("-")
    return slug.lower() or "item"


def _anchor(prefix: str, identifier: Any) -> str:
    return f"{prefix}-{_slug(identifier)}"


def _id_badge(identifier: Any, *, prefix: str | None = None) -> str:
    text = _escape(identifier)
    if prefix:
        return f'<a class="id-badge" href="#{_anchor(prefix, identifier)}">{text}</a>'
    return f'<span class="id-badge">{text}</span>'


def _relation_link(identifier: Any, prefix: str) -> str:
    return (
        f'<a class="relation-link" href="#{_anchor(prefix, identifier)}">'
        f"{_escape(identifier)}</a>"
    )


def _join_relations(values: Iterable[Any], prefix: str, empty: str = "None") -> str:
    values = list(values or [])
    if not values:
        return f'<span class="muted">{_escape(empty)}</span>'
    return " ".join(_relation_link(value, prefix) for value in values)


def _list(items: Iterable[Any], empty: str = "No information provided.") -> str:
    values = list(items or [])
    if not values:
        return f'<p class="empty">{_escape(empty)}</p>'
    return "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in values) + "</ul>"


def _priority(value: Any) -> str:
    label = _escape(value, "unknown")
    tone = _slug(value or "unknown")
    return f'<span class="priority priority-{tone}">{label}</span>'


def _record_header(identifier: Any, title: Any, prefix: str) -> str:
    return (
        f'<div class="record-header">'
        f'<div class="record-title"><span class="record-index">{_id_badge(identifier, prefix=prefix)}</span>'
        f'<h3>{_escape(title)}</h3></div>'
        f"</div>"
    )


def _render_overview(overview: dict[str, Any]) -> str:
    users = overview.get("target_users") or []
    user_cards = "".join(
        f'<article class="person-card" data-specora-id="{_escape(user.get("id"))}">'
        f'<div class="person-heading"><h3>{_escape(user.get("name"))}</h3>'
        f'<span class="small-id">{_escape(user.get("id"))}</span></div>'
        f'<p>{_escape(user.get("description"))}</p></article>'
        for user in users
        if isinstance(user, dict)
    )
    if not user_cards:
        user_cards = '<p class="empty">No target users provided.</p>'

    return f"""
      <div class="overview-lead">
        <div>
          <p class="field-label">Summary</p>
          <p class="lead-copy">{_escape(overview.get('summary'))}</p>
        </div>
        <div class="problem-box">
          <p class="field-label">Problem statement</p>
          <p>{_escape(overview.get('problem_statement'))}</p>
        </div>
      </div>
      <div class="overview-grid">
        <div class="content-block">
          <p class="field-label">Goals</p>
          {_list(overview.get('goals'), 'No goals provided.')}
        </div>
        <div class="content-block">
          <p class="field-label">Target users</p>
          <div class="people-grid">{user_cards}</div>
        </div>
      </div>
    """


def _render_functional_requirements(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="empty">No functional requirements generated.</p>'
    return "".join(
        f'<article class="record" id="{_anchor("fr", item.get("id"))}" '
        f'data-specora-id="{_escape(item.get("id"))}">'
        f'{_record_header(item.get("id"), item.get("title"), "fr")}'
        f'<div class="record-meta"><span>{_escape(item.get("actor"), "Actor not specified")}</span>'
        f'{_priority(item.get("priority"))}</div>'
        f'<p>{_escape(item.get("description"))}</p>'
        f'</article>'
        for item in items
    )


def _render_user_stories(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="empty">No user stories generated.</p>'
    return "".join(
        f'<article class="record" id="{_anchor("us", item.get("id"))}" '
        f'data-specora-id="{_escape(item.get("id"))}">'
        f'{_record_header(item.get("id"), item.get("feature"), "us")}'
        f'<p class="story"><strong>As a</strong> {_escape(item.get("as_a"))}, '
        f'<strong>I want</strong> {_escape(item.get("i_want"))}, '
        f'<strong>so that</strong> {_escape(item.get("so_that"))}.</p>'
        f'<div class="relationship"><span class="field-label">Related requirements</span>'
        f'<span class="relationship-values">{_join_relations(item.get("related_requirement_ids"), "fr", "None linked")}</span></div>'
        f'</article>'
        for item in items
    )


def _render_acceptance_criteria(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="empty">No acceptance criteria generated.</p>'
    return "".join(
        f'<article class="record" id="{_anchor("ac", item.get("id"))}" '
        f'data-specora-id="{_escape(item.get("id"))}">'
        f'<div class="record-header"><div class="record-title">'
        f'<span class="record-index">{_id_badge(item.get("id"), prefix="ac")}</span>'
        f'<h3>Acceptance criteria</h3></div>'
        f'<div class="criteria-story">User story {_relation_link(item.get("user_story_id"), "us")}</div></div>'
        f'<ol class="criteria-list">'
        + "".join(f"<li>{_escape(criterion)}</li>" for criterion in (item.get("criteria") or []))
        + "</ol></article>"
        for item in items
    )


def _render_non_functional_requirements(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="empty">No non-functional requirements generated.</p>'
    return "".join(
        f'<article class="record" id="{_anchor("nfr", item.get("id"))}" '
        f'data-specora-id="{_escape(item.get("id"))}">'
        f'{_record_header(item.get("id"), item.get("category"), "nfr")}'
        f'<div class="record-meta">{_priority(item.get("priority"))}</div>'
        f'<p>{_escape(item.get("description"))}</p>'
        f'</article>'
        for item in items
    )


def _render_questions(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="empty">No open questions generated.</p>'
    return "".join(
        f'<article class="record compact" id="{_anchor("q", item.get("id"))}" '
        f'data-specora-id="{_escape(item.get("id"))}">'
        f'<div class="record-header"><div class="record-title">'
        f'<span class="record-index">{_id_badge(item.get("id"), prefix="q")}</span>'
        f'<h3>{_escape(item.get("question"))}</h3></div>'
        f'<span class="topic">{_escape(item.get("related_area"))}</span></div>'
        f'</article>'
        for item in items
    )


def _render_assumptions(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="empty">No assumptions generated.</p>'
    return "".join(
        f'<article class="record compact" id="{_anchor("a", item.get("id"))}" '
        f'data-specora-id="{_escape(item.get("id"))}">'
        f'<div class="record-header"><div class="record-title">'
        f'<span class="record-index">{_id_badge(item.get("id"), prefix="a")}</span>'
        f'<h3>{_escape(item.get("statement"))}</h3></div>'
        f'<span class="validation {"needs-validation" if item.get("needs_validation") else "reviewed"}">'
        f'{"Needs validation" if item.get("needs_validation") else "Reviewed"}</span></div>'
        f'</article>'
        for item in items
    )


def render_specification_html(
    specification: dict[str, Any],
    *,
    raw_idea: str = "",
    generation_metadata: dict[str, Any] | None = None,
) -> str:
    """Render a complete, print-ready HTML export for a specification.

    The seven visible sections are deliberately assembled in the requested
    order.  ``project_overview.scope`` is never read or interpolated here, so
    both ``in_scope`` and ``out_of_scope`` stay out of the export.
    """
    overview = specification.get("project_overview") or {}
    metadata = generation_metadata or {}
    title = overview.get("proposed_name") or "Untitled specification"
    summary = overview.get("summary") or "Specification draft for human review."
    raw_idea_markup = (
        f'<div class="source-idea"><p class="field-label">Source idea</p>'
        f'<p>{_escape(raw_idea)}</p></div>'
        if raw_idea
        else ""
    )

    replacements = {
        "{{TITLE}}": _escape(title),
        "{{SUMMARY}}": _escape(summary),
        "{{RAW_IDEA}}": raw_idea_markup,
        "{{MODEL}}": _escape(metadata.get("model"), "Not recorded"),
        "{{BACKEND}}": _escape(metadata.get("backend"), "Not recorded"),
        "{{SCHEMA_VERSION}}": _escape(metadata.get("schema_version"), "1.0"),
        "{{OVERVIEW}}": _render_overview(overview),
        "{{FUNCTIONAL_REQUIREMENTS}}": _render_functional_requirements(
            specification.get("functional_requirements") or []
        ),
        "{{USER_STORIES}}": _render_user_stories(specification.get("user_stories") or []),
        "{{ACCEPTANCE_CRITERIA}}": _render_acceptance_criteria(
            specification.get("acceptance_criteria") or []
        ),
        "{{NON_FUNCTIONAL_REQUIREMENTS}}": _render_non_functional_requirements(
            specification.get("non_functional_requirements") or []
        ),
        "{{OPEN_QUESTIONS}}": _render_questions(specification.get("open_questions") or []),
        "{{ASSUMPTIONS}}": _render_assumptions(specification.get("assumptions") or []),
    }
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    for token, value in replacements.items():
        template = template.replace(token, value)
    return template
