#!/usr/bin/env python3
"""Validate Conference Discovery Harness run artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


ARTIFACTS_BY_STAGE = {
    "discovery": (
        "REQUEST.md",
        "AGGREGATORS.md",
        "CONFERENCE_SOURCES.md",
    ),
    "raw": (
        "REQUEST.md",
        "AGGREGATORS.md",
        "CONFERENCE_SOURCES.md",
        "RAW_CONFERENCES.json",
    ),
    "normalized": (
        "REQUEST.md",
        "AGGREGATORS.md",
        "CONFERENCE_SOURCES.md",
        "RAW_CONFERENCES.json",
        "NORMALIZED_CONFERENCES.json",
        "ENTITY_RESOLUTION.md",
        "QUALITY_REPORT.md",
    ),
    "complete": (
        "REQUEST.md",
        "AGGREGATORS.md",
        "CONFERENCE_SOURCES.md",
        "RAW_CONFERENCES.json",
        "NORMALIZED_CONFERENCES.json",
        "ENTITY_RESOLUTION.md",
        "QUALITY_REPORT.md",
        "REPORT.md",
    ),
}

ALLOWED_STATUSES = {
    "complete",
    "partial",
    "not-published",
    "not-applicable",
    "inaccessible",
    "not-authorized",
    "unresolved",
}

BRANCH_NAMES = (
    "identity_and_aliases",
    "series_edition_and_acronym",
    "organizers",
    "description_themes_topics_type_and_languages",
    "dates_times_timezone_recurrence_and_status",
    "websites_and_event_urls",
    "people_and_public_contacts",
    "committees_and_roles",
    "schedule_tracks_sessions_workshops_and_social_events",
    "registration",
    "venue",
    "sponsors_exhibitors_and_partners",
    "hotels_and_booking",
    "attendees_and_attendance",
    "provenance",
    "confidence",
    "contradictions",
    "unresolved_fields",
)

QUALITY_REPORT_SECTIONS = (
    "Run",
    "Artifact and Schema Results",
    "Entity Counts",
    "Duplicate Candidates and Resolution Outcomes",
    "Reference Integrity",
    "Branch Coverage",
    "Source-Class Coverage",
    "Conferences Without Official Sources",
    "Conflicts",
    "Translation Quality",
    "Attendee Privacy and Authorization",
    "Inaccessible Sources and Collection Gaps",
    "Blocking Warnings",
    "Non-Blocking Warnings",
)

QUALITY_REPORT_SUBSECTIONS = (
    "Unresolved Foreign Keys",
    "Unresolved Source References",
)

REQUEST_NONE_VALUES = {"none", "none supplied", "not applicable", "n/a"}
LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")

AGGREGATOR_RECORD_FIELDS = (
    "Stable aggregator ID",
    "Provider name",
    "Canonical public URL",
    "Observed geography",
    "Observed topics",
    "Observed languages",
    "Observed date coverage",
    "Reviewed listing page",
    "Access date",
    "Reviewability",
    "Reliability",
    "Limitations",
    "Access failures",
)

SOURCE_RECORD_FIELDS = (
    "Stable source ID",
    "Candidate conference ID",
    "Candidate conference name and aliases",
    "Source class",
    "Title",
    "Publisher or owner",
    "Public URL",
    "Publication or update date",
    "Access date",
    "Conference relationship",
    "Review state",
    "Bounded excerpt or faithful summary",
    "Supported fields or claims",
    "Reliability",
    "Independence",
    "Limitations",
    "Extraction eligibility",
    "Eligibility rationale",
)

SOURCE_CLAIM_BY_BRANCH = {
    "identity_and_aliases": "identity",
    "series_edition_and_acronym": "series",
    "organizers": "organizers",
    "description_themes_topics_type_and_languages": "description",
    "dates_times_timezone_recurrence_and_status": "dates",
    "websites_and_event_urls": "official-url",
    "people_and_public_contacts": "people",
    "committees_and_roles": "committees",
    "schedule_tracks_sessions_workshops_and_social_events": "schedule",
    "registration": "registration",
    "venue": "venue",
    "sponsors_exhibitors_and_partners": "sponsors",
    "hotels_and_booking": "hotels",
    "attendees_and_attendance": "attendance",
    "provenance": "provenance",
    "confidence": "confidence",
    "contradictions": "contradictions",
    "unresolved_fields": "unresolved-fields",
}

DIRECT_SOURCE_CLAIMS = set(SOURCE_CLAIM_BY_BRANCH.values())

REPORT_REQUIRED_SECTIONS = (
    "Search Scope",
    "Coverage",
    "Conference Comparison",
    "Conference Summaries",
    "Data-Quality Warnings",
    "Entity-Resolution Notes",
    "Translation Notes",
    "Source Index",
)

QUALITY_ENTITY_LABELS = {
    "Conferences": "conferences",
    "Conference series": "conference_series",
    "Organizations": "organizations",
    "People": "people",
    "Venues": "venues",
    "Sessions and events": "sessions_and_events",
    "Registration offers": "registration_offers",
    "Sponsors and partnerships": "sponsors_and_partnerships",
    "Hotels": "hotels",
    "Attendee records or aggregates": "attendee_records_or_aggregates",
    "Sources": "sources",
    "Translations": "translations",
    "Entity-resolution decisions": "entity_resolution_decisions",
}

BRANCH_DISPLAY_LABELS = {
    "Identity and aliases": "identity_and_aliases",
    "Series, edition, and acronym": "series_edition_and_acronym",
    "Organizers": "organizers",
    "Description, themes, topics, type, and languages": (
        "description_themes_topics_type_and_languages"
    ),
    "Dates, times, timezone, recurrence, and status": (
        "dates_times_timezone_recurrence_and_status"
    ),
    "Websites and event URLs": "websites_and_event_urls",
    "People and contacts": "people_and_public_contacts",
    "Committees and roles": "committees_and_roles",
    "Schedule, tracks, sessions, workshops, and social events": (
        "schedule_tracks_sessions_workshops_and_social_events"
    ),
    "Registration": "registration",
    "Venue": "venue",
    "Sponsors, exhibitors, and partners": "sponsors_exhibitors_and_partners",
    "Hotels": "hotels_and_booking",
    "Attendees and attendance aggregates": "attendees_and_attendance",
    "Provenance": "provenance",
    "Confidence": "confidence",
    "Contradictions": "contradictions",
    "Unresolved fields": "unresolved_fields",
}

QUALITY_STATUS_LABELS = {
    "Complete": "complete",
    "Partial": "partial",
    "Not published": "not-published",
    "Not applicable": "not-applicable",
    "Inaccessible": "inaccessible",
    "Not authorized": "not-authorized",
    "Unresolved": "unresolved",
}

CONFERENCE_BRANCH_FIELDS = {
    "identity_and_aliases": ("canonical_name", "aliases"),
    "series_edition_and_acronym": ("series_id", "edition", "acronym"),
    "organizers": ("organizer_ids",),
    "description_themes_topics_type_and_languages": (
        "description",
        "themes",
        "topics",
        "conference_type",
        "language_codes",
    ),
    "dates_times_timezone_recurrence_and_status": (
        "start_date",
        "end_date",
        "start_time",
        "end_time",
        "timezone",
        "recurrence",
        "event_status",
    ),
    "websites_and_event_urls": ("official_url", "event_urls"),
    "people_and_public_contacts": ("person_ids",),
    "committees_and_roles": ("committee_memberships",),
    "schedule_tracks_sessions_workshops_and_social_events": ("session_event_ids",),
    "registration": ("registration_offer_ids",),
    "venue": ("venue_ids",),
    "sponsors_exhibitors_and_partners": ("partnership_ids",),
    "hotels_and_booking": ("hotel_ids",),
    "attendees_and_attendance": ("attendee_record_ids", "intended_audience"),
    "contradictions": ("contradictions",),
    "unresolved_fields": ("unresolved_fields",),
}

CONFERENCE_FIELD_BRANCH = {
    field: branch
    for branch, fields in CONFERENCE_BRANCH_FIELDS.items()
    for field in fields
}

PROVENANCE_COLLECTIONS = (
    "conferences",
    "conference_series",
    "organizations",
    "people",
    "venues",
    "sessions_and_events",
    "registration_offers",
    "sponsors_and_partnerships",
    "hotels",
    "attendee_records_or_aggregates",
)

PROVENANCE_EXCLUDED_FIELDS = {
    "id",
    "field_provenance",
    "source_ids",
    "listing_source_ids",
    "translation_ids",
    "entity_resolution_decision_ids",
    "collection_statuses",
    "collection_status",
    "authorization_basis",
}

COLLECTION_PREFIXES = {
    "conferences": r"C[0-9]{3,}",
    "conference_series": r"CS[0-9]{3,}",
    "organizations": r"O[0-9]{3,}",
    "people": r"P[0-9]{3,}",
    "venues": r"V[0-9]{3,}",
    "sessions_and_events": r"E[0-9]{3,}",
    "registration_offers": r"R[0-9]{3,}",
    "sponsors_and_partnerships": r"SP[0-9]{3,}",
    "hotels": r"H[0-9]{3,}",
    "attendee_records_or_aggregates": r"AT[0-9]{3,}",
    "sources": r"(?:A|S)[0-9]{3,}",
    "translations": r"T[0-9]{3,}",
    "entity_resolution_decisions": r"ER[0-9]{3,}",
}

ENTITY_TYPE_COLLECTIONS = {
    "conference": "conferences",
    "conference-series": "conference_series",
    "organization": "organizations",
    "person": "people",
    "venue": "venues",
    "session-event": "sessions_and_events",
    "registration-offer": "registration_offers",
    "sponsor-partnership": "sponsors_and_partnerships",
    "hotel": "hotels",
    "attendee": "attendee_records_or_aggregates",
    "source": "sources",
    "translation": "translations",
    "entity-resolution-decision": "entity_resolution_decisions",
}

RUN_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_ID_RE = re.compile(r"^(?:A|S)[0-9]{3,}$")
MISSING = object()


def pointer_child(path: str, value: str | int) -> str:
    token = str(value).replace("~", "~0").replace("/", "~1")
    return f"{path}/{token}" if path else f"/{token}"


def display_path(path: str) -> str:
    return f"#{path}" if path else "#"


def resolve_json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        return MISSING
    current = document
    for encoded_token in pointer[1:].split("/"):
        token = encoded_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                return MISSING
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit():
                return MISSING
            index = int(token)
            if index >= len(current):
                return MISSING
            current = current[index]
        else:
            return MISSING
    return current


def normalize_markdown_value(value: str) -> str:
    result = value.strip()
    if len(result) >= 2 and result[0] == "`" and result[-1] == "`":
        result = result[1:-1].strip()
    return result


def markdown_field(text: str, label: str) -> str | None:
    match = re.search(
        rf"(?mi)^-\s+{re.escape(label)}:\s*(.+?)\s*$",
        text,
    )
    return normalize_markdown_value(match.group(1)) if match else None


def markdown_section(text: str, heading: str) -> str | None:
    match = re.search(
        rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
    )
    if not match:
        return None
    lines = [
        normalize_markdown_value(line.strip())
        for line in match.group(1).splitlines()
        if line.strip() and not line.lstrip().startswith(">")
    ]
    return " ".join(lines).strip() or None


def markdown_section_raw(text: str, heading: str) -> str | None:
    match = re.search(
        rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
    )
    return match.group(1).strip() if match and match.group(1).strip() else None


def markdown_subsection(text: str, heading: str) -> str | None:
    match = re.search(
        rf"(?ms)^###\s+{re.escape(heading)}\s*$\n"
        rf"(.*?)(?=^###\s+|^##\s+|\Z)",
        text,
    )
    if not match:
        return None
    content = " ".join(
        line.strip()
        for line in match.group(1).splitlines()
        if line.strip() and not line.lstrip().startswith(">")
    )
    return content or None


def markdown_table(section: str) -> tuple[list[str], list[list[str]]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [
            normalize_markdown_value(cell.strip())
            for cell in stripped[1:-1].split("|")
        ]
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return (rows[0], rows[1:]) if rows else ([], [])


def markdown_table_rows(section: str) -> list[list[str]]:
    return markdown_table(section)[1]


@dataclass(frozen=True)
class RequestInfo:
    run_id: str | None
    mode: str | None
    source_run_id: str | None
    objective: str | None
    attendee_mode: str | None
    attendee_authorization: str | None
    output_language: str | None
    scope_signature: tuple[tuple[str, str], ...] = ()


class SchemaValidator:
    """Small draft 2020-12 subset covering the repository schemas."""

    def __init__(self, root_schema: dict[str, Any], artifact: str):
        self.root_schema = root_schema
        self.artifact = artifact
        self.errors: list[str] = []

    def validate(self, instance: Any) -> list[str]:
        self._validate(instance, self.root_schema, "")
        return self.errors

    def _add(self, path: str, message: str) -> None:
        self.errors.append(f"{self.artifact}{display_path(path)}: {message}")

    def _resolve_ref(self, reference: str) -> dict[str, Any] | None:
        if not reference.startswith("#/"):
            return None
        current: Any = self.root_schema
        for token in reference[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            if not isinstance(current, dict) or token not in current:
                return None
            current = current[token]
        return current if isinstance(current, dict) else None

    def _matches(self, instance: Any, schema: dict[str, Any], path: str) -> bool:
        saved = self.errors
        self.errors = []
        self._validate(instance, schema, path)
        matched = not self.errors
        self.errors = saved
        return matched

    @staticmethod
    def _is_type(instance: Any, expected: str) -> bool:
        if expected == "null":
            return instance is None
        if expected == "object":
            return isinstance(instance, dict)
        if expected == "array":
            return isinstance(instance, list)
        if expected == "string":
            return isinstance(instance, str)
        if expected == "boolean":
            return isinstance(instance, bool)
        if expected == "integer":
            return isinstance(instance, int) and not isinstance(instance, bool)
        if expected == "number":
            return isinstance(instance, (int, float)) and not isinstance(instance, bool)
        return True

    @staticmethod
    def _valid_format(value: str, format_name: str) -> bool:
        try:
            if format_name == "date":
                date.fromisoformat(value)
            elif format_name == "date-time":
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            elif format_name == "time":
                time.fromisoformat(value.replace("Z", "+00:00"))
            elif format_name == "uri":
                parsed = urlparse(value)
                return bool(parsed.scheme and (parsed.netloc or parsed.path))
        except ValueError:
            return False
        return True

    def _validate(self, instance: Any, schema: dict[str, Any], path: str) -> None:
        reference = schema.get("$ref")
        if reference is not None:
            resolved = self._resolve_ref(reference)
            if resolved is None:
                self._add(path, f"schema contains unresolved reference {reference!r}")
            else:
                self._validate(instance, resolved, path)

        one_of = schema.get("oneOf")
        if one_of is not None:
            matches = sum(self._matches(instance, option, path) for option in one_of)
            if matches != 1:
                self._add(path, f"must match exactly one allowed shape; matched {matches}")

        expected_type = schema.get("type")
        if expected_type is not None:
            expected_types = (
                expected_type if isinstance(expected_type, list) else [expected_type]
            )
            if not any(self._is_type(instance, item) for item in expected_types):
                self._add(
                    path,
                    f"expected type {' or '.join(expected_types)}, got "
                    f"{type(instance).__name__}",
                )
                return

        if "const" in schema and instance != schema["const"]:
            self._add(path, f"must equal {schema['const']!r}")
        if "enum" in schema and instance not in schema["enum"]:
            self._add(path, f"value {instance!r} is not in the allowed enum")

        if isinstance(instance, str):
            if "minLength" in schema and len(instance) < schema["minLength"]:
                self._add(path, f"length must be at least {schema['minLength']}")
            if "maxLength" in schema and len(instance) > schema["maxLength"]:
                self._add(path, f"length must be at most {schema['maxLength']}")
            if "pattern" in schema and not re.search(schema["pattern"], instance):
                self._add(path, f"value {instance!r} does not match {schema['pattern']!r}")
            if "format" in schema and not self._valid_format(instance, schema["format"]):
                self._add(path, f"value {instance!r} is not a valid {schema['format']}")

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                self._add(path, f"value must be at least {schema['minimum']}")
            if "maximum" in schema and instance > schema["maximum"]:
                self._add(path, f"value must be at most {schema['maximum']}")

        if isinstance(instance, list):
            if "minItems" in schema and len(instance) < schema["minItems"]:
                self._add(path, f"must contain at least {schema['minItems']} items")
            if "maxItems" in schema and len(instance) > schema["maxItems"]:
                self._add(path, f"must contain at most {schema['maxItems']} items")
            if schema.get("uniqueItems"):
                encoded = [
                    json.dumps(item, sort_keys=True, separators=(",", ":"))
                    for item in instance
                ]
                if len(encoded) != len(set(encoded)):
                    self._add(path, "array items must be unique")
            item_schema = schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(instance):
                    self._validate(item, item_schema, pointer_child(path, index))

        if isinstance(instance, dict):
            if "minProperties" in schema and len(instance) < schema["minProperties"]:
                self._add(path, f"must contain at least {schema['minProperties']} properties")
            properties = schema.get("properties", {})
            for required in schema.get("required", []):
                if required not in instance:
                    self._add(pointer_child(path, required), "required property is missing")
            property_name_schema = schema.get("propertyNames")
            if isinstance(property_name_schema, dict):
                for key in instance:
                    self._validate(key, property_name_schema, pointer_child(path, key))
            for key, value in instance.items():
                child_path = pointer_child(path, key)
                if key in properties:
                    self._validate(value, properties[key], child_path)
                    continue
                additional = schema.get("additionalProperties", True)
                if additional is False:
                    self._add(child_path, "unexpected property")
                elif isinstance(additional, dict):
                    self._validate(value, additional, child_path)

        for sub_schema in schema.get("allOf", []):
            self._validate(instance, sub_schema, path)

        conditional = schema.get("if")
        if isinstance(conditional, dict):
            branch = schema.get("then") if self._matches(instance, conditional, path) else schema.get("else")
            if isinstance(branch, dict):
                self._validate(instance, branch, path)


class RunValidator:
    def __init__(
        self,
        run_dir: Path,
        stage: str,
        visited_run_dirs: set[Path] | None = None,
    ):
        self.run_dir = run_dir
        self.stage = stage
        resolved_run_dir = run_dir.resolve()
        self.visited_run_dirs = set(visited_run_dirs or set())
        self.refresh_cycle = resolved_run_dir in self.visited_run_dirs
        self.visited_run_dirs.add(resolved_run_dir)
        self.errors: list[str] = []
        self.markdown: dict[str, str] = {}
        self.json_data: dict[str, Any] = {}
        self.request = RequestInfo(None, None, None, None, None, None, None)
        self.aggregator_ids: set[str] = set()
        self.source_ids: set[str] = set()
        self.aggregator_ledger_records: dict[str, dict[str, str]] = {}
        self.source_ledger_records: dict[str, dict[str, str]] = {}
        self.eligible_direct_source_ids: set[str] = set()
        self.normalized_source_records: dict[str, dict[str, Any]] = {}
        self.refresh_source_normalized: dict[str, Any] | None = None

    def add_error(self, artifact: str, path: str, message: str) -> None:
        suffix = display_path(path) if path.startswith("/") or not path else f":{path}"
        self.errors.append(f"{artifact}{suffix}: {message}")

    def validate(self) -> list[str]:
        self._validate_directory()
        self._load_required_artifacts()
        if "REQUEST.md" in self.markdown:
            self.request = self._validate_request(self.markdown["REQUEST.md"])
        if "AGGREGATORS.md" in self.markdown:
            self.aggregator_ids = self._validate_ledger(
                "AGGREGATORS.md", self.markdown["AGGREGATORS.md"], "A"
            )
            self.aggregator_ledger_records = self._validate_ledger_records(
                "AGGREGATORS.md",
                self.markdown["AGGREGATORS.md"],
                "A",
                AGGREGATOR_RECORD_FIELDS,
            )
        if "CONFERENCE_SOURCES.md" in self.markdown:
            self.source_ids = self._validate_ledger(
                "CONFERENCE_SOURCES.md", self.markdown["CONFERENCE_SOURCES.md"], "S"
            )
            self.source_ledger_records = self._validate_ledger_records(
                "CONFERENCE_SOURCES.md",
                self.markdown["CONFERENCE_SOURCES.md"],
                "S",
                SOURCE_RECORD_FIELDS,
            )
        self._validate_markdown_run_ids()
        if "QUALITY_REPORT.md" in self.markdown:
            self._validate_quality_report(self.markdown["QUALITY_REPORT.md"])
        if "RAW_CONFERENCES.json" in self.json_data:
            self._validate_raw(self.json_data["RAW_CONFERENCES.json"])
        if "NORMALIZED_CONFERENCES.json" in self.json_data:
            self._validate_normalized(self.json_data["NORMALIZED_CONFERENCES.json"])
        if (
            "RAW_CONFERENCES.json" in self.json_data
            and "NORMALIZED_CONFERENCES.json" in self.json_data
        ):
            self._validate_raw_normalized_invariants(
                self.json_data["RAW_CONFERENCES.json"],
                self.json_data["NORMALIZED_CONFERENCES.json"],
            )
        if (
            "ENTITY_RESOLUTION.md" in self.markdown
            and "NORMALIZED_CONFERENCES.json" in self.json_data
        ):
            self._validate_entity_resolution_ledger(
                self.markdown["ENTITY_RESOLUTION.md"],
                self.json_data["NORMALIZED_CONFERENCES.json"],
            )
        if (
            "QUALITY_REPORT.md" in self.markdown
            and "NORMALIZED_CONFERENCES.json" in self.json_data
        ):
            self._validate_quality_report_metrics(
                self.markdown["QUALITY_REPORT.md"],
                self.json_data["NORMALIZED_CONFERENCES.json"],
            )
        if (
            "REPORT.md" in self.markdown
            and "NORMALIZED_CONFERENCES.json" in self.json_data
        ):
            self._validate_report(
                self.markdown["REPORT.md"],
                self.json_data["NORMALIZED_CONFERENCES.json"],
            )
        if (
            self.request.mode == "refresh"
            and self.refresh_source_normalized is not None
            and "NORMALIZED_CONFERENCES.json" in self.json_data
        ):
            self._validate_refresh_difference_reporting(
                self.refresh_source_normalized,
                self.json_data["NORMALIZED_CONFERENCES.json"],
            )
        return self.errors

    def _validate_directory(self) -> None:
        if self.refresh_cycle:
            self.errors.append(
                f"{self.run_dir}: refresh source chain contains a cycle"
            )
        if not self.run_dir.exists():
            self.errors.append(f"{self.run_dir}: run directory does not exist")
        elif not self.run_dir.is_dir():
            self.errors.append(f"{self.run_dir}: run path is not a directory")

    def _load_required_artifacts(self) -> None:
        if not self.run_dir.is_dir():
            return
        for artifact in ARTIFACTS_BY_STAGE[self.stage]:
            path = self.run_dir / artifact
            if not path.exists():
                self.errors.append(f"{artifact}: required artifact is missing")
                continue
            if not path.is_file():
                self.errors.append(f"{artifact}: artifact path is not a file")
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                self.errors.append(f"{artifact}: cannot read UTF-8 artifact: {error}")
                continue
            if artifact.endswith(".json"):
                try:
                    self.json_data[artifact] = json.loads(text)
                except json.JSONDecodeError as error:
                    self.errors.append(
                        f"{artifact}#/{error.lineno}:{error.colno}: invalid JSON: {error.msg}"
                    )
            else:
                self.markdown[artifact] = text
                first_line = text.splitlines()[0] if text.splitlines() else ""
                if artifact not in first_line:
                    self.errors.append(
                        f"{artifact}#L1: first heading must identify {artifact}"
                    )

    def _validate_request(self, text: str) -> RequestInfo:
        artifact = "REQUEST.md"
        if (
            "[required:" in text.lower()
            or "[run id" in text.lower()
            or re.search(r"(?m)^-\s+\[\s\]", text)
        ):
            self.errors.append(f"{artifact}: unresolved template placeholder is present")
        values = {
            "project": markdown_field(text, "Project"),
            "mode": markdown_field(text, "Mode"),
            "run_id": markdown_field(text, "Run ID"),
            "source_run_id": markdown_field(text, "Refresh source run"),
            "recorded_at": markdown_field(text, "Request recorded at"),
            "attendee_mode": markdown_field(text, "Attendee mode"),
            "attendee_authorization": markdown_field(text, "Authorization basis"),
            "output_language": markdown_field(text, "Output language"),
            "objective": markdown_section(text, "Search Objective"),
        }
        required_scope_fields = {
            "Start date": markdown_field(text, "Start date"),
            "End date": markdown_field(text, "End date"),
            "Geography": markdown_field(text, "Geography"),
            "Topics or keywords": markdown_field(text, "Topics or keywords"),
            "Search languages": markdown_field(text, "Search languages"),
            "Result limit": markdown_field(text, "Result limit"),
            "Required source behavior": markdown_field(
                text, "Required source behavior"
            ),
            "Required source classes": markdown_field(
                text, "Required source classes"
            ),
            "Excluded source classes": markdown_field(
                text, "Excluded source classes"
            ),
            "Required domains or publishers": markdown_field(
                text, "Required domains or publishers"
            ),
            "Excluded domains or publishers": markdown_field(
                text, "Excluded domains or publishers"
            ),
            "Access limits": markdown_field(text, "Access limits"),
            "Authorized input description": markdown_field(
                text, "Authorized input description"
            ),
            "Personal-data minimization": markdown_field(
                text, "Personal-data minimization"
            ),
        }
        for key, value in values.items():
            if value is None:
                self.errors.append(
                    f"{artifact}: required request field {key.replace('_', ' ')!r} is missing"
                )
        for label, value in required_scope_fields.items():
            if value is None:
                self.errors.append(f"{artifact}: required field {label!r} is missing")
        for heading in (
            "Known Public Sources",
            "User Constraints",
            "Clarification History",
            "Completion Check",
        ):
            if markdown_section(text, heading) is None:
                self.errors.append(
                    f"{artifact}: required section {heading!r} is missing or empty"
                )
        if values["project"] != "Conference Discovery Harness":
            self.errors.append(
                f"{artifact}: Project must be exactly 'Conference Discovery Harness'"
            )
        run_id = values["run_id"]
        if run_id is not None and not RUN_ID_RE.fullmatch(run_id):
            self.errors.append(f"{artifact}: Run ID {run_id!r} is not filesystem-safe")
        if run_id is not None and self.run_dir.name != run_id:
            self.errors.append(
                f"{artifact}: Run ID {run_id!r} does not match directory "
                f"name {self.run_dir.name!r}"
            )
        mode = values["mode"]
        if mode not in {"full", "discovery_only", "refresh"}:
            self.errors.append(f"{artifact}: Mode {mode!r} is invalid")
        recorded_at = values["recorded_at"]
        if recorded_at is not None:
            try:
                parsed_recorded_at = datetime.fromisoformat(
                    recorded_at.replace("Z", "+00:00")
                )
                if parsed_recorded_at.tzinfo is None:
                    raise ValueError
            except ValueError:
                self.errors.append(
                    f"{artifact}: Request recorded at must be an ISO 8601 "
                    "date-time with timezone"
                )
        attendee_mode = values["attendee_mode"]
        if attendee_mode not in {"public-only", "user-authorized-input", "disabled"}:
            self.errors.append(f"{artifact}: Attendee mode {attendee_mode!r} is invalid")
        parsed_dates: dict[str, date | None] = {}
        for label in ("Start date", "End date"):
            value = required_scope_fields[label]
            if value is None:
                continue
            if value.lower() == "open-ended":
                parsed_dates[label] = None
                continue
            try:
                parsed_dates[label] = date.fromisoformat(value)
            except ValueError:
                self.errors.append(
                    f"{artifact}: {label} must be YYYY-MM-DD or 'open-ended'"
                )
        if (
            parsed_dates.get("Start date") is not None
            and parsed_dates.get("End date") is not None
            and parsed_dates["Start date"] > parsed_dates["End date"]
        ):
            self.errors.append(f"{artifact}: Start date must not be after End date")
        for label in (
            "Geography",
            "Topics or keywords",
            "Search languages",
            "Required source behavior",
            "Access limits",
            "Personal-data minimization",
        ):
            value = required_scope_fields[label]
            if value is not None and value.strip().lower() in REQUEST_NONE_VALUES:
                self.errors.append(f"{artifact}: required field {label!r} is empty")
        search_languages = required_scope_fields["Search languages"]
        if search_languages is not None:
            language_values = [
                item.strip() for item in search_languages.split(",") if item.strip()
            ]
            if not language_values or any(
                not LANGUAGE_RE.fullmatch(item) for item in language_values
            ):
                self.errors.append(
                    f"{artifact}: Search languages must be comma-separated "
                    "language codes"
                )
        output_language = values["output_language"]
        if output_language is not None and not LANGUAGE_RE.fullmatch(output_language):
            self.errors.append(
                f"{artifact}: Output language must be a language code"
            )
        result_limit = required_scope_fields["Result limit"]
        if (
            result_limit is not None
            and result_limit != "no-limit"
            and (not result_limit.isdigit() or int(result_limit) < 1)
        ):
            self.errors.append(
                f"{artifact}: Result limit must be a positive integer or 'no-limit'"
            )
        source_run_value = values["source_run_id"]
        source_run_id = (
            None
            if source_run_value is None
            or source_run_value.lower() in {"none", "not applicable", "n/a"}
            else source_run_value
        )
        if mode == "refresh":
            if source_run_id is None or not RUN_ID_RE.fullmatch(source_run_id):
                self.errors.append(
                    f"{artifact}: refresh mode requires a filesystem-safe source run ID"
                )
            if source_run_id == run_id:
                self.errors.append(
                    f"{artifact}: refresh source run must differ from the new run ID"
                )
        elif source_run_id is not None:
            self.errors.append(
                f"{artifact}: Refresh source run must be none outside refresh mode"
            )
        authorization = values["attendee_authorization"]
        expected_authorization = {
            "public-only": "intentionally-public",
            "user-authorized-input": "user-authorized-input",
            "disabled": "disabled",
        }.get(attendee_mode)
        if (
            authorization is not None
            and expected_authorization is not None
            and authorization != expected_authorization
        ):
            self.errors.append(
                f"{artifact}: attendee authorization {authorization!r} does not match "
                f"mode {attendee_mode!r}"
            )
        authorized_input = required_scope_fields["Authorized input description"]
        if (
            attendee_mode == "user-authorized-input"
            and authorized_input is not None
            and authorized_input.lower() in {"none", "n/a", "not applicable"}
        ):
            self.errors.append(
                f"{artifact}: user-authorized-input mode requires an authorized "
                "input description"
            )
        elif (
            attendee_mode in {"public-only", "disabled"}
            and authorized_input is not None
            and authorized_input.lower() not in REQUEST_NONE_VALUES
        ):
            self.errors.append(
                f"{artifact}: Authorized input description must be none unless "
                "attendee mode is user-authorized-input"
            )
        known_sources = markdown_section_raw(text, "Known Public Sources")
        if known_sources is not None:
            rows = markdown_table_rows(known_sources)
            if not rows:
                self.errors.append(
                    f"{artifact}: Known Public Sources must contain a completed row"
                )
            for row_index, row in enumerate(rows):
                if len(row) < 4:
                    self.errors.append(
                        f"{artifact}: Known Public Sources row {row_index + 1} "
                        "must contain four columns"
                    )
                    continue
                source_class, name, public_url, _ = row[:4]
                none_row = (
                    source_class.lower() in REQUEST_NONE_VALUES
                    and name.lower() in REQUEST_NONE_VALUES
                    and public_url.lower() in REQUEST_NONE_VALUES
                )
                if not none_row:
                    parsed_url = urlparse(public_url)
                    if (
                        not source_class
                        or not name
                        or parsed_url.scheme not in {"http", "https"}
                        or not parsed_url.netloc
                    ):
                        self.errors.append(
                            f"{artifact}: Known Public Sources row "
                            f"{row_index + 1} must contain a class, name, and public "
                            "HTTP(S) URL"
                        )
        constraints = markdown_section_raw(text, "User Constraints")
        if constraints is not None and not re.search(r"(?m)^-\s+\S", constraints):
            self.errors.append(
                f"{artifact}: User Constraints must contain at least one item or none"
            )
        completion = markdown_section_raw(text, "Completion Check")
        if completion is not None and not re.search(
            r"(?mi)^-\s+\[[xX]\]\s+\S", completion
        ):
            self.errors.append(
                f"{artifact}: Completion Check must contain completed checklist items"
            )
        clarification = markdown_section_raw(text, "Clarification History")
        if clarification is not None:
            rows = markdown_table_rows(clarification)
            if not rows:
                self.errors.append(
                    f"{artifact}: Clarification History must contain a completed row"
                )
            for row_index, row in enumerate(rows):
                if len(row) < 5:
                    self.errors.append(
                        f"{artifact}: Clarification History row {row_index + 1} "
                        "must contain five columns"
                    )
                    continue
                try:
                    clarified_at = datetime.fromisoformat(
                        row[0].replace("Z", "+00:00")
                    )
                    if clarified_at.tzinfo is None:
                        raise ValueError
                except ValueError:
                    self.errors.append(
                        f"{artifact}: Clarification History row {row_index + 1} "
                        "must start with an ISO 8601 date-time with timezone"
                    )
                if any(not cell.strip() for cell in row[1:5]):
                    self.errors.append(
                        f"{artifact}: Clarification History row {row_index + 1} "
                        "contains an empty required value"
                    )
        scope_values = {
            "objective": values["objective"],
            "start_date": required_scope_fields["Start date"],
            "end_date": required_scope_fields["End date"],
            "geography": required_scope_fields["Geography"],
            "topics_or_keywords": required_scope_fields["Topics or keywords"],
            "search_languages": required_scope_fields["Search languages"],
            "output_language": values["output_language"],
            "result_limit": required_scope_fields["Result limit"],
            "required_source_behavior": required_scope_fields[
                "Required source behavior"
            ],
            "required_source_classes": required_scope_fields[
                "Required source classes"
            ],
            "excluded_source_classes": required_scope_fields[
                "Excluded source classes"
            ],
            "required_domains_or_publishers": required_scope_fields[
                "Required domains or publishers"
            ],
            "excluded_domains_or_publishers": required_scope_fields[
                "Excluded domains or publishers"
            ],
            "access_limits": required_scope_fields["Access limits"],
            "attendee_mode": attendee_mode,
            "authorization_basis": authorization,
            "personal_data_minimization": required_scope_fields[
                "Personal-data minimization"
            ],
            "user_constraints": markdown_section(text, "User Constraints"),
        }
        scope_signature = tuple(
            (key, str(value).strip())
            for key, value in sorted(scope_values.items())
            if value is not None
        )
        if mode == "refresh" and source_run_id is not None:
            self._validate_refresh_source_run(source_run_id, scope_signature)
        return RequestInfo(
            run_id=run_id,
            mode=mode,
            source_run_id=source_run_id,
            objective=values["objective"],
            attendee_mode=attendee_mode,
            attendee_authorization=authorization,
            output_language=values["output_language"],
            scope_signature=scope_signature,
        )

    def _validate_refresh_source_run(
        self,
        source_run_id: str,
        scope_signature: tuple[tuple[str, str], ...],
    ) -> None:
        artifact = "REQUEST.md"
        source_run = self.run_dir.parent / source_run_id
        if not source_run.is_dir():
            self.errors.append(
                f"{artifact}: refresh source run directory {source_run!s} does not exist"
            )
            return
        missing_artifacts = []
        for required_artifact in ARTIFACTS_BY_STAGE["complete"]:
            if not (source_run / required_artifact).is_file():
                missing_artifacts.append(required_artifact)
                self.errors.append(
                    f"{artifact}: refresh source run {source_run_id!r} is missing "
                    f"{required_artifact}"
                )
        if missing_artifacts:
            return
        source_validator = RunValidator(
            source_run,
            "complete",
            visited_run_dirs=self.visited_run_dirs,
        )
        source_errors = source_validator.validate()
        if source_errors:
            for error in source_errors:
                self.errors.append(
                    f"{artifact}: refresh source run {source_run_id!r} is invalid: "
                    f"{error}"
                )
            return
        source_normalized = source_validator.json_data.get(
            "NORMALIZED_CONFERENCES.json"
        )
        if isinstance(source_normalized, dict):
            self.refresh_source_normalized = source_normalized
        if source_validator.request.scope_signature != scope_signature:
            current_scope = dict(scope_signature)
            earlier_scope = dict(source_validator.request.scope_signature)
            changed_fields = sorted(
                key
                for key in set(current_scope) | set(earlier_scope)
                if current_scope.get(key) != earlier_scope.get(key)
            )
            self.errors.append(
                f"{artifact}: refresh request scope differs from source run "
                f"{source_run_id!r} in: {', '.join(changed_fields)}"
            )

    def _validate_ledger(self, artifact: str, text: str, prefix: str) -> set[str]:
        heading_pattern = re.compile(
            rf"(?m)^###\s+(?:`|\[)?({prefix}[0-9]{{3,}})(?:`|\])?(?:\s|$)"
        )
        field_label = "Stable aggregator ID" if prefix == "A" else "Stable source ID"
        field_pattern = re.compile(
            rf"(?mi)^-\s+{re.escape(field_label)}:\s*`?({prefix}[0-9]{{3,}})`?\s*$"
        )
        heading_ids = heading_pattern.findall(text)
        stable_ids = field_pattern.findall(text)
        for identifier, count in Counter(heading_ids).items():
            if count > 1:
                self.errors.append(
                    f"{artifact}: duplicate {prefix} ledger heading {identifier}"
                )
        for identifier, count in Counter(stable_ids).items():
            if count > 1:
                self.errors.append(
                    f"{artifact}: duplicate stable ID field {identifier}"
                )
        if set(heading_ids) != set(stable_ids):
            missing_fields = sorted(set(heading_ids) - set(stable_ids))
            missing_headings = sorted(set(stable_ids) - set(heading_ids))
            if missing_fields:
                self.errors.append(
                    f"{artifact}: headings lack matching stable ID fields: "
                    f"{', '.join(missing_fields)}"
                )
            if missing_headings:
                self.errors.append(
                    f"{artifact}: stable IDs lack matching headings: "
                    f"{', '.join(missing_headings)}"
                )
        malformed = re.findall(
            rf"(?m)^###\s+(?:`|\[)?({prefix}[0-9]+)(?:`|\])?(?:\s|$)", text
        )
        for identifier in malformed:
            if not re.fullmatch(rf"{prefix}[0-9]{{3,}}", identifier):
                self.errors.append(
                    f"{artifact}: ledger ID {identifier!r} has an invalid format"
                )
        return set(heading_ids)

    def _validate_ledger_records(
        self,
        artifact: str,
        text: str,
        prefix: str,
        required_fields: tuple[str, ...],
    ) -> dict[str, dict[str, str]]:
        required_sections = (
            (
                "Run",
                "Coverage Summary",
                "Aggregator Record",
                "Failed Aggregator Leads",
                "Freeze Record",
            )
            if prefix == "A"
            else (
                "Run",
                "Conference Source Record",
                "Failed and Ineligible Leads",
                "Conference-to-Source Coverage",
                "Freeze Record",
            )
        )
        for heading in required_sections:
            if markdown_section(text, heading) is None:
                self.errors.append(
                    f"{artifact}: required section {heading!r} is missing or empty"
                )
        records: dict[str, dict[str, str]] = {}
        pattern = re.compile(
            rf"(?ms)^###\s+({prefix}[0-9]{{3,}})(?:\s+[^\n]*)?\n"
            rf"(.*?)(?=^###\s+{prefix}[0-9]{{3,}}(?:\s|$)|^##\s+|\Z)"
        )
        for match in pattern.finditer(text):
            identifier = match.group(1)
            block = match.group(2)
            record: dict[str, str] = {}
            for label in required_fields:
                value = markdown_field(block, label)
                if value is None:
                    self.errors.append(
                        f"{artifact}: {identifier} is missing required field {label!r}"
                    )
                elif "[" in value or "]" in value:
                    self.errors.append(
                        f"{artifact}: {identifier} field {label!r} contains a placeholder"
                    )
                else:
                    record[label] = value
            stable_label = (
                "Stable aggregator ID" if prefix == "A" else "Stable source ID"
            )
            if record.get(stable_label) != identifier:
                self.errors.append(
                    f"{artifact}: {identifier} stable ID field does not match its heading"
                )
            for label in (
                ("Canonical public URL", "Reviewed listing page")
                if prefix == "A"
                else ("Public URL",)
            ):
                value = record.get(label)
                if value is not None:
                    parsed = urlparse(value)
                    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                        self.errors.append(
                            f"{artifact}: {identifier} field {label!r} must be a "
                            "public HTTP(S) URL"
                        )
            access_date = record.get("Access date")
            if access_date is not None:
                try:
                    date.fromisoformat(access_date)
                except ValueError:
                    self.errors.append(
                        f"{artifact}: {identifier} Access date must be YYYY-MM-DD"
                    )
            if prefix == "A":
                if record.get("Reviewability") not in {
                    "reviewed",
                    "partially-reviewed",
                    "inaccessible",
                    "unresolved",
                }:
                    self.errors.append(
                        f"{artifact}: {identifier} Reviewability is invalid"
                    )
                for subsection in (
                    "Matching Listings",
                    "Duplicate or Syndication Links",
                ):
                    if not re.search(
                        rf"(?m)^####\s+{re.escape(subsection)}\s*$", block
                    ):
                        self.errors.append(
                            f"{artifact}: {identifier} is missing subsection "
                            f"{subsection!r}"
                        )
            else:
                if record.get("Review state") not in {
                    "reviewed",
                    "partially-reviewed",
                    "inaccessible",
                    "removed",
                    "paywalled",
                    "unresolved",
                }:
                    self.errors.append(
                        f"{artifact}: {identifier} Review state is invalid"
                    )
                if record.get("Extraction eligibility") not in {
                    "eligible",
                    "limited",
                    "ineligible",
                }:
                    self.errors.append(
                        f"{artifact}: {identifier} Extraction eligibility is invalid"
                    )
                claims = {
                    claim.strip()
                    for claim in record.get(
                        "Supported fields or claims", ""
                    ).split(",")
                    if claim.strip()
                }
                invalid_claims = claims - DIRECT_SOURCE_CLAIMS
                if not claims or invalid_claims:
                    self.errors.append(
                        f"{artifact}: {identifier} Supported fields or claims must "
                        "use controlled direct-source tokens"
                    )
                review_state = record.get("Review state")
                eligibility = record.get("Extraction eligibility")
                if eligibility == "eligible" and review_state != "reviewed":
                    self.errors.append(
                        f"{artifact}: {identifier} eligible sources must be reviewed"
                    )
                if eligibility == "limited" and review_state not in {
                    "reviewed",
                    "partially-reviewed",
                }:
                    self.errors.append(
                        f"{artifact}: {identifier} limited sources must be reviewed "
                        "or partially reviewed"
                    )
            records[identifier] = record
        return records

    def _validate_markdown_run_ids(self) -> None:
        for artifact, text in self.markdown.items():
            if artifact == "REQUEST.md":
                continue
            run_id = markdown_field(text, "Run ID")
            if run_id is None:
                self.errors.append(f"{artifact}: Run ID field is missing")
            elif self.request.run_id is not None and run_id != self.request.run_id:
                self.errors.append(
                    f"{artifact}: Run ID {run_id!r} does not match "
                    f"REQUEST.md {self.request.run_id!r}"
                )

    def _validate_quality_report(self, text: str) -> None:
        artifact = "QUALITY_REPORT.md"
        for heading in QUALITY_REPORT_SECTIONS:
            if markdown_section(text, heading) is None:
                self.errors.append(
                    f"{artifact}: required section {heading!r} is missing or empty"
                )
        for heading in QUALITY_REPORT_SUBSECTIONS:
            if markdown_subsection(text, heading) is None:
                self.errors.append(
                    f"{artifact}: required subsection {heading!r} is missing or empty"
                )
        if (
            self.request.mode == "refresh"
            and markdown_section(text, "Refresh Differences") is None
        ):
            self.errors.append(
                f"{artifact}: refresh mode requires a nonempty 'Refresh Differences' "
                "section"
            )

    def _validate_quality_report_metrics(
        self, text: str, normalized: dict[str, Any]
    ) -> None:
        artifact = "QUALITY_REPORT.md"
        quality = normalized.get("quality_metrics")
        if not isinstance(quality, dict):
            return
        entity_section = markdown_section_raw(text, "Entity Counts")
        recorded_entity_counts: dict[str, int] = {}
        if entity_section is not None:
            for row in markdown_table_rows(entity_section):
                if len(row) < 2:
                    continue
                label, count = row[:2]
                if count.isdigit():
                    recorded_entity_counts[label] = int(count)
        expected_entity_counts = quality.get("entity_counts", {})
        if isinstance(expected_entity_counts, dict):
            for label, collection in QUALITY_ENTITY_LABELS.items():
                expected = expected_entity_counts.get(collection)
                if recorded_entity_counts.get(label) != expected:
                    self.errors.append(
                        f"{artifact}: Entity Counts row {label!r} records "
                        f"{recorded_entity_counts.get(label)!r}, expected {expected!r}"
                    )
        artifact_section = markdown_section_raw(
            text, "Artifact and Schema Results"
        )
        recorded_artifact_results: dict[str, str] = {}
        if artifact_section is not None:
            header, rows = markdown_table(artifact_section)
            if "Artifact" in header and "Result" in header:
                artifact_index = header.index("Artifact")
                result_index = header.index("Result")
                for row in rows:
                    if len(row) > max(artifact_index, result_index):
                        recorded_artifact_results[row[artifact_index]] = row[
                            result_index
                        ]
        for artifact_name in (
            "RAW_CONFERENCES.json",
            "NORMALIZED_CONFERENCES.json",
        ):
            if recorded_artifact_results.get(artifact_name) != "pass":
                self.errors.append(
                    f"{artifact}: Artifact and Schema Results must contain a "
                    f"passing row for {artifact_name}"
                )
        branch_section = markdown_section_raw(text, "Branch Coverage")
        if branch_section is not None:
            header, rows = markdown_table(branch_section)
            recorded_rows = {
                row[0]: row
                for row in rows
                if row
            }
            branch_coverage = quality.get("branch_coverage", {})
            for label, branch in BRANCH_DISPLAY_LABELS.items():
                row = recorded_rows.get(label)
                if row is None:
                    self.errors.append(
                        f"{artifact}: Branch Coverage is missing row {label!r}"
                    )
                    continue
                for status_label, status in QUALITY_STATUS_LABELS.items():
                    if status_label not in header:
                        self.errors.append(
                            f"{artifact}: Branch Coverage is missing column "
                            f"{status_label!r}"
                        )
                        continue
                    column = header.index(status_label)
                    recorded = (
                        int(row[column])
                        if len(row) > column and row[column].isdigit()
                        else None
                    )
                    expected = (
                        branch_coverage.get(branch, {}).get(status)
                        if isinstance(branch_coverage, dict)
                        and isinstance(branch_coverage.get(branch), dict)
                        else None
                    )
                    if recorded != expected:
                        self.errors.append(
                            f"{artifact}: Branch Coverage row {label!r} column "
                            f"{status_label!r} records {recorded!r}, expected "
                            f"{expected!r}"
                        )
        source_coverage_section = markdown_section_raw(
            text, "Source-Class Coverage"
        )
        if source_coverage_section is not None:
            header, rows = markdown_table(source_coverage_section)
            required_columns = (
                "Source class",
                "Reviewed count",
                "Eligible count",
                "Conferences covered",
                "Limitations",
            )
            if any(column not in header for column in required_columns):
                self.errors.append(
                    f"{artifact}: Source-Class Coverage is missing required columns"
                )
            else:
                indexes = {
                    column: header.index(column) for column in required_columns
                }
                recorded_coverage = {
                    row[indexes["Source class"]]: row
                    for row in rows
                    if len(row) > max(indexes.values())
                }
                expected_coverage = {
                    record.get("source_class"): record
                    for record in quality.get("source_class_coverage", [])
                    if isinstance(record, dict)
                }
                if set(recorded_coverage) != set(expected_coverage):
                    self.errors.append(
                        f"{artifact}: Source-Class Coverage rows do not match "
                        "JSON quality metrics"
                    )
                for source_class, expected in expected_coverage.items():
                    row = recorded_coverage.get(source_class)
                    if row is None:
                        continue
                    for column, field in (
                        ("Reviewed count", "reviewed_count"),
                        ("Eligible count", "eligible_count"),
                    ):
                        recorded = row[indexes[column]]
                        if not recorded.isdigit() or int(recorded) != expected.get(
                            field
                        ):
                            self.errors.append(
                                f"{artifact}: Source-Class Coverage row "
                                f"{source_class!r} column {column!r} does not match "
                                "JSON quality metrics"
                            )
                    recorded_conferences = {
                        item.strip()
                        for item in row[indexes["Conferences covered"]].split(",")
                        if item.strip() and item.strip().casefold() != "none"
                    }
                    if recorded_conferences != set(
                        expected.get("conference_ids", [])
                    ):
                        self.errors.append(
                            f"{artifact}: Source-Class Coverage row "
                            f"{source_class!r} conference IDs do not match JSON"
                        )
                    recorded_limitations = {
                        item.strip()
                        for item in row[indexes["Limitations"]].split(";")
                        if item.strip()
                    }
                    if recorded_limitations != set(
                        expected.get("limitations", [])
                    ):
                        self.errors.append(
                            f"{artifact}: Source-Class Coverage row "
                            f"{source_class!r} limitations do not match JSON"
                        )
        gaps_section = markdown_section_raw(
            text, "Inaccessible Sources and Collection Gaps"
        )
        if gaps_section is not None:
            header, rows = markdown_table(gaps_section)
            required_columns = (
                "JSON Pointer or source ID",
                "Source IDs",
                "Gap or access failure",
                "Status",
                "Reporting effect",
            )
            if any(column not in header for column in required_columns):
                self.errors.append(
                    f"{artifact}: Inaccessible Sources and Collection Gaps is "
                    "missing required columns"
                )
            else:
                indexes = {
                    column: header.index(column) for column in required_columns
                }
                recorded_gaps = {
                    row[indexes["JSON Pointer or source ID"]]: row
                    for row in rows
                    if len(row) > max(indexes.values())
                }
                for gap in quality.get("collection_gaps", []):
                    if not isinstance(gap, dict):
                        continue
                    pointer = gap.get("json_pointer")
                    row = recorded_gaps.get(pointer)
                    if row is None:
                        self.errors.append(
                            f"{artifact}: collection gap {pointer!r} is missing "
                            "from the Markdown quality report"
                        )
                        continue
                    if row[indexes["Status"]] != gap.get("condition"):
                        self.errors.append(
                            f"{artifact}: collection gap {pointer!r} status does "
                            "not match JSON"
                        )
                    if row[indexes["Gap or access failure"]] != gap.get("reason"):
                        self.errors.append(
                            f"{artifact}: collection gap {pointer!r} description "
                            "does not match JSON"
                        )
                    if "insufficient evidence" not in row[
                        indexes["Reporting effect"]
                    ].casefold():
                        self.errors.append(
                            f"{artifact}: collection gap {pointer!r} reporting "
                            "effect must require Insufficient evidence"
                        )
                    recorded_sources = {
                        item.strip()
                        for item in row[indexes["Source IDs"]].split(",")
                        if item.strip() and item.strip().casefold() != "none"
                    }
                    if recorded_sources != set(gap.get("source_ids", [])):
                        self.errors.append(
                            f"{artifact}: collection gap {pointer!r} source IDs "
                            "do not match JSON"
                        )
        privacy_section = markdown_section_raw(
            text, "Attendee Privacy and Authorization"
        ) or ""
        quality_checks = list(quality.get("attendee_privacy_checks", [])) + list(
            quality.get("attendee_authorization_checks", [])
        )
        expected_privacy_bullets = {
            "Attendee mode matches `REQUEST.md`: pass."
        }
        for check in quality_checks:
            if not isinstance(check, dict):
                continue
            check_text = str(check.get("check", "")).strip().rstrip(".")
            expected_privacy_bullets.add(
                f"{check_text}: {check.get('result')}."
            )
        actual_privacy_bullets = {
            match.group(1).strip()
            for match in re.finditer(r"(?m)^-\s+(.+?)\s*$", privacy_section)
        }
        for bullet in sorted(expected_privacy_bullets - actual_privacy_bullets):
            self.errors.append(
                f"{artifact}: Attendee Privacy and Authorization is missing "
                f"required result {bullet!r}"
            )
        for bullet in sorted(actual_privacy_bullets - expected_privacy_bullets):
            self.errors.append(
                f"{artifact}: Attendee Privacy and Authorization contains "
                f"unrecognized or contradictory result {bullet!r}"
            )
        for heading in (
            "Artifact and Schema Results",
            "Attendee Privacy and Authorization",
        ):
            section = markdown_section(text, heading) or ""
            if re.search(
                r"(?i)(?:\|\s*|:\s*)(?:fail|not-run)(?:\s*\||\b)",
                section,
            ):
                self.errors.append(
                    f"{artifact}: section {heading!r} contains a failed or "
                    "not-run check"
                )
        blocking_section = markdown_section(text, "Blocking Warnings") or ""
        normalized_blocking_section = re.sub(
            r"[-*.\s`]", "", blocking_section
        ).casefold()
        if not quality.get("blocking_warnings") and normalized_blocking_section != "none":
            self.errors.append(
                f"{artifact}: Blocking Warnings must state only 'None' when JSON "
                "blocking_warnings is empty"
            )

        def recorded_integer(label: str) -> int | None:
            value = markdown_field(text, label)
            if value is None:
                self.errors.append(
                    f"{artifact}: required quality summary field {label!r} is missing"
                )
                return None
            cleaned = value.rstrip(".").strip()
            if not cleaned.isdigit():
                self.errors.append(
                    f"{artifact}: quality summary field {label!r} must be an integer"
                )
                return None
            return int(cleaned)

        expected_integers = {
            "Duplicate candidates": quality.get("duplicate_candidates"),
            "Applied decisions": quality.get("resolution_outcomes", {}).get("applied")
            if isinstance(quality.get("resolution_outcomes"), dict)
            else None,
            "Rejected decisions": quality.get("resolution_outcomes", {}).get("rejected")
            if isinstance(quality.get("resolution_outcomes"), dict)
            else None,
            "Unresolved decisions": quality.get("resolution_outcomes", {}).get(
                "unresolved"
            )
            if isinstance(quality.get("resolution_outcomes"), dict)
            else None,
        }
        translation_coverage = quality.get("translation_coverage")
        if isinstance(translation_coverage, dict):
            expected_integers.update(
                {
                    "Translatable fields": translation_coverage.get(
                        "translatable_fields"
                    ),
                    "Translation records": translation_coverage.get(
                        "translated_fields"
                    ),
                    "LLM-generated translations": translation_coverage.get(
                        "llm_generated"
                    ),
                    "Official-source translations": translation_coverage.get(
                        "official_source"
                    ),
                    "Human-reviewed translations": translation_coverage.get(
                        "human_reviewed"
                    ),
                    "Uncertain translations": translation_coverage.get("uncertain"),
                }
            )
        for label, expected in expected_integers.items():
            recorded = recorded_integer(label)
            if recorded is not None and expected is not None and recorded != expected:
                self.errors.append(
                    f"{artifact}: quality summary field {label!r} records "
                    f"{recorded}, expected {expected}"
                )

        section_expectations = (
            (
                "Non-Blocking Warnings",
                quality.get("non_blocking_warnings", []),
            ),
            (
                "Inaccessible Sources and Collection Gaps",
                quality.get("inaccessible_sources", []),
            ),
            (
                "Conferences Without Official Sources",
                quality.get("conferences_without_official_sources", []),
            ),
            (
                "Translation Quality",
                quality.get("translation_uncertainties", []),
            ),
        )
        for heading, expected_values in section_expectations:
            section = markdown_section(text, heading) or ""
            normalized_section = section.casefold()
            for value in expected_values if isinstance(expected_values, list) else []:
                token = str(value).strip().rstrip(".").casefold()
                if token and token not in normalized_section:
                    self.errors.append(
                        f"{artifact}: section {heading!r} does not report "
                        f"quality value {value!r}"
                    )

        def require_none_or_values(
            heading: str,
            expected_values: Any,
            *,
            subsection: bool = False,
        ) -> None:
            section = (
                markdown_subsection(text, heading)
                if subsection
                else markdown_section(text, heading)
            ) or ""
            values = expected_values if isinstance(expected_values, list) else []
            normalized = re.sub(r"[-*.\s`]", "", section).casefold()
            if not values:
                if normalized != "none":
                    self.errors.append(
                        f"{artifact}: section {heading!r} must state only 'None' "
                        "when the JSON quality list is empty"
                    )
                return
            if normalized == "none":
                self.errors.append(
                    f"{artifact}: section {heading!r} cannot state 'None' when "
                    "the JSON quality list is populated"
                )
            normalized_section = section.casefold()
            for value in values:
                if isinstance(value, dict):
                    tokens = [
                        str(child).strip()
                        for child in value.values()
                        if isinstance(child, (str, int, float))
                    ]
                else:
                    tokens = [str(value).strip()]
                if tokens and not any(
                    token.casefold() in normalized_section for token in tokens
                ):
                    self.errors.append(
                        f"{artifact}: section {heading!r} does not reconcile "
                        f"JSON quality value {value!r}"
                    )

        require_none_or_values(
            "Unresolved Foreign Keys",
            quality.get("unresolved_foreign_keys", []),
            subsection=True,
        )
        require_none_or_values(
            "Unresolved Source References",
            quality.get("unresolved_source_references", []),
            subsection=True,
        )
        require_none_or_values(
            "Conferences Without Official Sources",
            quality.get("conferences_without_official_sources", []),
        )
        require_none_or_values("Conflicts", quality.get("conflicts", []))

    def _validate_schema(self, artifact: str, schema_name: str, data: Any) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / schema_name
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            self.errors.append(f"{artifact}: cannot load schema {schema_name}: {error}")
            return
        self.errors.extend(SchemaValidator(schema, artifact).validate(data))

    def _validate_metadata(self, artifact: str, metadata: Any) -> None:
        if not isinstance(metadata, dict):
            return
        comparisons = {
            "run_id": self.request.run_id,
            "mode": self.request.mode,
            "source_run_id": self.request.source_run_id,
            "objective": self.request.objective,
            "attendee_mode": self.request.attendee_mode,
            "output_language": self.request.output_language,
        }
        for key, expected in comparisons.items():
            if expected is not None and metadata.get(key) != expected:
                self.errors.append(
                    f"{artifact}#/run_metadata/{key}: value {metadata.get(key)!r} "
                    f"does not match REQUEST.md {expected!r}"
                )

    def _validate_raw(self, data: Any) -> None:
        artifact = "RAW_CONFERENCES.json"
        self._validate_schema(artifact, "raw-conference-data.schema.json", data)
        if not isinstance(data, dict):
            return
        if data.get("artifact") != artifact:
            self.errors.append(
                f"{artifact}#/artifact: artifact name must be exactly {artifact!r}"
            )
        self._validate_metadata(artifact, data.get("run_metadata"))
        sources = data.get("sources", [])
        conferences = data.get("conferences", [])
        raw_source_ids = self._validate_declared_ids(
            artifact, "sources", sources, r"S[0-9]{3,}"
        )
        raw_conference_ids = self._validate_declared_ids(
            artifact, "conferences", conferences, r"C[0-9]{3,}"
        )
        self.eligible_direct_source_ids = self._eligible_direct_sources(sources)
        self._validate_source_ledger_consistency(artifact, sources)
        for index, source in enumerate(sources if isinstance(sources, list) else []):
            if not isinstance(source, dict):
                continue
            source_id = source.get("id")
            if source.get("source_kind") != "direct":
                self.errors.append(
                    f"{artifact}#/sources/{index}/source_kind: raw extraction sources "
                    "must be direct sources"
                )
            if isinstance(source_id, str) and source_id not in self.source_ids:
                self.errors.append(
                    f"{artifact}#/sources/{index}/id: {source_id} is absent from "
                    "CONFERENCE_SOURCES.md"
                )
            candidate = source.get("candidate_conference_id")
            if candidate is not None and candidate not in raw_conference_ids:
                self.errors.append(
                    f"{artifact}#/sources/{index}/candidate_conference_id: "
                    f"unresolved conference reference {candidate!r}"
                )
        self._validate_source_references(
            artifact, data, raw_source_ids, allow_aggregators=False
        )
        for index, conference in enumerate(
            conferences if isinstance(conferences, list) else []
        ):
            if not isinstance(conference, dict):
                continue
            branches = conference.get("branches")
            self._validate_branches(
                artifact, f"/conferences/{index}/branches", branches
            )
        self._validate_raw_claim_support(data)
        self._validate_raw_attendee_rules(data)
        self._validate_raw_contact_evidence(data)

    def _validate_raw_contact_evidence(self, data: dict[str, Any]) -> None:
        artifact = "RAW_CONFERENCES.json"
        contact_key = re.compile(
            r"(?i)(?:^|_)(?:business_)?(?:e?mail|telephone|phone|contact)(?:_|$)"
        )
        contact_claim = re.compile(
            r"(?i)\b(?:e-?mail(?:\s+address)?|telephone|phone(?:\s+number)?|"
            r"business\s+contact|contact\s+(?:details?|information|address))\b"
        )
        sources_with_contact_evidence: set[str] = set()

        def walk_observed(
            observed: Any,
            raw_text: str,
            path: str,
            source_id: Any,
            field_name: str | None = None,
        ) -> None:
            if isinstance(observed, dict):
                for key, child in observed.items():
                    child_path = pointer_child(path, key)
                    if contact_key.search(key) and isinstance(child, str):
                        sources_with_contact_evidence.add(str(source_id))
                        if child.casefold() not in raw_text.casefold():
                            self.errors.append(
                                f"{artifact}{display_path(child_path)}: contact "
                                f"value {child!r} is absent from raw_text"
                            )
                    walk_observed(
                        child, raw_text, child_path, source_id, key
                    )
            elif isinstance(observed, list):
                for index, child in enumerate(observed):
                    walk_observed(
                        child,
                        raw_text,
                        pointer_child(path, index),
                        source_id,
                        field_name,
                    )
            elif field_name not in {
                None,
                "record_type",
                "capture_method",
            } and self._has_material_value(observed):
                raw_text_folded = raw_text.casefold()
                supported = False
                if isinstance(observed, (int, float)) and not isinstance(
                    observed, bool
                ):
                    supported = bool(
                        re.search(
                            rf"(?<![0-9]){re.escape(str(observed))}(?![0-9])",
                            raw_text,
                        )
                    )
                elif isinstance(observed, str):
                    observed_folded = re.sub(
                        r"\s+", " ", observed
                    ).strip().casefold()
                    supported = observed_folded in re.sub(
                        r"\s+", " ", raw_text_folded
                    )
                    if (
                        not supported
                        and field_name.endswith("_date")
                        and re.fullmatch(
                            r"[0-9]{4}-[0-9]{2}-[0-9]{2}", observed
                        )
                    ):
                        parsed = date.fromisoformat(observed)
                        month_names = (
                            "january",
                            "february",
                            "march",
                            "april",
                            "may",
                            "june",
                            "july",
                            "august",
                            "september",
                            "october",
                            "november",
                            "december",
                        )
                        month = month_names[parsed.month - 1]
                        supported = (
                            str(parsed.year) in raw_text_folded
                            and bool(
                                re.search(
                                    rf"(?<![0-9])0?{parsed.day}(?![0-9])",
                                    raw_text_folded,
                                )
                            )
                            and (
                                month in raw_text_folded
                                or month[:3] in raw_text_folded
                                or bool(
                                    re.search(
                                        rf"(?<![0-9])0?{parsed.month}(?![0-9])",
                                        raw_text_folded,
                                    )
                                )
                            )
                        )
                if not supported:
                    self.errors.append(
                        f"{artifact}{display_path(path)}: observed value "
                        f"{observed!r} is absent from raw_text"
                    )

        for conference_index, conference in enumerate(data.get("conferences", [])):
            if not isinstance(conference, dict):
                continue
            for branch_name, branch in conference.get("branches", {}).items():
                if not isinstance(branch, dict):
                    continue
                for value_index, raw_value in enumerate(branch.get("raw_values", [])):
                    if not isinstance(raw_value, dict):
                        continue
                    raw_text = str(raw_value.get("raw_text", ""))
                    source_id = raw_value.get("source_id")
                    if contact_claim.search(raw_text):
                        sources_with_contact_evidence.add(str(source_id))
                    walk_observed(
                        raw_value.get("observed_value"),
                        raw_text,
                        f"/conferences/{conference_index}/branches/{branch_name}/"
                        f"raw_values/{value_index}/observed_value",
                        source_id,
                    )
        summary_claim_patterns = {
            "identity": r"\bidentity\b",
            "series": r"\b(?:series|acronym)\b",
            "organizers": r"\borganizers?\b",
            "description": r"\b(?:description|themes?|topics?|format|languages?)\b",
            "dates": r"\b(?:dates?|times?|timezone|recurrence|status)\b",
            "official-url": r"\b(?:official\s+(?:site|url|website)|event\s+url)\b",
            "people": r"\b(?:people|person|professional|speakers?|committee)\b",
            "schedule": r"\b(?:schedule|sessions?|workshops?)\b",
            "registration": r"\b(?:registration|tickets?|prices?)\b",
            "venue": r"\b(?:venue|located\s+at)\b",
            "sponsors": r"\b(?:sponsors?|exhibitors?|partners?)\b",
            "hotels": r"\b(?:hotels?|accommodation|booking)\b",
            "attendance": r"\b(?:attendance|attendees?|aggregate\s+count)\b",
        }
        for source_index, source in enumerate(data.get("sources", [])):
            if not isinstance(source, dict):
                continue
            source_id = source.get("id")
            summary = str(
                source.get("bounded_excerpt_or_faithful_summary", "")
            )
            if (
                contact_claim.search(summary)
                and source_id not in sources_with_contact_evidence
            ):
                self.errors.append(
                    f"{artifact}#/sources/{source_index}/"
                    "bounded_excerpt_or_faithful_summary: summary claims public "
                    "contact data without extracted contact evidence"
                )
            source_claims = set(source.get("supported_fields_or_claims", []))
            for claim, pattern in summary_claim_patterns.items():
                if re.search(pattern, summary, re.IGNORECASE) and claim not in source_claims:
                    self.errors.append(
                        f"{artifact}#/sources/{source_index}/"
                        "bounded_excerpt_or_faithful_summary: summary contains "
                        f"{claim!r} content without that supported-claim token"
                    )

    def _validate_normalized(self, data: Any) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        self._validate_schema(artifact, "conference-dataset.schema.json", data)
        if not isinstance(data, dict):
            return
        if data.get("artifact") != artifact:
            self.errors.append(
                f"{artifact}#/artifact: artifact name must be exactly {artifact!r}"
            )
        self._validate_metadata(artifact, data.get("run_metadata"))
        ids_by_collection: dict[str, set[str]] = {}
        all_ids: dict[str, str] = {}
        for collection, pattern in COLLECTION_PREFIXES.items():
            ids = self._validate_declared_ids(
                artifact, collection, data.get(collection, []), pattern
            )
            ids_by_collection[collection] = ids
            for identifier in ids:
                previous = all_ids.get(identifier)
                if previous is not None:
                    self.errors.append(
                        f"{artifact}#/{collection}: ID {identifier} is also declared "
                        f"in {previous}"
                    )
                else:
                    all_ids[identifier] = collection
        normalized_source_ids = ids_by_collection.get("sources", set())
        normalized_sources = data.get("sources", [])
        self.normalized_source_records = {
            source.get("id"): source
            for source in normalized_sources
            if isinstance(source, dict) and isinstance(source.get("id"), str)
        }
        self.eligible_direct_source_ids = self._eligible_direct_sources(
            normalized_sources
        )
        self._validate_source_ledger_consistency(
            artifact,
            [
                source
                for source in normalized_sources
                if isinstance(source, dict)
                and source.get("source_kind") == "direct"
            ],
        )
        self._validate_aggregator_ledger_consistency(
            artifact,
            [
                source
                for source in normalized_sources
                if isinstance(source, dict)
                and source.get("source_kind") == "aggregator"
            ],
        )
        expected_ledger_sources = self.aggregator_ids | self.source_ids
        if normalized_source_ids != expected_ledger_sources:
            missing = sorted(expected_ledger_sources - normalized_source_ids)
            extra = sorted(normalized_source_ids - expected_ledger_sources)
            if missing:
                self.errors.append(
                    f"{artifact}#/sources: reviewed ledger IDs missing from normalized "
                    f"sources: {', '.join(missing)}"
                )
            if extra:
                self.errors.append(
                    f"{artifact}#/sources: source IDs absent from Markdown ledgers: "
                    f"{', '.join(extra)}"
                )
        self._validate_normalized_source_records(data, ids_by_collection)
        self._validate_source_references(
            artifact, data, normalized_source_ids, allow_aggregators=True
        )
        self._validate_aggregator_evidence_scope(data)
        self._validate_foreign_keys(data, ids_by_collection)
        self._validate_normalized_statuses(data)
        self._validate_conference_relationship_alignment(data)
        self._validate_normalized_claim_support(data)
        self._validate_normalized_attendee_rules(data)
        self._validate_quality_metrics(data, ids_by_collection)
        self._validate_alias_redirects(data, ids_by_collection)

    def _validate_declared_ids(
        self,
        artifact: str,
        collection: str,
        records: Any,
        pattern: str,
    ) -> set[str]:
        identifiers: list[str] = []
        if not isinstance(records, list):
            return set()
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            identifier = record.get("id")
            if not isinstance(identifier, str) or not re.fullmatch(pattern, identifier):
                self.errors.append(
                    f"{artifact}#/{collection}/{index}/id: ID {identifier!r} "
                    f"must match ^{pattern}$"
                )
                continue
            identifiers.append(identifier)
        for identifier, count in Counter(identifiers).items():
            if count > 1:
                self.errors.append(
                    f"{artifact}#/{collection}: duplicate ID {identifier}"
                )
        return set(identifiers)

    def _validate_branches(self, artifact: str, path: str, branches: Any) -> None:
        if not isinstance(branches, dict):
            return
        actual = set(branches)
        expected = set(BRANCH_NAMES)
        for missing in sorted(expected - actual):
            self.errors.append(
                f"{artifact}#{pointer_child(path, missing)}: required branch is missing"
            )
        for extra in sorted(actual - expected):
            self.errors.append(
                f"{artifact}#{pointer_child(path, extra)}: unexpected branch"
            )
        for branch_name, branch in branches.items():
            if not isinstance(branch, dict):
                continue
            status = branch.get("collection_status")
            if status not in ALLOWED_STATUSES:
                self.errors.append(
                    f"{artifact}#{path}/{branch_name}/collection_status: "
                    f"invalid collection status {status!r}"
                )
            raw_values = branch.get("raw_values")
            if status in {"complete", "partial"} and raw_values == []:
                self.errors.append(
                    f"{artifact}#{path}/{branch_name}/raw_values: status {status!r} "
                    "requires at least one raw value"
                )

    @staticmethod
    def _eligible_direct_sources(sources: Any) -> set[str]:
        if not isinstance(sources, list):
            return set()
        return {
            source.get("id")
            for source in sources
            if isinstance(source, dict)
            and source.get("source_kind") == "direct"
            and source.get("review_state") == "reviewed"
            and source.get("extraction_eligibility") in {"eligible", "limited"}
            and bool(source.get("supported_fields_or_claims"))
            and isinstance(source.get("id"), str)
        }

    def _validate_source_ledger_consistency(
        self, artifact: str, sources: Any
    ) -> None:
        if not isinstance(sources, list):
            return
        comparisons = {
            "Source class": "source_class",
            "Title": "title",
            "Publisher or owner": "publisher_or_owner",
            "Public URL": "public_url",
            "Publication or update date": "publication_or_update_date",
            "Access date": "access_date",
            "Conference relationship": "conference_relationship",
            "Review state": "review_state",
            "Bounded excerpt or faithful summary": (
                "bounded_excerpt_or_faithful_summary"
            ),
            "Extraction eligibility": "extraction_eligibility",
        }
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                continue
            source_id = source.get("id")
            if not isinstance(source_id, str):
                continue
            ledger = self.source_ledger_records.get(source_id)
            if ledger is None:
                continue
            for ledger_label, json_field in comparisons.items():
                ledger_value = ledger.get(ledger_label)
                json_value = source.get(json_field)
                comparable_ledger_value: Any = ledger_value
                if (
                    json_field == "publication_or_update_date"
                    and ledger_value is not None
                    and ledger_value.casefold()
                    in {"none", "not published", "unresolved"}
                ):
                    comparable_ledger_value = None
                if (
                    ledger_value is not None
                    and json_value != comparable_ledger_value
                ):
                    self.errors.append(
                        f"{artifact}#/sources/{index}/{json_field}: value "
                        f"{json_value!r} does not match CONFERENCE_SOURCES.md "
                        f"{ledger_value!r}"
                    )
            if "candidate_conference_id" in source:
                ledger_candidate = ledger.get("Candidate conference ID")
                if source.get("candidate_conference_id") != ledger_candidate:
                    self.errors.append(
                        f"{artifact}#/sources/{index}/candidate_conference_id: value "
                        f"{source.get('candidate_conference_id')!r} does not match "
                        f"CONFERENCE_SOURCES.md {ledger_candidate!r}"
                    )
            claims = source.get("supported_fields_or_claims")
            ledger_claims = {
                claim.strip()
                for claim in ledger.get("Supported fields or claims", "").split(",")
                if claim.strip()
            }
            if isinstance(claims, list):
                if set(claims) != ledger_claims:
                    self.errors.append(
                        f"{artifact}#/sources/{index}/supported_fields_or_claims: "
                        "values do not exactly match CONFERENCE_SOURCES.md"
                    )
            for ledger_label, json_field in (
                ("Reliability", "reliability"),
                ("Independence", "independence"),
            ):
                ledger_value = ledger.get(ledger_label)
                if (
                    ledger_value is not None
                    and ledger_value.split(";", 1)[0].strip() != source.get(json_field)
                ):
                    self.errors.append(
                        f"{artifact}#/sources/{index}/{json_field}: value "
                        f"{source.get(json_field)!r} does not match "
                        f"CONFERENCE_SOURCES.md {ledger_value!r}"
                    )
            ledger_limitations = {
                limitation.strip()
                for limitation in ledger.get("Limitations", "").split(";")
                if limitation.strip()
            }
            if set(source.get("limitations", [])) != ledger_limitations:
                self.errors.append(
                    f"{artifact}#/sources/{index}/limitations: values do not "
                    "exactly match CONFERENCE_SOURCES.md"
                )

    def _validate_aggregator_ledger_consistency(
        self, artifact: str, sources: Any
    ) -> None:
        if not isinstance(sources, list):
            return
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                continue
            source_id = source.get("id")
            if not isinstance(source_id, str):
                continue
            ledger = self.aggregator_ledger_records.get(source_id)
            if ledger is None:
                continue
            comparisons = {
                "Provider name": "publisher_or_owner",
                "Reviewed listing page": "public_url",
                "Access date": "access_date",
                "Reviewability": "review_state",
            }
            for ledger_label, json_field in comparisons.items():
                ledger_value = ledger.get(ledger_label)
                if ledger_value is not None and source.get(json_field) != ledger_value:
                    self.errors.append(
                        f"{artifact}#/sources/{index}/{json_field}: value "
                        f"{source.get(json_field)!r} does not match AGGREGATORS.md "
                        f"{ledger_value!r}"
                    )
            reliability = ledger.get("Reliability")
            if (
                reliability is not None
                and reliability.split(";", 1)[0].strip()
                != source.get("reliability")
            ):
                self.errors.append(
                    f"{artifact}#/sources/{index}/reliability: value "
                    f"{source.get('reliability')!r} does not match AGGREGATORS.md "
                    f"{reliability!r}"
                )
            if source.get("supported_fields_or_claims") != ["observed-listing"]:
                self.errors.append(
                    f"{artifact}#/sources/{index}/supported_fields_or_claims: "
                    "aggregator sources must support only 'observed-listing'"
                )
            ledger_limitations = {
                limitation.strip()
                for limitation in ledger.get("Limitations", "").split(";")
                if limitation.strip()
            }
            if set(source.get("limitations", [])) != ledger_limitations:
                self.errors.append(
                    f"{artifact}#/sources/{index}/limitations: values do not "
                    "exactly match AGGREGATORS.md"
                )

    def _validate_raw_claim_support(self, data: dict[str, Any]) -> None:
        artifact = "RAW_CONFERENCES.json"
        claims_by_source = {
            source.get("id"): set(source.get("supported_fields_or_claims", []))
            for source in data.get("sources", [])
            if isinstance(source, dict)
        }
        for conference_index, conference in enumerate(data.get("conferences", [])):
            if not isinstance(conference, dict):
                continue
            branches = conference.get("branches", {})
            if not isinstance(branches, dict):
                continue
            for branch, branch_data in branches.items():
                if not isinstance(branch_data, dict):
                    continue
                required_claim = SOURCE_CLAIM_BY_BRANCH.get(branch)
                if required_claim is None:
                    continue
                for value_index, raw_value in enumerate(
                    branch_data.get("raw_values", [])
                ):
                    if not isinstance(raw_value, dict):
                        continue
                    source_id = raw_value.get("source_id")
                    if required_claim not in claims_by_source.get(source_id, set()):
                        self.errors.append(
                            f"{artifact}#/conferences/{conference_index}/branches/"
                            f"{branch}/raw_values/{value_index}/source_id: source "
                            f"{source_id!r} does not declare support for claim "
                            f"{required_claim!r}"
                        )
        branch_by_claim = {
            claim: branch for branch, claim in SOURCE_CLAIM_BY_BRANCH.items()
        }
        conferences_by_id = {
            conference.get("id"): conference
            for conference in data.get("conferences", [])
            if isinstance(conference, dict)
        }
        for source_index, source in enumerate(data.get("sources", [])):
            if not isinstance(source, dict):
                continue
            source_id = source.get("id")
            conference = conferences_by_id.get(
                source.get("candidate_conference_id")
            )
            if not isinstance(source_id, str) or not isinstance(conference, dict):
                continue
            branches = conference.get("branches", {})
            for claim in source.get("supported_fields_or_claims", []):
                branch_name = branch_by_claim.get(claim)
                branch = (
                    branches.get(branch_name)
                    if isinstance(branches, dict) and branch_name is not None
                    else None
                )
                supports_claim = (
                    isinstance(branch, dict)
                    and branch.get("collection_status") in {"complete", "partial"}
                    and any(
                        isinstance(raw_value, dict)
                        and raw_value.get("source_id") == source_id
                        for raw_value in branch.get("raw_values", [])
                    )
                )
                if branch_name is not None and not supports_claim:
                    self.errors.append(
                        f"{artifact}#/sources/{source_index}/"
                        "supported_fields_or_claims: source "
                        f"{source_id!r} declares claim {claim!r}, but branch "
                        f"{branch_name!r} has no retained evidence from that source"
                    )

    def _validate_normalized_claim_support(self, data: dict[str, Any]) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        claims_by_source = {
            source.get("id"): set(source.get("supported_fields_or_claims", []))
            for source in data.get("sources", [])
            if isinstance(source, dict)
        }

        def validate_entry(
            collection: str,
            record_index: int,
            field_pointer: str,
            entry: Any,
            allowed_claims: set[str],
        ) -> None:
            if not isinstance(entry, dict):
                return
            for source_index, source_id in enumerate(entry.get("source_ids", [])):
                if not isinstance(source_id, str):
                    continue
                if source_id.startswith("A"):
                    continue
                source_claims = claims_by_source.get(source_id, set())
                if source_claims.isdisjoint(allowed_claims):
                    self.errors.append(
                        f"{artifact}#/{collection}/{record_index}/field_provenance/"
                        f"{field_pointer.replace('/', '~1')}/source_ids/"
                        f"{source_index}: source {source_id!r} does not declare "
                        f"support for any of {sorted(allowed_claims)!r}"
                    )

        for record_index, conference in enumerate(data.get("conferences", [])):
            if not isinstance(conference, dict):
                continue
            for field_pointer, entry in conference.get(
                "field_provenance", {}
            ).items():
                tokens = field_pointer.lstrip("/").split("/")
                branch = CONFERENCE_FIELD_BRANCH.get(tokens[0]) if tokens else None
                required_claim = SOURCE_CLAIM_BY_BRANCH.get(branch)
                if required_claim is not None:
                    validate_entry(
                        "conferences",
                        record_index,
                        field_pointer,
                        entry,
                        {required_claim},
                    )

        collection_claims = {
            "conference_series": {"series"},
            "organizations": {
                "organizers",
                "people",
                "venue",
                "sponsors",
                "hotels",
            },
            "people": {"people", "committees"},
            "venues": {"venue"},
            "sessions_and_events": {"schedule"},
            "registration_offers": {"registration"},
            "sponsors_and_partnerships": {"sponsors"},
            "hotels": {"hotels"},
            "attendee_records_or_aggregates": {"attendance"},
        }
        for collection, allowed_claims in collection_claims.items():
            for record_index, record in enumerate(data.get(collection, [])):
                if not isinstance(record, dict):
                    continue
                for field_pointer, entry in record.get(
                    "field_provenance", {}
                ).items():
                    validate_entry(
                        collection,
                        record_index,
                        field_pointer,
                        entry,
                        allowed_claims,
                    )

    def _validate_source_references(
        self,
        artifact: str,
        value: Any,
        available_source_ids: set[str],
        allow_aggregators: bool,
        path: str = "",
    ) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = pointer_child(path, key)
                if key == "source_id" and isinstance(child, str):
                    self._check_source_reference(
                        artifact,
                        child_path,
                        child,
                        available_source_ids,
                        allow_aggregators,
                    )
                elif key in {
                    "source_ids",
                    "verification_source_ids",
                    "listing_source_ids",
                } and isinstance(child, list):
                    for index, source_id in enumerate(child):
                        if isinstance(source_id, str):
                            self._check_source_reference(
                                artifact,
                                pointer_child(child_path, index),
                                source_id,
                                available_source_ids,
                                allow_aggregators,
                            )
                self._validate_source_references(
                    artifact,
                    child,
                    available_source_ids,
                    allow_aggregators,
                    child_path,
                )
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._validate_source_references(
                    artifact,
                    child,
                    available_source_ids,
                    allow_aggregators,
                    pointer_child(path, index),
                )

    def _check_source_reference(
        self,
        artifact: str,
        path: str,
        source_id: str,
        available_source_ids: set[str],
        allow_aggregators: bool,
    ) -> None:
        if not SOURCE_ID_RE.fullmatch(source_id):
            self.errors.append(
                f"{artifact}{display_path(path)}: invalid source ID {source_id!r}"
            )
        elif source_id not in available_source_ids:
            self.errors.append(
                f"{artifact}{display_path(path)}: unresolved source reference "
                f"{source_id!r}"
            )
        elif source_id.startswith("A") and not allow_aggregators:
            self.errors.append(
                f"{artifact}{display_path(path)}: aggregator IDs cannot support raw "
                "conference facts"
            )
        elif (
            source_id.startswith("S")
            and source_id not in self.eligible_direct_source_ids
        ):
            self.errors.append(
                f"{artifact}{display_path(path)}: direct source {source_id} is not "
                "reviewed and eligible for factual use"
            )

    def _validate_normalized_source_records(
        self, data: dict[str, Any], ids_by_collection: dict[str, set[str]]
    ) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        for index, source in enumerate(data.get("sources", [])):
            if not isinstance(source, dict):
                continue
            source_id = source.get("id")
            source_kind = source.get("source_kind")
            if isinstance(source_id, str) and source_id.startswith("A"):
                if source_kind != "aggregator":
                    self.errors.append(
                        f"{artifact}#/sources/{index}/source_kind: A IDs must identify "
                        "aggregator sources"
                    )
                if not source.get("observed_listing_only"):
                    self.errors.append(
                        f"{artifact}#/sources/{index}/observed_listing_only: "
                        "aggregator sources must be listing-only"
                    )
            elif isinstance(source_id, str) and source_id.startswith("S"):
                if source_kind != "direct":
                    self.errors.append(
                        f"{artifact}#/sources/{index}/source_kind: S IDs must identify "
                        "direct sources"
                    )
                if "observed-listing" in source.get(
                    "supported_fields_or_claims", []
                ):
                    self.errors.append(
                        f"{artifact}#/sources/{index}/supported_fields_or_claims: "
                        "direct sources cannot use the aggregator-only "
                        "'observed-listing' claim"
                    )
            for ref_index, related in enumerate(source.get("related_entities", [])):
                if not isinstance(related, dict):
                    continue
                entity_type = related.get("entity_type")
                entity_id = related.get("entity_id")
                collection = ENTITY_TYPE_COLLECTIONS.get(entity_type)
                if collection is None:
                    continue
                if entity_id not in ids_by_collection.get(collection, set()):
                    self.errors.append(
                        f"{artifact}#/sources/{index}/related_entities/{ref_index}/"
                        f"entity_id: unresolved {entity_type} reference {entity_id!r}"
                    )

    def _validate_aggregator_evidence_scope(self, data: dict[str, Any]) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        material_collections = (
            "conferences",
            "conference_series",
            "organizations",
            "people",
            "venues",
            "sessions_and_events",
            "registration_offers",
            "sponsors_and_partnerships",
            "hotels",
            "attendee_records_or_aggregates",
            "translations",
        )

        def walk(value: Any, path: str) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    child_path = pointer_child(path, key)
                    if key == "listing_source_ids":
                        continue
                    if key == "field_provenance" and isinstance(child, dict):
                        for field_pointer, entry in child.items():
                            if not isinstance(entry, dict):
                                continue
                            for source_index, source_id in enumerate(
                                entry.get("source_ids", [])
                            ):
                                if (
                                    isinstance(source_id, str)
                                    and source_id.startswith("A")
                                    and "listing" not in field_pointer
                                ):
                                    self.errors.append(
                                        f"{artifact}{display_path(pointer_child(pointer_child(child_path, field_pointer), 'source_ids'))}"
                                        f"/{source_index}: aggregator source {source_id} "
                                        "can support only an observed-listing field"
                                    )
                        continue
                    if key in {"source_id", "source_ids", "verification_source_ids"}:
                        source_values = child if isinstance(child, list) else [child]
                        for source_index, source_id in enumerate(source_values):
                            if isinstance(source_id, str) and source_id.startswith("A"):
                                suffix = (
                                    pointer_child(child_path, source_index)
                                    if isinstance(child, list)
                                    else child_path
                                )
                                self.errors.append(
                                    f"{artifact}{display_path(suffix)}: aggregator "
                                    f"source {source_id} can support only observed-listing "
                                    "claims"
                                )
                    walk(child, child_path)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, pointer_child(path, index))

        for collection in material_collections:
            walk(data.get(collection, []), f"/{collection}")

    def _check_ref(
        self,
        artifact: str,
        path: str,
        identifier: Any,
        available: set[str],
    ) -> None:
        if identifier is None:
            return
        if identifier not in available:
            self.errors.append(
                f"{artifact}{display_path(path)}: unresolved foreign key {identifier!r}"
            )

    def _check_ref_list(
        self,
        artifact: str,
        path: str,
        identifiers: Any,
        available: set[str],
    ) -> None:
        if not isinstance(identifiers, list):
            return
        for index, identifier in enumerate(identifiers):
            self._check_ref(
                artifact, pointer_child(path, index), identifier, available
            )

    def _validate_foreign_keys(
        self, data: dict[str, Any], ids: dict[str, set[str]]
    ) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        conferences = ids["conferences"]
        series = ids["conference_series"]
        organizations = ids["organizations"]
        people = ids["people"]
        venues = ids["venues"]
        events = ids["sessions_and_events"]
        registrations = ids["registration_offers"]
        partnerships = ids["sponsors_and_partnerships"]
        hotels = ids["hotels"]
        attendees = ids["attendee_records_or_aggregates"]
        translations = ids["translations"]
        decisions = ids["entity_resolution_decisions"]
        all_ids = set().union(*ids.values())

        for index, conference in enumerate(data.get("conferences", [])):
            if not isinstance(conference, dict):
                continue
            base = f"/conferences/{index}"
            self._check_ref(artifact, f"{base}/series_id", conference.get("series_id"), series)
            self._check_ref_list(artifact, f"{base}/organizer_ids", conference.get("organizer_ids"), organizations)
            self._check_ref_list(artifact, f"{base}/person_ids", conference.get("person_ids"), people)
            self._check_ref_list(artifact, f"{base}/session_event_ids", conference.get("session_event_ids"), events)
            self._check_ref_list(artifact, f"{base}/registration_offer_ids", conference.get("registration_offer_ids"), registrations)
            self._check_ref_list(artifact, f"{base}/venue_ids", conference.get("venue_ids"), venues)
            self._check_ref_list(artifact, f"{base}/partnership_ids", conference.get("partnership_ids"), partnerships)
            self._check_ref_list(artifact, f"{base}/hotel_ids", conference.get("hotel_ids"), hotels)
            self._check_ref_list(artifact, f"{base}/attendee_record_ids", conference.get("attendee_record_ids"), attendees)
            self._check_ref_list(artifact, f"{base}/translation_ids", conference.get("translation_ids"), translations)
            self._check_ref_list(artifact, f"{base}/entity_resolution_decision_ids", conference.get("entity_resolution_decision_ids"), decisions)
            for membership_index, membership in enumerate(conference.get("committee_memberships", [])):
                if not isinstance(membership, dict):
                    continue
                membership_path = f"{base}/committee_memberships/{membership_index}"
                self._check_ref(artifact, f"{membership_path}/person_id", membership.get("person_id"), people)
                self._check_ref(artifact, f"{membership_path}/organization_id", membership.get("organization_id"), organizations)

        for index, record in enumerate(data.get("conference_series", [])):
            if isinstance(record, dict):
                self._check_ref_list(artifact, f"/conference_series/{index}/organizer_ids", record.get("organizer_ids"), organizations)
                self._check_ref_list(artifact, f"/conference_series/{index}/conference_ids", record.get("conference_ids"), conferences)
        for index, record in enumerate(data.get("people", [])):
            if not isinstance(record, dict):
                continue
            self._check_ref_list(artifact, f"/people/{index}/organization_ids", record.get("organization_ids"), organizations)
            for role_index, role in enumerate(record.get("conference_roles", [])):
                if isinstance(role, dict):
                    self._check_ref(artifact, f"/people/{index}/conference_roles/{role_index}/conference_id", role.get("conference_id"), conferences)
        for index, record in enumerate(data.get("venues", [])):
            if not isinstance(record, dict):
                continue
            for relation_index, relation in enumerate(record.get("conference_relationships", [])):
                if isinstance(relation, dict):
                    self._check_ref(artifact, f"/venues/{index}/conference_relationships/{relation_index}/conference_id", relation.get("conference_id"), conferences)
        for index, record in enumerate(data.get("sessions_and_events", [])):
            if not isinstance(record, dict):
                continue
            base = f"/sessions_and_events/{index}"
            self._check_ref(artifact, f"{base}/conference_id", record.get("conference_id"), conferences)
            self._check_ref(artifact, f"{base}/parent_event_id", record.get("parent_event_id"), events)
            self._check_ref_list(artifact, f"{base}/speaker_ids", record.get("speaker_ids"), people)
            self._check_ref_list(artifact, f"{base}/organizer_ids", record.get("organizer_ids"), organizations)
            self._check_ref(artifact, f"{base}/venue_id", record.get("venue_id"), venues)
        for collection in ("registration_offers", "sponsors_and_partnerships", "hotels", "attendee_records_or_aggregates"):
            for index, record in enumerate(data.get(collection, [])):
                if not isinstance(record, dict):
                    continue
                base = f"/{collection}/{index}"
                self._check_ref(artifact, f"{base}/conference_id", record.get("conference_id"), conferences)
                self._check_ref(artifact, f"{base}/organization_id", record.get("organization_id"), organizations)
                self._check_ref(artifact, f"{base}/venue_id", record.get("venue_id"), venues)
                self._check_ref(artifact, f"{base}/person_id", record.get("person_id"), people)
        for index, translation in enumerate(data.get("translations", [])):
            if isinstance(translation, dict):
                self._check_ref(artifact, f"/translations/{index}/entity_id", translation.get("entity_id"), all_ids)
        for index, decision in enumerate(data.get("entity_resolution_decisions", [])):
            if not isinstance(decision, dict):
                continue
            self._check_ref(artifact, f"/entity_resolution_decisions/{index}/canonical_entity_id", decision.get("canonical_entity_id"), all_ids)
            self._check_ref_list(artifact, f"/entity_resolution_decisions/{index}/created_entity_ids", decision.get("created_entity_ids"), all_ids)
        quality = data.get("quality_metrics", {})
        if isinstance(quality, dict):
            self._check_ref_list(artifact, "/quality_metrics/conferences_without_official_sources", quality.get("conferences_without_official_sources"), conferences)
            self._check_ref_list(artifact, "/quality_metrics/translation_uncertainties", quality.get("translation_uncertainties"), translations)
            self._check_ref_list(artifact, "/quality_metrics/inaccessible_sources", quality.get("inaccessible_sources"), ids["sources"])
            for index, coverage in enumerate(quality.get("source_class_coverage", [])):
                if isinstance(coverage, dict):
                    self._check_ref_list(artifact, f"/quality_metrics/source_class_coverage/{index}/conference_ids", coverage.get("conference_ids"), conferences)

    def _validate_normalized_statuses(self, data: dict[str, Any]) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        for index, conference in enumerate(data.get("conferences", [])):
            if not isinstance(conference, dict):
                continue
            statuses = conference.get("collection_statuses")
            if not isinstance(statuses, dict):
                continue
            if set(statuses) != set(BRANCH_NAMES):
                for missing in sorted(set(BRANCH_NAMES) - set(statuses)):
                    self.errors.append(
                        f"{artifact}#/conferences/{index}/collection_statuses/{missing}: "
                        "required branch status is missing"
                    )
            for branch, status in statuses.items():
                if status not in ALLOWED_STATUSES:
                    self.errors.append(
                        f"{artifact}#/conferences/{index}/collection_statuses/{branch}: "
                        f"invalid collection status {status!r}"
                    )
        self._walk_collection_statuses(artifact, data)

    def _validate_conference_relationship_alignment(
        self, data: dict[str, Any]
    ) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        conferences = {
            conference.get("id"): conference
            for conference in data.get("conferences", [])
            if isinstance(conference, dict)
            and isinstance(conference.get("id"), str)
        }

        def check_relation(
            collection: str,
            record_index: int,
            record_id: Any,
            conference_id: Any,
            branch: str,
            conference_reference_field: str,
        ) -> None:
            conference = conferences.get(conference_id)
            if conference is None:
                return
            status = conference.get("collection_statuses", {}).get(branch)
            if status not in {"complete", "partial"}:
                self.errors.append(
                    f"{artifact}#/{collection}/{record_index}: record {record_id!r} "
                    f"relates to conference {conference_id!r}, but branch {branch!r} "
                    f"has status {status!r}"
                )
            references = conference.get(conference_reference_field)
            if isinstance(references, list) and record_id not in references:
                self.errors.append(
                    f"{artifact}#/{collection}/{record_index}/id: record "
                    f"{record_id!r} is not listed in conference "
                    f"{conference_id!r} field {conference_reference_field!r}"
                )

        direct_relations = (
            (
                "sessions_and_events",
                "schedule_tracks_sessions_workshops_and_social_events",
                "session_event_ids",
            ),
            ("registration_offers", "registration", "registration_offer_ids"),
            (
                "sponsors_and_partnerships",
                "sponsors_exhibitors_and_partners",
                "partnership_ids",
            ),
            ("hotels", "hotels_and_booking", "hotel_ids"),
            (
                "attendee_records_or_aggregates",
                "attendees_and_attendance",
                "attendee_record_ids",
            ),
        )
        for collection, branch, reference_field in direct_relations:
            for record_index, record in enumerate(data.get(collection, [])):
                if not isinstance(record, dict):
                    continue
                check_relation(
                    collection,
                    record_index,
                    record.get("id"),
                    record.get("conference_id"),
                    branch,
                    reference_field,
                )

        for record_index, venue in enumerate(data.get("venues", [])):
            if not isinstance(venue, dict):
                continue
            for relationship in venue.get("conference_relationships", []):
                if isinstance(relationship, dict):
                    check_relation(
                        "venues",
                        record_index,
                        venue.get("id"),
                        relationship.get("conference_id"),
                        "venue",
                        "venue_ids",
                    )

        for record_index, person in enumerate(data.get("people", [])):
            if not isinstance(person, dict):
                continue
            for relationship in person.get("conference_roles", []):
                if isinstance(relationship, dict):
                    check_relation(
                        "people",
                        record_index,
                        person.get("id"),
                        relationship.get("conference_id"),
                        "people_and_public_contacts",
                        "person_ids",
                    )

        for record_index, series in enumerate(data.get("conference_series", [])):
            if not isinstance(series, dict):
                continue
            for conference_id in series.get("conference_ids", []):
                conference = conferences.get(conference_id)
                if conference is None:
                    continue
                status = conference.get("collection_statuses", {}).get(
                    "series_edition_and_acronym"
                )
                if status not in {"complete", "partial"}:
                    self.errors.append(
                        f"{artifact}#/conference_series/{record_index}: series "
                        f"{series.get('id')!r} relates to conference "
                        f"{conference_id!r}, but the series branch has status "
                        f"{status!r}"
                    )
                if conference.get("series_id") != series.get("id"):
                    self.errors.append(
                        f"{artifact}#/conference_series/{record_index}/conference_ids: "
                        f"conference {conference_id!r} does not reference series "
                        f"{series.get('id')!r}"
                    )

    def _walk_collection_statuses(
        self, artifact: str, value: Any, path: str = ""
    ) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = pointer_child(path, key)
                if key == "collection_status" and child not in ALLOWED_STATUSES:
                    self.errors.append(
                        f"{artifact}{display_path(child_path)}: invalid collection "
                        f"status {child!r}"
                    )
                self._walk_collection_statuses(artifact, child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._walk_collection_statuses(
                    artifact, child, pointer_child(path, index)
                )

    def _authorization_bases(
        self, value: Any, path: str = ""
    ) -> Iterable[tuple[str, dict[str, Any]]]:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = pointer_child(path, key)
                if key == "authorization_basis" and isinstance(child, dict):
                    yield child_path, child
                yield from self._authorization_bases(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from self._authorization_bases(
                    child, pointer_child(path, index)
                )

    def _validate_raw_attendee_rules(self, data: dict[str, Any]) -> None:
        artifact = "RAW_CONFERENCES.json"
        mode = self.request.attendee_mode
        for conference_index, conference in enumerate(data.get("conferences", [])):
            if not isinstance(conference, dict):
                continue
            branch = conference.get("branches", {}).get("attendees_and_attendance")
            if not isinstance(branch, dict):
                continue
            path = f"/conferences/{conference_index}/branches/attendees_and_attendance"
            values = branch.get("raw_values", [])
            if mode == "disabled":
                if values:
                    self.errors.append(
                        f"{artifact}#{path}/raw_values: attendee mode disabled "
                        "requires an empty attendee branch"
                    )
                if branch.get("collection_status") not in {
                    "not-authorized",
                    "not-applicable",
                }:
                    self.errors.append(
                        f"{artifact}#{path}/collection_status: attendee mode disabled "
                        "requires not-authorized or not-applicable"
                    )
            for value_index, raw_value in enumerate(
                values if isinstance(values, list) else []
            ):
                if not isinstance(raw_value, dict):
                    continue
                authorization = raw_value.get("authorization_basis")
                basis = authorization.get("basis") if isinstance(authorization, dict) else None
                observed_value = raw_value.get("observed_value")
                record_type = (
                    observed_value.get("record_type")
                    if isinstance(observed_value, dict)
                    else None
                )
                if basis is None:
                    self.errors.append(
                        f"{artifact}#{path}/raw_values/{value_index}/authorization_basis: "
                        "attendee evidence requires an authorization basis"
                    )
                elif mode == "public-only" and basis != "intentionally-public":
                    self.errors.append(
                        f"{artifact}#{path}/raw_values/{value_index}/authorization_basis/"
                        "basis: public-only mode requires intentionally-public evidence"
                    )
                elif mode == "user-authorized-input" and basis not in {
                    "intentionally-public",
                    "user-authorized-input",
                }:
                    self.errors.append(
                        f"{artifact}#{path}/raw_values/{value_index}/authorization_basis/"
                        "basis: authorization is incompatible with attendee mode"
                    )
                if record_type not in {
                    "individual-record",
                    "aggregate",
                    "attendance-estimate",
                    "intended-audience",
                }:
                    self.errors.append(
                        f"{artifact}#{path}/raw_values/{value_index}/observed_value/"
                        "record_type: attendee evidence requires a recognized record type"
                    )
                elif mode == "public-only" and record_type == "individual-record":
                    self.errors.append(
                        f"{artifact}#{path}/raw_values/{value_index}/observed_value/"
                        "record_type: public-only mode cannot contain individual "
                        "attendee records"
                    )
                elif (
                    record_type == "individual-record"
                    and basis != "user-authorized-input"
                ):
                    self.errors.append(
                        f"{artifact}#{path}/raw_values/{value_index}/authorization_basis/"
                        "basis: individual attendee records require user-authorized-input"
                    )
        self._validate_authorization_records(artifact, data)

    def _validate_normalized_attendee_rules(self, data: dict[str, Any]) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        mode = self.request.attendee_mode
        attendee_records = data.get("attendee_records_or_aggregates", [])
        if mode == "disabled" and attendee_records:
            self.errors.append(
                f"{artifact}#/attendee_records_or_aggregates: attendee mode disabled "
                "requires an empty collection"
            )
        for index, record in enumerate(
            attendee_records if isinstance(attendee_records, list) else []
        ):
            if not isinstance(record, dict):
                continue
            basis = (
                record.get("authorization_basis", {}).get("basis")
                if isinstance(record.get("authorization_basis"), dict)
                else None
            )
            record_type = record.get("record_type")
            if mode == "public-only":
                if basis != "intentionally-public":
                    self.errors.append(
                        f"{artifact}#/attendee_records_or_aggregates/{index}/"
                        "authorization_basis/basis: public-only mode requires "
                        "intentionally-public evidence"
                    )
                if record_type == "individual-record":
                    self.errors.append(
                        f"{artifact}#/attendee_records_or_aggregates/{index}/"
                        "record_type: public-only mode cannot contain individual "
                        "attendee records"
                    )
            elif mode == "user-authorized-input":
                if basis not in {"intentionally-public", "user-authorized-input"}:
                    self.errors.append(
                        f"{artifact}#/attendee_records_or_aggregates/{index}/"
                        "authorization_basis/basis: incompatible authorization basis"
                    )
                if record_type == "individual-record" and basis != "user-authorized-input":
                    self.errors.append(
                        f"{artifact}#/attendee_records_or_aggregates/{index}/"
                        "authorization_basis/basis: individual attendee records require "
                        "user-authorized-input"
                    )
        for conference_index, conference in enumerate(data.get("conferences", [])):
            if (
                mode == "disabled"
                and isinstance(conference, dict)
                and conference.get("attendee_record_ids")
            ):
                self.errors.append(
                    f"{artifact}#/conferences/{conference_index}/attendee_record_ids: "
                    "attendee mode disabled requires no attendee references"
                )
        self._validate_authorization_records(artifact, data)

    def _validate_authorization_records(
        self, artifact: str, data: dict[str, Any]
    ) -> None:
        mode = self.request.attendee_mode
        for path, authorization in self._authorization_bases(data):
            basis = authorization.get("basis")
            if basis in {"not-authorized", "unresolved"}:
                self.errors.append(
                    f"{artifact}{display_path(pointer_child(path, 'basis'))}: "
                    "a retained value cannot use an unclear or denied authorization basis"
                )
            if basis == "user-authorized-input":
                if mode != "user-authorized-input":
                    self.errors.append(
                        f"{artifact}{display_path(pointer_child(path, 'basis'))}: "
                        "user-authorized data is not allowed by REQUEST.md"
                    )
                record = authorization.get("authorization_record")
                if not isinstance(record, str) or not record.strip():
                    self.errors.append(
                        f"{artifact}{display_path(pointer_child(path, 'authorization_record'))}: "
                        "user-authorized data requires a nonempty authorization record"
                    )
            if basis == "intentionally-public" and not authorization.get("source_ids"):
                self.errors.append(
                    f"{artifact}{display_path(pointer_child(path, 'source_ids'))}: "
                    "intentionally-public data requires source provenance"
                )
            if basis == "intentionally-public":
                description = str(authorization.get("description", "")).casefold()
                if re.search(
                    r"\b(?:guess(?:ed|ing)?|infer(?:red|ence)?|"
                    r"deriv(?:ed|ation)|never\s+publish(?:ed|es|ing)?|"
                    r"social\s+activity|does\s+not\s+display|"
                    r"calculat(?:ed|ion)|photographs?|photos?|"
                    r"not\s+(?:intentionally\s+)?public(?:ly|ished)?|"
                    r"private|nonpublic)\b",
                    description,
                ):
                    self.errors.append(
                        f"{artifact}{display_path(pointer_child(path, 'description'))}: "
                        "intentionally-public authorization cannot be guessed, "
                        "private, nonpublic, or explicitly negated"
                    )
                if not re.search(
                    r"\b(?:public|publish(?:es|ed|ing)?|official)\b",
                    description,
                ):
                    self.errors.append(
                        f"{artifact}{display_path(pointer_child(path, 'description'))}: "
                        "intentionally-public authorization description must explain "
                        "the public publication basis"
                    )

    def _validate_quality_metrics(
        self, data: dict[str, Any], ids: dict[str, set[str]]
    ) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        quality = data.get("quality_metrics")
        if not isinstance(quality, dict):
            return
        counts = quality.get("entity_counts")
        if isinstance(counts, dict):
            for collection in COLLECTION_PREFIXES:
                expected = len(data.get(collection, [])) if isinstance(data.get(collection), list) else 0
                if counts.get(collection) != expected:
                    self.errors.append(
                        f"{artifact}#/quality_metrics/entity_counts/{collection}: "
                        f"recorded {counts.get(collection)!r}, expected {expected}"
                    )
        artifact_results = quality.get("artifact_schema_results", [])
        recorded_artifacts = {
            result.get("artifact")
            for result in artifact_results
            if isinstance(result, dict)
        }
        expected_artifacts = {
            "RAW_CONFERENCES.json",
            "NORMALIZED_CONFERENCES.json",
        }
        if recorded_artifacts != expected_artifacts:
            self.errors.append(
                f"{artifact}#/quality_metrics/artifact_schema_results: must contain "
                "results for RAW_CONFERENCES.json and NORMALIZED_CONFERENCES.json"
            )
        for index, result in enumerate(artifact_results):
            if isinstance(result, dict) and result.get("result") != "pass":
                self.errors.append(
                    f"{artifact}#/quality_metrics/artifact_schema_results/{index}/"
                    "result: completed normalized validation requires 'pass'"
                )
        for key in ("unresolved_foreign_keys", "unresolved_source_references"):
            if quality.get(key):
                self.errors.append(
                    f"{artifact}#/quality_metrics/{key}: successful validation requires "
                    "this unresolved-reference list to be empty"
                )
        decisions = [
            decision
            for decision in data.get("entity_resolution_decisions", [])
            if isinstance(decision, dict)
        ]
        expected_outcomes = Counter(decision.get("outcome") for decision in decisions)
        recorded_outcomes = quality.get("resolution_outcomes")
        if isinstance(recorded_outcomes, dict):
            for outcome in ("applied", "rejected", "unresolved"):
                if recorded_outcomes.get(outcome) != expected_outcomes.get(outcome, 0):
                    self.errors.append(
                        f"{artifact}#/quality_metrics/resolution_outcomes/{outcome}: "
                        f"recorded {recorded_outcomes.get(outcome)!r}, expected "
                        f"{expected_outcomes.get(outcome, 0)}"
                    )
        expected_coverage = {
            branch: Counter(
                conference.get("collection_statuses", {}).get(branch)
                for conference in data.get("conferences", [])
                if isinstance(conference, dict)
            )
            for branch in BRANCH_NAMES
        }
        coverage = quality.get("branch_coverage")
        if isinstance(coverage, dict):
            for branch in BRANCH_NAMES:
                recorded = coverage.get(branch)
                if not isinstance(recorded, dict):
                    continue
                for status in ALLOWED_STATUSES:
                    expected = expected_coverage[branch].get(status, 0)
                    if recorded.get(status) != expected:
                        self.errors.append(
                            f"{artifact}#/quality_metrics/branch_coverage/{branch}/"
                            f"{status}: recorded {recorded.get(status)!r}, expected "
                            f"{expected}"
                        )
        translations = [
            translation
            for translation in data.get("translations", [])
            if isinstance(translation, dict)
        ]
        translation_coverage = quality.get("translation_coverage")
        if isinstance(translation_coverage, dict):
            expected_translation_counts = {
                "translated_fields": len(translations),
                "llm_generated": sum(
                    translation.get("translation_method") == "llm-generated"
                    for translation in translations
                ),
                "official_source": sum(
                    translation.get("translation_method") == "official-source"
                    for translation in translations
                ),
                "human_reviewed": sum(
                    translation.get("translation_method") == "human-reviewed"
                    for translation in translations
                ),
                "uncertain": sum(
                    translation.get("uncertainty") != "none"
                    for translation in translations
                ),
            }
            for field, expected in expected_translation_counts.items():
                if translation_coverage.get(field) != expected:
                    self.errors.append(
                        f"{artifact}#/quality_metrics/translation_coverage/{field}: "
                        f"recorded {translation_coverage.get(field)!r}, expected "
                        f"{expected}"
                    )
        expected_uncertainties = {
            translation.get("id")
            for translation in translations
            if translation.get("uncertainty") != "none"
        }
        if set(quality.get("translation_uncertainties", [])) != expected_uncertainties:
            self.errors.append(
                f"{artifact}#/quality_metrics/translation_uncertainties: values do "
                "not match uncertain translation records"
            )
        for key in ("attendee_privacy_checks", "attendee_authorization_checks"):
            checks = quality.get(key, [])
            if not checks:
                self.errors.append(
                    f"{artifact}#/quality_metrics/{key}: at least one completed "
                    "quality check is required"
                )
            for index, check in enumerate(checks):
                if isinstance(check, dict) and check.get("result") != "pass":
                    self.errors.append(
                        f"{artifact}#/quality_metrics/{key}/{index}/result: "
                        "completed validation requires 'pass'"
                    )
        if quality.get("blocking_warnings"):
            self.errors.append(
                f"{artifact}#/quality_metrics/blocking_warnings: completed "
                "validation cannot pass with blocking warnings"
            )
        expected_inaccessible = {
            source.get("id")
            for source in data.get("sources", [])
            if isinstance(source, dict)
            and source.get("review_state") in {"inaccessible", "removed", "paywalled"}
        }
        if set(quality.get("inaccessible_sources", [])) != expected_inaccessible:
            self.errors.append(
                f"{artifact}#/quality_metrics/inaccessible_sources: values do not "
                "match inaccessible, removed, or paywalled source records"
            )
        eligible_official_conferences = {
            related.get("entity_id")
            for source in data.get("sources", [])
            if isinstance(source, dict)
            and source.get("id") in self.eligible_direct_source_ids
            and source.get("source_class") == "official-conference"
            for related in source.get("related_entities", [])
            if isinstance(related, dict)
            and related.get("entity_type") == "conference"
        }
        expected_without_official = ids["conferences"] - eligible_official_conferences
        if (
            set(quality.get("conferences_without_official_sources", []))
            != expected_without_official
        ):
            self.errors.append(
                f"{artifact}#/quality_metrics/conferences_without_official_sources: "
                "values do not match eligible official-conference coverage"
            )
        expected_source_coverage: dict[str, dict[str, Any]] = {}
        for source in data.get("sources", []):
            if not isinstance(source, dict):
                continue
            source_class = source.get("source_class")
            if not isinstance(source_class, str):
                continue
            coverage_record = expected_source_coverage.setdefault(
                source_class,
                {
                    "reviewed_count": 0,
                    "eligible_count": 0,
                    "conference_ids": set(),
                },
            )
            if source.get("review_state") == "reviewed":
                coverage_record["reviewed_count"] += 1
            if source.get("id") in self.eligible_direct_source_ids:
                coverage_record["eligible_count"] += 1
            coverage_record["conference_ids"].update(
                related.get("entity_id")
                for related in source.get("related_entities", [])
                if isinstance(related, dict)
                and related.get("entity_type") == "conference"
            )
        recorded_source_coverage = {
            coverage.get("source_class"): coverage
            for coverage in quality.get("source_class_coverage", [])
            if isinstance(coverage, dict)
        }
        if set(recorded_source_coverage) != set(expected_source_coverage):
            self.errors.append(
                f"{artifact}#/quality_metrics/source_class_coverage: source classes "
                "do not match normalized source records"
            )
        for source_class, expected in expected_source_coverage.items():
            recorded = recorded_source_coverage.get(source_class)
            if not isinstance(recorded, dict):
                continue
            for field in ("reviewed_count", "eligible_count"):
                if recorded.get(field) != expected[field]:
                    self.errors.append(
                        f"{artifact}#/quality_metrics/source_class_coverage/"
                        f"{source_class}/{field}: recorded {recorded.get(field)!r}, "
                        f"expected {expected[field]}"
                    )
            if set(recorded.get("conference_ids", [])) != expected["conference_ids"]:
                self.errors.append(
                    f"{artifact}#/quality_metrics/source_class_coverage/"
                    f"{source_class}/conference_ids: values do not match source "
                    "relationships"
                )
        expected_conflicts = [
            conflict
            for conference in data.get("conferences", [])
            if isinstance(conference, dict)
            for conflict in conference.get("contradictions", [])
            if isinstance(conflict, dict)
        ]
        encode_conflict = lambda item: json.dumps(
            item, sort_keys=True, separators=(",", ":")
        )
        if Counter(map(encode_conflict, quality.get("conflicts", []))) != Counter(
            map(encode_conflict, expected_conflicts)
        ):
            self.errors.append(
                f"{artifact}#/quality_metrics/conflicts: values must exactly "
                "match conference contradiction records"
            )
        expected_gaps: dict[str, str] = {}
        for conference_index, conference in enumerate(data.get("conferences", [])):
            if not isinstance(conference, dict):
                continue
            for branch, status in conference.get("collection_statuses", {}).items():
                if status in {"complete", "partial"}:
                    continue
                condition = (
                    "unresolved-conflict" if status == "unresolved" else status
                )
                expected_gaps[
                    f"/conferences/{conference_index}/collection_statuses/{branch}"
                ] = condition
        recorded_gaps = {
            gap.get("json_pointer"): gap.get("condition")
            for gap in quality.get("collection_gaps", [])
            if isinstance(gap, dict)
        }
        for pointer, condition in expected_gaps.items():
            if recorded_gaps.get(pointer) != condition:
                self.errors.append(
                    f"{artifact}#/quality_metrics/collection_gaps: missing "
                    f"{condition!r} gap for {pointer}"
                )

    def _validate_alias_redirects(
        self, data: dict[str, Any], ids: dict[str, set[str]]
    ) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        top_level = data.get("alias_redirects", [])
        decisions = data.get("entity_resolution_decisions", [])
        embedded = [
            redirect
            for decision in decisions
            if isinstance(decision, dict)
            for redirect in decision.get("alias_redirects", [])
        ]
        encode = lambda item: json.dumps(item, sort_keys=True, separators=(",", ":"))
        if Counter(map(encode, top_level)) != Counter(map(encode, embedded)):
            self.errors.append(
                f"{artifact}#/alias_redirects: top-level redirects must exactly match "
                "redirects recorded in entity-resolution decisions"
            )
        all_ids = set().union(*ids.values())
        decision_ids = ids["entity_resolution_decisions"]
        for index, redirect in enumerate(top_level):
            if not isinstance(redirect, dict):
                continue
            self._check_ref(
                artifact,
                f"/alias_redirects/{index}/canonical_id",
                redirect.get("canonical_id"),
                all_ids,
            )
            self._check_ref(
                artifact,
                f"/alias_redirects/{index}/decision_id",
                redirect.get("decision_id"),
                decision_ids,
            )

    def _validate_raw_normalized_invariants(
        self, raw: dict[str, Any], normalized: dict[str, Any]
    ) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        raw_by_id = {
            record.get("id"): record
            for record in raw.get("conferences", [])
            if isinstance(record, dict)
        }
        created_ids = {
            identifier
            for decision in normalized.get("entity_resolution_decisions", [])
            if isinstance(decision, dict)
            for identifier in decision.get("created_entity_ids", [])
        }
        for index, conference in enumerate(normalized.get("conferences", [])):
            if not isinstance(conference, dict):
                continue
            conference_id = conference.get("id")
            raw_record = raw_by_id.get(conference_id)
            if raw_record is None:
                if conference_id not in created_ids:
                    self.errors.append(
                        f"{artifact}#/conferences/{index}/id: normalized conference "
                        f"{conference_id!r} has no raw record or split decision"
                    )
                continue
            raw_branches = raw_record.get("branches", {})
            normalized_statuses = conference.get("collection_statuses", {})
            if not isinstance(raw_branches, dict) or not isinstance(normalized_statuses, dict):
                continue
            for branch in BRANCH_NAMES:
                raw_branch = raw_branches.get(branch)
                raw_status = (
                    raw_branch.get("collection_status")
                    if isinstance(raw_branch, dict)
                    else None
                )
                if normalized_statuses.get(branch) != raw_status:
                    self.errors.append(
                        f"{artifact}#/conferences/{index}/collection_statuses/{branch}: "
                        f"status {normalized_statuses.get(branch)!r} does not match "
                        f"RAW_CONFERENCES.json {raw_status!r}"
                    )
                if raw_status not in {"complete", "partial"}:
                    for field in CONFERENCE_BRANCH_FIELDS.get(branch, ()):
                        if self._has_material_value(conference.get(field)):
                            self.errors.append(
                                f"{artifact}#/conferences/{index}/{field}: normalized "
                                f"value cannot be present when branch {branch!r} has "
                                f"status {raw_status!r}"
                            )
        raw_sources = {
            source.get("id")
            for source in raw.get("sources", [])
            if isinstance(source, dict)
        }
        normalized_direct_sources = {
            source.get("id")
            for source in normalized.get("sources", [])
            if isinstance(source, dict) and source.get("source_kind") == "direct"
        }
        missing = raw_sources - normalized_direct_sources
        if missing:
            self.errors.append(
                f"{artifact}#/sources: raw direct sources missing from normalized "
                f"source collection: {', '.join(sorted(missing))}"
            )
        self._validate_provenance_pointers(raw, normalized)

    @staticmethod
    def _has_material_value(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict)):
            return bool(value)
        return True

    def _material_leaf_pointers(self, value: Any, path: str) -> Iterable[str]:
        if isinstance(value, dict):
            for key, child in value.items():
                yield from self._material_leaf_pointers(child, pointer_child(path, key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from self._material_leaf_pointers(
                    child, pointer_child(path, index)
                )
        elif self._has_material_value(value):
            yield path

    @staticmethod
    def _provenance_covers(pointer: str, material_pointer: str) -> bool:
        return material_pointer == pointer or material_pointer.startswith(f"{pointer}/")

    def _validate_material_field_provenance(
        self, normalized: dict[str, Any]
    ) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        for collection in PROVENANCE_COLLECTIONS:
            records = normalized.get(collection, [])
            if not isinstance(records, list):
                continue
            for record_index, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                provenance = record.get("field_provenance")
                if not isinstance(provenance, dict):
                    continue
                provenance_pointers = tuple(provenance)
                for field, value in record.items():
                    if field in PROVENANCE_EXCLUDED_FIELDS:
                        continue
                    for material_pointer in self._material_leaf_pointers(
                        value, pointer_child("", field)
                    ):
                        if not any(
                            self._provenance_covers(pointer, material_pointer)
                            for pointer in provenance_pointers
                        ):
                            self.errors.append(
                                f"{artifact}#/{collection}/{record_index}/"
                                f"field_provenance: material field "
                                f"{material_pointer!r} lacks field-level provenance"
                            )

    def _validate_provenance_pointers(
        self, raw: dict[str, Any], normalized: dict[str, Any]
    ) -> None:
        raw_conference_indexes = {
            conference.get("id"): index
            for index, conference in enumerate(raw.get("conferences", []))
            if isinstance(conference, dict)
            and isinstance(conference.get("id"), str)
        }
        for conference_index, conference in enumerate(raw.get("conferences", [])):
            if not isinstance(conference, dict):
                continue
            provenance = conference.get("field_provenance", {})
            if not isinstance(provenance, dict):
                continue
            for field_pointer, entry in provenance.items():
                base = (
                    f"RAW_CONFERENCES.json#/conferences/{conference_index}/"
                    f"field_provenance/{field_pointer.replace('/', '~1')}"
                )
                if resolve_json_pointer(conference, field_pointer) is MISSING:
                    self.errors.append(
                        f"{base}: field provenance pointer does not resolve within "
                        "the raw conference record"
                    )
                if isinstance(entry, dict):
                    for pointer_index, evidence_pointer in enumerate(
                        entry.get("raw_evidence_pointers", [])
                    ):
                        if resolve_json_pointer(raw, evidence_pointer) is MISSING:
                            self.errors.append(
                                f"{base}/raw_evidence_pointers/{pointer_index}: "
                                f"raw evidence pointer {evidence_pointer!r} does not resolve"
                            )
        for collection in COLLECTION_PREFIXES:
            for record_index, record in enumerate(normalized.get(collection, [])):
                if not isinstance(record, dict):
                    continue
                provenance = record.get("field_provenance")
                if not isinstance(provenance, dict):
                    continue
                for field_pointer, entry in provenance.items():
                    base = (
                        f"NORMALIZED_CONFERENCES.json#/{collection}/{record_index}/"
                        f"field_provenance/{field_pointer.replace('/', '~1')}"
                    )
                    if resolve_json_pointer(record, field_pointer) is MISSING:
                        self.errors.append(
                            f"{base}: field provenance pointer does not resolve within "
                            "the normalized record"
                        )
                    if isinstance(entry, dict):
                        for pointer_index, raw_pointer in enumerate(
                            entry.get("raw_artifact_pointers", [])
                        ):
                            if collection == "conferences":
                                tokens = field_pointer.lstrip("/").split("/")
                                branch = (
                                    CONFERENCE_FIELD_BRANCH.get(tokens[0])
                                    if tokens
                                    else None
                                )
                                raw_conference_index = raw_conference_indexes.get(
                                    record.get("id")
                                )
                                if (
                                    branch is not None
                                    and raw_conference_index is not None
                                    and not raw_pointer.startswith(
                                        f"/conferences/{raw_conference_index}/"
                                        f"branches/{branch}/raw_values/"
                                    )
                                ):
                                    self.errors.append(
                                        f"{base}/raw_artifact_pointers/"
                                        f"{pointer_index}: provenance for "
                                        f"{field_pointer!r} must point to branch "
                                        f"{branch!r}"
                                    )
                            if resolve_json_pointer(raw, raw_pointer) is MISSING:
                                self.errors.append(
                                    f"{base}/raw_artifact_pointers/{pointer_index}: "
                                    f"raw artifact pointer {raw_pointer!r} does not resolve"
                                )
        self._validate_material_field_provenance(normalized)
        for translation_index, translation in enumerate(
            normalized.get("translations", [])
        ):
            if (
                isinstance(translation, dict)
                and resolve_json_pointer(
                    normalized, translation.get("field_pointer")
                )
                is MISSING
            ):
                self.errors.append(
                    f"NORMALIZED_CONFERENCES.json#/translations/{translation_index}/"
                    "field_pointer: translation target pointer does not resolve"
                )
        self._validate_provenance_value_alignment(raw, normalized)

    def _validate_provenance_value_alignment(
        self, raw: dict[str, Any], normalized: dict[str, Any]
    ) -> None:
        artifact = "NORMALIZED_CONFERENCES.json"
        translated_pointers = {
            translation.get("field_pointer")
            for translation in normalized.get("translations", [])
            if isinstance(translation, dict)
            and isinstance(translation.get("field_pointer"), str)
        }
        excluded_tokens = {
            "id",
            "source_id",
            "source_ids",
            "listing_source_ids",
            "verification_source_ids",
            "translation_ids",
            "entity_resolution_decision_ids",
            "authorization_basis",
            "collection_status",
            "collection_statuses",
            "confidence",
            "contradictions",
            "unresolved_fields",
            "organization_types",
            "contact_type",
        }

        def evidence_scalars(value: Any) -> Iterable[Any]:
            if isinstance(value, dict):
                for child in value.values():
                    yield from evidence_scalars(child)
            elif isinstance(value, list):
                for child in value:
                    yield from evidence_scalars(child)
            elif self._has_material_value(value):
                yield value

        def semantic_comparison_required(pointer: str) -> bool:
            tokens = pointer.lstrip("/").split("/")
            for token in tokens:
                if token in excluded_tokens:
                    return False
                if token.endswith("_id") or token.endswith("_ids"):
                    return False
            return True

        def evidence_supports(value: Any, evidence: list[Any]) -> bool:
            if isinstance(value, bool):
                return any(item is value for item in evidence)
            if isinstance(value, (int, float)):
                return any(
                    isinstance(item, (int, float))
                    and not isinstance(item, bool)
                    and item == value
                    for item in evidence
                )
            if not isinstance(value, str):
                return False

            def normalized_text(text: Any) -> str:
                rendered = re.sub(r"\s+", " ", str(text)).strip().casefold()
                return rendered.strip(" \t\r\n\"'`.,;:")

            normalized_value = normalized_text(value)
            for item in evidence:
                rendered = normalized_text(item)
                if not rendered:
                    continue
                if normalized_value == rendered:
                    return True
            return False

        for collection in PROVENANCE_COLLECTIONS:
            records = normalized.get(collection, [])
            if not isinstance(records, list):
                continue
            for record_index, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                provenance = record.get("field_provenance")
                if not isinstance(provenance, dict):
                    continue
                for leaf_pointer in self._material_leaf_pointers(record, ""):
                    tokens = leaf_pointer.lstrip("/").split("/")
                    if tokens and tokens[0] in PROVENANCE_EXCLUDED_FIELDS:
                        continue
                    if not semantic_comparison_required(leaf_pointer):
                        continue
                    absolute_pointer = (
                        f"/{collection}/{record_index}{leaf_pointer}"
                    )
                    if absolute_pointer in translated_pointers:
                        continue
                    entry = next(
                        (
                            candidate
                            for field_pointer, candidate in provenance.items()
                            if self._provenance_covers(
                                field_pointer, leaf_pointer
                            )
                            and isinstance(candidate, dict)
                        ),
                        None,
                    )
                    if entry is None:
                        continue
                    normalized_value = resolve_json_pointer(record, leaf_pointer)
                    evidence = [
                        scalar
                        for raw_pointer in entry.get(
                            "raw_artifact_pointers", []
                        )
                        for scalar in evidence_scalars(
                            resolve_json_pointer(raw, raw_pointer)
                        )
                    ]
                    if not evidence_supports(normalized_value, evidence):
                        self.errors.append(
                            f"{artifact}#/{collection}/{record_index}"
                            f"{leaf_pointer}: normalized value "
                            f"{normalized_value!r} is not supported by its raw "
                            "artifact provenance"
                        )

    def _validate_entity_resolution_ledger(
        self, text: str, normalized: dict[str, Any]
    ) -> None:
        artifact = "ENTITY_RESOLUTION.md"
        for label in (
            "Merge",
            "Split",
            "Alias",
            "Rejected candidate",
            "Unresolved candidate",
        ):
            if not re.search(
                rf"(?mi)^\|\s*{re.escape(label)}\s*\|", text
            ):
                self.errors.append(
                    f"{artifact}: Decision Summary is missing row {label!r}"
                )
        ledger_ids = self._heading_ids(artifact, text, "ER")
        decisions = [
            record
            for record in normalized.get("entity_resolution_decisions", [])
            if isinstance(record, dict)
        ]
        data_ids = {record.get("id") for record in decisions}
        if ledger_ids != data_ids:
            missing = sorted(data_ids - ledger_ids)
            extra = sorted(ledger_ids - data_ids)
            if missing:
                self.errors.append(
                    f"{artifact}: decision IDs missing from Markdown ledger: "
                    f"{', '.join(missing)}"
                )
            if extra:
                self.errors.append(
                    f"{artifact}: decision IDs absent from normalized JSON: "
                    f"{', '.join(extra)}"
                )
        for decision in decisions:
            decision_id = decision.get("id")
            if not isinstance(decision_id, str):
                continue
            match = re.search(
                rf"(?ms)^###\s+{re.escape(decision_id)}(?:\s+[^\n]*)?\n"
                rf"(.*?)(?=^###\s+ER[0-9]{{3,}}(?:\s|$)|^##\s+|\Z)",
                text,
            )
            if not match:
                continue
            block = match.group(1)
            required_fields = (
                "Decision ID",
                "Decision type",
                "Outcome",
                "Entity type",
                "Candidate or original IDs",
                "Canonical ID",
                "Created IDs",
                "Source IDs",
                "Compared attributes",
                "Corroborating evidence",
                "Conflicting evidence",
                "Confidence",
                "Rationale",
                "Alias redirects",
            )
            fields = {}
            for label in required_fields:
                value = markdown_field(block, label)
                if value is None:
                    self.errors.append(
                        f"{artifact}: {decision_id} is missing required field "
                        f"{label!r}"
                    )
                else:
                    fields[label] = value
            comparisons = {
                "Decision ID": "id",
                "Decision type": "decision_type",
                "Outcome": "outcome",
                "Entity type": "entity_type",
            }
            for label, json_field in comparisons.items():
                if (
                    label in fields
                    and fields[label] != str(decision.get(json_field))
                ):
                    self.errors.append(
                        f"{artifact}: {decision_id} field {label!r} does not match "
                        f"NORMALIZED_CONFERENCES.json value "
                        f"{decision.get(json_field)!r}"
                    )
        if (
            self.request.mode == "refresh"
            and markdown_section(text, "Refresh Differences") is None
        ):
            self.errors.append(
                f"{artifact}: refresh mode requires a nonempty 'Refresh Differences' "
                "section"
            )

    def _heading_ids(self, artifact: str, text: str, prefix: str) -> set[str]:
        identifiers = re.findall(
            rf"(?m)^###\s+(?:`|\[)?({prefix}[0-9]{{3,}})(?:`|\])?(?:\s|$)",
            text,
        )
        for identifier, count in Counter(identifiers).items():
            if count > 1:
                self.errors.append(f"{artifact}: duplicate heading ID {identifier}")
        return set(identifiers)

    def _validate_refresh_difference_reporting(
        self,
        source_normalized: dict[str, Any],
        current_normalized: dict[str, Any],
    ) -> None:
        ignored_keys = {
            "field_provenance",
            "source_ids",
            "listing_source_ids",
            "verification_source_ids",
            "translation_ids",
            "entity_resolution_decision_ids",
            "quality_metrics",
            "run_metadata",
            "template_notice",
            "access_date",
        }

        def comparable(value: Any) -> Any:
            if isinstance(value, dict):
                return {
                    key: comparable(child)
                    for key, child in sorted(value.items())
                    if key not in ignored_keys
                }
            if isinstance(value, list):
                return [comparable(child) for child in value]
            return value

        def collect_differences(
            before: Any,
            after: Any,
            path: tuple[str, ...] = (),
        ) -> list[tuple[tuple[str, ...], Any, Any]]:
            if isinstance(before, dict) and isinstance(after, dict):
                differences: list[tuple[tuple[str, ...], Any, Any]] = []
                for key in sorted(set(before) | set(after)):
                    if key not in before or key not in after:
                        differences.append(
                            (path + (key,), before.get(key, MISSING), after.get(key, MISSING))
                        )
                    else:
                        differences.extend(
                            collect_differences(
                                before[key], after[key], path + (key,)
                            )
                        )
                return differences
            if isinstance(before, list) and isinstance(after, list):
                if all(
                    isinstance(item, dict) and isinstance(item.get("id"), str)
                    for item in before + after
                ):
                    before_by_id = {item["id"]: item for item in before}
                    after_by_id = {item["id"]: item for item in after}
                    differences = []
                    for identifier in sorted(set(before_by_id) | set(after_by_id)):
                        if (
                            identifier not in before_by_id
                            or identifier not in after_by_id
                        ):
                            differences.append(
                                (
                                    path + (identifier,),
                                    before_by_id.get(identifier, MISSING),
                                    after_by_id.get(identifier, MISSING),
                                )
                            )
                        else:
                            differences.extend(
                                collect_differences(
                                    before_by_id[identifier],
                                    after_by_id[identifier],
                                    path + (identifier,),
                                )
                            )
                    return differences
                differences = []
                for index in range(max(len(before), len(after))):
                    if index >= len(before) or index >= len(after):
                        differences.append(
                            (
                                path + (str(index),),
                                before[index] if index < len(before) else MISSING,
                                after[index] if index < len(after) else MISSING,
                            )
                        )
                    else:
                        differences.extend(
                            collect_differences(
                                before[index],
                                after[index],
                                path + (str(index),),
                            )
                        )
                return differences
            if before != after:
                return [(path, before, after)]
            return []

        source_comparable = comparable(source_normalized)
        current_comparable = comparable(current_normalized)
        differences = collect_differences(
            source_comparable, current_comparable
        )
        changed = bool(differences)
        component_terms = {
            "conference_series": {"series"},
            "organizations": {"organization", "organizer"},
            "people": {"person", "people", "speaker"},
            "venues": {"venue", "location"},
            "sessions_and_events": {"schedule", "session", "event"},
            "registration_offers": {"registration", "ticket", "price"},
            "sponsors_and_partnerships": {"sponsor", "partner", "partnership"},
            "hotels": {"hotel", "booking"},
            "attendee_records_or_aggregates": {"attendee", "attendance"},
            "sources": {"source"},
            "canonical_name": {"canonical name", "name", "identity"},
            "aliases": {"alias", "identity"},
            "series_id": {"series"},
            "edition": {"edition", "series"},
            "acronym": {"acronym", "series"},
            "organizer_ids": {"organizer"},
            "description": {"description"},
            "themes": {"theme"},
            "topics": {"topic"},
            "conference_type": {"conference type", "format"},
            "language_codes": {"language"},
            "start_date": {"start date", "date", "dates"},
            "end_date": {"end date", "date", "dates"},
            "start_time": {"start time", "time"},
            "end_time": {"end time", "time"},
            "timezone": {"timezone"},
            "recurrence": {"recurrence"},
            "event_status": {"event status", "status"},
            "official_url": {"official url", "website"},
            "event_urls": {"event url", "website"},
            "person_ids": {"person", "people", "speaker"},
            "committee_memberships": {"committee"},
            "session_event_ids": {"schedule", "session", "event"},
            "registration_offer_ids": {"registration", "ticket"},
            "venue_ids": {"venue", "location"},
            "partnership_ids": {"sponsor", "partner"},
            "hotel_ids": {"hotel", "booking"},
            "attendee_record_ids": {"attendee", "attendance"},
            "intended_audience": {"audience", "attendee"},
            "publication_or_update_date": {
                "publication",
                "update date",
                "source",
            },
            "source_class": {"source class", "source"},
            "title": {"title"},
            "registration_status": {"registration", "status"},
            "registration_url": {"registration", "url"},
            "ticket_class": {"ticket", "registration"},
            "price": {"price", "registration"},
            "relationship_type": {"relationship", "sponsor", "partner"},
            "tier": {"tier", "sponsor"},
            "aggregate_count": {"attendance", "count"},
            "estimate_min": {"attendance", "estimate"},
            "estimate_max": {"attendance", "estimate"},
            "scope": {"scope", "attendance"},
        }
        category_by_component = {
            "conference_series": "series",
            "organizations": "organizers",
            "people": "people",
            "venues": "venue",
            "sessions_and_events": "schedule",
            "registration_offers": "registration",
            "sponsors_and_partnerships": "sponsors",
            "hotels": "hotels",
            "attendee_records_or_aggregates": "attendance",
            "sources": "source",
            "canonical_name": "identity",
            "aliases": "identity",
            "series_id": "series",
            "edition": "series",
            "acronym": "series",
            "organizer_ids": "organizers",
            "description": "description",
            "themes": "description",
            "topics": "description",
            "conference_type": "description",
            "language_codes": "description",
            "start_date": "dates",
            "end_date": "dates",
            "start_time": "dates",
            "end_time": "dates",
            "timezone": "dates",
            "recurrence": "dates",
            "event_status": "dates",
            "official_url": "official-url",
            "event_urls": "official-url",
            "person_ids": "people",
            "committee_memberships": "committees",
            "session_event_ids": "schedule",
            "registration_offer_ids": "registration",
            "venue_ids": "venue",
            "partnership_ids": "sponsors",
            "hotel_ids": "hotels",
            "attendee_record_ids": "attendance",
            "intended_audience": "attendance",
            "publication_or_update_date": "source",
            "source_class": "source",
            "registration_status": "registration",
            "registration_url": "registration",
            "ticket_class": "registration",
            "price": "registration",
            "relationship_type": "sponsors",
            "tier": "sponsors",
            "aggregate_count": "attendance",
            "estimate_min": "attendance",
            "estimate_max": "attendance",
            "scope": "attendance",
        }
        actual_change_terms: set[str] = set()
        actual_change_categories: set[str] = set()
        previous_change_values: set[str] = set()
        current_change_values: set[str] = set()
        for path, before, after in differences:
            for component in path:
                actual_change_terms.update(component_terms.get(component, set()))
                category = category_by_component.get(component)
                if category is not None:
                    actual_change_categories.add(category)
            for value, destination in (
                (before, previous_change_values),
                (after, current_change_values),
            ):
                if isinstance(value, (str, int, float)) and not isinstance(
                    value, bool
                ):
                    rendered = str(value).strip().casefold()
                    if len(rendered) >= 4:
                        actual_change_terms.add(rendered)
                        destination.add(rendered)

        def section_mentions_actual_change(section: str) -> bool:
            normalized_section = section.casefold()
            for term in actual_change_terms:
                if " " in term or not term.isalnum():
                    if term in normalized_section:
                        return True
                elif re.search(rf"\b{re.escape(term)}\b", normalized_section):
                    return True
            return False

        sections = (
            (
                "ENTITY_RESOLUTION.md",
                "Refresh Differences",
                self.markdown.get("ENTITY_RESOLUTION.md"),
            ),
            (
                "QUALITY_REPORT.md",
                "Refresh Differences",
                self.markdown.get("QUALITY_REPORT.md"),
            ),
            (
                "REPORT.md",
                "Refresh Changes",
                self.markdown.get("REPORT.md"),
            ),
        )
        for artifact, heading, text in sections:
            if text is None:
                continue
            section = markdown_section(text, heading) or ""
            claims_no_change = bool(
                re.search(
                    r"(?i)(?:\bno\b.{0,40}\bchanges?\b|"
                    r"\bchanges?\b\s*:\s*none\b|"
                    r"\bnone\b.{0,20}\bchanges?\b)",
                    section,
                )
            )
            reports_difference = bool(
                re.search(
                    r"(?i)\b(addition|removal|change|unresolved difference)s?\b",
                    section,
                )
            )
            if changed and claims_no_change:
                self.errors.append(
                    f"{artifact}: {heading} claims no changes, but normalized "
                    "data differs from the source run"
                )
            elif changed and not reports_difference:
                self.errors.append(
                    f"{artifact}: {heading} must report at least one addition, "
                    "removal, change, or unresolved difference"
                )
            elif changed and not section_mentions_actual_change(section):
                self.errors.append(
                    f"{artifact}: {heading} does not identify the actual changed "
                    "field or collection"
                )
            elif changed:
                normalized_section = section.casefold()
                category_patterns = {
                    "identity": r"\b(?:identity|canonical\s+name|alias)\b",
                    "series": r"\b(?:series|edition|acronym)\b",
                    "organizers": r"\borganizers?\b",
                    "description": (
                        r"\b(?:description|themes?|topics?|format|languages?)\b"
                    ),
                    "dates": r"\b(?:dates?|times?|timezone|recurrence|status)\b",
                    "official-url": r"\b(?:official\s+url|website)\b",
                    "people": r"\b(?:people|person|speakers?)\b",
                    "committees": r"\bcommittees?\b",
                    "schedule": r"\b(?:schedule|sessions?|workshops?)\b",
                    "registration": r"\b(?:registration|tickets?|prices?)\b",
                    "venue": r"\b(?:venue|location)\b",
                    "sponsors": r"\b(?:sponsors?|exhibitors?|partners?)\b",
                    "hotels": r"\b(?:hotels?|booking|accommodation)\b",
                    "attendance": r"\b(?:attendance|attendees?|audience)\b",
                    "source": r"\b(?:source|publication)\b",
                }
                reported_categories = {
                    category
                    for category, pattern in category_patterns.items()
                    if re.search(pattern, normalized_section)
                }
                unsupported_categories = (
                    reported_categories - actual_change_categories
                )
                if unsupported_categories:
                    self.errors.append(
                        f"{artifact}: {heading} reports unchanged categories "
                        f"{sorted(unsupported_categories)!r}"
                    )
                mentions_previous_value = any(
                    value in normalized_section
                    for value in previous_change_values - current_change_values
                )
                mentions_current_value = any(
                    value in normalized_section for value in current_change_values
                )
                if mentions_previous_value and not mentions_current_value:
                    self.errors.append(
                        f"{artifact}: {heading} mentions a previous value without "
                        "the actual current value"
                    )
                for previous_value in (
                    previous_change_values - current_change_values
                ):
                    if re.search(
                        rf"(?i)(?:actual\s+current|current|remains?)"
                        rf".{{0,40}}{re.escape(previous_value)}",
                        section,
                    ):
                        self.errors.append(
                            f"{artifact}: {heading} presents a previous value as "
                            "the current result"
                        )
                        break
            elif not changed and reports_difference and not claims_no_change:
                self.errors.append(
                    f"{artifact}: {heading} reports a difference, but normalized "
                    "data matches the source run"
                )

    def _validate_report(self, text: str, normalized: dict[str, Any]) -> None:
        artifact = "REPORT.md"
        for heading in REPORT_REQUIRED_SECTIONS:
            if markdown_section(text, heading) is None:
                self.errors.append(
                    f"{artifact}: required section {heading!r} is missing or empty"
                )
        available_sources = {
            source.get("id")
            for source in normalized.get("sources", [])
            if isinstance(source, dict)
        }
        citations = re.findall(r"\[((?:A|S)[0-9]{3,})\]", text)
        for citation in sorted(set(citations)):
            if citation not in available_sources:
                self.errors.append(
                    f"{artifact}: unresolved report citation [{citation}]"
                )
            elif citation.startswith("S") and citation not in self.eligible_direct_source_ids:
                self.errors.append(
                    f"{artifact}: direct source citation [{citation}] is not reviewed "
                    "and eligible for factual use"
                )
            elif citation.startswith("A"):
                source = self.normalized_source_records.get(citation, {})
                if source.get("review_state") != "reviewed":
                    self.errors.append(
                        f"{artifact}: aggregator citation [{citation}] is not from a "
                        "reviewed listing"
                    )
        aggregator_section = re.search(
            r"(?ms)^###\s+Aggregators\s*$\n(.*?)(?=^###\s+|^##\s+|\Z)",
            text,
        )
        aggregator_range = (
            (aggregator_section.start(1), aggregator_section.end(1))
            if aggregator_section
            else None
        )
        for match in re.finditer(r"\[(A[0-9]{3,})\]", text):
            if aggregator_range is None or not (
                aggregator_range[0] <= match.start() < aggregator_range[1]
            ):
                self.errors.append(
                    f"{artifact}: aggregator citation [{match.group(1)}] appears "
                    "outside the observed-listing coverage section"
                )
        def records_by_id(collection: str) -> dict[str, dict[str, Any]]:
            return {
                record["id"]: record
                for record in normalized.get(collection, [])
                if isinstance(record, dict) and isinstance(record.get("id"), str)
            }

        conferences_by_id = records_by_id("conferences")
        series_by_id = records_by_id("conference_series")
        organizations_by_id = records_by_id("organizations")
        people_by_id = records_by_id("people")
        venues_by_id = records_by_id("venues")
        events_by_id = records_by_id("sessions_and_events")
        registration_by_id = records_by_id("registration_offers")
        partnerships_by_id = records_by_id("sponsors_and_partnerships")
        hotels_by_id = records_by_id("hotels")
        attendees_by_id = records_by_id("attendee_records_or_aggregates")
        conference_ids = set(conferences_by_id)
        report_ids = self._heading_ids(artifact, text, "C")
        if conference_ids != report_ids:
            missing = sorted(conference_ids - report_ids)
            extra = sorted(report_ids - conference_ids)
            if missing:
                self.errors.append(
                    f"{artifact}: normalized conferences missing summaries: "
                    f"{', '.join(missing)}"
                )
            if extra:
                self.errors.append(
                    f"{artifact}: report summaries have no normalized conference: "
                    f"{', '.join(extra)}"
                )
        comparison = markdown_section_raw(text, "Conference Comparison")
        if comparison is not None:
            comparison_header, comparison_rows = markdown_table(comparison)
            if len(comparison_rows) != len(conference_ids):
                self.errors.append(
                    f"{artifact}: Conference Comparison has "
                    f"{len(comparison_rows)} data rows, expected {len(conference_ids)}"
                )
            for row_index, row in enumerate(comparison_rows):
                if not any(
                    re.fullmatch(r"\[S[0-9]{3,}\]", cell)
                    or re.search(r"\[S[0-9]{3,}\]", cell)
                    for cell in row
                ):
                    self.errors.append(
                        f"{artifact}: Conference Comparison row {row_index + 1} "
                        "lacks a direct source citation"
                    )
            conferences_by_name = {
                conference.get("canonical_name"): conference
                for conference in normalized.get("conferences", [])
                if isinstance(conference, dict)
            }
            comparison_claims = {
                "Conference": ("identity", "identity_and_aliases"),
                "Dates": (
                    "dates",
                    "dates_times_timezone_recurrence_and_status",
                ),
                "Location": ("venue", "venue"),
                "Venue": ("venue", "venue"),
                "Format": (
                    "description",
                    "description_themes_topics_type_and_languages",
                ),
                "Registration state": ("registration", "registration"),
                "Official URL": ("official-url", "websites_and_event_urls"),
            }
            for row_index, row in enumerate(comparison_rows):
                if not row:
                    continue
                conference = conferences_by_name.get(row[0])
                if conference is None:
                    self.errors.append(
                        f"{artifact}: Conference Comparison row {row_index + 1} "
                        f"does not match a normalized canonical name"
                    )
                    continue
                row_sources = set(
                    re.findall(r"\[(S[0-9]{3,})\]", " ".join(row))
                )
                for column_label, (claim, branch) in comparison_claims.items():
                    if column_label not in comparison_header:
                        self.errors.append(
                            f"{artifact}: Conference Comparison is missing column "
                            f"{column_label!r}"
                        )
                        continue
                    column = comparison_header.index(column_label)
                    if len(row) <= column:
                        continue
                    value = row[column].strip()
                    if not value or "insufficient evidence" in value.casefold():
                        continue
                    status = conference.get("collection_statuses", {}).get(branch)
                    if status not in {"complete", "partial"}:
                        self.errors.append(
                            f"{artifact}: Conference Comparison row "
                            f"{row_index + 1} column {column_label!r} is populated "
                            f"while branch {branch!r} has status {status!r}"
                        )
                    if not any(
                        claim
                        in set(
                            self.normalized_source_records.get(source_id, {}).get(
                                "supported_fields_or_claims", []
                            )
                        )
                        for source_id in row_sources
                    ):
                        self.errors.append(
                            f"{artifact}: Conference Comparison row "
                            f"{row_index + 1} column {column_label!r} lacks a cited "
                            f"source supporting claim {claim!r}"
                        )
                    expected_values: set[str] = set()
                    if column_label == "Conference":
                        expected_values.add(str(conference.get("canonical_name")))
                    elif column_label == "Dates":
                        start_date = conference.get("start_date")
                        end_date = conference.get("end_date")
                        if start_date and end_date:
                            expected_values.add(
                                start_date
                                if start_date == end_date
                                else f"{start_date} through {end_date}"
                            )
                            if start_date != end_date:
                                expected_values.add(f"{start_date} to {end_date}")
                    elif column_label == "Official URL":
                        if conference.get("official_url"):
                            expected_values.add(str(conference.get("official_url")))
                    elif column_label == "Format":
                        if conference.get("conference_type"):
                            expected_values.add(str(conference.get("conference_type")))
                    elif column_label == "Venue":
                        expected_values.update(
                            str(venues_by_id[venue_id].get("canonical_name"))
                            for venue_id in conference.get("venue_ids", [])
                            if venue_id in venues_by_id
                            and venues_by_id[venue_id].get("canonical_name")
                        )
                    elif column_label == "Location":
                        for venue_id in conference.get("venue_ids", []):
                            venue = venues_by_id.get(venue_id)
                            if not isinstance(venue, dict):
                                continue
                            parts = [
                                venue.get("locality"),
                                venue.get("administrative_area"),
                                venue.get("country"),
                            ]
                            parts = [str(part) for part in parts if part]
                            expected_values.update(parts)
                            if parts:
                                expected_values.add(", ".join(parts))
                    elif column_label == "Registration state":
                        expected_values.update(
                            str(registration_by_id[offer_id].get("registration_status"))
                            for offer_id in conference.get(
                                "registration_offer_ids", []
                            )
                            if offer_id in registration_by_id
                            and registration_by_id[offer_id].get(
                                "registration_status"
                            )
                        )
                    if value not in expected_values:
                        self.errors.append(
                            f"{artifact}: Conference Comparison row "
                            f"{row_index + 1} column {column_label!r} value "
                            f"{value!r} does not match normalized data"
                        )

        def report_claim_for_label(label: str) -> str | None:
            normalized_label = label.casefold()
            keyword_claims = (
                (("identity",), "identity"),
                (("series", "edition", "acronym"), "series"),
                (("organizer",), "organizers"),
                (
                    ("description", "theme", "topic", "conference type", "language"),
                    "description",
                ),
                (("date", "time", "timezone", "event status"), "dates"),
                (("official url", "website"), "official-url"),
                (("committee",), "committees"),
                (("public professional", "person", "speaker"), "people"),
                (("schedule", "session", "workshop", "social event"), "schedule"),
                (("registration", "ticket", "price"), "registration"),
                (("venue", "location"), "venue"),
                (("sponsor", "partner", "exhibitor"), "sponsors"),
                (("hotel", "booking"), "hotels"),
                (("attendee", "attendance"), "attendance"),
            )
            for keywords, claim in keyword_claims:
                if any(keyword in normalized_label for keyword in keywords):
                    return claim
            return None

        def add_material_value(values: set[str], value: Any) -> None:
            if isinstance(value, (str, int, float)) and not isinstance(value, bool):
                rendered = str(value).strip()
                if rendered:
                    values.add(rendered)

        def summary_values(
            conference: dict[str, Any], claim: str
        ) -> set[str]:
            values: set[str] = set()
            if claim == "identity":
                add_material_value(values, conference.get("canonical_name"))
                for alias in conference.get("aliases", []):
                    add_material_value(values, alias)
            elif claim == "series":
                series = series_by_id.get(conference.get("series_id"))
                if isinstance(series, dict):
                    add_material_value(values, series.get("canonical_name"))
                    add_material_value(values, series.get("acronym"))
                add_material_value(values, conference.get("edition"))
                add_material_value(values, conference.get("acronym"))
            elif claim == "organizers":
                for organization_id in conference.get("organizer_ids", []):
                    organization = organizations_by_id.get(organization_id, {})
                    add_material_value(values, organization.get("canonical_name"))
                    for alias in organization.get("aliases", []):
                        add_material_value(values, alias)
            elif claim == "description":
                for field in ("description", "conference_type"):
                    add_material_value(values, conference.get(field))
                for field in ("themes", "topics", "language_codes"):
                    for value in conference.get(field, []):
                        add_material_value(values, value)
            elif claim == "dates":
                for field in (
                    "start_date",
                    "end_date",
                    "start_time",
                    "end_time",
                    "timezone",
                    "recurrence",
                    "event_status",
                ):
                    add_material_value(values, conference.get(field))
            elif claim == "official-url":
                add_material_value(values, conference.get("official_url"))
                for value in conference.get("event_urls", []):
                    add_material_value(values, value)
            elif claim in {"people", "committees"}:
                for person_id in conference.get("person_ids", []):
                    person = people_by_id.get(person_id, {})
                    add_material_value(values, person.get("name"))
                    add_material_value(
                        values, person.get("public_professional_role")
                    )
                if claim == "committees":
                    for membership in conference.get("committee_memberships", []):
                        if not isinstance(membership, dict):
                            continue
                        add_material_value(values, membership.get("role"))
                        person = people_by_id.get(membership.get("person_id"), {})
                        add_material_value(values, person.get("name"))
            elif claim == "schedule":
                for event_id in conference.get("session_event_ids", []):
                    event = events_by_id.get(event_id, {})
                    for field in ("title", "event_type", "track", "start_at"):
                        add_material_value(values, event.get(field))
            elif claim == "registration":
                for offer_id in conference.get("registration_offer_ids", []):
                    offer = registration_by_id.get(offer_id, {})
                    for field in (
                        "registration_status",
                        "registration_url",
                        "ticket_class",
                        "price",
                        "eligibility",
                    ):
                        add_material_value(values, offer.get(field))
            elif claim == "venue":
                for venue_id in conference.get("venue_ids", []):
                    venue = venues_by_id.get(venue_id, {})
                    for field in (
                        "canonical_name",
                        "locality",
                        "administrative_area",
                        "country",
                        "postal_address",
                    ):
                        add_material_value(values, venue.get(field))
            elif claim == "sponsors":
                for partnership_id in conference.get("partnership_ids", []):
                    partnership = partnerships_by_id.get(partnership_id, {})
                    for field in ("relationship_type", "tier", "official_url"):
                        add_material_value(values, partnership.get(field))
                    organization = organizations_by_id.get(
                        partnership.get("organization_id"), {}
                    )
                    add_material_value(values, organization.get("canonical_name"))
            elif claim == "hotels":
                for hotel_id in conference.get("hotel_ids", []):
                    hotel = hotels_by_id.get(hotel_id, {})
                    for field in (
                        "canonical_name",
                        "locality",
                        "administrative_area",
                        "country",
                        "booking_url",
                    ):
                        add_material_value(values, hotel.get(field))
            elif claim == "attendance":
                for attendee_id in conference.get("attendee_record_ids", []):
                    attendee = attendees_by_id.get(attendee_id, {})
                    for field in (
                        "aggregate_count",
                        "estimate_min",
                        "estimate_max",
                        "scope",
                        "public_professional_role",
                    ):
                        add_material_value(values, attendee.get(field))
                    for audience in attendee.get("intended_audience", []):
                        add_material_value(values, audience)
                for audience in conference.get("intended_audience", []):
                    add_material_value(values, audience)
            return values

        def statement_matches_values(
            statement: str, expected_values: set[str]
        ) -> bool:
            normalized_statement = statement.casefold()
            for value in expected_values:
                normalized_value = value.casefold()
                if len(normalized_value) <= 2 and normalized_value.isalnum():
                    if re.search(
                        rf"\b{re.escape(normalized_value)}\b",
                        normalized_statement,
                    ):
                        return True
                elif normalized_value in normalized_statement:
                    return True
            return False

        def statement_without_citations(statement: str) -> str:
            return re.sub(r"\[(?:A|S)[0-9]{3,}\]", "", statement).strip()

        def normalized_statement_text(statement: str) -> str:
            plain = statement_without_citations(statement)
            return re.sub(r"[.`*_]+$", "", plain).strip().casefold()

        def validate_statement_details(
            conference_id: str,
            conference: dict[str, Any],
            claim: str,
            statement: str,
            expected_values: set[str],
        ) -> None:
            plain = statement_without_citations(statement)
            normalized_plain = normalized_statement_text(statement)
            if claim in {"identity", "organizers"}:
                allowed = {value.casefold() for value in expected_values}
                for prefix in (
                    "canonical name is ",
                    "organized by ",
                    "organizer is ",
                ):
                    if normalized_plain.startswith(prefix):
                        normalized_plain = normalized_plain[len(prefix) :].strip()
                if normalized_plain not in allowed:
                    self.errors.append(
                        f"{artifact}: conference summary {conference_id} {claim} "
                        "statement contains unsupported narrative or values"
                    )
            if claim == "dates":
                recorded_dates = set(
                    re.findall(r"\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b", plain)
                )
                month_numbers = {
                    name: index
                    for index, name in enumerate(
                        (
                            "",
                            "january",
                            "february",
                            "march",
                            "april",
                            "may",
                            "june",
                            "july",
                            "august",
                            "september",
                            "october",
                            "november",
                            "december",
                        )
                    )
                    if name
                }
                month_pattern = "|".join(month_numbers)
                natural_matches = [
                    (year, month_numbers[month.casefold()], day)
                    for month, day, year in re.findall(
                        rf"(?i)\b({month_pattern})\s+([0-9]{{1,2}})"
                        rf"(?:st|nd|rd|th)?(?:,\s*|\s+)([0-9]{{4}})\b",
                        plain,
                    )
                ]
                natural_matches.extend(
                    (year, month_numbers[month.casefold()], day)
                    for day, month, year in re.findall(
                        rf"(?i)\b([0-9]{{1,2}})(?:st|nd|rd|th)?\s+"
                        rf"({month_pattern})\s+([0-9]{{4}})\b",
                        plain,
                    )
                )
                for year, month, day in natural_matches:
                    try:
                        recorded_dates.add(
                            date(int(year), int(month), int(day)).isoformat()
                        )
                    except ValueError:
                        self.errors.append(
                            f"{artifact}: conference summary {conference_id} "
                            "dates statement contains an invalid calendar date"
                        )
                expected_dates = {
                    value
                    for value in expected_values
                    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value)
                }
                unexpected_dates = recorded_dates - expected_dates
                if unexpected_dates:
                    self.errors.append(
                        f"{artifact}: conference summary {conference_id} dates "
                        f"statement contains unsupported dates "
                        f"{sorted(unexpected_dates)!r}"
                    )
            if claim == "official-url":
                recorded_urls = {
                    url.rstrip(".,;")
                    for url in re.findall(r"https?://[^\s)\]]+", plain)
                }
                expected_urls = {
                    value for value in expected_values if value.startswith("http")
                }
                if recorded_urls - expected_urls:
                    self.errors.append(
                        f"{artifact}: conference summary {conference_id} "
                        "official-url statement contains an unsupported URL"
                    )
            if claim == "people":
                matched_people = []
                for person_id in conference.get("person_ids", []):
                    person = people_by_id.get(person_id, {})
                    name = str(person.get("name", "")).strip()
                    if name and name.casefold() in normalized_plain:
                        matched_people.append(person)
                if not matched_people:
                    self.errors.append(
                        f"{artifact}: conference summary {conference_id} people "
                        "statement does not identify a linked normalized person"
                    )
                for person in matched_people:
                    roles = {
                        str(person.get("public_professional_role", "")).strip()
                    }
                    roles.update(
                        str(role.get("role", "")).strip()
                        for role in person.get("conference_roles", [])
                        if isinstance(role, dict)
                        and role.get("conference_id") == conference_id
                    )
                    roles.discard("")
                    if roles and not any(
                        role.casefold() in normalized_plain for role in roles
                    ):
                        self.errors.append(
                            f"{artifact}: conference summary {conference_id} "
                            "people statement does not match the normalized role"
                        )
                    name = str(person.get("name", "")).strip().casefold()
                    allowed_statements = set()
                    for role in roles:
                        normalized_role = role.casefold()
                        allowed_statements.update(
                            {
                                f"{name} — {normalized_role}",
                                f"{name} - {normalized_role}",
                                f"{name} is listed as {normalized_role}",
                                f"{name} is listed as a {normalized_role}",
                                f"{name} is listed as a synthetic "
                                f"{normalized_role}",
                            }
                        )
                    if roles and normalized_plain not in allowed_statements:
                        self.errors.append(
                            f"{artifact}: conference summary {conference_id} "
                            "people statement contains unsupported role narrative"
                        )
            if claim == "attendance":
                recorded_numbers = {
                    int(value)
                    for value in re.findall(r"\b[0-9]+\b", plain)
                }
                number_values = {
                    "zero": 0,
                    "one": 1,
                    "two": 2,
                    "three": 3,
                    "four": 4,
                    "five": 5,
                    "six": 6,
                    "seven": 7,
                    "eight": 8,
                    "nine": 9,
                    "ten": 10,
                    "eleven": 11,
                    "twelve": 12,
                    "thirteen": 13,
                    "fourteen": 14,
                    "fifteen": 15,
                    "sixteen": 16,
                    "seventeen": 17,
                    "eighteen": 18,
                    "nineteen": 19,
                    "twenty": 20,
                    "thirty": 30,
                    "forty": 40,
                    "fifty": 50,
                    "sixty": 60,
                    "seventy": 70,
                    "eighty": 80,
                    "ninety": 90,
                }
                number_words = tuple(number_values) + ("hundred", "thousand")
                word_pattern = "|".join(number_words)
                for match in re.finditer(
                    rf"(?i)\b((?:(?:{word_pattern})(?:[\s-]+|$))+?)"
                    r"(?:people|attendees?|participants?)\b",
                    plain,
                ):
                    total = 0
                    current = 0
                    for word in re.findall(word_pattern, match.group(1).casefold()):
                        if word == "hundred":
                            current = max(current, 1) * 100
                        elif word == "thousand":
                            total += max(current, 1) * 1000
                            current = 0
                        else:
                            current += number_values[word]
                    recorded_numbers.add(total + current)
                expected_numbers = {
                    int(value)
                    for expected in expected_values
                    for value in re.findall(r"\b[0-9]+\b", expected)
                }
                if recorded_numbers - expected_numbers:
                    self.errors.append(
                        f"{artifact}: conference summary {conference_id} "
                        "attendance statement contains unsupported numeric values"
                    )
            embedded_claim_patterns = {
                "registration": r"\b(?:registration|tickets?|sold\s+out|price)\b",
                "venue": r"\b(?:venue|located\s+at)\b",
                "schedule": r"\b(?:schedule|sessions?|workshops?)\b",
                "sponsors": r"\b(?:sponsors?|exhibitors?|partners?)\b",
                "hotels": r"\b(?:hotels?|booking)\b",
            }
            for embedded_claim, pattern in embedded_claim_patterns.items():
                if (
                    embedded_claim != claim
                    and re.search(pattern, normalized_plain)
                    and not summary_values(conference, embedded_claim)
                ):
                    self.errors.append(
                        f"{artifact}: conference summary {conference_id} {claim} "
                        f"statement contains unsupported {embedded_claim} content"
                    )

        for conference_id in conference_ids:
            conference = conferences_by_id[conference_id]
            match = re.search(
                rf"(?ms)^###\s+{re.escape(conference_id)}(?:\s|$)(.*?)(?=^###\s+C[0-9]{{3,}}(?:\s|$)|^##\s+|\Z)",
                text,
            )
            if match:
                direct_citations = set(
                    re.findall(r"\[(S[0-9]{3,})\]", match.group(1))
                )
                if not direct_citations:
                    self.errors.append(
                        f"{artifact}: conference summary {conference_id} lacks a "
                        "direct source citation"
                    )
                for citation in direct_citations:
                    source = self.normalized_source_records.get(citation, {})
                    related_conferences = {
                        related.get("entity_id")
                        for related in source.get("related_entities", [])
                        if isinstance(related, dict)
                        and related.get("entity_type") == "conference"
                    }
                    if conference_id not in related_conferences:
                        self.errors.append(
                            f"{artifact}: source [{citation}] cited for conference "
                            f"{conference_id} does not declare that relationship"
                        )
                for line in match.group(1).splitlines():
                    stripped = line.strip()
                    if not stripped.startswith("-") or ":" not in stripped:
                        continue
                    label, statement = stripped[1:].split(":", 1)
                    claim = report_claim_for_label(label)
                    if "insufficient evidence" in statement.casefold():
                        continue
                    line_citations = set(
                        re.findall(r"\[(S[0-9]{3,})\]", statement)
                    )
                    if claim is None:
                        normalized_label = label.strip().casefold()
                        if normalized_label in {
                            "collection status",
                            "collection statuses",
                            "unresolved field",
                            "unresolved fields",
                        }:
                            continue
                        if not line_citations:
                            self.errors.append(
                                f"{artifact}: uncited material statement in "
                                f"conference summary {conference_id}: "
                                f"{label.strip()!r}"
                            )
                        continue
                    if not line_citations:
                        self.errors.append(
                            f"{artifact}: material {claim!r} claim in conference "
                            f"summary {conference_id} lacks a direct source citation"
                        )
                        continue
                    for citation in line_citations:
                        source_claims = set(
                            self.normalized_source_records.get(citation, {}).get(
                                "supported_fields_or_claims", []
                            )
                        )
                        if claim not in source_claims:
                            self.errors.append(
                                f"{artifact}: source [{citation}] does not declare "
                                f"support for report claim {claim!r} in "
                                f"conference summary {conference_id}"
                            )
                    expected_values = summary_values(conference, claim)
                    if not expected_values:
                        self.errors.append(
                            f"{artifact}: conference summary {conference_id} "
                            f"{claim} statement has no matching normalized data"
                        )
                    elif not statement_matches_values(statement, expected_values):
                        self.errors.append(
                            f"{artifact}: conference summary {conference_id} "
                            f"{claim} statement does not match normalized data"
                        )
                    else:
                        validate_statement_details(
                            conference_id,
                            conference,
                            claim,
                            statement,
                            expected_values,
                        )
        if conference_ids and not citations:
            self.errors.append(f"{artifact}: report contains no stable source citations")
        source_index = markdown_section_raw(text, "Source Index")
        if source_index is not None:
            header, rows = markdown_table(source_index)
            required_columns = (
                "Source ID",
                "Title or provider",
                "Source class",
                "Public URL",
                "Access date",
            )
            if any(column not in header for column in required_columns):
                self.errors.append(
                    f"{artifact}: Source Index is missing one or more required columns"
                )
            else:
                column_indexes = {
                    column: header.index(column) for column in required_columns
                }
                indexed_sources = {
                    row[column_indexes["Source ID"]]: row
                    for row in rows
                    if len(row) > max(column_indexes.values())
                }
                expected_source_ids = set(self.normalized_source_records)
                if set(indexed_sources) != expected_source_ids:
                    self.errors.append(
                        f"{artifact}: Source Index IDs do not match normalized "
                        "source records"
                    )
                for source_id, source in self.normalized_source_records.items():
                    row = indexed_sources.get(source_id)
                    if row is None:
                        continue
                    expected_values = {
                        "Title or provider": (
                            source.get("publisher_or_owner")
                            if source_id.startswith("A")
                            else source.get("title")
                        ),
                        "Source class": source.get("source_class"),
                        "Public URL": source.get("public_url"),
                        "Access date": source.get("access_date"),
                    }
                    for column, expected in expected_values.items():
                        recorded = row[column_indexes[column]]
                        if recorded != expected:
                            self.errors.append(
                                f"{artifact}: Source Index row {source_id} column "
                                f"{column!r} records {recorded!r}, expected "
                                f"{expected!r}"
                            )
        if (
            self.request.mode == "refresh"
            and markdown_section(text, "Refresh Changes") is None
        ):
            self.errors.append(
                f"{artifact}: refresh mode requires a nonempty 'Refresh Changes' "
                "section"
            )


def validate_run(run_dir: Path, stage: str = "complete") -> list[str]:
    return RunValidator(run_dir, stage).validate()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a Conference Discovery Harness run directory."
    )
    parser.add_argument("run_dir", type=Path, help="Path to one run directory")
    parser.add_argument(
        "--stage",
        choices=tuple(ARTIFACTS_BY_STAGE),
        default="complete",
        help="Validation boundary; defaults to complete",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    errors = validate_run(arguments.run_dir, arguments.stage)
    if errors:
        print(
            f"Validation failed for {arguments.run_dir} "
            f"at stage {arguments.stage}: {len(errors)} error(s)",
            file=sys.stderr,
        )
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print(f"Validation passed for {arguments.run_dir} at stage {arguments.stage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
