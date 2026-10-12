import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GroupKFold

from inference.backend import EMBEDDING_MODEL, Embedder
from preprocessing.sections import ALIASES
from training.split_sections import load_section_rows

def alias_examples():
    return [(alias, label) for label, aliases in ALIASES.items() for alias in aliases + [label.replace("_", " ")]]

def fit(rows, embed, seed=42):
    aliases = alias_examples()
    X = np.vstack([embed([r["text"] for r in rows]), embed([a for a, _ in aliases])])
    y = [r["label"] for r in rows] + [l for _, l in aliases]
    return LogisticRegression(max_iter=3000, C=10.0, class_weight="balanced", random_state=seed).fit(X, y)

def scores(y_true, y_pred):
    return {"accuracy": round(accuracy_score(y_true, y_pred), 4),
            "macro_f1": round(f1_score(y_true, y_pred, average="macro", zero_division=0), 4),
            "weighted_f1": round(f1_score(y_true, y_pred, average="weighted", zero_division=0), 4)}

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", default=str(ROOT / "annotations" / "sections.json"))
    p.add_argument("--output", default=str(ROOT / "models" / "section_classifier"))
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args()

    rows = load_section_rows(a.data)
    cache = {}

    def embed(texts):
        missing = [t for t in texts if t not in cache]
        if missing:
            cache.update(zip(missing, Embedder.encode(missing)))
        return np.vstack([cache[t] for t in texts])

    train = [r for r in rows if r["split"] == "train"]
    test = [r for r in rows if r["split"] == "test"]
    print(f"train blocks={len(train)} test blocks={len(test)} labels={dict(Counter(r['label'] for r in train))}")

    groups = np.array([r["document_id"] for r in rows])
    cv = []
    for fold, (tr, te) in enumerate(GroupKFold(n_splits=4).split(rows, groups=groups), 1):
        head = fit([rows[i] for i in tr], embed, a.seed)
        cv.append(scores([rows[i]["label"] for i in te], head.predict(embed([rows[i]["text"] for i in te]))))
        print(f"fold {fold}: {cv[-1]}")
    cv_mean = {k: round(float(np.mean([c[k] for c in cv])), 4) for k in cv[0]}
    cv_std = {k: round(float(np.std([c[k] for c in cv])), 4) for k in cv[0]}

    head = fit(train, embed, a.seed)
    predictions = head.predict(embed([r["text"] for r in test]))
    held_out = scores([r["label"] for r in test], predictions)
    
    print(classification_report([r["label"] for r in test], predictions, zero_division=0))
    print("held-out:", held_out, "| 4-fold CV mean:", cv_mean, "std:", cv_std)

    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    
    joblib.dump({"head": head, "embedding_model": EMBEDDING_MODEL}, out / "section_head.joblib")
    metrics = {"model": f"{EMBEDDING_MODEL} embeddings (frozen) + LogisticRegression(C=10, balanced)",
               "train_resumes": sorted({r["source_file"] for r in train}),
               "test_resumes": sorted({r["source_file"] for r in test}),
               "held_out": held_out, "cv_4fold_mean": cv_mean, "cv_4fold_std": cv_std,
               "classification_report": classification_report([r["label"] for r in test], predictions,
                                                              zero_division=0, output_dict=True)}
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved {out / 'section_head.joblib'}")

if __name__ == "__main__":
    main()
