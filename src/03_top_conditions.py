"""List the most common conditions in the Eunomia data, to choose a cohort."""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eunomia.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    rows = con.execute(
        """
        SELECT co.concept_name             AS condition_name,
               c.condition_concept_id      AS concept_id,
               COUNT(DISTINCT c.person_id) AS patients,
               COUNT(*)                    AS records
        FROM condition_occurrence c
        JOIN concept co ON co.concept_id = c.condition_concept_id
        GROUP BY co.concept_name, c.condition_concept_id
        ORDER BY patients DESC
        LIMIT 15
        """
    ).fetchall()
    con.close()

    print(f"{'condition_name':<42}{'concept_id':>12}{'patients':>10}{'records':>10}")
    print("-" * 74)
    for name, cid, patients, records in rows:
        print(f"{str(name)[:41]:<42}{cid:>12}{patients:>10,}{records:>10,}")


if __name__ == "__main__":
    main()
