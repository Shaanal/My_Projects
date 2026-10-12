# Resume Parser — Evaluation Report

This report covers both implementations. They share everything except the learned components, so their scores are directly comparable:

| | Approach A — `resume_parser_spacy/` | Approach B — `resume_parser_transformer/` |
|---|---|---|
| Entity extraction | spaCy transition-based NER, CNN tok2vec + static word vectors, trained from scratch | `roberta-base` fine-tuned for BIO token classification |
| Section classifier | TF-IDF (word 1-2 + char 3-5-grams) + Logistic Regression | frozen `all-MiniLM-L6-v2` sentence embeddings + Logistic Regression |
| Semantic skill matching | character n-gram TF-IDF cosine | sentence-embedding cosine |
| Shared | ingestion, OCR, cleaning, hybrid section rules, skill ontology, record parsing, JSON schema, CLI, API, evaluation scripts | same files, byte-identical |

All numbers below were produced by the scripts in `evaluation/` and are stored in `evaluation/results/*.json` of each project.

## 1. Problem understanding

A resume parser has to solve four sub-problems that fail in different ways:

1. **Reading order.** Two-column PDFs, tables and scans scramble text before any NLP runs. A perfect NER model cannot fix interleaved columns.
2. **Structure.** Which block is "experience" and which is "skills", when headings vary ("Technical Expertise", "Tech Arsenal") or are missing.
3. **Entities.** Names, companies, titles, dates, degrees, institutions and skills appear in free text with no fixed position.
4. **Normalization and assembly.** "ReactJS" and "React.js" are one skill, and a title, a company and two dates have to be grouped into one employment record.

The design uses learned models where variation is open-ended (entities, unseen headings, skill variants), and deterministic logic where the format is rigid (emails, phone numbers, date arithmetic) or where a curated knowledge base is more reliable than a small dataset (skill categories).

## 2. Architecture

```
resume file (PDF / DOCX / image / text)
  │
  ├─ 1. ingest.py     PyMuPDF text blocks + two-column detection, 
  |                   python-docx in document order,
  │                   Tesseract OCR for images and scanned pages
  |
  ├─ 2. clean_text    fix whitespace, re-join hyphenated words,  
  |                   remove icon characters
  |
  ├─ 3. sections.py   a. heading aliases and keyword rules
  │                   b. learned classifier for unknown headings 
  |                      (heading + next 3 lines)
  │                   c. learned classifier for text under no 
  |                      heading
  |
  ├─ 4. parser.py     contact details (email / phone / links), 
  |                   NER entities → name, location
  |
  ├─ 5. records.py    split experience, education and projects 
  |                   into records;
  │                   job dates → total experience and overlaps
  |
  ├─ 6. normalize.py  skill ontology + semantic matcher → 
  |                   normalized, categorized skills
  │
  └▶ JSON(schema.py), with optional confidence + evidence per field
```

### Technology choices

| Layer | Choice | Why |
|---|---|---|
| PDF | **PyMuPDF** | Fast, and gives text blocks with coordinates. A gutter search on block x-positions recovers two-column reading order: left column, then right, with full-width banners kept in place. pdfplumber is slower and its strength, table geometry, is rarely needed for resumes. |
| DOCX | **python-docx** (XML walk) | Walking the body in order keeps layout tables where they appear, reads text boxes, and skips Word's duplicate `mc:Fallback` copies. Layout cells are read one after another; data rows stay on one line. |
| OCR | **Tesseract** | Offline, CPU-only, and detects columns by default. PaddleOCR is more accurate on noisy scans but adds a heavy framework dependency; it's listed as an improvement. |
| NER (A) | **spaCy** | Fast on CPU, small (45 MB), simple to train and serve. It represents the traditional/feature-learning route. |
| NER (B) | **RoBERTa-base** | Cased (helps names and companies) and pretrained on web text. Byte-level BPE gives exact character offsets, so labels come straight from annotated spans. |
| Sections | **hybrid**: rules → classifier | See §3.2. |
| Skills | **knowledge base + semantic fallback** | See §3.4. |
| API | **FastAPI** | Typed upload endpoint with automatic `/docs` for the demo. |

