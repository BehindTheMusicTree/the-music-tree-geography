# TheMusicTree geography

Geographic evidence and spatial processing extracted from the Apache-2.0
`BehindTheMusicTree/the-music-tree-pipelines` geohistory pipeline.

The base package exposes immutable evidence records without Django, Polars,
NumPy or Shapely. Install the `processing` extra for spatial resolution,
reference land processing, Wikidata statement classification and historical
time-span/succession transforms.

Geographic relationships are evidence, not musical membership. Unknown periods
remain unknown; conflicting evidence remains explicit. Succession, display
geometry and overlap alone do not prove containment. Entity IDs, provenance,
statement ranks and existing processing results are preserved.

Pipelines retains ingestion, credentials, scheduling, artifact paths, curated
inputs and musical interpretation. Generated datasets stay outside this repo.

## Ownership and compatibility

The processing modules preserve the geohistory algorithms, source names, ranks,
entity IDs, temporal precision and relation decisions from pipelines commit
`d382634`. Pipelines owns Bronze schemas, loading curated overrides, orchestration,
Parquet paths and musical interpretation. Callers pass frames and overrides into
`entity_time_span.resolve_time_spans` and `entity_succession.resolve_succession`;
these functions return frames without reading or writing artifacts. Unknown dates
stay null, and succession edges remain evidence rather than musical membership.

The recorded staging-anchor regression stays in pipelines because it validates
its Wikidata Bronze producer schema. Standalone processing tests here use local
synthetic inputs; neither pipelines nor Django is a runtime/test dependency.

Source data is not redistributed. Natural Earth, Glottolog, Cliopatria and
Wikidata keep their upstream licenses and attribution; processing records retain
source provenance. See [NOTICE](NOTICE) for the code's extraction provenance.

## Development

`uv sync --extra processing` then `uv run pytest` and `uv run ruff check .` /
`uv run ruff format --check .`. Python 3.12 and 3.14 are supported. CI builds the sdist and wheel, verifies
base-wheel imports in an environment with no processing dependencies, and runs
the processing suite against the installed wheel outside the source checkout.
`Lint` and `Tests success` are the required PR gates declared in github-config.

## Distribution

Version 0.1.0 is prepared but unpublished. Release publication and consumer
release pins require separate approval. Do not merge consumers until the package
is resolvable by their frozen install. No runtime service or database is added.
