"""    python evaluation/evaluate_sections.py    """
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.metrics import accuracy_score, classification_report, f1_score

from inference.backend import load_components, APPROACH
from preprocessing.sections import label_lines
from training.split_sections import documents, load_section_rows

# Labels the annotations don't have, mapped to the closest one.
MERGE = {"CAREER_OBJECTIVE": "SUMMARY", "LANGUAGES": "OTHER", "INTERESTS": "OTHER", "REFERENCES": "OTHER",
         "COURSEWORK": "EDUCATION", "EXTRACURRICULAR": "ACHIEVEMENTS", "ADDITIONAL": "OTHER"}


def gold_lines(blocks):
    lines, labels = [], []
    for block in blocks:
        for line in block["text"].splitlines():
            if line.strip():
                lines.append(line.strip())
                labels.append(block["label"])
    return lines, labels


def summarize(name, gold, pred):
    pred = [MERGE.get(p, p) for p in pred]
    result = {"system": name, "lines": len(gold),
              "accuracy": round(accuracy_score(gold, pred), 4),
              "macro_f1": round(f1_score(gold, pred, average="macro", zero_division=0), 4),
              "weighted_f1": round(f1_score(gold, pred, average="weighted", zero_division=0), 4)}
    print(f"{name:<18}{result['accuracy']:>10.3f}{result['macro_f1']:>10.3f}{result['weighted_f1']:>13.3f}")
    return result, pred


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", default=str(ROOT / "annotations" / "sections.json"))
    p.add_argument("--split", default="test")
    p.add_argument("--output", default=str(ROOT / "evaluation" / "results" / "sections.json"))
    a = p.parse_args()

    classifier = load_components(use_ner=False).section_classifier
    if classifier is None:
        raise SystemExit("No section classifier found; run training/train_section_classifier.py first.")
    
    docs = documents(load_section_rows(a.data, a.split))
    gold, rules, alone, hybrid = [], [], [], []
    
    for blocks in docs.values():
        lines, labels = gold_lines(blocks)
        text = "\n".join(lines)
        gold += labels
        rules += [x["label"] for x in label_lines(text, None)[1]]
        hybrid += [x["label"] for x in label_lines(text, classifier)[1]]
        alone += [label for label, _ in classifier.predict(lines)]

    print(f"Approach {APPROACH}")
    print(f"Held-out resumes: {len(docs)}  lines: {len(gold)}")
    print(f"{'SYSTEM':<18}{'ACCURACY':>10}{'MACRO F1':>10}{'WEIGHTED F1':>13}")
    
    results = []
    for name, pred in (("rules only", rules), ("classifier only", alone), ("hybrid", hybrid)):
        result, merged = summarize(name, gold, pred)
        results.append(result)
    
    print("\nHybrid per-section report:")
    print(classification_report(gold, merged, zero_division=0))

    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"approach": APPROACH, "documents": sorted(docs), "results": results,
                               "hybrid_report": classification_report(gold, merged, zero_division=0, output_dict=True)},
                              indent=2), encoding="utf-8")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
