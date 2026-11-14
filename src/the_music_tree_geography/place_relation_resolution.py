"""Consolidate spatial evidence before choosing a containment source."""

import json
from collections import defaultdict
from functools import lru_cache

import shapely

from the_music_tree_geography.place_relation_geometry import Extent, ReferenceGeometry, resolve_geometry

from .contracts import Decision, PlaceStatement, RelationDecision, SpatialEvidence


def resolve_relations(
    evidence: list[SpatialEvidence], overrides: dict[tuple[str, str], tuple[Decision, str]]
) -> list[RelationDecision]:
    """Resolve each pair without letting source priority erase contradictory evidence."""
    groups: dict[tuple[str, str], set[SpatialEvidence]] = defaultdict(set)
    for item in evidence:
        if not item.child_id or not item.parent_id or item.child_id == item.parent_id:
            raise ValueError("spatial evidence requires two distinct entity ids")
        if not item.source or not item.statement_id or item.extent not in {"full", "partial", "unknown"}:
            raise ValueError("invalid spatial evidence")
        groups[(item.child_id, item.parent_id)].add(item)
    for pair, (extent, override_reason) in overrides.items():
        if (
            not all(pair)
            or pair[0] == pair[1]
            or extent not in {"full", "partial", "reject"}
            or not override_reason.strip()
        ):
            raise ValueError(f"invalid place relation override: {pair}")
        groups.setdefault(pair, set())

    decisions = []
    for (child, parent), items in sorted(groups.items()):
        ordered = tuple(
            sorted(
                items,
                key=lambda item: (item.source, item.statement_id, item.extent, item.scoped, item.geometry_json or ""),
            )
        )
        proven = {item.extent for item in ordered if item.extent != "unknown"}
        conflict = len(proven) > 1
        reason: str | None
        if (child, parent) in overrides:
            extent, reason = overrides[(child, parent)]
        else:
            extent = next(iter(proven)) if len(proven) == 1 else "unknown"
            reason = None
        decisions.append(RelationDecision(child, parent, extent, ordered, conflict, reason))
    return decisions


def resolve_statement_evidence(
    statements: list[PlaceStatement],
    references: dict[str, ReferenceGeometry],
    *,
    precision: float,
) -> list[SpatialEvidence]:
    """Resolve subject boundaries, never the unrestricted boundary of a P518 part."""
    result = []
    for statement in statements:
        child = references.get(statement.child_id)
        parent = references.get(statement.parent_id)
        extent: Extent = "unknown"
        if child is not None and parent is not None:
            extent = resolve_geometry(
                child,
                parent,
                (statement.child_id, statement.parent_id),
                precision=precision,
                start_year=statement.start_year,
                end_year=statement.end_year,
            )
        geometry_json = _geometry_details(child, parent, extent) if child is not None and parent is not None else None
        result.append(
            SpatialEvidence(
                statement.child_id,
                statement.parent_id,
                statement.source,
                statement.statement_id,
                extent,
                statement.scoped,
                geometry_json,
            )
        )
    return result


@lru_cache(maxsize=2048)
def _geometry_details(child: ReferenceGeometry, parent: ReferenceGeometry, extent: Extent) -> str:
    outside = shapely.difference(shapely.make_valid(child.geometry), shapely.make_valid(parent.geometry))
    return json.dumps(
        {
            "extent": extent,
            "uncertainty_m": child.uncertainty_m + parent.uncertainty_m,
            "outside_area_degrees2": outside.area,
            "outside_fraction": outside.area / child.geometry.area if child.geometry.area else None,
            "outside_components": len(shapely.get_parts(outside)),
            "child_complete": child.complete,
            "parent_complete": parent.complete,
            "child_period": [child.start_year, child.end_year],
            "parent_period": [parent.start_year, parent.end_year],
        },
        sort_keys=True,
    )
