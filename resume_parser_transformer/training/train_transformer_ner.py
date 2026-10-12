import argparse
import json
import math
import os
import random
import sys
import time
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer, get_linear_schedule_with_warmup

from inference.backend import TransformerNER, windows
from preprocessing.ingest import restore_line_breaks

def load_rows(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    for row in rows:
        row["text"] = restore_line_breaks(row["text"])
    return rows

def window_examples(rows, tokenizer, label2id, max_length, stride):
    examples, dropped = [], 0
    for row in rows:
        spans = sorted((int(e["start"]), int(e["end"]), e["label"].upper()) for e in row["entities"])
        enc = windows(tokenizer, row["text"], max_length, stride)
        for ids, mask, offsets in zip(enc["input_ids"], enc["attention_mask"], enc["offset_mapping"]):
            labels, k = [], 0
            for s, e in offsets:
                if e <= s:  
                    labels.append(-100)
                    continue
                while k < len(spans) and spans[k][1] <= s:
                    k += 1
                tag = "O"
                if k < len(spans) and spans[k][0] < e:
                    start, _, label = spans[k]
                    tag = ("B-" if s <= start else "I-") + label
                labels.append(label2id.get(tag, label2id["O"]))
            examples.append({"input_ids": ids, "attention_mask": mask, "labels": labels})
        dropped += sum(1 for a, b in zip(spans, spans[1:]) if b[0] < a[1])
    return examples, dropped

def collate(batch, pad_id):
    width = max(len(x["input_ids"]) for x in batch)
    pad = lambda key, value: torch.tensor([x[key] + [value] * (width - len(x[key])) for x in batch])
    return {"input_ids": pad("input_ids", pad_id), "attention_mask": pad("attention_mask", 0),
            "labels": pad("labels", -100)}

def exact_f1(ner, rows):
    tp = fp = fn = 0
    for row in rows:
        gold = {(int(e["start"]), int(e["end"]), e["label"].upper()) for e in row["entities"]}
        pred = {(e["start"], e["end"], e["label"]) for e in ner(row["text"])}
        tp += len(gold & pred); fp += len(pred - gold); fn += len(gold - pred)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)

class _InMemoryNER(TransformerNER):

    def __init__(self, model, tokenizer, device):
        self.torch, self.model, self.tokenizer, self.device = torch, model, tokenizer, device
        self.id2label = {int(k): v for k, v in model.config.id2label.items()}
        self.batch_size = 8

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train", default=str(ROOT / "annotations" / "splits" / "train.json"))
    ap.add_argument("--dev", default=str(ROOT / "annotations" / "splits" / "validation.json"))
    ap.add_argument("--model-name", default="roberta-base")
    ap.add_argument("--output", default=str(ROOT / "models" / "resume_transformer"))
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--patience", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--grad-accum", type=int, default=2)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--stride", type=int, default=128)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    train_rows, dev_rows = load_rows(a.train), load_rows(a.dev)
    if {r["resume_id"] for r in train_rows} & {r["resume_id"] for r in dev_rows}:
        raise SystemExit("Train and validation splits share resume IDs")
    
    entity_labels = sorted({e["label"].upper() for r in train_rows for e in r["entities"]})
    labels = ["O"] + [f"{p}-{l}" for l in entity_labels for p in ("B", "I")]
    
    label2id = {x: i for i, x in enumerate(labels)}
    id2label = {i: x for x, i in label2id.items()}

    tokenizer = AutoTokenizer.from_pretrained(a.model_name, use_fast=True,
                                              add_prefix_space=True if "roberta" in a.model_name else None)
    train_examples, overlaps = window_examples(train_rows, tokenizer, label2id, a.max_length, a.stride)
    print(f"device={device} train resumes={len(train_rows)} windows={len(train_examples)} "
          f"validation resumes={len(dev_rows)} labels={entity_labels} nested-span overlaps resolved={overlaps}")

    model = AutoModelForTokenClassification.from_pretrained(
        a.model_name, num_labels=len(labels), id2label=id2label, label2id=label2id).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    steps = math.ceil(len(train_examples) / (a.batch_size * a.grad_accum)) * a.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, int(0.1 * steps), steps)
    scaler = torch.amp.GradScaler(enabled=device == "cuda")
    out = Path(a.output); out.mkdir(parents=True, exist_ok=True)

    best_f, best_epoch, history, started = -1.0, 0, [], time.time()
    for epoch in range(1, a.epochs + 1):
        model.train(); random.shuffle(train_examples); total = 0.0
        batches = [train_examples[i:i + a.batch_size] for i in range(0, len(train_examples), a.batch_size)]
        
        for step, batch in enumerate(batches, 1):
            batch = {k: v.to(device) for k, v in collate(batch, tokenizer.pad_token_id).items()}
            with torch.autocast(device_type=device, dtype=torch.float16, enabled=device == "cuda"):
                loss = model(**batch).loss / a.grad_accum
            scaler.scale(loss).backward(); total += loss.item() * a.grad_accum
           
            if step % a.grad_accum == 0 or step == len(batches):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer); scaler.update(); optimizer.zero_grad(); scheduler.step()
        
        model.eval()
        p, r, f = exact_f1(_InMemoryNER(model, tokenizer, device), dev_rows)
        history.append({"epoch": epoch, "loss": round(total / len(batches), 4),
                        "dev_p": round(p, 4), "dev_r": round(r, 4), "dev_f1": round(f, 4)})
        
        print(f"epoch {epoch}/{a.epochs} loss={total / len(batches):.4f} dev_P={p:.3f} dev_R={r:.3f} dev_F1={f:.3f} "
              f"({(time.time() - started) / 60:.1f} min)", flush=True)
        
        if f > best_f:
            best_f, best_epoch = f, epoch
            model.save_pretrained(out); tokenizer.save_pretrained(out)
        elif epoch - best_epoch >= a.patience:
            print(f"Early stopping: no validation improvement for {a.patience} epochs")
            break

    summary = {"base_model": a.model_name, "best_epoch": best_epoch, "best_dev_f1": round(best_f, 4),
               "labels": labels, "train_resumes": len(train_rows), "train_windows": len(train_examples),
               "validation_resumes": len(dev_rows), "lr": a.lr, "batch_size": a.batch_size,
               "grad_accum": a.grad_accum, "max_length": a.max_length, "stride": a.stride, "seed": a.seed,
               "device": device, "minutes": round((time.time() - started) / 60, 1), "history": history}
    (out / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Best validation exact-span F1 {best_f:.3f} at epoch {best_epoch}; saved to {out}. Test data was not used.")

if __name__ == "__main__":
    main()
