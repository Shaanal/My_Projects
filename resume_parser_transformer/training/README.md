# Training — Approach B (transformers)

Run every command from the project folder (`resume_parser_transformer/`). It uses the same annotation files and splits as the spaCy project, so scores are directly comparable. The test split is never used for training or model selection.

## 1. Data splits (already in the repository)

```bash
python3 training/split_entities.py      # regenerates annotations/splits/* from annotations/entities.json (seed 42)
python3 training/split_sections.py --export annotations/sections_labelstudio_export.json
```

## 2. NER (fine-tuned RoBERTa token classification)

```bash
python3 training/train_transformer_ner.py --model-name roberta-base --epochs 15 --patience 3
```

- **Base model:** `roberta-base` (125M parameters). It is cased, which helps for names and companies, and pretrained on web text. Its byte-level BPE gives exact character offsets for every sub-word, so entity labels are assigned straight from the annotated character spans with no word-alignment step.
- **Long resumes:** most are longer than 512 tokens, so they are split into overlapping 512-token windows with stride 128. At inference each token keeps the prediction from the window where it sits most centrally.
- **Optimisation:** a plain PyTorch loop with AdamW, lr 3e-5, linear warm-up/decay, fp16 on GPU, batch 4 × gradient accumulation 2, and early stopping on **validation exact-span F1 of full resumes**, the same selection metric as the spaCy model.
- **Output:** `models/resume_transformer/` (Hugging Face format) with `training_summary.json` holding the per-epoch curve.
- **Hardware:** fits a 4 GB GPU. On an RTX 3050 Ti one epoch takes under a minute; CPU-only training works but is much slower.
- **Alternatives:** try `--model-name bert-base-cased` or `microsoft/deberta-v3-base` (needs `sentencepiece`; slower, and fp16 can be unstable).

## 3. Section classifier (sentence embeddings + Logistic Regression)

```bash
python3 training/train_section_classifier.py
```

It encodes every block with frozen `sentence-transformers/all-MiniLM-L6-v2` embeddings and trains a Logistic Regression head, using the same data, aliases and splits as the spaCy project's TF-IDF model. It saves `models/section_classifier/section_head.joblib` and `metrics.json`. The embedding model downloads once (about 90 MB) and is shared with the semantic skill matcher.

## 4. Evaluate (held-out test resumes)

```bash
python3 evaluation/evaluate_ner.py
python3 evaluation/evaluate_sections.py
python3 evaluation/evaluate_fields.py
```

Results are written to `evaluation/results/*.json`; the write-up and the comparison with Approach A are in `evaluation/REPORT.md`.
