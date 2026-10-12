import argparse
import json
import random
from pathlib import Path

def to_row(task, idx):
    data = task.get("data", {})
    text = data.get("text", "")
    annotations = [x for x in task.get("annotations") or task.get("completions") or [] if not x.get("was_cancelled")]
    if not text or not annotations:
        return None
    if len(annotations) > 1:
        raise SystemExit(f"Task {task.get('id', idx)} has several annotations; resolve them first.")

    entities = []
    for result in annotations[0].get("result", []):
        value = result.get("value", {})
        if result.get("type") != "labels" or not value.get("labels"):
            continue
        start, end = int(value["start"]), int(value["end"])
        if not (0 <= start < end <= len(text)) or value.get("text") not in (None, text[start:end]):
            raise SystemExit(f"Bad span {start}:{end} in task {task.get('id', idx)}")
        entities.append({"start": start, "end": end, "label": value["labels"][0].upper()})

    entities.sort(key=lambda e: (e["start"], e["end"]))
    for left, right in zip(entities, entities[1:]):
        if right["start"] < left["end"]:
            raise SystemExit(f"Overlapping spans in task {task.get('id', idx)}")
    rid = str(data.get("resume_id") or data.get("source_id") or task.get("id") or f"ls_{idx:04d}")
    return {"resume_id": rid, "text": text, "entities": entities}

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("export", help="Label Studio JSON export")
    p.add_argument("--output", default="annotations/labelstudio_import")
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args()

    tasks = json.loads(Path(a.export).read_text(encoding="utf-8"))
    rows = [r for r in (to_row(t, i) for i, t in enumerate(tasks, 1)) if r]
    if len(rows) < 3:
        raise SystemExit(f"Need at least 3 annotated resumes; found {len(rows)}")
    if len({r["resume_id"] for r in rows}) != len(rows):
        raise SystemExit("Duplicate resume IDs; give each task a unique data.resume_id")

    random.Random(a.seed).shuffle(rows)
    n = len(rows)
    n_test = n_dev = max(1, round(0.2 * n))
    splits = {"train": rows[:n - n_dev - n_test], "validation": rows[n - n_dev - n_test:n - n_test],
              "test": rows[n - n_test:]}

    out = Path(a.output)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"Output folder is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    for name, subset in splits.items():
        (out / f"{name}.json").write_text(json.dumps(subset, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{name}: {len(subset)} resumes")

if __name__ == "__main__":
    main()
