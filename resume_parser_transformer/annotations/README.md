# Annotation strategy and datasets

Two kinds of labels train the two learned parts of the pipeline:

| Dataset | Unit | Used for | Size |
|---|---|---|---|
| `splits/{train,validation,test}.json` | character spans in full resume text | NER (both approaches) | 310 resumes, 15,681 spans, split 248 / 31 / 31 by resume |
| `sections.json` | one text block (line) with a section label | section classifier (both approaches) | 509 blocks from 12 resumes in `data/input`, split 9 / 3 by resume |

All splits are made **per resume**, so text from one resume never appears on both sides. Both approaches use the same files, which makes their scores directly comparable.

## Entity schema

The NER label set is deliberately **coarse**: a span model learns *where* an entity is. Finer distinctions are delegated to steps that are cheaper and more reliable than extra NER classes:

| NER label | Meaning (annotate…) | Becomes |
|---|---|---|
| PERSON | the candidate's full name | `candidate.full_name` |
| EMAIL | email address | `candidate.email` |
| LOCATION | city / region / country of the candidate or an employer | `candidate.location`, `work_experience[].location` |
| JOB_TITLE | designation, e.g. "Senior Python Developer" | `work_experience[].designation`, current role |
| COMPANY | employer or client organisation | `work_experience[].company` |
| SKILL | any technology, tool, method or skill phrase | skills → **ontology classifies** into programming language / framework / library / database / cloud / DevOps / tool / other |
| DATE | dates and date ranges | employment and education dates |
| DEGREE | degree name, e.g. "B.Tech", "Bachelor of Science in CS" | `education[].degree` (+ specialization) |
| INSTITUTION | university / college / school | `education[].institution` |

The assessment's finer labels (PROGRAMMING_LANGUAGE, FRAMEWORK, DATABASE, CLOUD_PLATFORM, DEVOPS_TOOL, PROJECT_*, PHONE, EXPERIENCE, CERTIFICATION, SPECIALIZATION) are all in [`labelstudio_entities.xml`](labelstudio_entities.xml) for future annotation rounds. In the current pipeline they are produced without dedicated NER classes:

- **Skill sub-types** come from the skill ontology (`preprocessing/normalize.py`). With ~7,000 SKILL spans, splitting them into 6 classes would leave rare classes such as CLOUD_PLATFORM with very few examples. A type is also a property of the technology, not of its context: "AWS" is always cloud.
- **PHONE / EMAIL** formats are rigid, so patterns are more precise than a model. EMAIL is annotated anyway because it is a useful sanity check of the NER.
- **Projects, certifications and total experience** are recovered from section structure plus record splitting, and from employment dates.

Example from the assessment, in this schema:

```
John Smith is a Senior Python Developer with 6 years of experience working with AWS and Django.
PERSON = "John Smith"   JOB_TITLE = "Senior Python Developer"   SKILL = "AWS", "Django"
→ ontology: AWS → cloud_technologies, Django → frameworks;  "6 years of experience" → total_experience (pattern)
```

### Annotation guidelines

1. Spans are exact character ranges with no leading or trailing spaces or punctuation: annotate `Python`, not `Python,`.
2. Spans are flat (no nesting). In "Senior Python Developer", annotate the whole JOB_TITLE, not a SKILL inside it.
3. Label every mention, not just the first. NER learns from context, so unlabelled repeats are taught as negatives.
4. A DATE covers one date (`Jan 2019`). Ranges are two DATE spans; the parser pairs them.
5. Reference persons, schools in course names, and so on still get their label. The parser decides which one is the candidate's (for example, the first PERSON in the header).
6. When unsure, leave the span out and add a comment. A missing label costs less than an inconsistent one.

### Section schema

`PERSONAL_INFORMATION, SUMMARY, SKILLS, EXPERIENCE, EDUCATION, PROJECTS, CERTIFICATIONS, ACHIEVEMENTS, VOLUNTEERING, OTHER`. Each block takes the label of the section it belongs to, and **headings take the label of the section they open**. That's how the classifier learns that "Technical Expertise" means SKILLS. The interface is [`labelstudio_sections.xml`](labelstudio_sections.xml). Convert an export with:

```bash
python training/split_sections.py --export annotations/sections_labelstudio_export.json
```

## Known data-quality issues

- The XML corpus stores line breaks as runs of spaces. `preprocessing.ingest.restore_line_breaks` turns the last space of each run into `\n` without changing offsets, and training, evaluation and inference all use it.
- Some spans include trailing spaces or punctuation, or start or end inside a token. The transformer labels sub-word tokens from character offsets directly and can represent 98% of spans exactly. spaCy's token-based NER has to contract or skip about 800 of them; see the review workflow below.
- PERSON is annotated only 428 times in 310 resumes, and some resumes are anonymised (`[email]`, `*****`).

---

## Label Studio workflows

Install and start Label Studio once:

```bash
python3 -m venv .venv-labelstudio
source .venv-labelstudio/bin/activate
python -m pip install label-studio
label-studio start          # http://localhost:8080
```

### Annotate new resumes (entities)

1. Create a project and paste `annotations/labelstudio_entities.xml` into **Settings → Labeling Interface**.
2. Import tasks shaped like `{"data": {"text": "...", "resume_id": "unique-id"}}`. For example, take the text from `data/extracted/*.txt` after running `batch_parse.py`.
3. Annotate following the guidelines above, then **Export → JSON**.
4. Convert the export into a new split folder (existing splits are not modified):

```bash
python training/import_labelstudio.py export.json --output annotations/labelstudio_import
```

### Annotate sections

Create a second project with `annotations/labelstudio_sections.xml`. Import one task per text block, with `text`, `document_id`, `source_file`, `page_number` and `block_index`. Export, then run `training/split_sections.py`.

### Review spans with token-boundary problems (spaCy project)

`training/export_alignment_review.py` makes a task only for resumes with spans that don't map cleanly to spaCy tokens, with those spans pre-highlighted:

1. `python training/export_alignment_review.py` writes `annotations/alignment_review_tasks.json` (generated, not kept in the repository).
2. Create a project named `Resume Span Boundary Review` with `labelstudio_entities.xml`, and import the tasks file.
3. Highlighted spans are imported as **predictions**. Accept or copy them into an annotation, fix the boundary or label, and **Submit** every task (an unchanged task still needs a submit). See the [predictions guide](https://labelstud.io/guide/predictions).
4. Export JSON to `annotations/alignment_review_export.json`, then:

```bash
python training/merge_alignment_review.py annotations/alignment_review_export.json
python training/train_spacy_ner.py --train annotations/alignment_reviewed/train.json \
  --dev annotations/alignment_reviewed/validation.json --output models/resume_ner_reviewed
```

The merge writes fresh splits to `annotations/alignment_reviewed/` and refuses unsafe offsets, IDs or overlaps. Keep the test split for the final evaluation only.

Resume data contains personal information: keep exports private unless you have permission to share them.
