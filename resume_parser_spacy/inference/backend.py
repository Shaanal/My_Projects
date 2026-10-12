import os
from pathlib import Path

os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from inference.parser import Components
from preprocessing.normalize import CANONICAL, ONTOLOGY, skill_key

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NER = ROOT / "models" / "resume_ner_spacy_vectors" / "model-best"
DEFAULT_SECTION = ROOT / "models" / "section_classifier" / "section_classifier.joblib"
APPROACH = "A: spaCy CNN NER + TF-IDF/LogReg sections + char n-gram skill matching"

class SpacyNER:
    def __init__(self, path):
        import spacy
        self.nlp = spacy.load(path)

    def __call__(self, text):
        return [{"text": e.text, "label": e.label_, "start": e.start_char, "end": e.end_char, "score": None}
                for e in self.nlp(text).ents]

class SectionClassifier:

    def __init__(self, path):
        import joblib
        self.pipeline = joblib.load(path)

    def predict(self, texts):
        if not texts:
            return []
        probabilities = self.pipeline.predict_proba(list(texts))
        best = probabilities.argmax(axis=1)
        
        return [(str(self.pipeline.classes_[i]), float(p[i])) for i, p in zip(best, probabilities)]

class CharNgramSkillMatcher:
    threshold = 0.8

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        forms = sorted({form for skills in ONTOLOGY.values()
                        for name, (aliases, _) in skills.items() for form in [name] + aliases})
        self.names = [CANONICAL[skill_key(f)][0] for f in forms]
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), lowercase=True)
        self.matrix = self.vectorizer.fit_transform(forms)

    def match(self, texts):
        if not texts:
            return []
        
        scores = (self.vectorizer.transform(texts) @ self.matrix.T).toarray()
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

    components = Components(skill_matcher=CharNgramSkillMatcher(), info={"approach": APPROACH})
    if use_ner:
        if ner_path.exists():
            components.model = _load("ner_model", SpacyNER, ner_path, components, verbose)
        elif verbose:
            print(f"NER model not found at {ner_path}; using rules and the skill ontology only.")
    
    if use_sections and section_path.exists():
        components.section_classifier = _load("section_model", SectionClassifier, section_path, components, verbose)
    return components
