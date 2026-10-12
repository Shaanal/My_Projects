import re
from preprocessing.normalize import lookup_skill

ALIASES = {
    "PERSONAL_INFORMATION": ["contact", "contacts", "contact information", "contact details",
                             "personal details", "personal information", "personal info", "personal data"],
    "SUMMARY": ["summary", "professional summary", "profile", "professional profile",
                "career summary", "about me", "about", "career overview", "overview",
                "executive summary", "summary of qualifications", "personal statement"],
    "CAREER_OBJECTIVE": ["objective", "career objective", "professional objective", "objectives"],
    "SKILLS": ["skills", "technical skills", "technical expertise", "core competencies",
               "technology stack", "tech stack", "technical proficiencies", "technical skills and tools",
               "key skills", "skill set", "skills set", "technical skills set", "competencies",
               "areas of expertise", "expertise", "tools and technologies", "technologies",
               "soft skills", "technical and soft skills", "interpersonal skills"],
    "EXPERIENCE": ["experience", "work experience", "professional experience",
                   "employment history", "work history", "internships", "internship", "work",
                   "employment", "career history", "relevant experience", "experiences"],
    "EDUCATION": ["education", "academic background", "academics", "educational qualifications",
                  "academic qualifications", "qualifications", "education and training",
                  "educational background", "academic history"],
    "PROJECTS": ["projects", "personal projects", "academic projects", "selected projects",
                 "key projects", "project experience", "notable projects", "project"],
    "CERTIFICATIONS": ["certifications", "certificates", "licenses", "certification",
                       "licenses and certifications", "courses", "trainings", "training"],
    "ACHIEVEMENTS": ["achievements", "awards", "honors", "honours", "accomplishments",
                     "awards and honors", "awards and achievements"],
    "VOLUNTEERING": ["volunteering", "volunteer experience", "community involvement", "volunteer work"],
    "COURSEWORK": ["coursework", "course work", "relevant coursework", "relevant courses",
                   "courses taken", "academic coursework", "key courses"],
    "EXTRACURRICULAR": ["extracurricular", "extra curricular", "extracurricular activities",
                        "extra curricular activities", "positions of responsibility", "leadership",
                        "leadership experience", "clubs", "co curricular activities"],
    "ADDITIONAL": ["others", "other", "additional information", "miscellaneous", "misc"],
    "LANGUAGES": ["languages", "language skills", "language"],
    "INTERESTS": ["interests", "hobbies", "hobbies and interests", "activities"],
    "REFERENCES": ["references", "referees", "recommendations"],
}

KEYWORDS = [
    ("COURSEWORK", r"course ?work"),
    ("EXTRACURRICULAR", r"extra ?curricular|co ?curricular"),
    ("CERTIFICATIONS", r"certif|licen[cs]e"),
    ("VOLUNTEERING", r"volunteer"),
    ("ACHIEVEMENTS", r"award|honou?r|achievement|accomplishment"),
    ("EDUCATION", r"education|academic|degree"),
    ("PROJECTS", r"project"),
    ("EXPERIENCE", r"experience|employment|internship|work history"),
    ("SKILLS", r"skill|competenc|expertise|technolog|proficienc"),
    ("CAREER_OBJECTIVE", r"objective"),
    ("SUMMARY", r"summary|profile|about me"),
    ("PERSONAL_INFORMATION", r"contact|personal"),
    ("EXTRACURRICULAR", r"responsibilit|leadership"), 
    ("LANGUAGES", r"language"),
]

HEADING_THRESHOLD = 0.5
CONTENT_THRESHOLD = 0.45

_ALIAS_LOOKUP = {alias: label for label, aliases in ALIASES.items() for alias in aliases}
_ALIAS_LOOKUP.update({label.lower().replace("_", " "): label for label in ALIASES})


def _strip_residue(line):
    """Drop OCR icon residue: '@ EVENTS' -> 'EVENTS', 'm EDUCATION' -> 'EDUCATION'."""
    line = re.sub(r"^[\W_]+", "", line.strip())
    return re.sub(r"^[a-z]\s+(?=[A-Z]{3})", "", line)


def _norm(line):
    s = re.sub(r"^[\W_]+|[\W_]+$", "", _strip_residue(line).lower())
    s = s.replace("&", " and ").replace("-", " ")
    return re.sub(r"\s+", " ", s).strip()


def heading_label(line):
    return _ALIAS_LOOKUP.get(_norm(line))