LayoutLMv3 was considered for B. It needs word bounding boxes in the training data, and the annotated corpus is plain text without coordinates, so it would need a new annotation round. Column-aware ingestion addresses the main layout failure (interleaved columns) without it.

## 3. Method

### 3.1 Data and annotation

- **Entities.** 310 resumes with 15,681 character-span annotations over 9 labels: PERSON, EMAIL, LOCATION, JOB_TITLE, COMPANY, SKILL, DATE, DEGREE, INSTITUTION. They are split **by resume** 248 / 31 / 31 (80/10/10). The corpus stores line breaks as runs of spaces; `restore_line_breaks` turns the last space of each run into `\n` (offsets unchanged), so models train on the same line structure they see at inference.
- **Sections.** 509 blocks from 12 resumes in `data/input` (PDF, DOCX, JPG), labelled in Label Studio with 10 section classes. Split by resume: 9 train / 3 test.
- **Label design.** NER labels are kept coarse on purpose. Skill sub-types (language, framework, database, cloud, DevOps, tool) come from the ontology rather than NER classes, because the type is a property of the technology, not of its context, and splitting ~7,000 SKILL spans six ways would starve rare classes. The full assessment schema (PHONE, FRAMEWORK, PROJECT_NAME, …) is in the Label Studio config for future rounds. Guidelines are in `annotations/README.md`.
- **Annotation quality.** In spaCy's tokenisation, 476 spans don't align to token boundaries and 342 start or end on punctuation. spaCy training contracts, trims or skips them (317 / 291 / 194 in train). The transformer labels sub-words from character offsets and reproduces 98% of spans exactly. A Label Studio review workflow for these spans is included (`training/export_alignment_review.py`).

### 3.2 Section identification: hybrid

Detection runs in this order:

1. **Exact alias table** (≈100 headings).
2. **Keyword rule** (`skill`, `experience`, `certif`…), only for heading-shaped lines (≤5 words, upper-case or ending with ":", no digits, bullets, commas or URLs).
3. **Learned classifier** for unknown heading-shaped lines. It reads the heading **plus the next three lines**, because "WORKED WITH" alone is ambiguous but the list under it is not. A prediction equal to the current section is treated as content, which keeps upper-case job titles out of headings.
4. **Learned classifier on content lines** that sit under no heading, with smoothing.

**Why hybrid.** Rules alone are precise but brittle. A line classifier alone is weak: a single line such as "Led a team of 5" is genuinely ambiguous, and per-line accuracy is about 0.5. Combined, the rules handle the common case at confidence 1.0, and the classifier handles the long tail. It mapped an OCR-misspelled "SERTIFICAT" to CERTIFICATIONS and "WORKED WITH" to SKILLS, neither of which any rule covers.

### 3.3 Entity extraction

| | A: spaCy | B: RoBERTa |
|---|---|---|
| Input | full resume | 512-token windows, stride 128; each token keeps the prediction from the window where it is most central |
| Training | blank `en` + static vectors from `en_core_web_md`, batch 8, dropout 0.2, CPU | AdamW lr 3e-5, warm-up 10%, fp16, batch 4×2, GPU (RTX 3050 Ti, 4 GB) |
| Model selection | best **validation exact-span F1** of full resumes, early stopping | same metric, same validation resumes |
| Selected (final run, recorded in `execute.ipynb`) | epoch 23 of 29, val F1 0.506 | epoch 9 of 12, val F1 0.630 |
| Train time | 16 min (CPU) | 11 min (GPU) |

The test split was not used for training or selection. Approach A's two variants (with and without vectors) were chosen between on validation, not test (vectors 0.527 vs 0.515 in the first comparison run). Re-running training reproduces B closely (val F1 0.634 → 0.630). A varies more between runs (0.527 → 0.506), because spaCy's CPU training is not fully deterministic even with a fixed seed.

### 3.4 Skill identification, normalization and classification

