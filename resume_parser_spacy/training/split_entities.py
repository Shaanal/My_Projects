import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "annotations" / "entities.json"
OUTPUT = ROOT / "annotations" / "splits"

def main():
    rows = [r for r in json.loads(SOURCE.read_text(encoding="utf-8")) if r.get("text") and r.get("entities")]
    random.Random(42).shuffle(rows)
    n_train, n_val = int(len(rows) * 0.8), int(len(rows) * 0.1)
    splits = {"train": rows[:n_train], "validation": rows[n_train:n_train + n_val], "test": rows[n_train + n_val:]}

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, records in splits.items():
        (OUTPUT / f"{name}.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{name}: {len(records)} resumes")

if __name__ == "__main__":
    main()
