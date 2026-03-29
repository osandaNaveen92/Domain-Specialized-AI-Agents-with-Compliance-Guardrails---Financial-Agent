import json
from pathlib import Path

def load_controls(path="config/control_catalog.json"):
    catalog_path = Path(path)
    if not catalog_path.is_absolute():
        catalog_path = Path(__file__).resolve().parents[1] / catalog_path

    with open(catalog_path, "r", encoding="utf-8") as f:
        return json.load(f)
