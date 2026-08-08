"""Phase 5.5 — comparative safety: NSAID new-users vs acetaminophen-only (active comparator)."""

import math
from pathlib import Path

import duckdb
import statsmodels.formula.api as smf

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eunomia.duckdb"

QUERY = """
WITH nsaid AS (
    SELECT d.person_id, MIN(CAST(d.drug_exposure_start_date AS DATE)) AS idx
    FROM drug_exposure d JOIN concept co ON co.concept_id = d.drug_concept_id
    WHERE lower(co.concept_name) LIKE '%ibuprofen%' OR lower(co.concept_name) LIKE '%naproxen%'
    GROUP BY d.person_id
),
acet AS (
    SELECT d.person_id, MIN(CAST(d.drug_exposure_start_date AS DATE)) AS idx
    FROM drug_exposure d JOIN concept co ON co.concept_id = d.drug_concept_id
    WHERE lower(co.concept_name) LIKE '%acetaminophen%'
    GROUP BY d.person_id
),
cohort AS (
    SELECT person_id, 'NSAID' AS grp, idx AS index_date FROM nsaid
    UNION ALL
    SELECT person_id, 'Acetaminophen' AS grp, idx AS index_date
    FROM acet WHERE person_id NOT IN (SELECT person_id FROM nsaid)
),
first_bleed AS (
    SELECT person_id, MIN(CAST(condition_start_date AS DATE)) AS bleed
    FROM condition_occurrence
    WHERE condition_concept_id IN (4027663, 192671)
    GROUP BY person_id
)
SELECT c.grp,
       date_part('year', c.index_date) - p.year_of_birth AS age,
       upper(g.concept_name) AS sex,
       CASE WHEN fb.bleed > c.index_date THEN 1 ELSE 0 END AS outcome,
       CASE WHEN fb.bleed <= c.index_date THEN 1 ELSE 0 END AS prior_bleed
FROM cohort c
JOIN person p ON p.person_id = c.person_id
JOIN concept g ON g.concept_id = p.gender_concept_id
LEFT JOIN first_bleed fb ON fb.person_id = c.person_id
"""


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(QUERY).df()
    con.close()

    df = df[df["prior_bleed"] == 0].copy()  # incident events only

    print("Active-comparator design (incident GI bleed after index):\n")
    tab = df.groupby("grp")["outcome"].agg(["size", "sum"])
    for grp in ["NSAID", "Acetaminophen"]:
        n, ev = int(tab.loc[grp, "size"]), int(tab.loc[grp, "sum"])
        print(f"  {grp:<14} n={n:,}  events={ev:,}  risk={100 * ev / n:.1f}%")

    a, n1 = int(tab.loc["NSAID", "sum"]), int(tab.loc["NSAID", "size"])
    c, n0 = int(tab.loc["Acetaminophen", "sum"]), int(tab.loc["Acetaminophen", "size"])
    rr = (a / n1) / (c / n0)
    if a > 0 and c > 0:
        se = math.sqrt(1 / a - 1 / n1 + 1 / c - 1 / n0)
        lo, hi = math.exp(math.log(rr) - 1.96 * se), math.exp(math.log(rr) + 1.96 * se)
        print(f"\n  Crude risk ratio = {rr:.2f}  (95% CI {lo:.2f}-{hi:.2f})")
    else:
        print(f"\n  Crude risk ratio = {rr:.2f}  (CI unstable: too few events)")

    df["exposed"] = (df["grp"] == "NSAID").astype(int)
    df["female"] = (df["sex"] == "FEMALE").astype(int)
    try:
        model = smf.logit("outcome ~ exposed + age + female", data=df).fit(disp=False)
        if model.mle_retvals.get("converged", False):
            or_adj = math.exp(model.params["exposed"])
            ci = model.conf_int().loc["exposed"]
            print(f"  Adjusted odds ratio (age+sex) = {or_adj:.2f}  "
                  f"(95% CI {math.exp(ci[0]):.2f}-{math.exp(ci[1]):.2f})")
        else:
            print("  Adjusted model did not converge (too few events).")
    except (OverflowError, ValueError) as exc:
        print(f"  Adjusted model unstable: {exc}")


if __name__ == "__main__":
    main()
