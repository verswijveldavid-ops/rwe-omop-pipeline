"""Phase 4 — NSAID switching: % who move ibuprofen<->naproxen within 12 months of start."""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eunomia.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    # Every NSAID exposure tagged with its ingredient.
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW nsaid_ing AS
        SELECT d.person_id,
               CAST(d.drug_exposure_start_date AS DATE) AS start_date,
               CASE WHEN lower(co.concept_name) LIKE '%ibuprofen%' THEN 'ibuprofen'
                    WHEN lower(co.concept_name) LIKE '%naproxen%'  THEN 'naproxen' END AS ingredient
        FROM drug_exposure d
        JOIN concept co ON co.concept_id = d.drug_concept_id
        WHERE lower(co.concept_name) LIKE '%ibuprofen%'
           OR lower(co.concept_name) LIKE '%naproxen%'
        """
    )

    # Each patient's starting ingredient and index date.
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW first_ing AS
        SELECT person_id,
               arg_min(ingredient, start_date) AS index_ingredient,
               MIN(start_date)                 AS index_date
        FROM nsaid_ing
        GROUP BY person_id
        """
    )

    size = con.execute("SELECT COUNT(*) FROM first_ing").fetchone()[0]
    switched = con.execute(
        """
        SELECT COUNT(DISTINCT f.person_id)
        FROM first_ing f
        JOIN nsaid_ing n ON n.person_id = f.person_id
        WHERE n.ingredient <> f.index_ingredient
          AND n.start_date >  f.index_date
          AND n.start_date <= f.index_date + INTERVAL 365 DAY
        """
    ).fetchone()[0]

    print(f"NSAID new-users: {size:,}")
    print(f"Switched ingredient within 12 months: {switched:,} ({100 * switched / size:.1f}%)")

    print("\nStarting ingredient breakdown:")
    for ing, n in con.execute(
        "SELECT index_ingredient, COUNT(*) FROM first_ing GROUP BY index_ingredient ORDER BY 2 DESC"
    ).fetchall():
        print(f"  {ing:<12}{n:>7,}  ({100 * n / size:.1f}%)")

    con.close()


if __name__ == "__main__":
    main()
