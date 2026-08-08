"""Download the OHDSI Eunomia 'GiBleed' OMOP dataset (CSV tables) into data/GiBleed/."""

from pathlib import Path
import zipfile

import requests

URL = "https://raw.githubusercontent.com/OHDSI/EunomiaDatasets/main/datasets/GiBleed/GiBleed_5.3.zip"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ZIP_PATH = DATA_DIR / "GiBleed_5.3.zip"
CSV_DIR = DATA_DIR / "GiBleed"


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    print(f"Downloading Eunomia GiBleed from:\n  {URL}")
    response = requests.get(URL, timeout=120)
    response.raise_for_status()
    ZIP_PATH.write_bytes(response.content)
    print(f"Saved zip: {ZIP_PATH.name}  ({ZIP_PATH.stat().st_size / 1_000_000:.1f} MB)")

    CSV_DIR.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        zf.extractall(CSV_DIR)

    csvs = sorted(CSV_DIR.rglob("*.csv"))
    print(f"\nExtracted {len(csvs)} CSV files into data/GiBleed/:")
    for f in csvs:
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()
