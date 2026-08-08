# My Learning Log — RWE / OMOP Pipeline (Project 2)

> Plain record of **what I did and what it means** — no code. This is Project 2 (real-world evidence
> on OMOP data), completely separate from Project 1 (clinical-trial data). Claude handles the code; this
> is for me, to remember the journey and explain it in interviews.

---

## Phase 0 — Project setup
- (add your own words here after this step)


## Phase 1 — What OMOP is (no code)
- Learned what OMOP CDM is: a standardized structure for real-world health data (claims/EHR), the way SDTM is the standard for clinical-trial data. Two separate standards, each with its own governing body — CDISC for trials (pre-approval), OHDSI for OMOP (real-world, post-approval).
- The tables all link through one patient key, **person_id** — without it you couldn't tell which records belong to which person. A "cohort" is just a list of person_ids that meet a rule.
- Every disease/drug/test is stored as a number (**concept_id**), not text, so the meaning is identical across databases, languages and borders. You join to the CONCEPT dictionary to turn the number back into a readable name.
- **RWE** = using real-world data to answer safety/usage questions about a drug after it's on the market — what actually happens when millions of ordinary people take it, versus a controlled trial.
