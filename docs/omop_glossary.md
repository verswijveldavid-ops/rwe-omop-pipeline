# OMOP / RWE Glossary

Plain-English definitions of the core terms for this project.

- **RWD (Real-World Data)** — health data collected outside clinical trials, from routine care: insurance claims, electronic health records (EHR), registries.
- **RWE (Real-World Evidence)** — clinical evidence about a drug's use/benefits/risks derived from RWD. What actually happens when real populations use a drug, post-approval.
- **OHDSI** ("Odyssey") — the open research community that maintains the OMOP standard and its tools.
- **OMOP CDM (Common Data Model)** — a single standardized structure (same tables, columns, codes) for real-world health data, so one analysis runs against any database that adopts it.
- **Core tables** — PERSON (who), VISIT_OCCURRENCE (healthcare interactions), CONDITION_OCCURRENCE (diagnoses), DRUG_EXPOSURE (drugs taken), MEASUREMENT (labs/vitals), OBSERVATION (other facts), DEATH (death date).
- **person_id** — the patient key present in every table; the thread that ties one patient's whole history together.
- **concept_id** — the integer code OMOP uses for every clinical idea (condition, drug, lab, gender). Universal across all OMOP databases.
- **CONCEPT table** — the dictionary that translates a concept_id into a human-readable name, its source vocabulary, and its type.
- **Vocabularies** — SNOMED CT (conditions), RxNorm (drugs), LOINC (lab tests) — the source coding systems OMOP maps into concept_ids.
- **Athena** — OHDSI's public searchable directory of concept_ids.
- **Cohort** — a defined group of patients meeting specific criteria; the fundamental unit of RWE analysis (built as a list of person_ids).
- **Eunomia** — OHDSI's small (~2,700-patient) synthetic OMOP test dataset; our data source.

## OMOP CDM vs. CDISC SDTM (one line)
SDTM standardizes one clinical trial for a regulator BEFORE approval; OMOP standardizes real-world claims/EHR data for research across many databases AFTER approval.
