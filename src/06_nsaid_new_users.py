"""Phase 4 — build the NSAID new-user (incident-user) cohort and describe it."""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eunomia.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    # Code-list: every ibuprofen/naproxen product present (nonselective NSAIDs).
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW nsaid_drug AS
        SELECT DISTINCT d.drug_concept_id
        FROM drug_exposure d
        JOIN concept co ON co.concept_id = d.drug_concept_id
        WHERE lower(co.concept_name) LIKE '%ibuprofen%'
           OR lower(co.concept_name) LIKE '%naproxen%'
        """
    )

    # New-user cohort: each patient's FIRST NSAID exposure = index date.
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW nsaid_new_user AS
        SELECT person_id,
               MIN(CAST(drug_exposure_start_date AS DATE)) AS index_date
        FROM drug_exposure
        WHERE drug_concept_id IN (SELECT drug_concept_id FROM nsaid_drug)
        GROUP BY person_id
        """
    )

    size = con.execute("SELECT COUNT(*) FROM nsaid_new_user").fetchone()[0]
    total = con.execute("SELECT COUNT(*) FROM person").fetchone()[0]
    print(f"NSAID new-user cohort: {size:,} patients ({100 * size / total:.1f}% of {total:,})\n")

    mean_age, median_age = con.execute(
        """
        SELECT AVG(date_part('year', n.index_date) - p.year_of_birth),
               MEDIAN(date_part('year', n.index_date) - p.year_of_birth)
        FROM nsaid_new_user n
        JOIN person p ON p.person_id = n.person_id
        """
    ).fetchone()
    print(f"Age at first NSAID:  mean {mean_age:.1f}   median {median_age:.0f}\n")

    print("NSAID products in the code-list (by patients):")
    for name, cid, pts in con.execute(
        """
        SELECT co.concept_name, d.drug_concept_id, COUNT(DISTINCT d.person_id)
        FROM drug_exposure d
        JOIN concept co ON co.concept_id = d.drug_concept_id
        WHERE d.drug_concept_id IN (SELECT drug_concept_id FROM nsaid_drug)
        GROUP BY co.concept_name, d.drug_concept_id
        ORDER BY 3 DESC
        """
    ).fetchall():
        print(f"  {str(name)[:45]:<47}{cid:>10}{pts:>8,}")

    con.close()


if __name__ == "__main__":
    main()
