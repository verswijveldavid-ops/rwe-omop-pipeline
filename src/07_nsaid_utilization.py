"""Phase 4 — NSAID utilization: prescriptions per patient and treatment span (days)."""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eunomia.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW nsaid_exposure AS
        SELECT d.person_id,
               CAST(d.drug_exposure_start_date AS DATE) AS start_date,
               CAST(COALESCE(d.drug_exposure_end_date, d.drug_exposure_start_date) AS DATE) AS end_date
        FROM drug_exposure d
        JOIN concept co ON co.concept_id = d.drug_concept_id
        WHERE lower(co.concept_name) LIKE '%ibuprofen%'
           OR lower(co.concept_name) LIKE '%naproxen%'
        """
    )

    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW patient_util AS
        SELECT person_id,
               COUNT(*)                                        AS n_rx,
               date_diff('day', MIN(start_date), MAX(end_date)) AS span_days
        FROM nsaid_exposure
        GROUP BY person_id
        """
    )

    mean_rx, median_rx, max_rx = con.execute(
        "SELECT AVG(n_rx), MEDIAN(n_rx), MAX(n_rx) FROM patient_util"
    ).fetchone()
    print(f"NSAID prescriptions per patient:  mean {mean_rx:.1f}   median {median_rx:.0f}   max {max_rx}")

    lo, p25, med, p75, hi, mean = con.execute(
        """
        SELECT MIN(span_days), quantile_cont(span_days, 0.25), MEDIAN(span_days),
               quantile_cont(span_days, 0.75), MAX(span_days), AVG(span_days)
        FROM patient_util
        """
    ).fetchone()
    print("\nTreatment span (first dose -> last dose end), in days:")
    print(f"  min {lo:.0f}   p25 {p25:.0f}   median {med:.0f}   p75 {p75:.0f}   max {hi:.0f}   mean {mean:.1f}")

    con.close()


if __name__ == "__main__":
    main()