1. **Identify.** NER SKILL spans, plus a dictionary scan of ~330 ontology surface forms compiled into one longest-first pattern, so "React Native" is not also counted as "React". Ambiguous names (C, R, Go, Spring, Express…) are accepted only in canonical case inside list context, or anywhere in a SKILLS section. Skills are collected **per section**, so technologies mentioned only inside project or experience descriptions are found too.
2. **Normalize.** A punctuation-insensitive key ("React.js", "ReactJS" and "React JS" all become `reactjs`) is looked up against canonical names and aliases.
3. **Semantic fallback** for unknown strings.
   - Approach A uses character n-gram TF-IDF cosine at threshold 0.80. It catches spelling variants: "Microsoft SQL Srv" → Microsoft SQL Server (0.96), "Kubernets" → Kubernetes.
   - Approach B uses sentence-embedding cosine at threshold 0.85. It catches meaning: "Deep neural networks" → Deep Learning (0.89), "AWS Cloud services" → AWS.
   - Each handles cases the other misses, so combining them is a cheap improvement.
4. **Classify.** The ontology category (programming language / framework / library / database / cloud / DevOps / tool / other) and parent concepts (AWS → Cloud, Infrastructure; React → Frontend, JavaScript Ecosystem) are reported in `extraction_metadata.skill_normalization`. Spoken languages and soft skills are kept out of the technical lists.
5. **Deduplicate** on the canonical name; the raw forms are kept for explainability.
6. **Filter unknown terms.** A term the ontology doesn't know is kept only when it is listed in a Skills section, appears in a comma-separated list, or the transformer is ≥ 0.7 confident. Category labels inside skills lists ("Tech based") are skipped, and terms that turn out to be a job's company, title or location are removed. Without this filter, NER mistakes such as a company name, a professor's surname or a project title appeared as skills.

A knowledge base is the primary mechanism because skill → category is stable, curated knowledge; a classifier would have to relearn it from little data. The semantic layer covers the open-ended variation.

### 3.5 Record assembly and advanced features

- **Records.** Experience entries split on dated lines, repeated role lines, and title lines followed by a date. Wrapped bullet continuations (lines starting lower-case) never start a record. Company, title and location come from NER entities in the record, falling back to a "Title – Company" split and the date line ("Dec 2021 – Jul 2025, Dubai").
- **Total experience.** Computed from employment date ranges with overlaps merged (e.g. "7 years 7 months"). A stated value ("8+ years of experience") is preferred for the output field; both are reported.
- **Duplicate and overlap detection.** Overlapping employment pairs and duplicates (same company and title) are listed in `extraction_metadata.experience_analysis`.
- **Confidence.** Each field gets a value: the model probability for transformer entities, otherwise a documented prior by source (pattern 0.9–0.99, NER 0.8–0.85, heuristic 0.5), scaled by section confidence and field completeness for records. These are **not calibrated** probabilities.
- **Output.** By default the API, CLI and batch script return only the schema fields. `extraction_metadata` (confidence, evidence, sections, skill details) is returned on request (`?include_metadata=true`, `--with-metadata`).
- **Explainability.** `extraction_metadata.evidence` records each field's source (`ner:PERSON`, `pattern:email`, `heuristic:header_line`…) and section. Every skill lists its raw forms, method, confidence and the sections it was found in, and every section records its heading, method and confidence.

## 4. Evaluation methodology

| Level | Data | Metric |
|---|---|---|
| Entity | 31 held-out resumes, 1,492 gold spans | per-label P/R/F1, **exact** span and **overlap** match |
| Section | 3 held-out resumes, 202 lines | per-line accuracy and macro-F1: rules only vs classifier only vs hybrid; plus grouped 4-fold CV of the classifier over all 12 resumes |
| Field | 31 held-out resumes | gold values derived from the entity annotations (first PERSON = name, EMAIL, first LOCATION, SKILL set, DEGREE, INSTITUTION, COMPANY, JOB_TITLE). Scalar fields: exact (location: token overlap ≥ 0.5). List fields: F1 with fuzzy matching. |
| Document | 31 held-out resumes | mean field score per resume; "fully correct" = all scalar fields right and every list F1 ≥ 0.8 |

Every level compares against a **rules + ontology baseline** with no learned model, so the contribution of learning is visible.

## 5. Results

### 5.1 Entity extraction (test, 31 resumes)

