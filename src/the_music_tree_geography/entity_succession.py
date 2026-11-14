import polars as pl


def resolve_succession(claims: pl.DataFrame, crosswalk: pl.DataFrame) -> pl.DataFrame:
    succession = (
        claims.filter(pl.col("property").is_in(["P1365", "P1366"]))
        .select(
            pl.when(pl.col("property") == "P1365")
            .then(pl.col("value"))
            .otherwise(pl.col("item_id"))
            .alias("predecessor_item"),
            pl.when(pl.col("property") == "P1365")
            .then(pl.col("item_id"))
            .otherwise(pl.col("value"))
            .alias("successor_item"),
            pl.col("property").alias("source"),
        )
        .join(
            crosswalk.rename({"entity_id": "predecessor_id", "wikidata_id": "predecessor_item"}),
            on="predecessor_item",
        )
        .join(
            crosswalk.rename({"entity_id": "successor_id", "wikidata_id": "successor_item"}),
            on="successor_item",
        )
        .filter(pl.col("predecessor_id") != pl.col("successor_id"))
        .group_by("predecessor_id", "successor_id")
        .agg(pl.col("source").unique().sort().str.join(","))
        .sort("predecessor_id", "successor_id")
    )

    return succession
