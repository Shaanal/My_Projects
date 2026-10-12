import argparse
import json
from pathlib import Path

import spacy

SPLITS = ("train", "validation", "test")

def find_issues(doc, text, entity):
    start, end = int(entity["start"]), int(entity["end"])
    exact = doc.char_span(start, end, alignment_mode="strict")
    
    if exact is None:
        return "character boundary does not match spaCy tokens"
    if exact.start == exact.end or doc[exact.start].is_space or doc[exact.end - 1].is_space:
        return "span includes a whitespace token boundary"
    if doc[exact.start].is_punct or doc[exact.end - 1].is_punct:
        return "span begins or ends on punctuation"
    
    return None

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", default="annotations/splits")
    parser.add_argument("--output", default="annotations/alignment_review_tasks.json")
    args = parser.parse_args()
    nlp = spacy.blank("en")
    
    tasks = []
    totals = {name: {"documents": 0, "spans": 0} for name in SPLITS}
    for split in SPLITS:
        rows = json.loads((Path(args.splits) / f"{split}.json").read_text(encoding="utf-8"))
        
        for row in rows:
            flagged = []
            doc = nlp.make_doc(row["text"])
            
            for index, entity in enumerate(row.get("entities", [])):
                reason = find_issues(doc, row["text"], entity)
                if reason:
                    flagged.append((index, entity, reason))
            if not flagged:
                continue
            
            totals[split]["documents"] += 1
            totals[split]["spans"] += len(flagged)
            
            predictions = []
            span_map = {}
            for index, entity, reason in flagged:
                result_id = f"entity_{index}"
                start, end = int(entity["start"]), int(entity["end"])
                predictions.append({
                    "id": result_id,
                    "from_name": "label",
                    "to_name": "text",
                    "type": "labels",
                    "value": {"start": start, "end": end, "text": row["text"][start:end], "labels": [entity["label"]]},
                    "score": 1.0,
                })
                span_map[result_id] = {"entity_index": index, "reason": reason}
            
            tasks.append({
                "data": {"resume_id": str(row["resume_id"]), "split": split, "text": row["text"], "review_span_map": span_map},
                "predictions": [{"model_version": "existing_annotations_for_boundary_review", "result": predictions}],
            })
    
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"Wrote {len(tasks)} Label Studio tasks to {output}")
    for split, counts in totals.items():
        print(f"{split}: {counts['documents']} resumes, {counts['spans']} spans")
    print(f"Total: {sum(v['documents'] for v in totals.values())} resumes, {sum(v['spans'] for v in totals.values())} spans")

if __name__ == "__main__":
    main()
