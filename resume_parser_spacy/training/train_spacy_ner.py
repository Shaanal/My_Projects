import argparse
import json
import random
import sys
import time
from pathlib import Path

import spacy
from spacy.tokens import Span
from spacy.training import Example
from spacy.util import minibatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preprocessing.ingest import restore_line_breaks

def load_rows(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not rows:
        raise ValueError(f"No annotation rows in {path}")
    seen = set()
    for row in rows:
        rid = row.get("resume_id")
        if rid in seen:
            raise ValueError(f"Duplicate resume_id {rid!r} in {path}")
        seen.add(rid)
        row["text"] = text = restore_line_breaks(row.get("text", ""))

        spans = sorted((int(e["start"]), int(e["end"]), e["label"].upper()) for e in row.get("entities", []))
        for start, end, label in spans:
            if not (0 <= start < end <= len(text)) or not label:
                raise ValueError(f"Invalid entity in {rid}: {start}:{end} {label!r}")
        for left, right in zip(spans, spans[1:]):
            if right[0] < left[1]:
                raise ValueError(f"Overlapping entities in {rid}: {left} and {right}")
    return rows


def to_examples(nlp, rows):
    examples, labels = [], set()
    counts = {"contracted": 0, "trimmed": 0, "skipped": 0}
    for row in rows:
        text = row["text"]
        doc = nlp.make_doc(text)
        ents = []
        for e in row.get("entities", []):
            label = e["label"].upper()
            labels.add(label)
            start, end = int(e["start"]), int(e["end"])

            span = doc.char_span(start, end, label=label, alignment_mode="strict")
            if span is None:
                span = doc.char_span(start, end, label=label, alignment_mode="contract")
                if span is None:
                    counts["skipped"] += 1
                    continue
                counts["contracted"] += 1
            if text[start:end].rstrip().endswith(("#", "+")):  # C#, C++: left to the skill ontology
                counts["skipped"] += 1
                continue

            left, right = span.start, span.end
            while left < right and (doc[left].is_punct or doc[left].is_space):
                left += 1
            while right > left and (doc[right - 1].is_punct or doc[right - 1].is_space):
                right -= 1
            if (left, right) != (span.start, span.end):
                counts["trimmed"] += 1
            if left >= right:
                counts["skipped"] += 1
                continue
            ents.append(Span(doc, left, right, label=label))

        flat = []
        for span in sorted(ents, key=lambda x: (x.start, x.end)):
            if flat and span.start < flat[-1].end:
                counts["skipped"] += 1
            else:
                flat.append(span)
        
        examples.append(Example.from_dict(doc, {"entities": [(x.start_char, x.end_char, x.label_) for x in flat]}))
    return examples, labels, counts


def ner_config(with_vectors):
    if not with_vectors:
        return {}
    tok2vec = {"@architectures": "spacy.HashEmbedCNN.v2", "pretrained_vectors": True, "width": 96, "depth": 4,
               "embed_size": 2000, "window_size": 1, "maxout_pieces": 3, "subword_features": True}
    
    return {"model": {"@architectures": "spacy.TransitionBasedParser.v2", "state_type": "ner",
                      "extra_state_tokens": False, "hidden_width": 64, "maxout_pieces": 2,
                      "use_upper": True, "nO": None, "tok2vec": tok2vec}}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--train", default="annotations/splits/train.json")
    p.add_argument("--dev", default="annotations/splits/validation.json")
    p.add_argument("--output", default="models/resume_ner_spacy_vectors")
    p.add_argument("--vectors", default=None, help="spaCy package with static vectors, e.g. en_core_web_md")
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--patience", type=int, default=6, help="Stop after this many epochs without improvement")
    p.add_argument("--dropout", type=float, default=0.2)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--gpu", action="store_true", help="Use the GPU (needs CuPy)")
    a = p.parse_args()

    random.seed(a.seed)
    if a.gpu and not spacy.prefer_gpu():
        p.error("GPU requested but unavailable")

    train_rows, dev_rows = load_rows(a.train), load_rows(a.dev)
    if {r["resume_id"] for r in train_rows} & {r["resume_id"] for r in dev_rows}:
        raise ValueError("Train and validation splits share resume IDs")

    nlp = spacy.blank("en")
    if a.vectors:
        exclude = ["tagger", "parser", "ner", "lemmatizer", "attribute_ruler", "senter", "tok2vec"]
        nlp.vocab.vectors = spacy.load(a.vectors, exclude=exclude).vocab.vectors
    train_examples, labels, train_counts = to_examples(nlp, train_rows)
    dev_examples, dev_labels, dev_counts = to_examples(nlp, dev_rows)
    print(f"Span alignment: train {train_counts}; validation {dev_counts}")

    ner = nlp.add_pipe("ner", config=ner_config(a.vectors))
    for label in sorted(labels | dev_labels):
        ner.add_label(label)
    optimizer = nlp.initialize(lambda: train_examples)

    output = Path(a.output)
    best_path = output / "model-best"
    output.mkdir(parents=True, exist_ok=True)
    best_f, best_epoch, history, started = -1.0, 0, [], time.time()
    for epoch in range(1, a.epochs + 1):
        random.shuffle(train_examples)
        losses = {}
        for batch in minibatch(train_examples, size=a.batch_size):
            nlp.update(batch, sgd=optimizer, drop=a.dropout, losses=losses)

        scores = nlp.evaluate(dev_examples)
        p_, r_, f = (float(scores.get(k, 0.0)) for k in ("ents_p", "ents_r", "ents_f"))
        history.append({"epoch": epoch, "loss": round(float(losses.get("ner", 0)), 3),
                        "dev_p": round(p_, 4), "dev_r": round(r_, 4), "dev_f1": round(f, 4)})
        print(f"epoch {epoch}/{a.epochs} ner_loss={losses.get('ner', 0):.3f} "
              f"dev_P={p_:.3f} dev_R={r_:.3f} dev_F1={f:.3f}", flush=True)

        if f > best_f:
            best_f, best_epoch = f, epoch
            nlp.to_disk(best_path)
        elif epoch - best_epoch >= a.patience:
            print(f"Early stopping: no validation improvement for {a.patience} epochs")
            break

    summary = {"best_epoch": best_epoch, "best_dev_f1": round(best_f, 4), "vectors": a.vectors, "dropout": a.dropout,
               "batch_size": a.batch_size, "seed": a.seed, "minutes": round((time.time() - started) / 60, 1),
               "history": history}
    (output / "training_history.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    
    print(f"Best validation entity F1: {best_f:.3f} at epoch {best_epoch}; model saved to {best_path}")
    print(f"Split sizes: train={len(train_rows)}, validation={len(dev_rows)}. Test data was not used.")

if __name__ == "__main__":
    main()
