"""Compare independent reference boundaries without promoting overlaps to containment."""

from math import cos, isfinite, radians
from functools import lru_cache

import numpy as np
import shapely
from shapely.geometry.base import BaseGeometry

from .contracts import Extent, ReferenceGeometry


@lru_cache(maxsize=512)
def _normalized_geometry(geometry: BaseGeometry, precision: float) -> BaseGeometry:
    return shapely.set_precision(shapely.make_valid(geometry), precision)


@lru_cache(maxsize=2048)
def resolve_geometry(
    child: ReferenceGeometry,
    parent: ReferenceGeometry,
    pair: tuple[str, str],
    *,
    precision: float,
    start_year: int | None = None,
    end_year: int | None = None,
) -> Extent:
    """Return only conclusions supported by independent boundaries.

    ``precision`` is the coordinate grid of the source, in its CRS units. A point-derived
    footprint must never be supplied as a reference boundary. A complete child covered by
    a known subset of its parent is fully contained, but an incomplete parent cannot prove
    that any part of the child lies outside it.
    """
    if not isfinite(precision) or precision <= 0:
        raise ValueError("precision must be finite and positive")
    if start_year is not None and end_year is not None and start_year > end_year:
        raise ValueError("relation start year must not exceed end year")
    for reference in (child, parent):
        if not isfinite(reference.uncertainty_m) or reference.uncertainty_m < 0:
            raise ValueError("boundary uncertainty must be finite and nonnegative")
        if (
            reference.start_year is not None
            and reference.end_year is not None
            and reference.start_year > reference.end_year
        ):
            raise ValueError("reference start year must not exceed end year")
    if child.boundary_kind != "independent" or parent.boundary_kind != "independent":
        return "unknown"
    if pair in child.derived_from or pair in parent.derived_from:
        return "unknown"
    if not child.complete:
        return "unknown"
    for reference in (child, parent):
        if (reference.start_year is not None or reference.end_year is not None) and (
            start_year is None or end_year is None
        ):
            return "unknown"
        if start_year is not None and (reference.start_year is None or reference.start_year > start_year):
            return "unknown"
        if end_year is not None and (reference.end_year is None or reference.end_year < end_year):
            return "unknown"
    child_geom = _normalized_geometry(child.geometry, precision)
    parent_geom = _normalized_geometry(parent.geometry, precision)
    if child_geom.is_empty or parent_geom.is_empty or child_geom.area == 0 or parent_geom.area == 0:
        return "unknown"
    if shapely.covers(parent_geom, child_geom):
        return "full"
    overlap = shapely.intersection(child_geom, parent_geom).area
    if overlap > 0:
        # Independently rounded borders can disagree within one source coordinate grid.
        # Clip before buffering to avoid offsetting an entire country's detailed coast.
        west, south, east, north = child_geom.bounds
        nearby_parent = shapely.make_valid(
            shapely.clip_by_rect(
                parent_geom, west - precision * 2, south - precision * 2, east + precision * 2, north + precision * 2
            )
        )
        if shapely.covers(shapely.buffer(nearby_parent, precision), child_geom):
            return "full"
    uncertainty_m = child.uncertainty_m + parent.uncertainty_m
    if overlap > 0 and uncertainty_m and _within_uncertainty(child_geom, parent_geom, uncertainty_m):
        return "unknown"
    if parent.complete and overlap > 0 and shapely.difference(child_geom, parent_geom).area > 0:
        return "partial"
    return "unknown"


def _within_uncertainty(child: BaseGeometry, parent: BaseGeometry, distance_m: float) -> bool:
    for component in shapely.get_parts(child):
        west, south, east, north = component.bounds
        # Keep the local metric approximation away from poles, the seam and large spans.
        if east - west > 10 or north - south > 10 or max(abs(south), abs(north)) > 75:
            return False
        nearby = shapely.make_valid(shapely.clip_by_rect(parent, west - 1, south - 1, east + 1, north + 1))
        if nearby.is_empty or shapely.intersection(component, nearby).area == 0:
            return False
        latitude = (south + north) / 2
        scale = np.array([111195 * cos(radians(latitude)), 111195])
        origin = np.array([west, south])

        def transform(coordinates):
            return (coordinates - origin) * scale

        projected_parent = shapely.transform(nearby, transform)
        projected_child = shapely.transform(component, transform)
        if not shapely.covers(shapely.buffer(projected_parent, distance_m), projected_child):
            return False
    return True
