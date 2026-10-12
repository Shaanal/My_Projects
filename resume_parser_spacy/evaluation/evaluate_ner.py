"""    python3 evaluation/evaluate_ner.py    """
import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inference.backend import load_components, APPROACH
from preprocessing.ingest import restore_line_breaks


def prf(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return round(precision, 4), round(recall, 4), round(f1, 4)


def overlap_matches(pred, gold):
    used, tp = set(), 0
    for ps, pe, pl in sorted(pred):
        for g in sorted(gold):
            if g not in used and g[2] == pl and ps < g[1] and g[0] < pe:
                used.add(g)
                tp += 1
                break
    return tp


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default=str(ROOT / "annotations" / "splits" / "test.json"))
    parser.add_argument("--model", default=None, help="NER model; defaults to this project's trained model")
    parser.add_argument("--output", default=str(ROOT / "evaluation" / "results" / "ner_test.json"))
    args = parser.parse_args()

    rows = json.loads(Path(args.data).read_text(encoding="utf-8"))
    if not rows:
        raise SystemExit("Test dataset is empty.")
    
    ner = load_components(ner_path=args.model, use_sections=False).model
    if ner is None:
        raise SystemExit("No NER model could be loaded.")

    exact = defaultdict(lambda: [0, 0, 0])
    relaxed = defaultdict(lambda: [0, 0, 0])
    seconds = []
    
    for row in rows:
        text = restore_line_breaks(row["text"])
        gold = {(int(e["start"]), int(e["end"]), e["label"].upper()) for e in row.get("entities", [])}
        
        started = time.perf_counter()
        pred = {(int(e["start"]), int(e["end"]), e["label"].upper()) for e in ner(text)
                if e.get("start") is not None and e.get("end") is not None}
        seconds.append(time.perf_counter() - started)
        
        for label in {x[2] for x in gold | pred}:
            p = {x for x in pred if x[2] == label}
            g = {x for x in gold if x[2] == label}
            exact[label][0] += len(p & g)
            exact[label][1] += len(p - g)
            exact[label][2] += len(g - p)
            tp = overlap_matches(p, g)
            relaxed[label][0] += tp
            relaxed[label][1] += len(p) - tp
            relaxed[label][2] += len(g) - tp

    print(f"Approach {APPROACH}")
    print(f"Evaluated resumes: {len(rows)}; mean NER time per resume: {1000 * sum(seconds) / len(seconds):.0f} ms")
    print(f"{'LABEL':<14}{'EXACT P':>9}{'R':>7}{'F1':>7}   {'OVERLAP P':>9}{'R':>7}{'F1':>7}{'SUPPORT':>9}")
    
    per_label = {}
    for label in sorted(exact):
        e, r = prf(*exact[label]), prf(*relaxed[label])
        support = exact[label][0] + exact[label][2]
        per_label[label] = {"exact": dict(zip("prf", e)), "overlap": dict(zip("prf", r)), "support": support}
        print(f"{label:<14}{e[0]:>9.3f}{e[1]:>7.3f}{e[2]:>7.3f}   {r[0]:>9.3f}{r[1]:>7.3f}{r[2]:>7.3f}{support:>9}")
    
    micro_e = prf(*[sum(v[i] for v in exact.values()) for i in range(3)])
    micro_r = prf(*[sum(v[i] for v in relaxed.values()) for i in range(3)])
    
    print("-" * 70)
    print(f"{'MICRO':<14}{micro_e[0]:>9.3f}{micro_e[1]:>7.3f}{micro_e[2]:>7.3f}   {micro_r[0]:>9.3f}{micro_r[1]:>7.3f}{micro_r[2]:>7.3f}")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"approach": APPROACH, "data": str(args.data), "resumes": len(rows),
                               "ms_per_resume": round(1000 * sum(seconds) / len(seconds), 1),
                               "micro": {"exact": dict(zip("prf", micro_e)), "overlap": dict(zip("prf", micro_r))},
                               "per_label": per_label}, indent=2), encoding="utf-8")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
