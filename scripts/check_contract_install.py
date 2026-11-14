"""Run in a clean environment containing only the built base wheel."""

from dataclasses import FrozenInstanceError
from importlib.metadata import distribution
from importlib.util import find_spec

from the_music_tree_geography import PlaceStatement, RelationDecision, SpatialEvidence

package = distribution("the-music-tree-geography")
assert not any(requirement for requirement in package.requires or [] if "extra ==" not in requirement)
for name in ("polars", "numpy", "shapely", "django", "common", "geohistory", "wikidata"):
    assert find_spec(name) is None, f"unexpected base dependency: {name}"

statement = PlaceStatement("Q1", "Q2", "P131", "Q1$statement", False)
assert statement.start_year is None and statement.end_year is None
assert statement.child_id == "Q1"
evidence = SpatialEvidence(statement.child_id, statement.parent_id, statement.source, statement.statement_id, "unknown")
decision = RelationDecision("Q1", "Q2", "unknown", (evidence,), False)
assert decision.evidence[0].statement_id == "Q1$statement"
try:
    statement.parent_id = "Q3"
except FrozenInstanceError:
    pass
else:
    raise AssertionError("contracts must be immutable")
