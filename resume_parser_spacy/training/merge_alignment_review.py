import argparse
import json
from collections import Counter
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", help="Label Studio JSON export after submitting reviewed tasks")
    parser.add_argument("--splits", default="annotations/splits")
    parser.add_argument("--output", default="annotations/alignment_reviewed")
    
    args = parser.parse_args()
    source = Path(args.splits)
    output = Path(args.output)
    if output.exists() and any(output.iterdir()):
        parser.error(f"Output folder is not empty: {output}; choose a new --output")

    rows_by_split = {}
    rows_by_key = {}
    
    for split in ("train", "validation", "test"):
        rows = json.loads((source / f"{split}.json").read_text(encoding="utf-8"))
        rows_by_split[split] = rows
        for row in rows:
            rows_by_key[(split, str(row["resume_id"]))] = row

    tasks = json.loads(Path(args.export).read_text(encoding="utf-8"))
    updated = set()
    changes = Counter()
    
    for task in tasks:
        data = task.get("data", {})
        split, rid = data.get("split"), str(data.get("resume_id", ""))
        
        key = (split, rid)
        if key not in rows_by_key:
            raise ValueError(f"Export task references unknown split/resume: {key}")
        if key in updated:
            raise ValueError(f"Duplicate exported task for {key}")
        
        updated.add(key)
        row = rows_by_key[key]
        
        if data.get("text") != row["text"]:
            raise ValueError(f"Resume text changed for {key}; refusing to merge offsets")
        mapping = data.get("review_span_map", {})
        expected = {f"entity_{i}" for i in (v["entity_index"] for v in mapping.values())}
        
        annotations = task.get("annotations", [])
        if len(annotations) != 1 or not annotations[0].get("was_cancelled", False) and not annotations[0].get("result") is not None:
            raise ValueError(f"Task {key} must have one submitted annotation; please finish and export all tasks")
        
        result_by_id = {}
        for result in annotations[0].get("result", []):
            if result.get("from_name") != "label" or result.get("to_name") != "text":
                continue
            result_by_id[result.get("id")] = result
        unknown = set(result_by_id) - set(mapping)
        if unknown:
            raise ValueError(f"Task {key} has reviewed result IDs not in source map: {sorted(unknown)}")

        original = row["entities"]
        replacements = {}
        for result_id, info in mapping.items():
            entity_index = int(info["entity_index"])
            if not 0 <= entity_index < len(original):
                raise ValueError(f"Invalid entity index in review map for {key}: {entity_index}")
            
            result = result_by_id.get(result_id)
            if result is None:
                replacements[entity_index] = None
                changes["deleted"] += 1
                continue
            
            value = result.get("value", {})
            labels = value.get("labels", [])
            if len(labels) != 1:
                raise ValueError(f"Reviewed span {result_id} in {key} must have exactly one label")
            
            start, end = int(value["start"]), int(value["end"])
            text = row["text"]
            if not (0 <= start < end <= len(text)) or value.get("text") != text[start:end]:
                raise ValueError(f"Bad offsets/text for reviewed span {result_id} in {key}")
            
            replacements[entity_index] = {"start": start, "end": end, "label": labels[0].upper()}
            old = original[entity_index]
            changes["corrected" if replacements[entity_index] != {"start": int(old["start"]), "end": int(old["end"]), "label": old["label"].upper()} else "confirmed"] += 1
       
        row["entities"] = [replacements.get(i, entity) for i, entity in enumerate(original) if replacements.get(i, entity) is not None]
        row["entities"].sort(key=lambda e: (int(e["start"]), int(e["end"])))
        for left, right in zip(row["entities"], row["entities"][1:]):
            if int(right["start"]) < int(left["end"]):
                raise ValueError(f"Reviewed offsets create overlapping spans in {key}: {left} / {right}")

    if len(updated) != len(tasks):
        raise ValueError("Some exported tasks could not be matched")
    output.mkdir(parents=True, exist_ok=True)
    
    for split, rows in rows_by_split.items():
        (output / f"{split}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "merge_summary.json").write_text(json.dumps({"reviewed_tasks": len(updated), "changes": dict(changes)}, indent=2), encoding="utf-8")
    
    print(f"Wrote reviewed splits to {output}")
    print(f"Reviewed tasks: {len(updated)}; changes: {dict(changes)}")

if __name__ == "__main__":
    main()
