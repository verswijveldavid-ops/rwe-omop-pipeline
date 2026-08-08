# RWE Pipeline on OMOP — Project 2

> **Sister project to** `clinical-data-pipeline/` (Project 1, CDISC clinical-trial data).
> This one is **Real-World Evidence (RWE)** on **OMOP CDM** synthetic data (Eunomia).
> Separate repo, separate venv, separate learning log. Nothing shared with Project 1 except David's brain.

## What this project is
A Real-World Evidence pipeline: load OMOP-standardized synthetic patient data (Eunomia, ~2,700 patients)
into DuckDB, build patient cohorts, and run descriptive RWE analyses — drug utilization and post-market
safety signals — surfaced in a Streamlit dashboard. Proves the analyst can work in the real-world-data
world (OMOP CDM), complementing Project 1's clinical-trial world (CDISC SDTM/ADaM).

## Working mode — READ FIRST (stricter than Project 1's end state)
David is learning OMOP from zero and wants to understand every step.
1. NO AUTONOMOUS ACTIONS by Claude. David runs every command, creates every file, commits himself.
2. Claude WRITES + EXPLAINS code; David RUNS it. Per file: what it does & why -> what to type -> expected output. Then WAIT.
3. Explain before every step: WHAT -> WHY (clinical/RWE reason) -> HOW -> WHAT COMES OUT. Define all jargon.
4. Start from zero on OMOP/CDM/RWE/DuckDB/cohorts.
5. One step at a time. Never batch. Wait for David's "next"/"go".
6. Learning notes go ONLY in learning_log_omop.md (no code), in David's own words.
7. Fully isolated from clinical-data-pipeline (separate venv/git/docs).
Full spec pasted by David at project start governs the phases (0-8).

## Tech stack
DuckDB (analytics database, one file) + Python/pandas + Streamlit (dashboard) + requests/openpyxl.
Data: OHDSI Eunomia synthetic OMOP dataset. Free tools only. No R, no SDTM/ADaM, no cloud beyond
Streamlit Community Cloud, no Docker, no ML.

## Repo layout
- data/  raw dataset + DuckDB file (gitignored, regenerable)
- src/   analysis scripts
- app/   Streamlit dashboard (app.py)
- docs/  omop_glossary.md, architecture diagram, screenshots

## Status
Phase 0 (setup): DONE — folder, isolated venv, requirements.txt, layout, git init, .gitignore, these docs.
NEXT: Phase 1 — teach OMOP CDM before touching data (pure teaching, no code).
