"""RWE dashboard: NSAID utilization and GI-bleed safety on OMOP/Eunomia data."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
import analysis as A  # noqa: E402

st.set_page_config(page_title="RWE · NSAID & GI bleed", layout="wide")


@st.cache_resource
def get_con():
    return A.get_connection()


con = get_con()

st.title("Real-World Evidence — NSAID utilization & GI-bleed safety")
st.caption("OMOP CDM · OHDSI Eunomia synthetic data (~2,700 patients) · DuckDB")

drug_label = st.sidebar.selectbox("Exposure drug", list(A.DRUG_PRESETS))
subs = A.DRUG_PRESETS[drug_label]
st.sidebar.markdown("**Outcome:** GI bleed\n\n(peptic ulcer + GI hemorrhage)")

m = A.cohort_metrics(con, subs)
u = A.utilization(con, subs)
s = A.safety(con, subs)

k = st.columns(4)
k[0].metric("Cohort size", f"{m['size']:,}", f"{m['pct']:.1f}% of population")
k[1].metric("Mean age at start", f"{m['mean_age']:.0f}" if m["mean_age"] else "—")
k[2].metric("Median course", f"{u['median_days_supply']:.0f} days" if u["median_days_supply"] else "—")
k[3].metric("GI-bleed risk ratio", f"{s['rr']:.2f}" if s["rr"] == s["rr"] else "—")

left, right = st.columns(2)
with left:
    st.subheader("Sex")
    st.bar_chart(A.sex_breakdown(con, subs).set_index("sex"))
with right:
    st.subheader("Utilization")
    st.write(f"Prescriptions per patient — median **{u['median_rx']:.0f}**, mean **{u['mean_rx']:.1f}**")
    st.write(f"Single course length — median **{u['median_days_supply']:.0f}** days")

st.subheader("Top concomitant medications")
st.dataframe(A.concomitant(con, subs), use_container_width=True, hide_index=True)

st.subheader("Safety signal — GI bleed")
st.table(pd.DataFrame({
    "group": [f"{drug_label} users (after start)", "Non-users (ever)"],
    "with GI bleed": [s["exp_ev"], s["unexp_ev"]],
    "cohort size": [s["exp_n"], s["unexp_n"]],
    "risk %": [round(s["r_exp"], 1), round(s["r_unexp"], 1)],
}))
st.warning(
    "**Association, not causation.** This naive comparison is biased by an asymmetric "
    "follow-up window (exposed counted only after start; non-users over their whole record), "
    "selection bias, and confounding. A rigorous study needs a new-user / active-comparator "
    "design, matched follow-up, and confounder adjustment."
)
