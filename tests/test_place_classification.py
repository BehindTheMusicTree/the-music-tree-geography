import json

import polars as pl
import pytest

from the_music_tree_geography.place_classification import current_administrative_kinds


def statement(target, *, qualifiers=None, rank="normal"):
    return {
        "rank": rank,
        "mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": target}}},
        "qualifiers": qualifiers or {},
    }


def time(year, precision=9):
    return {
        "snaktype": "value",
        "datavalue": {
            "value": {
                "time": f"+{year}-00-00T00:00:00Z",
                "precision": precision,
                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
            }
        },
    }


def classify(statements, classes=None, *, current_admin=False, curated=False):
    claims = {
        "Q1": {"P31": statements},
        "Q2": {"P279": [statement("Q56061")]},
        "Q56061": {},
        "Q1620908": {"P279": [statement("Q56061")]},
        **(classes or {}),
    }
    metadata = pl.DataFrame(
        [{"resolved_id": item, "status": "found", "claims_json": json.dumps(values)} for item, values in claims.items()]
    )
    entities = pl.DataFrame({"entity_id": ["Q1"], "kind": ["historical_region"]})
    return current_administrative_kinds(
        entities,
        metadata,
        as_of_year=2026,
        curated_ids=frozenset({"Q1"}) if curated else frozenset(),
        current_administrative_ids=frozenset({"Q1"}) if current_admin else frozenset(),
    )["kind"].item()


def test_current_administration_replaces_expired_historical_type():
    assert (
        classify(
            [
                statement("Q1620908", qualifiers={"P582": [time(1983)]}),
                statement("Q2", qualifiers={"P580": [time(1983)]}),
            ]
        )
        == "admin_unit"
    )


@pytest.mark.parametrize(
    "qualifiers",
    [
        {"P582": [time(1983)]},
        {"P580": [time(2027)]},
        {"P580": [time(2026)]},
        {"P580": [time(1900, 7)]},
        {"P580": [{"snaktype": "somevalue"}]},
        {"P585": [time(2025)]},
        {"P518": [{"snaktype": "novalue"}]},
    ],
)
def test_uncertain_scoped_or_expired_administrative_type_does_not_reclassify(qualifiers):
    assert classify([statement("Q2", qualifiers=qualifiers)]) == "historical_region"


def test_historical_class_is_not_current_administration_even_if_it_has_admin_ancestors():
    assert classify([statement("Q1620908")]) == "historical_region"


def test_deprecated_or_nonpreferred_class_does_not_reclassify():
    assert classify([statement("Q2", rank="deprecated")]) == "historical_region"
    assert classify([statement("Q2"), statement("Q1620908", rank="preferred")]) == "historical_region"


def test_missing_class_fails_instead_of_guessing():
    with pytest.raises(ValueError, match="rerun Wikidata Bronze"):
        classify([statement("Q999")])


def test_subclass_cycles_terminate_and_expired_subclass_is_not_used():
    assert classify([statement("Q2")], {"Q2": {"P279": [statement("Q2")]}}) == "historical_region"
    assert (
        classify(
            [statement("Q2")],
            {"Q2": {"P279": [statement("Q56061", qualifiers={"P582": [time(1983)]})]}},
        )
        == "historical_region"
    )


@pytest.mark.parametrize("reverse", [False, True])
def test_undated_historical_class_blocks_administrative_reclassification(reverse):
    statements = [statement("Q1620908"), statement("Q2")]
    assert classify(statements[::-1] if reverse else statements) == "historical_region"


def test_current_city_is_not_reclassified_as_administrative_unit():
    assert classify([statement("Q2"), statement("Q515")], {"Q515": {}}, current_admin=True) == "city"


def test_classification_end_does_not_mean_entity_end():
    assert classify([statement("Q1620908", qualifiers={"P582": [time(1900)]}), statement("Q2")]) == "admin_unit"


def test_city_and_historical_class_need_current_administrative_evidence():
    statements = [statement("Q515"), statement("Q1620908"), statement("Q2")]
    assert classify(statements, {"Q515": {}}) == "historical_region"
    assert classify(statements, {"Q515": {}}, current_admin=True) == "city"


def test_historical_city_location_does_not_prove_current_municipality():
    assert classify([statement("Q515"), statement("Q1620908")], {"Q515": {}}, current_admin=True) == "historical_region"


def test_current_city_country_keeps_country_precedence():
    classes = {"Q515": {}, "Q6256": {"P279": [statement("Q56061")]}}
    assert classify([statement("Q515"), statement("Q6256")], classes, current_admin=True) == "country"


def test_curated_kind_is_not_rewritten():
    assert classify([statement("Q2")]) == "admin_unit"
    assert classify([statement("Q2")], curated=True) == "historical_region"
