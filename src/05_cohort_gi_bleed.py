"""Phase 3 — build & describe the GI-bleed cohort (peptic ulcer + GI hemorrhage)."""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eunomia.duckdb"

# GI-bleed phenotype = a curated list of condition concept_ids:
#   4027663 = Peptic ulcer, 192671 = Gastrointestinal hemorrhage
GI_BLEED_CONCEPTS = (4027663, 192671)


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    # Cohort = each patient's FIRST GI-bleed date (their 'index date').
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW cohort AS
        SELECT person_id,
               MIN(CAST(condition_start_date AS DATE)) AS index_date
        FROM condition_occurrence
        WHERE condition_concept_id IN (4027663, 192671)
        GROUP BY person_id
        """
    )

    size = con.execute("SELECT COUNT(*) FROM cohort").fetchone()[0]
    total = con.execute("SELECT COUNT(*) FROM person").fetchone()[0]
    print(f"GI-bleed cohort: {size:,} patients ({100 * size / total:.1f}% of {total:,})\n")

    mean_age, median_age = con.execute(
        """
        SELECT AVG(date_part('year', c.index_date) - p.year_of_birth),
               MEDIAN(date_part('year', c.index_date) - p.year_of_birth)
        FROM cohort c
        JOIN person p ON p.person_id = c.person_id
        """
    ).fetchone()
    print(f"Age at first GI bleed:  mean {mean_age:.1f}   median {median_age:.0f}\n")

    print("Sex breakdown:")
    for sex, n in con.execute(
        """
        SELECT g.concept_name AS sex, COUNT(*) AS n
        FROM cohort c
        JOIN person p ON p.person_id = c.person_id
        JOIN concept g ON g.concept_id = p.gender_concept_id
        GROUP BY g.concept_name
        ORDER BY n DESC
        """
    ).fetchall():
        print(f"  {sex:<10} {n:>6,}  ({100 * n / size:.1f}%)")

    con.close()


if __name__ == "__main__":
    main()
