# TheMusicTree geography

Python package of geographic evidence records and spatial/time processing extracted from the pipelines geohistory pipeline. Read `README.md` for ownership and compatibility rules.

- Setup and checks: `uv sync --extra processing`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`. Supported Python: 3.12 and 3.14.
- The base package must import without Django, Polars, NumPy or Shapely; only the `processing` extra may depend on them.
- Geographic relations are evidence, not musical membership: keep unknown dates null, preserve entity IDs, provenance and ranks, never infer containment from overlap or succession.
- Ingestion, credentials, scheduling and artifact paths belong to pipelines; do not add them here. Source data is not redistributed.
- Releases are manual: reviewed PR for `pyproject.toml` version and `CHANGELOG.md`, then an annotated `v<version>` tag (see README Distribution).
