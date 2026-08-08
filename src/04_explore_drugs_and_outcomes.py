"""Verify the NSAID -> GI-bleed story exists: top drugs + GI-bleed/ulcer conditions."""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eunomia.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)

    print("TOP 15 DRUGS (by number of patients):")
    print(f"{'drug_name':<48}{'concept_id':>12}{'patients':>10}")
    print("-" * 70)
    drugs = con.execute(
        """
        SELECT co.concept_name              AS drug_name,
               d.drug_concept_id            AS concept_id,
               COUNT(DISTINCT d.person_id)  AS patients
        FROM drug_exposure d
        JOIN concept co ON co.concept_id = d.drug_concept_id
        GROUP BY co.concept_name, d.drug_concept_id
        ORDER BY patients DESC
        LIMIT 15
        """
    ).fetchall()
    for name, cid, patients in drugs:
        print(f"{str(name)[:47]:<48}{cid:>12}{patients:>10,}")

    print("\nGI-BLEED / ULCER CONDITIONS present in the data:")
    print(f"{'condition_name':<48}{'concept_id':>12}{'patients':>10}")
    print("-" * 70)
    bleeds = con.execute(
        """
        SELECT co.concept_name              AS condition_name,
               c.condition_concept_id       AS concept_id,
               COUNT(DISTINCT c.person_id)  AS patients
        FROM condition_occurrence c
        JOIN concept co ON co.concept_id = c.condition_concept_id
        WHERE lower(co.concept_name) LIKE '%bleed%'
           OR lower(co.concept_name) LIKE '%ulcer%'
           OR lower(co.concept_name) LIKE '%hemorrhage%'
           OR lower(co.concept_name) LIKE '%melena%'
           OR lower(co.concept_name) LIKE '%hematemesis%'
        GROUP BY co.concept_name, c.condition_concept_id
        ORDER BY patients DESC
        """
    ).fetchall()
    for name, cid, patients in bleeds:
        print(f"{str(name)[:47]:<48}{cid:>12}{patients:>10,}")

    con.close()


if __name__ == "__main__":
    main()
