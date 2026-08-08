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

## Phase 2 — Got the data + loaded it into DuckDB
- Downloaded the OHDSI **Eunomia "GiBleed"** dataset — ~2,700 synthetic patients, already in OMOP format — as 37 CSV files (one per OMOP table), using a reproducible Python script.
- Loaded all 37 into a single **DuckDB** database file (`eunomia.duckdb`). DuckDB = a fast, single-file analytics database; loading turns 37 loose text files into one queryable database.
- First look inside — row counts: PERSON 2,694, CONDITION_OCCURRENCE 65,332, DRUG_EXPOSURE 67,707, MEASUREMENT 44,053. Two things to remember: **DEATH is empty (0 rows)** and **VISIT_OCCURRENCE is sparse (1,037)** — so this dataset's real strength is conditions + drugs, which is exactly what our cohort/utilization/safety work needs.
- Lesson: the first job with any real-world dataset is checking which tables actually have data before designing an analysis.

## Phase 3 — First cohort (the GI-bleed cohort)
- Learned what a **cohort** is: a group of patients defined by a rule — the fundamental unit of real-world evidence. You can't study "everyone"; you study a defined group.
- Explored the data first instead of assuming: no hypertension here; it's Synthea primary-care data built around **GI bleeding** ("GiBleed"). Locked the project on the classic real-world signal: **NSAID painkillers → GI bleeds**. Verified both halves exist (NSAIDs: ibuprofen/naproxen/aspirin/celecoxib; outcomes: peptic ulcer + GI hemorrhage).
- Built my first cohort — patients with a GI bleed — using a **code-list (phenotype)** of concept_ids, and each patient's **index date** (first bleed). Result: **1,015 patients (37.7%)**, sex ~50/50, mean age ~31.
- Key judgment: mean age 31 is unrealistically young for GI bleeds (real world = 60s–70s) — a synthetic-data artifact. Lesson: the data validates my *method*, but the *numbers* aren't real epidemiology. Never confuse the two.

## Phase 4 — Drug utilization (the NSAID exposure cohort)
- Built the **NSAID new-user cohort** (first-ever ibuprofen/naproxen exposure) = 1,896 patients (70%). Learned the core vocabulary: **new-user (incident-user) design** (start everyone at their first dose to avoid "survivor" bias), **index date** (time zero), and **washout / look-back window**.
- Defined the drug cohort with a **code-list built from the data** (name search), which caught extra products (Ibuprofen 100mg, Naproxen 500mg) a top-15 list would have missed. Lesson: build cohorts from code-lists, not eyeballed lists.
- Measured treatment duration and hit a key lesson: my first metric (first dose -> last dose) gave a nonsense 45-year max because it counted gaps. Fixed it with **days_supply** -> a sane median ~21-day course. Two independent measures agreed = a good cross-check. "Median plausible, tail absurd" is how you catch a broken metric.
- Concomitant meds: mostly primary-care background (vaccines, acetaminophen) — real concomitancy needs a time window. But spotted a real signal: 70% also on aspirin, 68% on celecoxib (other GI-risk drugs). Switching was rare (0.5%). Ibuprofen was first-line (70%).

## Phase 5 — Safety signal (and why it was misleading)
- Asked the real question: do NSAID users get GI bleeds more than non-users? Naive result: NSAID users 16.4% vs non-users 40.1%, **RR 0.41** — i.e. NSAIDs look *protective*. That's the OPPOSITE of known truth (NSAIDs cause bleeds), so the analysis is wrong, not the medicine.
- Diagnosed three causes: (1) **asymmetric follow-up window** (exposed counted only after start, non-users over their whole life) — fixing it (ever vs ever) moved RR from 0.41 to ~0.91; (2) **selection bias** (non-users are an unusual 30% leftover); (3) **confounding** (age, aspirin).
- Lesson: observational RWE shows **association, not causation**. A naive 2x2 can give a confidently wrong answer. Rigorous designs (new-user, active-comparator, matched follow-up, confounder adjustment) exist precisely to fight these biases.
