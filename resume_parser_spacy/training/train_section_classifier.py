import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline

from preprocessing.sections import ALIASES
from training.split_sections import load_section_rows

def alias_examples():
    return [(alias, label) for label, aliases in ALIASES.items() for alias in aliases + [label.replace("_", " ")]]

def build_model(seed=42):
    return Pipeline([
        ("features", FeatureUnion([
            ("word", TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2),
                                     sublinear_tf=True, max_features=50000)),
            ("char", TfidfVectorizer(analyzer="char_wb", lowercase=True, ngram_range=(3, 5),
                                     sublinear_tf=True, max_features=50000)),
        ])),
        ("classifier", LogisticRegression(max_iter=3000, C=5.0, class_weight="balanced", random_state=seed)),
    ])

def fit(rows, seed=42):
    texts = [r["text"] for r in rows] + [a for a, _ in alias_examples()]
    labels = [r["label"] for r in rows] + [l for _, l in alias_examples()]
    return build_model(seed).fit(texts, labels)

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
    train = [r for r in rows if r["split"] == "train"]
    test = [r for r in rows if r["split"] == "test"]
    print(f"train blocks={len(train)} test blocks={len(test)} labels={dict(Counter(r['label'] for r in train))}")

    groups = np.array([r["document_id"] for r in rows])
    cv = []
    for fold, (tr, te) in enumerate(GroupKFold(n_splits=4).split(rows, groups=groups), 1):
        model = fit([rows[i] for i in tr], a.seed)
        cv.append(scores([rows[i]["label"] for i in te], model.predict([rows[i]["text"] for i in te])))
        print(f"fold {fold}: {cv[-1]}")
    cv_mean = {k: round(float(np.mean([c[k] for c in cv])), 4) for k in cv[0]}
    cv_std = {k: round(float(np.std([c[k] for c in cv])), 4) for k in cv[0]}

    model = fit(train, a.seed)
    predictions = model.predict([r["text"] for r in test])
    held_out = scores([r["label"] for r in test], predictions)
    
    report = classification_report([r["label"] for r in test], predictions, zero_division=0)
    print(report)
    print("held-out:", held_out, "| 4-fold CV mean:", cv_mean, "std:", cv_std)

    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out / "section_classifier.joblib")
    
    metrics = {"model": "TF-IDF word(1-2)+char_wb(3-5) + LogisticRegression(C=5, balanced)",
               "train_resumes": sorted({r["source_file"] for r in train}),
               "test_resumes": sorted({r["source_file"] for r in test}),
               "held_out": held_out, "cv_4fold_mean": cv_mean, "cv_4fold_std": cv_std,
               "classification_report": classification_report([r["label"] for r in test], predictions,
                                                              zero_division=0, output_dict=True)}
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved {out / 'section_classifier.joblib'}")

if __name__ == "__main__":
    main()
