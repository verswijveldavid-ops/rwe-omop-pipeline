"""Phase 4 — honest duration of a SINGLE NSAID prescription (days_supply vs start->end)."""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eunomia.duckdb"


def stats(con, expr, where):
    return con.execute(
        f"""
        SELECT MIN({expr}), quantile_cont({expr}, 0.25), MEDIAN({expr}),
               quantile_cont({expr}, 0.75), MAX({expr}), AVG({expr})
        FROM nsaid_rx WHERE {where}
        """
    ).fetchone()


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW nsaid_rx AS
        SELECT d.days_supply,
               date_diff('day', CAST(d.drug_exposure_start_date AS DATE),
                                CAST(d.drug_exposure_end_date AS DATE)) AS span_days
        FROM drug_exposure d
        JOIN concept co ON co.concept_id = d.drug_concept_id
        WHERE lower(co.concept_name) LIKE '%ibuprofen%'
           OR lower(co.concept_name) LIKE '%naproxen%'
        """
    )

    n_total, n_missing = con.execute(
        "SELECT COUNT(*), COUNT(*) FILTER (WHERE days_supply IS NULL OR days_supply = 0) FROM nsaid_rx"
    ).fetchone()
    print(f"NSAID prescriptions: {n_total:,}   (days_supply missing/zero: {n_missing:,})\n")

    labels = "  min {:.0f}   p25 {:.0f}   median {:.0f}   p75 {:.0f}   max {:.0f}   mean {:.1f}"

    print("Single prescription length via days_supply (days):")
    print(labels.format(*stats(con, "days_supply", "days_supply IS NOT NULL AND days_supply > 0")))

    print("\nSingle prescription length via start->end date span (days):")
    print(labels.format(*stats(con, "span_days", "span_days IS NOT NULL")))

    con.close()


if __name__ == "__main__":
    main()
