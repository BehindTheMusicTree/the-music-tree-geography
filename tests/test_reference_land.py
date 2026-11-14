import shapely

from the_music_tree_geography.reference_land import IslandLandIndex


def test_island_component_requires_unique_interior_hit_and_identity():
    island = shapely.box(0, 0, 2, 2)
    land = shapely.MultiPolygon([island, shapely.box(3, 0, 4, 1)])
    point = shapely.Point(1, 1)
    index = IslandLandIndex(land)
    result = index.select(point, is_simple_island=True, verify_identity=lambda part: part.equals(island))
    assert result.equals(island)
    assert index.select(point, is_simple_island=True, verify_identity=lambda _: False) is None
    assert index.select(point, is_simple_island=False, verify_identity=lambda _: True) is None
    assert index.select(shapely.Point(2, 1), is_simple_island=True, verify_identity=lambda _: True) is None
    assert index.select(shapely.Point(2.5, 1), is_simple_island=True, verify_identity=lambda _: True) is None


def test_invalid_land_and_non_points_are_indeterminate():
    invalid = shapely.Polygon([(0, 0), (2, 2), (2, 0), (0, 2)])
    assert (
        IslandLandIndex(invalid).select(shapely.Point(1, 1), is_simple_island=True, verify_identity=lambda _: True)
        is None
    )
    assert (
        IslandLandIndex(shapely.box(0, 0, 2, 2)).select(
            shapely.LineString([(0, 0), (1, 1)]), is_simple_island=True, verify_identity=lambda _: True
        )
        is None
    )


def test_touching_components_and_antimeridian_require_verified_identity():
    touching = shapely.MultiPolygon([shapely.box(0, 0, 1, 1), shapely.box(1, 1, 2, 2)])
    assert (
        IslandLandIndex(touching).select(shapely.Point(1, 1), is_simple_island=True, verify_identity=lambda _: True)
        is None
    )

    east, west = shapely.box(179, 0, 180, 1), shapely.box(-180, 0, -179, 1)
    index = IslandLandIndex(shapely.MultiPolygon([east, west]))
    assert index.select(shapely.Point(179.5, 0.5), is_simple_island=True, verify_identity=lambda _: False) is None


def test_physical_qid_and_independent_coordinate_must_identify_same_land():
    import polars as pl

    from the_music_tree_geography.reference_land import reference_island_geometries

    island, neighbor = shapely.box(0, 0, 4, 4), shapely.box(10, 0, 14, 4)
    admin = pl.DataFrame({"level": [0], "geometry_wkb": [shapely.union_all([island, neighbor]).wkb]})
    physical = pl.DataFrame(
        {
            "wikidata_id": ["Q1", "Q2", "Q3"],
            "kind": ["Island", "Island", "Island group"],
            "geometry_wkb": [island.wkb, neighbor.wkb, island.wkb],
        }
    )
    crosswalk = pl.DataFrame({"wikidata_id": ["Q1", "Q2", "Q3"], "entity_id": ["one", "wrong", "group"]})
    entities = pl.DataFrame(
        {"entity_id": ["one", "wrong", "group"], "latitude": [2.0, 2.0, 2.0], "longitude": [2.0, 2.0, 2.0]}
    )
    result = reference_island_geometries(admin, physical, crosswalk, entities)
    assert set(result) == {"one"}
    assert shapely.equals(result["one"], island)


def test_composed_boundaries_keep_completeness_and_circular_dependencies():
    from the_music_tree_geography.place_relation_geometry import ReferenceGeometry, resolve_geometry
    from the_music_tree_geography.reference_land import composed_references

    first = ReferenceGeometry(shapely.box(0, 0, 1, 1), True, "admin", "independent")
    second = ReferenceGeometry(shapely.box(1, 0, 2, 1), True, "admin", "independent")
    members = {("a", "region"), ("b", "region"), ("region", "outer")}
    result = composed_references({"a": first, "b": second}, members, complete_entities=set())
    assert not result["region"].complete
    assert not result["outer"].complete
    assert result["outer"].derived_from == frozenset(members)
    assert resolve_geometry(first, result["region"], ("a", "region"), precision=0.001) == "unknown"
    result = composed_references({"a": first, "b": second}, members, complete_entities={"region", "outer"})
    assert result["outer"].complete
    assert shapely.equals(result["outer"].geometry, shapely.box(0, 0, 2, 1))
    assert composed_references({}, {("a", "b"), ("b", "a")}, complete_entities=set()) == {}


def test_antimeridian_components_cannot_certify_a_complete_island():
    from the_music_tree_geography.reference_land import IslandLandIndex

    land = shapely.MultiPolygon([shapely.box(179, 0, 180, 1), shapely.box(-180, 0, -179, 1)])
    index = IslandLandIndex(land)
    for longitude in (179.5, -179.5):
        assert (
            index.select(shapely.Point(longitude, 0.5), is_simple_island=True, verify_identity=lambda _: True) is None
        )


def test_reference_frames_map_admin_and_identify_island_without_artifact_paths():
    import polars as pl

    from the_music_tree_geography.reference_land import (
        reference_admin_geometries,
        reference_island_geometries,
        reference_land,
    )

    land = shapely.box(0, 0, 2, 2)
    admin = pl.DataFrame({"ne_id": ["ne1"], "level": [0], "geometry_wkb": [shapely.to_wkb(land)]})
    mapping = pl.DataFrame({"ne_id": ["ne1"], "entity_id": ["country"]})
    assert shapely.equals(reference_land(admin), land)
    assert shapely.equals(reference_admin_geometries(admin, mapping)["country"], land)
    physical = pl.DataFrame(
        {"kind": ["Island"], "wikidata_id": ["Q1"], "geometry_wkb": [shapely.to_wkb(shapely.box(0.5, 0.5, 1.5, 1.5))]}
    )
    crosswalk = pl.DataFrame({"wikidata_id": ["Q1"], "entity_id": ["island"]})
    entities = pl.DataFrame({"entity_id": ["island"], "latitude": [1.0], "longitude": [1.0]})
    assert shapely.equals(reference_island_geometries(admin, physical, crosswalk, entities)["island"], land)


def test_missing_reference_country_fails_instead_of_inventing_land():
    import polars as pl
    import pytest

    from the_music_tree_geography.reference_land import reference_land

    with pytest.raises(ValueError, match="no admin-0 country"):
        reference_land(pl.DataFrame(schema={"level": pl.Int64, "geometry_wkb": pl.Binary}))
