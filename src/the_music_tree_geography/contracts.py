"""Geographic evidence records; no processing dependencies required."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from shapely.geometry.base import BaseGeometry

Extent = Literal["full", "partial", "unknown"]


@dataclass(frozen=True)
class ReferenceGeometry:
    geometry: BaseGeometry
    complete: bool
    source: str
    boundary_kind: Literal["independent", "point", "succession", "display"]
    derived_from: frozenset[tuple[str, str]] = frozenset()
    start_year: int | None = None
    end_year: int | None = None
    uncertainty_m: float = 0


Decision = Literal["full", "partial", "unknown", "reject"]


@dataclass(frozen=True)
class SpatialEvidence:
    child_id: str
    parent_id: str
    source: str
    statement_id: str
    extent: Extent
    scoped: bool = False
    geometry_json: str | None = None


@dataclass(frozen=True)
class RelationDecision:
    child_id: str
    parent_id: str
    extent: Decision
    evidence: tuple[SpatialEvidence, ...]
    conflict: bool
    override_reason: str | None = None


@dataclass(frozen=True)
class PlaceStatement:
    child_id: str
    parent_id: str
    source: str
    statement_id: str
    scoped: bool
    start_year: int | None = None
    end_year: int | None = None
