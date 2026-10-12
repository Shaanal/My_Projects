import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "annotations" / "sections.json"

def load_section_rows(path=DEFAULT_OUTPUT, split=None):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return [r for r in rows if split is None or r["split"] == split]

def documents(rows):
    grouped = {}
    for row in sorted(rows, key=lambda r: (r["document_id"], r["page_number"], r["block_index"])):
        grouped.setdefault(row["document_id"], []).append(row)
    return grouped

def _label(task):
    for annotation in task.get("annotations", []):
        if annotation.get("was_cancelled"):
            continue
        for result in annotation.get("result", []):
            choices = result.get("value", {}).get("choices", [])
            if result.get("from_name") == "section_label" and choices:
                return choices[0]
    return None

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--export", default=str(ROOT / "annotations" / "sections_labelstudio_export.json"))
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--test-size", type=float, default=0.25)
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args()

    from sklearn.model_selection import GroupShuffleSplit

    rows = []
    for task in json.loads(Path(a.export).read_text(encoding="utf-8")):
        data = task.get("data", {})
        text, label = str(data.get("text", "")).strip(), _label(task)
        if text and label:
            rows.append({"document_id": str(data.get("document_id") or data.get("source_file")),
                         "source_file": data.get("source_file"),
                         "page_number": int(data.get("page_number") or 1),
                         "block_index": int(data.get("block_index") or 0),
                         "text": text, "label": label})

    splitter = GroupShuffleSplit(n_splits=1, test_size=a.test_size, random_state=a.seed)
    train_idx, test_idx = next(splitter.split(rows, groups=[r["document_id"] for r in rows]))
    for i in train_idx:
        rows[i]["split"] = "train"
    for i in test_idx:
        rows[i]["split"] = "test"

    Path(a.output).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    for split in ("train", "test"):
        subset = [r for r in rows if r["split"] == split]
        print(f"{split}: {len(subset)} blocks from {len({r['document_id'] for r in subset})} resumes; "
              f"labels {dict(Counter(r['label'] for r in subset))}")

if __name__ == "__main__":
    main()
