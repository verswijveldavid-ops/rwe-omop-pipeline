"""Load Eunomia GiBleed CSVs into a single DuckDB database and print core row counts."""

from pathlib import Path

import duckdb

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_DIR = DATA_DIR / "GiBleed"
DB_PATH = DATA_DIR / "eunomia.duckdb"

CORE_TABLES = [
    "PERSON",
    "VISIT_OCCURRENCE",
    "CONDITION_OCCURRENCE",
    "DRUG_EXPOSURE",
    "MEASUREMENT",
    "OBSERVATION",
    "DEATH",
]


def main() -> None:
    # Recursive search (rglob) — CSVs may sit in a nested subfolder.
    # Skip macOS '._' AppleDouble junk files.
    csvs = sorted(f for f in CSV_DIR.rglob("*.csv") if not f.name.startswith("._"))

    con = duckdb.connect(str(DB_PATH))

    loaded = 0
    for csv in csvs:
        table = csv.stem.upper()
        try:
            con.execute(
                f'CREATE OR REPLACE TABLE "{table}" AS '
                "SELECT * FROM read_csv_auto(?, header=true)",
                [str(csv)],
            )
            loaded += 1
        except Exception as exc:
            print(f"  !! skipped {csv.name}: {exc}")

    print(f"Loaded {loaded} tables into {DB_PATH.name}\n")

    print("Row counts for the core OMOP tables:")
    for t in CORE_TABLES:
        n = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"  {t:<22} {n:>9,}")

    con.close()


if __name__ == "__main__":
    main()
