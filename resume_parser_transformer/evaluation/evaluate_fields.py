"""    python3 evaluation/evaluate_fields.py   """
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inference.backend import load_components, APPROACH
from inference.parser import parse_resume
from preprocessing.ingest import restore_line_breaks
from preprocessing.normalize import normalize_skill

SCALAR = ("full_name", "email", "location")
LISTS = ("skills", "degree", "institution", "company", "designation")


def tokens(value):
    return set(re.findall(r"[a-z0-9+#]+", (value or "").lower()))


def similar(a, b):
    ta, tb = tokens(a), tokens(b)
    return bool(ta and tb) and len(ta & tb) / max(len(ta), len(tb)) >= 0.5


def same(a, b):
    return bool(a and b) and " ".join(a.lower().split()) == " ".join(b.lower().split())


def list_f1(pred, gold, match):
    pred, gold = list(dict.fromkeys(p for p in pred if p)), list(dict.fromkeys(g for g in gold if g))
    if not gold and not pred:
        return None
    used, tp = set(), 0
    
    for p in pred:
        for i, g in enumerate(gold):
            if i not in used and match(p, g):
                used.add(i); tp += 1
                break
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(gold) if gold else 0.0
    
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def gold_fields(row, text):
    spans = sorted(row.get("entities", []), key=lambda e: e["start"])
    by = lambda label: [text[e["start"]:e["end"]].strip() for e in spans if e["label"].upper() == label]
    
    return {
        "full_name": (by("PERSON") or [None])[0],
        "email": by("EMAIL"),
        "location": (by("LOCATION") or [None])[0],
        "skills": [normalize_skill(s).lower() for s in by("SKILL")],
        "degree": by("DEGREE"), "institution": by("INSTITUTION"),
        "company": by("COMPANY"), "designation": by("JOB_TITLE"),
    }


def predicted_fields(result):
    c, exp = result["candidate"], result["work_experience"]
    skills = [d["skill"].lower() for d in result["extraction_metadata"]["skill_normalization"]["details"]]
    designations = [x["designation"] for x in exp] + [result["professional_information"]["current_or_most_recent_role"]]
    
    return {
        "full_name": c["full_name"], "email": c["email"], "location": c["location"],
        "skills": skills,
        "degree": [x["degree"] for x in result["education"]],
        "institution": [x["institution"] for x in result["education"]],
        "company": [x["company"] for x in exp], "designation": designations,
    }


def score_document(pred, gold):
    scores = {}
    
    if gold["full_name"]:
        scores["full_name"] = float(same(pred["full_name"], gold["full_name"]))
    if gold["email"]:
        scores["email"] = float(any(same(pred["email"], g) for g in gold["email"]))
    if gold["location"]:
        scores["location"] = float(similar(pred["location"], gold["location"]))
    
    for field in LISTS:
        match = (lambda a, b: a == b or (len(a) > 2 and (a in b or b in a))) if field == "skills" else similar
        f1 = list_f1(pred[field], gold[field], match)
        if f1 is not None and gold[field]:
            scores[field] = f1
    
    return scores


def evaluate(rows, components):
    per_doc = []
    
    for row in rows:
        text = restore_line_breaks(row["text"])
        scores = score_document(predicted_fields(parse_resume(text, components)), gold_fields(row, text))
        per_doc.append({"resume_id": row["resume_id"], "scores": scores})
    fields = {}
    
    for field in SCALAR + LISTS:
        values = [d["scores"][field] for d in per_doc if field in d["scores"]]
        fields[field] = {"score": round(sum(values) / len(values), 4) if values else None, "documents": len(values)}
    doc_scores = [sum(d["scores"].values()) / len(d["scores"]) for d in per_doc if d["scores"]]
    complete = [all(v == 1.0 for k, v in d["scores"].items() if k in SCALAR) and
                all(v >= 0.8 for k, v in d["scores"].items() if k in LISTS) for d in per_doc if d["scores"]]
    
    return {"fields": fields,
            "document_mean_score": round(sum(doc_scores) / len(doc_scores), 4),
            "documents_fully_correct": round(sum(complete) / len(complete), 4),
            "per_document": per_doc}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", default=str(ROOT / "annotations" / "splits" / "test.json"))
    p.add_argument("--output", default=str(ROOT / "evaluation" / "results" / "fields_test.json"))
    a = p.parse_args()
    rows = json.loads(Path(a.data).read_text(encoding="utf-8"))

    systems = {"baseline (rules + ontology)": load_components(use_ner=False, use_sections=False, verbose=False),
               "full system": load_components()}
    results = {name: evaluate(rows, comp) for name, comp in systems.items()}

    print(f"Approach {APPROACH}\nResumes: {len(rows)}")
    
    names = list(results)
    print(f"{'FIELD':<14}" + "".join(f"{n:>30}" for n in names))
    
    for field in SCALAR + LISTS:
        cells = [results[n]["fields"][field]["score"] for n in names]
        print(f"{field:<14}" + "".join(f"{(c if c is not None else float('nan')):>30.3f}" for c in cells))
    
    print(f"{'DOC MEAN':<14}" + "".join(f"{results[n]['document_mean_score']:>30.3f}" for n in names))
    print(f"{'DOC CORRECT':<14}" + "".join(f"{results[n]['documents_fully_correct']:>30.3f}" for n in names))

    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"approach": APPROACH, "components": systems["full system"].info,
                               "results": results}, indent=2), encoding="utf-8")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
