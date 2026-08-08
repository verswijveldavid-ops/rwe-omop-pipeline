"""Phase 5 — safety signal: GI-bleed risk in NSAID users (after start) vs non-users."""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eunomia.duckdb"
GI = "(4027663, 192671)"  # peptic ulcer, GI hemorrhage


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW nsaid_cohort AS
        SELECT d.person_id, MIN(CAST(d.drug_exposure_start_date AS DATE)) AS index_date
        FROM drug_exposure d
        JOIN concept co ON co.concept_id = d.drug_concept_id
        WHERE lower(co.concept_name) LIKE '%ibuprofen%'
           OR lower(co.concept_name) LIKE '%naproxen%'
        GROUP BY d.person_id
        """
    )

    total = con.execute("SELECT COUNT(*) FROM person").fetchone()[0]
    exp_n = con.execute("SELECT COUNT(*) FROM nsaid_cohort").fetchone()[0]
    unexp_n = total - exp_n

    exp_ev = con.execute(
        f"""
        SELECT COUNT(DISTINCT c.person_id)
        FROM nsaid_cohort c
        JOIN condition_occurrence co ON co.person_id = c.person_id
        WHERE co.condition_concept_id IN {GI}
          AND CAST(co.condition_start_date AS DATE) > c.index_date
        """
    ).fetchone()[0]

    unexp_ev = con.execute(
        f"""
        SELECT COUNT(DISTINCT person_id)
        FROM condition_occurrence
        WHERE condition_concept_id IN {GI}
          AND person_id NOT IN (SELECT person_id FROM nsaid_cohort)
        """
    ).fetchone()[0]

    r_exp, r_unexp = exp_ev / exp_n, unexp_ev / unexp_n
    rr = r_exp / r_unexp if r_unexp else float("nan")

    print("GI-bleed risk:")
    print(f"  NSAID users (bleed AFTER start): {exp_ev:>4,} / {exp_n:,} = {100 * r_exp:.1f}%")
    print(f"  Non-users (bleed ever):          {unexp_ev:>4,} / {unexp_n:,} = {100 * r_unexp:.1f}%")
    print(f"\n  Risk ratio (RR) = {rr:.2f}")


if __name__ == "__main__":
    main()
