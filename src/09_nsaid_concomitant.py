"""Phase 4 — concomitant medications in the NSAID new-user cohort (+ PPI gastroprotection)."""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eunomia.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

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
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW nsaid_cohort AS
        SELECT DISTINCT person_id FROM drug_exposure
        WHERE drug_concept_id IN (SELECT drug_concept_id FROM nsaid_drug)
        """
    )

    size = con.execute("SELECT COUNT(*) FROM nsaid_cohort").fetchone()[0]

    print("Top 10 concomitant drugs (other than the NSAIDs), by patients:")
    for name, pts in con.execute(
        """
        SELECT co.concept_name, COUNT(DISTINCT d.person_id) AS patients
        FROM drug_exposure d
        JOIN concept co ON co.concept_id = d.drug_concept_id
        WHERE d.person_id IN (SELECT person_id FROM nsaid_cohort)
          AND d.drug_concept_id NOT IN (SELECT drug_concept_id FROM nsaid_drug)
        GROUP BY co.concept_name
        ORDER BY patients DESC
        LIMIT 10
        """
    ).fetchall():
        print(f"  {str(name)[:50]:<52}{pts:>7,}  ({100 * pts / size:.1f}%)")

    ppi = con.execute(
        """
        SELECT COUNT(DISTINCT d.person_id)
        FROM drug_exposure d
        JOIN concept co ON co.concept_id = d.drug_concept_id
        WHERE d.person_id IN (SELECT person_id FROM nsaid_cohort)
          AND lower(co.concept_name) LIKE '%prazole%'
        """
    ).fetchone()[0]
    print(f"\nGastroprotection: {ppi:,} of {size:,} NSAID users ({100 * ppi / size:.1f}%) also received a PPI.")

    con.close()


if __name__ == "__main__":
    main()
