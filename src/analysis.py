"""Reusable RWE analysis over the Eunomia DuckDB. Imported by the dashboard."""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eunomia.duckdb"
GI_BLEED = (4027663, 192671)  # peptic ulcer, GI hemorrhage

DRUG_PRESETS = {
    "Nonselective NSAIDs (ibuprofen + naproxen)": ["ibuprofen", "naproxen"],
    "Ibuprofen": ["ibuprofen"],
    "Naproxen": ["naproxen"],
    "Celecoxib (COX-2 selective)": ["celecoxib"],
    "Acetaminophen (non-NSAID reference)": ["acetaminophen"],
}


def get_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)


def _like(subs):
    return "(" + " OR ".join(f"lower(co.concept_name) LIKE '%{s}%'" for s in subs) + ")"


def _cohort_cte(subs):
    return f"""
        WITH cohort AS (
            SELECT d.person_id,
                   MIN(CAST(d.drug_exposure_start_date AS DATE)) AS index_date
            FROM drug_exposure d
            JOIN concept co ON co.concept_id = d.drug_concept_id
            WHERE {_like(subs)}
            GROUP BY d.person_id
        )
    """


def cohort_metrics(con, subs):
    cte = _cohort_cte(subs)
    size = con.execute(cte + "SELECT COUNT(*) FROM cohort").fetchone()[0]
    total = con.execute("SELECT COUNT(*) FROM person").fetchone()[0]
    mean_age, median_age = con.execute(
        cte + """
        SELECT AVG(date_part('year', c.index_date) - p.year_of_birth),
               MEDIAN(date_part('year', c.index_date) - p.year_of_birth)
        FROM cohort c JOIN person p ON p.person_id = c.person_id
        """
    ).fetchone()
    return {"size": size, "total": total,
            "pct": 100 * size / total if total else 0,
            "mean_age": mean_age, "median_age": median_age}


def sex_breakdown(con, subs):
    return con.execute(
        _cohort_cte(subs) + """
        SELECT g.concept_name AS sex, COUNT(*) AS patients
        FROM cohort c
        JOIN person p ON p.person_id = c.person_id
        JOIN concept g ON g.concept_id = p.gender_concept_id
        GROUP BY g.concept_name ORDER BY patients DESC
        """
    ).df()


def utilization(con, subs):
    like = _like(subs)
    med_days, mean_days = con.execute(
        f"""
        SELECT MEDIAN(days_supply), AVG(days_supply)
        FROM drug_exposure d JOIN concept co ON co.concept_id = d.drug_concept_id
        WHERE {like} AND days_supply IS NOT NULL AND days_supply > 0
        """
    ).fetchone()
    mean_rx, median_rx = con.execute(
        f"""
        SELECT AVG(n), MEDIAN(n) FROM (
            SELECT d.person_id, COUNT(*) AS n
            FROM drug_exposure d JOIN concept co ON co.concept_id = d.drug_concept_id
            WHERE {like} GROUP BY d.person_id
        )
        """
    ).fetchone()
    return {"median_days_supply": med_days, "mean_days_supply": mean_days,
            "mean_rx": mean_rx, "median_rx": median_rx}


def concomitant(con, subs):
    like = _like(subs)
    return con.execute(
        f"""
        WITH cohort AS (
            SELECT DISTINCT d.person_id
            FROM drug_exposure d JOIN concept co ON co.concept_id = d.drug_concept_id
            WHERE {like}
        )
        SELECT co.concept_name AS drug, COUNT(DISTINCT d.person_id) AS patients
        FROM drug_exposure d JOIN concept co ON co.concept_id = d.drug_concept_id
        WHERE d.person_id IN (SELECT person_id FROM cohort) AND NOT {like}
        GROUP BY co.concept_name ORDER BY patients DESC LIMIT 10
        """
    ).df()


def safety(con, subs, outcome=GI_BLEED):
    like = _like(subs)
    oc = ", ".join(str(x) for x in outcome)
    total = con.execute("SELECT COUNT(*) FROM person").fetchone()[0]
    exp_n = con.execute(
        f"""SELECT COUNT(DISTINCT d.person_id)
            FROM drug_exposure d JOIN concept co ON co.concept_id = d.drug_concept_id
            WHERE {like}"""
    ).fetchone()[0]
    unexp_n = total - exp_n
    exp_ev = con.execute(
        _cohort_cte(subs) + f"""
        SELECT COUNT(DISTINCT c.person_id)
        FROM cohort c JOIN condition_occurrence o ON o.person_id = c.person_id
        WHERE o.condition_concept_id IN ({oc})
          AND CAST(o.condition_start_date AS DATE) > c.index_date
        """
    ).fetchone()[0]
    unexp_ev = con.execute(
        f"""
        SELECT COUNT(DISTINCT person_id) FROM condition_occurrence
        WHERE condition_concept_id IN ({oc})
          AND person_id NOT IN (
            SELECT d.person_id FROM drug_exposure d
            JOIN concept co ON co.concept_id = d.drug_concept_id WHERE {like})
        """
    ).fetchone()[0]
    r_exp = exp_ev / exp_n if exp_n else 0
    r_unexp = unexp_ev / unexp_n if unexp_n else 0
    rr = r_exp / r_unexp if r_unexp else float("nan")
    return {"exp_n": exp_n, "exp_ev": exp_ev, "r_exp": 100 * r_exp,
            "unexp_n": unexp_n, "unexp_ev": unexp_ev, "r_unexp": 100 * r_unexp,
            "rr": rr}

_COMPARATIVE_QUERY = """
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

def age_distribution(con, subs):
    return con.execute(
        _cohort_cte(subs) + """
        SELECT date_part('year', c.index_date) - p.year_of_birth AS age
        FROM cohort c JOIN person p ON p.person_id = c.person_id
        WHERE date_part('year', c.index_date) - p.year_of_birth BETWEEN 0 AND 110
        """
    ).df()

def comparative_safety(con):
    import math
    import statsmodels.formula.api as smf

    df = con.execute(_COMPARATIVE_QUERY).df()
    df = df[df["prior_bleed"] == 0].copy()
    tab = df.groupby("grp")["outcome"].agg(["size", "sum"])
    groups = {}
    for grp in ("NSAID", "Acetaminophen"):
        n, ev = int(tab.loc[grp, "size"]), int(tab.loc[grp, "sum"])
        groups[grp] = {"n": n, "events": ev, "risk": 100 * ev / n}
    a, n1 = groups["NSAID"]["events"], groups["NSAID"]["n"]
    c, n0 = groups["Acetaminophen"]["events"], groups["Acetaminophen"]["n"]
    rr = (a / n1) / (c / n0)
    se = math.sqrt(1 / a - 1 / n1 + 1 / c - 1 / n0)
    rr_ci = (math.exp(math.log(rr) - 1.96 * se), math.exp(math.log(rr) + 1.96 * se))
    df["exposed"] = (df["grp"] == "NSAID").astype(int)
    df["female"] = (df["sex"] == "FEMALE").astype(int)
    model = smf.logit("outcome ~ exposed + age + female", data=df).fit(disp=False)
    or_adj = math.exp(model.params["exposed"])
    ci = model.conf_int().loc["exposed"]
    return {"groups": groups, "rr": rr, "rr_ci": rr_ci,
            "or_adj": or_adj, "or_ci": (math.exp(ci[0]), math.exp(ci[1]))}
