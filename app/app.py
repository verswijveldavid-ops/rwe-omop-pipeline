"""RWE dashboard: NSAID utilization & GI-bleed safety on OMOP/Eunomia data."""

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
import analysis as A  # noqa: E402

st.set_page_config(page_title="RWE · NSAID & GI bleed", page_icon="💊", layout="wide")

BLUE, ORANGE, MUTED = "#2a78d6", "#eb6834", "#898781"


@st.cache_resource
def get_con():
    return A.get_connection()


@st.cache_data
def load_safety():
    return A.comparative_safety(get_con())


con = get_con()

st.title("Real-World Evidence — NSAID utilization & GI-bleed safety")
st.caption("OMOP CDM · OHDSI Eunomia synthetic data (~2,700 patients) · DuckDB · statsmodels")

drug_label = st.sidebar.selectbox("Exposure drug (descriptive tabs)", list(A.DRUG_PRESETS))
subs = A.DRUG_PRESETS[drug_label]
st.sidebar.markdown("---")
st.sidebar.caption("The **Safety** tab is a fixed comparison: NSAID vs acetaminophen.")

m = A.cohort_metrics(con, subs)
u = A.utilization(con, subs)
cs = load_safety()

k = st.columns(4)
k[0].metric("Cohort size", f"{m['size']:,}", f"{m['pct']:.0f}% of population")
k[1].metric("Mean age at start", f"{m['mean_age']:.0f}" if m["mean_age"] else "—")
k[2].metric("Median course", f"{u['median_days_supply']:.0f} d" if u["median_days_supply"] else "—")
k[3].metric("Adjusted OR (GI bleed)", f"{cs['or_adj']:.2f}",
            f"CI {cs['or_ci'][0]:.2f}–{cs['or_ci'][1]:.2f}", delta_color="off")

tab_over, tab_util, tab_safety, tab_methods = st.tabs(
    ["Overview", "Utilization", "Safety signal", "Methods & data"]
)

with tab_over:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Sex")
        st.altair_chart(
            alt.Chart(A.sex_breakdown(con, subs)).mark_bar(color=BLUE, cornerRadiusEnd=4, size=40).encode(
                x=alt.X("patients:Q", title="patients"),
                y=alt.Y("sex:N", title=None),
                tooltip=["sex", "patients"],
            ).properties(height=160),
            use_container_width=True,
        )
    with c2:
        st.subheader("Age at first exposure")
        st.altair_chart(
            alt.Chart(A.age_distribution(con, subs)).mark_bar(color=BLUE).encode(
                x=alt.X("age:Q", bin=alt.Bin(maxbins=30), title="age (years)"),
                y=alt.Y("count()", title="patients"),
                tooltip=[alt.Tooltip("count()", title="patients")],
            ).properties(height=160),
            use_container_width=True,
        )

with tab_util:
    st.subheader(f"How {drug_label} is used")
    a, b, c = st.columns(3)
    a.metric("Median Rx / patient", f"{u['median_rx']:.0f}")
    b.metric("Mean Rx / patient", f"{u['mean_rx']:.1f}")
    c.metric("Median course length", f"{u['median_days_supply']:.0f} days")
    st.subheader("Top concomitant medications")
    st.altair_chart(
        alt.Chart(A.concomitant(con, subs)).mark_bar(color=BLUE, cornerRadiusEnd=4).encode(
            x=alt.X("patients:Q", title="patients"),
            y=alt.Y("drug:N", sort="-x", title=None),
            tooltip=["drug", "patients"],
        ).properties(height=320),
        use_container_width=True,
    )

