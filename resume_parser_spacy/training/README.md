# Training — Approach A (spaCy + classical ML)

Run every command from the project folder (`resume_parser_spacy/`). The test split is never used for training or model selection.

## 1. Data splits (already in the repository)

```bash
python3 training/split_entities.py      # regenerates annotations/splits/* from annotations/entities.json (seed 42)
python3 training/split_sections.py --export annotations/sections_labelstudio_export.json
```

The entity split is 248 / 31 / 31 resumes (80/10/10). With only 310 resumes, keeping 80% for training matters more than a larger validation set. The test set (31 resumes, about 1,500 entities) is still big enough for per-label scores. The section data is split 9 / 3 by resume.

## 2. NER (spaCy transition-based NER, CNN tok2vec)

```bash
python3 -m spacy download en_core_web_md   # once
python3 training/train_spacy_ner.py --output models/resume_ner_spacy_vectors --vectors en_core_web_md --epochs 40 --patience 6
```

- Trains from scratch: a blank English pipeline with one `ner` component, on CPU.
- Texts are trained with line breaks restored, matching inference.
- Spans that don't align to spaCy tokens are contracted, trimmed or skipped, and the counts are printed (see `annotations/README.md` for the review workflow).
- The best validation exact-span F1 checkpoint is saved to `models/resume_ner_spacy/model-best`, with the per-epoch curve in `training_history.json`.
- `--vectors en_core_web_md` adds pretrained static word vectors (download first with `python -m spacy download en_core_web_md`). `--gpu` uses CuPy if installed.

## 3. Section classifier (TF-IDF + Logistic Regression)

```bash
python3 training/train_section_classifier.py
```

Features are word 1-2-grams plus character 3-5-grams, and the heading aliases from `preprocessing/sections.py` are added as weakly supervised examples. The script prints held-out and 4-fold grouped CV scores and saves `models/section_classifier/section_classifier.joblib` and `metrics.json`.

## 4. Evaluate (held-out test resumes)

```bash
python3 evaluation/evaluate_ner.py         # entity P/R/F1, exact and overlap matching
python3 evaluation/evaluate_sections.py    # per-line section accuracy: rules vs classifier vs hybrid
python3 evaluation/evaluate_fields.py      # field- and document-level accuracy, baseline vs full system
```

Results are written to `evaluation/results/*.json`; the write-up is `evaluation/REPORT.md`.

The model paths used by the CLI, API and batch script can be overridden with `RESUME_PARSER_MODEL` and `RESUME_SECTION_MODEL`.
