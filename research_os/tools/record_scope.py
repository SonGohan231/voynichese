"""Canonical record-universe policy for EXP-2026-001."""

from __future__ import annotations

import re
from typing import Any


CONTENT_ROLES = {"FOLIO", "UNRESOLVED"}


def is_manuscript_content(record: dict[str, Any]) -> bool:
    """Include every manuscript-content canvas, including compound/foldout parts."""
    source = record.get("source", {})
    role = source.get("logical_role")
    return role == "FOLIO" or (
        role == "UNRESOLVED"
        and bool(re.search(r"\d+", str(source.get("folio_or_cover_id", ""))))
    )