with tab_safety:
    st.subheader("Do NSAID users get more GI bleeds than acetaminophen users?")
    g = cs["groups"]
    risk_df = pd.DataFrame([
        {"group": "NSAID", "risk": g["NSAID"]["risk"], "events": g["NSAID"]["events"], "n": g["NSAID"]["n"]},
        {"group": "Acetaminophen", "risk": g["Acetaminophen"]["risk"],
         "events": g["Acetaminophen"]["events"], "n": g["Acetaminophen"]["n"]},
    ])
    order = ["Crude RR", "Adjusted OR (age+sex)"]
    fp = pd.DataFrame([
        {"measure": "Crude RR", "est": cs["rr"], "lo": cs["rr_ci"][0], "hi": cs["rr_ci"][1]},
        {"measure": "Adjusted OR (age+sex)", "est": cs["or_adj"], "lo": cs["or_ci"][0], "hi": cs["or_ci"][1]},
    ])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Incident GI-bleed risk by group**")
        st.altair_chart(
            alt.Chart(risk_df).mark_bar(cornerRadiusEnd=4, size=48).encode(
                x=alt.X("group:N", title=None),
                y=alt.Y("risk:Q", title="risk (%)"),
                color=alt.Color("group:N", legend=None,
                                scale=alt.Scale(domain=["NSAID", "Acetaminophen"], range=[BLUE, ORANGE])),
                tooltip=["group", alt.Tooltip("risk:Q", format=".1f"), "events", "n"],
            ).properties(height=280),
            use_container_width=True,
        )
    with c2:
        st.markdown("**Effect estimate — crude vs adjusted**")
        null_line = alt.Chart(pd.DataFrame({"x": [1]})).mark_rule(color=MUTED, strokeDash=[4, 4]).encode(x="x:Q")
        ci_bar = alt.Chart(fp).mark_rule(size=3, color=BLUE).encode(
            x=alt.X("lo:Q", scale=alt.Scale(type="log"), title="ratio (log) — 1 = no effect"),
            x2="hi:Q", y=alt.Y("measure:N", sort=order, title=None))
        pts = alt.Chart(fp).mark_point(size=140, filled=True, color=BLUE).encode(
            x="est:Q", y=alt.Y("measure:N", sort=order, title=None),
            tooltip=[alt.Tooltip("est:Q", format=".2f", title="estimate"),
                     alt.Tooltip("lo:Q", format=".2f", title="CI low"),
                     alt.Tooltip("hi:Q", format=".2f", title="CI high")])
        st.altair_chart((null_line + ci_bar + pts).properties(height=280), use_container_width=True)
    st.success(
        f"**Headline:** the crude risk ratio ({cs['rr']:.2f}) makes NSAIDs look protective — but after "
        f"adjusting for age and sex the odds ratio is {cs['or_adj']:.2f} "
        f"(95% CI {cs['or_ci'][0]:.2f}–{cs['or_ci'][1]:.2f}), crossing 1. The apparent effect was **confounding**."
    )
    st.warning(
        "Association, not causation. Residual confounding remains (no adjustment for aspirin co-use, "
        "comorbidity, or health-seeking behaviour); follow-up is not matched on person-time; data is synthetic. "
        "A production study would use propensity-score matching and person-time incidence rates."
    )

with tab_methods:
    st.markdown("""
### Data
**OHDSI Eunomia** (GiBleed), ~2,700 synthetic patients in the **OMOP Common Data Model** (v5.3),
loaded into **DuckDB**. Synthetic — no privacy constraints; distributions are not real epidemiology.

### Design
- **Cohorts** from concept-id code-lists (drugs: ibuprofen/naproxen/…; outcome: peptic ulcer + GI hemorrhage).
- **New-user** design (first exposure = index date).
- **Safety:** new-user **active-comparator** (NSAID vs acetaminophen-only), incident GI bleed after index,
  prevalent cases excluded, **age/sex-adjusted** logistic regression with 95% CIs.

### Key limitations
- Synthetic data likely encodes no true NSAID→bleed effect — numbers validate the *method*, not clinical reality.
- Residual confounding; unmatched follow-up time; single database.

### Stack
Python · DuckDB · pandas · statsmodels · Streamlit · Altair.
""")
