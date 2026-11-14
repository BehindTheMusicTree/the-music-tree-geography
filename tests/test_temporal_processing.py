import polars as pl

from the_music_tree_geography.entity_succession import resolve_succession
from the_music_tree_geography.entity_time_span import resolve_time_spans


def test_succession_preserves_identity_and_both_sources_without_self_or_unknown_edges():
    claims = pl.DataFrame(
        {
            "item_id": ["Q2", "Q1", "Q3", "Q3"],
            "property": ["P1365", "P1366", "P1365", "P1366"],
            "value": ["Q1", "Q2", "Q3", "Q99"],
        }
    )
    crosswalk = pl.DataFrame({"entity_id": ["place:1", "place:2", "place:3"], "wikidata_id": ["Q1", "Q2", "Q3"]})
    assert resolve_succession(claims, crosswalk).rows() == [("place:1", "place:2", "P1365,P1366")]
    assert resolve_succession(claims.clear(), crosswalk).is_empty()


def test_temporal_priorities_provenance_unknowns_and_curated_overrides():
    claims = pl.DataFrame(
        [
            ("Q1", "P571", "-3500-01-01T00:00:00Z", 7),
            ("Q1", "P580", "-4000-01-01T00:00:00Z", 9),
            ("Q1", "P576", "-1800-01-01T00:00:00Z", 7),
            ("Q2", "P2348", "Q20", None),
            ("Q20", "P580", "+0500-01-01T00:00:00Z", 8),
            ("Q20", "P582", "+0700-01-01T00:00:00Z", 8),
            ("Q3", "P580", "-2500000000-01-01T00:00:00Z", 1),
        ],
        schema={"item_id": pl.String, "property": pl.String, "value": pl.String, "time_precision": pl.Int8},
        orient="row",
    )
    entities = pl.DataFrame({"entity_id": ["Q1", "Q2", "Q3", "lang1"]})
    crosswalk = pl.DataFrame({"entity_id": ["Q1", "Q2", "Q3", "lang1"], "wikidata_id": ["Q1", "Q2", "Q3", "Q4"]})
    languoids = pl.DataFrame(
        {"glottocode": ["lang1"], "first_year_of_documentation": [1800], "last_year_of_documentation": [1900]}
    )
    overrides = pl.DataFrame({"entity_id": ["Q1"], "start_year": [None], "end_year": [-1700]})
    rows = {
        row["entity_id"]: row
        for row in resolve_time_spans(languoids, claims, entities, crosswalk, overrides).to_dicts()
    }
    assert (rows["Q1"]["start_year"], rows["Q1"]["start_source"], rows["Q1"]["start_precision"]) == (-3500, "P571", 7)
    assert (rows["Q1"]["end_year"], rows["Q1"]["end_source"], rows["Q1"]["end_precision"]) == (-1700, "curation", None)
    assert (rows["Q2"]["start_year"], rows["Q2"]["end_year"], rows["Q2"]["start_source"]) == (500, 700, "period")
    assert rows["Q3"]["start_year"] is None
    assert rows["Q3"]["end_year"] is None
    assert (rows["lang1"]["start_year"], rows["lang1"]["end_source"]) == (1800, "glottolog")