| Label | Support | A exact F1 | B exact F1 | A overlap F1 | B overlap F1 |
|---|---:|---:|---:|---:|---:|
| PERSON | 58 | 0.771 | **0.889** | 0.771 | **0.906** |
| EMAIL | 54 | 0.952 | **0.982** | 0.952 | **0.982** |
| LOCATION | 177 | 0.502 | **0.706** | 0.588 | **0.814** |
| JOB_TITLE | 192 | 0.490 | **0.630** | 0.702 | **0.809** |
| COMPANY | 112 | 0.241 | **0.608** | 0.382 | **0.750** |
| DATE | 182 | 0.652 | **0.778** | 0.696 | **0.874** |
| DEGREE | 66 | 0.496 | **0.527** | 0.701 | **0.730** |
| INSTITUTION | 75 | 0.512 | **0.544** | 0.612 | **0.734** |
| SKILL | 576 | 0.426 | **0.542** | 0.507 | **0.657** |
| **Micro** | 1,492 | 0.494 | **0.633** | 0.593 | **0.756** |

These are the final models, whose training and evaluation outputs are stored in each project's `execute.ipynb`. The final evaluation ran on the CPU for both projects. B's GPU evaluation of the same model gave micro exact F1 0.624, because CPU and GPU arithmetic round differently and a few borderline tokens flip. An earlier checkpoint (5 epochs on flattened text, since removed) scored micro exact F1 **0.221** on the same test set. Restoring line breaks and training to convergence account for most of A's improvement. In an earlier run, static vectors changed A's test score only slightly (0.516 with vs 0.511 without); PERSON gained a lot and LOCATION lost.

### 5.2 Section identification

| System | A (TF-IDF) acc / macro-F1 | B (embeddings) acc / macro-F1 |
|---|---|---|
| Rules only | 0.579 / 0.416 | 0.579 / 0.416 |
| Classifier only (each line) | 0.431 / 0.365 | 0.455 / 0.367 |
| **Hybrid** | **0.629 / 0.502** | **0.639 / 0.505** |
| Classifier, grouped 4-fold CV (12 resumes) | 0.513 ± 0.068 / 0.403 ± 0.096 | 0.516 ± 0.068 / 0.414 ± 0.087 |

### 5.3 Field level and document level (test, 31 resumes)

| Field | Baseline (no models) | A | B |
|---|---:|---:|---:|
| Full name | 0.857 | 0.893 | **0.964** |
| Email | 1.000 | 1.000 | 1.000 |
| Location | 0.567 | 0.567 | **0.767** |
| Skills (F1) | 0.381 | 0.456 | **0.559** |
| Degree (F1) | 0.603 | **0.756** | 0.753 |
| Institution (F1) | 0.622 | **0.660** | 0.643 |
| Company (F1) | 0.291 | 0.476 | **0.656** |
| Designation (F1) | 0.373 | 0.571 | **0.667** |
| **Document mean** | 0.596 | 0.678 | **0.755** |
| Documents fully correct | 3.2% | 3.2% | 3.2% |

Compared with the first version of this report, the final parser reads the candidate's name and location only from the header (everything before the first section heading) or a contact block, and filters unknown skill terms (§3.4). The header rule stops a person or city named inside a job entry (for example "under Prof. Kamal Karlapalem") from being reported as the candidate's own; it leaves the location empty when the header has none, rather than guessing. Degree improved (A 0.66 → 0.76). Skill F1 fell (A 0.58 → 0.46) because the gold annotations count descriptive phrases ("hardware and software troubleshooting") as skills, which the filter now drops on purpose. Document-level scores stayed about the same.

### 5.4 Approach comparison

| Criterion | A: spaCy + classical ML | B: transformers |
|---|---|---|
| Accuracy | entity F1 0.49, document 0.68 | **entity F1 0.63, document 0.76**; best on 9 of 9 labels (exact) and 5 of 8 fields |
| Training effort | 16 min CPU, no GPU needed | 11 min on a 4 GB GPU; impractical on CPU |
| Data requirements | learns representations from scratch, so it needs more labels to learn context (COMPANY 0.29 F1) | pretraining already knows names, places and organisations; better with the same 248 resumes |
| Generalization | depends on surface features; static vectors help names | contextual: "Wisdomise" recognised as a company from context alone |
| Processing time (NER per resume, measured in the evaluation) | **~75 ms** (CPU) | ~0.2 s GPU, ~1–1.5 s CPU |
| Model size | 45 MB | 478 MB (+ 90 MB embedding model) |
| Complexity / maintenance | one pip package, simple to retrain | torch + transformers version management (transformers ≥ 5 breaks with torch 2.5), GPU for retraining |