def keyword_label(line):
    s = _norm(line)
    return next((label for label, pattern in KEYWORDS if re.search(pattern, s)), None)


def heading_shape(line):
    """'strong' (UPPER CASE or ends with ':'), 'weak' (Title Case) or None if it can't be a heading."""
    if re.match(r"^\s*[-•*–·▪●◦]\s", line): 
        return None

    s = _strip_residue(line).rstrip()
    core = s.rstrip(":").strip()
    words = core.split()
    if not words or len(words) > 5 or len(core) > 45:
        return None
    if ":" in core or "," in core or re.search(r"[@\d]|https?:|www\.|\.\w", core):
        return None
    if core.endswith((".", ",", ";", "*")):
        return None
    if sum(c.isalpha() for c in core) < 4 or lookup_skill(core):  
        return None

    if core.isupper() or s.endswith(":"):
        return "strong"
    if all(w[0].isupper() or w.lower() in {"and", "of", "&", "/", "in"} for w in words):
        return "weak"
    return None


def _predict(classifier, texts):
    if classifier is None or not texts:
        return [(None, 0.0)] * len(texts)
    try:
        return list(classifier.predict(texts))
    except Exception:
        return [(None, 0.0)] * len(texts)


def _classify_headings(lines, classifier):
    """For each line: None, or (label, method, confidence, content kept from the heading line)."""
    decisions = [None] * len(lines)
    pending = []
    for i, line in enumerate(lines):
        label = heading_label(line)
        if label:
            decisions[i] = (label, "alias", 1.0, None)
            continue

        shape = heading_shape(line)
        if shape is None:
            continue

        label = keyword_label(line)

        if label and shape == "weak":
            words = _norm(line).split()
            if not 2 <= len(words) <= 3 or keyword_label(words[-1]) != label:
                label = None

        if label:
            decisions[i] = (label, "keyword", 0.9, None)
        elif shape == "strong" or not keyword_label(line):
            pending.append((i, shape))

    contexts = ["\n".join(lines[i:i + 4]) for i, _ in pending]
    for (i, shape), (label, confidence) in zip(pending, _predict(classifier, contexts)):
        threshold = HEADING_THRESHOLD if shape == "strong" else 0.85
        if label and label != "OTHER" and confidence >= threshold:
            decisions[i] = (label, "classifier", float(confidence), lines[i])  # keep the line as content too
    return decisions


def label_lines(text, classifier=None):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    decisions = _classify_headings(lines, classifier)

    assigned = []
    current = {"label": "OTHER", "heading": None, "method": "none", "confidence": 0.0}
    for line, decision in zip(lines, decisions):
        if decision and decision[1] in ("classifier", "keyword") and decision[0] == current["label"]:
            decision = None

        if decision:
            label, method, confidence, content = decision
            current = {"label": label, "heading": line, "method": method, "confidence": confidence}
            assigned.append({**current, "is_heading": True, "content": content})
        else:
            assigned.append({**current, "is_heading": False, "content": line})

    if classifier is not None:
        index = [i for i, a in enumerate(assigned) if a["label"] == "OTHER" and not a["is_heading"]]
        previous_i, previous = None, None
        for i, (label, confidence) in zip(index, _predict(classifier, [lines[i] for i in index])):
            if previous_i is None or i != previous_i + 1:
                previous = None
            if not label or confidence < CONTENT_THRESHOLD:
                label, confidence = previous or "OTHER", 0.0
            assigned[i].update(label=label, method="content_classifier", confidence=float(confidence))
            previous_i, previous = i, label
    return lines, assigned


def split_sections(text, classifier=None):
    _, assigned = label_lines(text, classifier)

    sections = []
    for a in assigned:
        same = (sections and sections[-1]["label"] == a["label"]
                and (not a["is_heading"] or a["heading"] == sections[-1]["heading"]
                     or a["method"] == "content_classifier"))
        if not same:
            heading = a["heading"] if a["method"] != "content_classifier" else None
            sections.append({"label": a["label"], "heading": heading, "method": a["method"],
                             "scores": [], "lines": []})
        if a["content"]:
            sections[-1]["lines"].append(a["content"])
        sections[-1]["scores"].append(a["confidence"])

    result = []
    for section in sections:
        if section["lines"]:
            scores = section.pop("scores")
            section["confidence"] = round(sum(scores) / len(scores), 3)
            section["text"] = "\n".join(section.pop("lines"))
            result.append(section)
    return result
