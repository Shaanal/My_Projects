import json
import os
from pathlib import Path

os.environ.setdefault("USE_TF", "0")                
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")   

import numpy as np

from inference.parser import Components
from preprocessing.normalize import CANONICAL, ONTOLOGY, skill_key

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NER = ROOT / "models" / "resume_transformer"
DEFAULT_SECTION = ROOT / "models" / "section_classifier" / "section_head.joblib"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
APPROACH = "B: fine-tuned RoBERTa NER + sentence-embedding sections + embedding skill matching"

def _device():
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"

def windows(tokenizer, text, max_length=512, stride=128):
    return tokenizer(text, truncation=True, max_length=max_length, stride=stride,
                     return_overflowing_tokens=True, return_offsets_mapping=True, padding=False)

def decode_entities(text, offsets, tags, scores):
    spans, current = [], None
    for (start, end), tag, score in zip(offsets, tags, scores):
        if tag == "O":
            current = None
            continue
        prefix, label = tag.split("-", 1)
        if current and prefix == "I" and current["label"] == label:
            current["end"] = end
            current["scores"].append(score)
        else:
            current = {"label": label, "start": start, "end": end, "scores": [score]}
            spans.append(current)

    result = []
    for s in spans:
        start, end = s["start"], s["end"]
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1] in " \n\t,;:":
            end -= 1
        if start < end:
            result.append({"text": text[start:end], "label": s["label"], "start": start, "end": end,
                           "score": round(float(np.mean(s["scores"])), 4)})
    return result

class TransformerNER:
    def __init__(self, path, device=None, batch_size=8):
        import torch
        from transformers import AutoModelForTokenClassification, AutoTokenizer
        from transformers.utils import logging as hf_logging
        hf_logging.set_verbosity_error()

        self.torch = torch
        self.device = device or _device()
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForTokenClassification.from_pretrained(path).to(self.device).eval()
        self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}
        self.batch_size = batch_size

    def __call__(self, text):
        if not text.strip():
            return []
        enc = windows(self.tokenizer, text)
        best = {}  
        with self.torch.no_grad():
            for i in range(0, len(enc["input_ids"]), self.batch_size):
                batch = self.tokenizer.pad({"input_ids": enc["input_ids"][i:i + self.batch_size],
                                            "attention_mask": enc["attention_mask"][i:i + self.batch_size]},
                                           return_tensors="pt").to(self.device)
                probs = self.torch.softmax(self.model(**batch).logits.float(), dim=-1).cpu().numpy()
                for w in range(probs.shape[0]):
                    offsets = enc["offset_mapping"][i + w]
                    for t, (s, e) in enumerate(offsets):
                        if e <= s:
                            continue

                        centrality = min(t, len(offsets) - 1 - t)
                        label_id = int(probs[w, t].argmax())
                        if (s, e) not in best or centrality > best[(s, e)][0]:
                            best[(s, e)] = (centrality, label_id, float(probs[w, t, label_id]))

        offsets = sorted(best)
        tags = [self.id2label[best[o][1]] for o in offsets]
        scores = [best[o][2] for o in offsets]
        return decode_entities(text, offsets, tags, scores)

class Embedder:
    _model = None

    @classmethod
    def encode(cls, texts, name=EMBEDDING_MODEL):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(name, device=_device())
        return cls._model.encode(list(texts), batch_size=64, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False)

class EmbeddingSectionClassifier:
    def __init__(self, path):
        import joblib
        bundle = joblib.load(path)
        self.head = bundle["head"]
        self.embedding_model = bundle.get("embedding_model", EMBEDDING_MODEL)

    def predict(self, texts):
        if not texts:
            return []
        probabilities = self.head.predict_proba(Embedder.encode(texts, self.embedding_model))
        best = probabilities.argmax(axis=1)
        return [(str(self.head.classes_[i]), float(p[i])) for i, p in zip(best, probabilities)]

class EmbeddingSkillMatcher:
    threshold = 0.85

    def __init__(self):
        forms = sorted({form for skills in ONTOLOGY.values()
                        for name, (aliases, _) in skills.items() for form in [name] + aliases})
        self.names = [CANONICAL[skill_key(f)][0] for f in forms]
        self.matrix = Embedder.encode(forms)

    def match(self, texts):
        if not texts:
            return []
        scores = Embedder.encode(texts) @ self.matrix.T
        best = scores.argmax(axis=1)
        return [(self.names[j], float(scores[i, j])) for i, j in enumerate(best)]

def _load(kind, cls, path, components, verbose):
    try:
        component = cls(path)
        components.info[kind] = str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
        return component
    except Exception as exc:
        if verbose:
            print(f"{kind} could not be loaded from {path}: {exc}")
        return None

def load_components(ner_path=None, section_path=None, use_ner=True, use_sections=True, verbose=True):
    ner_path = ROOT / Path(ner_path or os.getenv("RESUME_PARSER_MODEL") or DEFAULT_NER)
    section_path = ROOT / Path(section_path or os.getenv("RESUME_SECTION_MODEL") or DEFAULT_SECTION)

    components = Components(info={"approach": APPROACH})
    try:
        components.skill_matcher = EmbeddingSkillMatcher()
        components.info["embedding_model"] = EMBEDDING_MODEL
    except Exception as exc:
        if verbose:
            print(f"Embedding skill matcher unavailable ({exc}); using the skill dictionary only.")

    if use_ner:
        if (ner_path / "config.json").exists():
            components.model = _load("ner_model", TransformerNER, ner_path, components, verbose)
            summary = ner_path / "training_summary.json"
            if components.model and summary.exists():
                components.info["ner_base_model"] = json.loads(summary.read_text()).get("base_model")
        elif verbose:
            print(f"NER model not found at {ner_path}; using rules and the skill ontology only.")
    
    if use_sections and section_path.exists():
        components.section_classifier = _load("section_model", EmbeddingSectionClassifier, section_path,
                                              components, verbose)
    return components