**Recommendation.** Use B where accuracy matters and a GPU or ~1 s CPU latency is acceptable, for example batch screening. A is a reasonable fallback for CPU-only, high-throughput or embedded use. The shared hybrid sections, ontology and record logic mean switching between them changes only the model files.

## 6. Error analysis

- **COMPANY is the weakest entity, especially for A.** Companies are open-vocabulary proper nouns, often unmarked ("Telecommunication Systems") or abbreviated ("ABB" vs "Asea Brown Boveri"). A's from-scratch CNN has seen too few to generalise; B's pretraining helps (0.29 → 0.62). Before a plausibility filter was added, heuristic fallbacks put responsibilities, "Present", cities or the candidate's name in `company` when NER found nothing.
- **SKILL boundaries are inconsistent in the gold data.** The annotations mix short tokens ("Java") with long phrases ("Excellent knowledge in IP Networking", "hardware and software troubleshooting"). Exact F1 penalises this heavily (B 0.54 exact vs 0.66 overlap). Normalization then cannot map phrases like these to the ontology, so they land in `other_relevant_technologies`.
- **DEGREE boundaries** ("B.S. in Computer Science" vs "B.S.") explain the large exact-vs-overlap gap (0.51 vs 0.72).
- **Sections.** The weakest classes are SUMMARY content without a heading (the classifier confuses self-descriptions with experience) and EXPERIENCE vs PROJECTS bullets, which are linguistically identical. The test resumes include one PDF whose annotated block order differs from its reading order.
- **Two-column PDFs.** A text block that overhung the column gutter by a few points was read as a full-width banner, which interleaved both columns from that point on. The gutter is now placed in the middle of the widest empty band, with a small tolerance.
- **Record splitting.** Errors came from wrapped bullet continuations, "production-grade …" being read as a "Title - description" project line, and substring matching ("ESI" inside "Designed"). All three are fixed: continuation lines never open a record, separators need spaces, and entity matching uses word boundaries.
- **Documents fully correct is about 3% for every system.** The criterion needs name, email and location exactly right *and* five list fields at F1 ≥ 0.8. Skill-phrase granularity alone makes 0.8 rare, so this measures annotation granularity as much as the parser.

## 7. Limitations and caveats

- **Quantitative evaluation is on the XML-derived corpus.** Its text comes from one source format. Performance on PDFs, DOCX and scans is shown qualitatively on the 33 mixed-format files in `data/input` (all parse without errors; outputs in `data/parsed/`) but is not measured, because those files have no entity gold.
- **Field gold is derived from entity spans**, not a hand-built structured JSON. Phone numbers, projects, specialization, grades and dates per record are therefore not scored.
- **Test-set reuse.** Some generic parser fixes (record splitting, company plausibility, heading-shape rules, the "Leadership & Experience" keyword order) were made after looking at field-level and section errors on the test resumes. The unknown-skill filter was tuned on the validation split. The NER scores are clean (models were selected on validation only), but the field and section numbers are somewhat optimistic. The section test set is only 3 resumes, so the grouped CV figures are the more reliable estimate for the classifier.
- **Confidence values are heuristic priors**, not calibrated probabilities.
- PERSON has only 428 spans across 310 resumes, and some resumes are anonymised (`[email]`, `*****`).

## 8. Future improvements

1. Annotate 30–50 mixed-format resumes (PDF / DOCX / scans) with a structured JSON gold standard to measure field accuracy where layout actually varies.
2. Fix SKILL and DEGREE span guidelines (atomic technologies, not phrases), then re-annotate with the Label Studio review workflow. That would raise both exact F1 and normalization coverage.
3. Combine both semantic matchers (typos and meaning), and grow the ontology from unmatched skills with frequency counts.
4. Train B with the section label as an extra input feature, or add a CRF layer for BIO consistency. Try `deberta-v3-base` and domain-adaptive pretraining on unlabelled resumes.
5. Collect word bounding boxes (PyMuPDF / Tesseract give them) to train LayoutLMv3 on visually complex templates.
6. PaddleOCR for low-quality scans, calibrated confidences (temperature scaling on validation), and Docker images for both services.
