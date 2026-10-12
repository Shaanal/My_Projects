import re
from dataclasses import dataclass, field

from inference.patterns import (ADDRESS, AMBIGUOUS_PATTERNS, BULLET, CATEGORY_LABEL, COUNTRIES, EMAIL,
                                JUNK_LINE, LINK_WORDS, ROLE_WORDS, SKILL_FILLER, SKILL_LABELS, URL,
                                VOCAB_PATTERN, entity_values, find_phone, lines_of, mentions, uniq)
from inference.records import experience_analysis, parse_education, parse_experience, parse_projects
from preprocessing.normalize import analyze_skills, lookup_skill
from preprocessing.sections import heading_label, heading_shape, keyword_label, split_sections

OUTPUT_KEYS = ("candidate", "professional_information", "skills", "education", "projects",
               "work_experience", "certifications", "achievements", "volunteering")
UNKNOWN_SKILL_MIN_SCORE = 0.7

@dataclass
class Components:
    model: object = None
    section_classifier: object = None
    skill_matcher: object = None
    info: dict = field(default_factory=dict)

# ---------- small helpers ----------

def _get_entities(text, model):
    if model is None:
        return []
    try:
        doc = model(text)
        if isinstance(doc, list):
            return doc
        return [{"text": e.text, "label": e.label_, "start": e.start_char, "end": e.end_char, "score": None}
                for e in doc.ents]
    except Exception:
        return []

def _section_body(sections, label):
    return "\n".join(s["text"] for s in sections if s["label"] == label).strip() or None

def _paragraph(body):
    if not body:
        return None
    return " ".join(BULLET.sub("", x) for x in body.splitlines()).strip() or None

def _section_of(sections, snippet):
    if not snippet:
        return None
    return next((s["label"] for s in sections if snippet.lower() in s["text"].lower()), None)

def _score(entity, default):
    score = entity.get("score") if entity else None
    return round(float(score), 3) if score is not None else default

def _clean_items(lines):
    kept = []
    for line in lines:
        if sum(c.isalpha() for c in line) < 4 or JUNK_LINE.search(line) or find_phone(line) or ADDRESS.search(line):
            continue
        if line.strip(" .").lower() in COUNTRIES | LINK_WORDS or EMAIL.search(line):
            continue
        if re.fullmatch(r"[a-z]+", line.strip()):  # single lower-case token: OCR noise
            continue
        kept.append(line)
    return kept

# ---------- contact details ----------

def _extract_links(text, extra=()):
    links = {"linkedin": None, "github": None, "portfolio": None}
    email_domains = {m.group(0).split("@", 1)[1].lower() for m in EMAIL.finditer(text)}
    candidates = [x for x in extra if not x.lower().startswith(("mailto:", "tel:"))] + URL.findall(text)
    
    for u in candidates:
        low = u.lower().rstrip("./")
        url = u if low.startswith("http") else "https://" + u
        
        if "linkedin.com" in low:
            links["linkedin"] = links["linkedin"] or url
        
        elif "github.com" in low:
            links["github"] = links["github"] or url
        
        elif not links["portfolio"]:
            host = re.sub(r"^https?://(?:www\.)?", "", low).split("/")[0]
            explicit = low.startswith(("http", "www."))
            known_tld = re.search(r"\.(?:com|io|dev|me|net|org|app|site|co|in|ai|page)$", host)
            
            if host not in email_domains and not lookup_skill(u) and (explicit or known_tld):
                links["portfolio"] = url
    
    return links

def _contact_lines(lines, sections, header):
    area = [line for line in lines if ADDRESS.search(line)]
    area += header
    
    for section in sections:
        if section["label"] == "PERSONAL_INFORMATION":
            area += section["text"].splitlines()
    
    for i, line in enumerate(lines):
        if find_phone(line) or EMAIL.search(line):
            area += lines[max(0, i - 1):i + 2]
    
    return list(dict.fromkeys(area))

def _best_entity(entities, labels, lines):
    area = "\n".join(lines)
    return next((e for e in entities if e.get("label", "").upper() in labels
                 and e.get("text", "").strip() and mentions(area, e["text"])), None)

def _guess_name(lines):
    header = [re.sub(r"^[^A-Za-zÀ-ÿ]+", "", line).strip() for line in lines[:6]]
    
    # A name split over two lines: "ABDELKADER" / "BERKANI".
    for first, second in zip(header, header[1:]):
        one_word = r"[A-ZÀ-Þ][A-Za-zÀ-ÿ'-]+"
        if re.fullmatch(one_word, first) and re.fullmatch(one_word, second) \
                and not heading_label(first) and not heading_label(second):
            header.insert(0, f"{first} {second}")
            break

    for line in header:
        words = line.split()
        if not 2 <= len(words) <= 5 or len(line) > 50:
            continue
        if EMAIL.search(line) or any(c.isdigit() for c in line) or lookup_skill(line):
            continue
        if heading_label(line) or heading_shape(line) and keyword_label(line):
            continue
        if re.search(r"\b(?:resume|curriculum|vitae|cv|profile|summary|about)\b", line, re.I) or ROLE_WORDS.search(line):
            continue
        if all(re.fullmatch(r"[A-ZÀ-Þ][A-Za-zÀ-ÿ.'-]*|(?:al|el|de|da|van|von|bin|ibn)", w) for w in words):
            return line
    return None

def _guess_location(lines):
    for line in lines:
        labelled = re.search(r"\b(?i:residence|address|location|city|based in)\s*[:\-]\s*([A-Za-z][^|:;\n]{1,60}?)"
                             r"(?=\s*(?:\||;|$|\b[A-Z][a-z]+(?:\s+[a-z]+){0,2}:))", line)
        if labelled:
            return labelled.group(1).strip(" ,.")

    city_state = r"\b([A-Z][a-zA-Z]+(?:[ -][A-Z][a-zA-Z]+)*,\s*(?:[A-Z]{2}\b|[A-Z][a-zA-Z]+(?: (?:of |de |the )?[A-Z][a-zA-Z]+)*))"
    for line in lines:
        line = EMAIL.sub("", line)
        
        if re.match(r"^\d+\s+\S", line) and "," in line:
            line = line.split(",", 1)[1]  # "123 Somewhere Road, Niceville, FL" -> "Niceville, FL"
        
        for match in re.finditer(city_state, line):
            parts = [x.strip() for x in match.group(1).split(",")]
            
            if ROLE_WORDS.search(match.group(1)) or re.search(r"\b(?:University|College|Institute|School)\b", match.group(1)):
                continue
            if any(lookup_skill(x) or x.isupper() and len(x) > 2 for x in parts):
                continue
            return match.group(1)
        
        city = re.search(r"\b(Hyderabad|Bengaluru|Bangalore|Chennai|Mumbai|Delhi|Pune|Kolkata|Noida|Gurugram|India)\b",
                         line, re.I)
        
        if city:
            return city.group(1)
    return None

def _name(entities, lines, header, confidence, evidence):
    person = _best_entity(entities, {"PERSON", "FULL_NAME"}, header)
    guess = _guess_name(lines)
    name = person["text"].strip() if person else None

    if name and guess and len(name.split()) == 1 and len(guess.split()) > 1 and \
            any(w.lower().startswith(name.lower()) for w in guess.split()):
        name = guess  # NER caught only part of it: "ROB" in "ROBERT COOPER"
        confidence["full_name"], evidence["full_name"] = 0.7, {"source": "ner:PERSON+header_line", "text": name}
    
    elif name:
        confidence["full_name"], evidence["full_name"] = _score(person, 0.85), {"source": "ner:PERSON", "text": name}
    
    elif guess:
        name = guess
        confidence["full_name"], evidence["full_name"] = 0.5, {"source": "heuristic:header_line", "text": name}
    
    else:
        person = next((e for e in entities if e.get("label", "").upper() in {"PERSON", "FULL_NAME"}
                       and e.get("text", "").strip()), None)
        if person:
            name = person["text"].strip()
            confidence["full_name"] = round(0.6 * _score(person, 0.85), 3)
            evidence["full_name"] = {"source": "ner:PERSON (outside header)", "text": name}
    return name

def _location(entities, contact, confidence, evidence):
    place = _best_entity(entities, {"LOCATION", "GPE"}, contact)
    if place:
        location = place["text"].strip()
        confidence["location"], evidence["location"] = _score(place, 0.8), {"source": "ner:LOCATION", "text": location}
        return location
    
    location = _guess_location(contact)
    if location:
        confidence["location"], evidence["location"] = 0.5, {"source": "heuristic:contact_pattern", "text": location}
    return location

# ---------- skills ----------

def find_skills(text, entities=None, list_context=False):
    found = [" ".join(m.group(0).lower().split()) for m in VOCAB_PATTERN.finditer(text)]
    for skill, (strict, loose) in AMBIGUOUS_PATTERNS.items():
        if (loose if list_context else strict).search(text):
            found.append(skill)
    for e in entities or []:
        if e.get("label", "").upper() in SKILL_LABELS and mentions(text, e.get("text")):
            found.append(" ".join(e["text"].split()))
    return uniq(found)

def _skill_items(body):
    items = []
    for line in (body or "").splitlines():
        line = BULLET.sub("", line).strip()
        head, colon, rest = line.partition(":")
        
        if colon and len(head.split()) <= 4:
            line = rest
        parts = [re.sub(r"\s*\([^()]*\)|\s+etc\.?$", "", x).strip(" .:")
                 for x in re.split(r"[,;|•·]|\s{2,}|\s+[-–—]\s+|\s+and\s+", line)]
        parts = [x for x in parts if x]
        
        if not parts or line.rstrip().endswith(".") and len(parts) == 1 or any(len(x.split()) > 5 for x in parts):
            continue

        for part in parts:
            if "(" in part or ")" in part or "/" in part[:2] or "www" in part or "http" in part:
                continue
            if sum(c.isalpha() for c in part) < 3 and not lookup_skill(part):
                continue
            if not (part[0].isupper() or part[0].isdigit() or lookup_skill(part)):
                continue  
            if re.fullmatch(r"\d+\+?\s*(?:years?|yrs?|months?)", part, re.I):
                continue
            if SKILL_FILLER.match(part) or heading_label(part) or EMAIL.search(part):
                continue
            if CATEGORY_LABEL.search(part) and not lookup_skill(part):
                continue  
            items.append(part)
    
    return items

def _in_list(text, value):
    v = re.escape(value.strip())
    return re.search(rf"(?:,\s*(?:and\s+)?{v}\b|\b{v}\s*,\s*\S+\s*,)", text, re.I) is not None

def _skills(text, sections, entities, skill_matcher):
    raw_skills, skill_sections = [], {}
    skipped = {"PERSONAL_INFORMATION", "LANGUAGES", "INTERESTS", "REFERENCES", "COURSEWORK"}
    
    for section in sections:
        if section["label"] in skipped:
            continue
        found = find_skills(section["text"], entities, list_context=section["label"] == "SKILLS")
        
        if section["label"] == "SKILLS":
            found = uniq(found + _skill_items(section["text"]))
        for skill in found:
            raw_skills.append(skill)
            skill_sections.setdefault(skill.lower(), set()).add(section["label"])

    ner_scores = {}
    for e in entities:
        if e.get("label", "").upper() in SKILL_LABELS and e.get("score") is not None:
            key = " ".join(e["text"].split()).lower()
            ner_scores[key] = max(ner_scores.get(key, 0.0), float(e["score"]))

    categorized, details = analyze_skills(raw_skills, matcher=skill_matcher)
    kept, dropped = [], set()
    
    for detail in details:
        found_in = set().union(*(skill_sections.get(r.lower(), set()) for r in detail["raw"]))
        detail["sections"] = sorted(found_in)
        
        confident = max((ner_scores.get(r.lower(), 0.0) for r in detail["raw"]), default=0.0) >= UNKNOWN_SKILL_MIN_SCORE
        listed = any(_in_list(text, r) for r in detail["raw"])
        
        if detail["method"] == "unmatched" and "SKILLS" not in found_in and not confident and not listed:
            dropped.add(detail["skill"].lower())
        else:
            kept.append(detail)

    categorized = {k: [s for s in v if s.lower() not in dropped] for k, v in categorized.items()}
    return raw_skills, categorized, kept, dropped

# ---------- main ----------

def parse_resume_text(text, model=None, section_classifier=None, skill_matcher=None, links=None):
    links = links or []
    entities = _get_entities(text, model)
    sections = split_sections(text, classifier=section_classifier)
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    confidence, evidence = {}, {}

    # Contact details. The header ends at the first section heading.
    first_heading = next((i for i, line in enumerate(lines[:10]) if heading_label(line) and i > 0), 10)
    header = lines[:max(first_heading, 1)]
    contact = _contact_lines(lines, sections, header)

    email_match = EMAIL.search(text)
    email = email_match.group(0) if email_match else next(
        (x[len("mailto:"):].split("?")[0] for x in links if x.lower().startswith("mailto:")), None)
    phone = find_phone(text)
    web = _extract_links(text, links)
    name = _name(entities, lines, header, confidence, evidence)
    location = _location(entities, contact, confidence, evidence)

    if email:
        source = "pattern:email" if email_match else "link:mailto"
        confidence["email"], evidence["email"] = 0.99, {"source": source, "text": email}
    
    if phone:
        confidence["phone_number"], evidence["phone_number"] = 0.9, {"source": "pattern:phone", "text": phone}
    for key in ("linkedin", "github", "portfolio"):
        if web[key]:
            from_link = any(web[key].rstrip("/") == x.rstrip("/") for x in links)
            evidence[key] = {"source": "link" if from_link else "pattern:url", "text": web[key]}

    summary = _paragraph(_section_body(sections, "SUMMARY"))
    objective = _paragraph(_section_body(sections, "CAREER_OBJECTIVE"))

    # Skills, experience, education, projects.
    raw_skills, categorized, skill_details, dropped = _skills(text, sections, entities, skill_matcher)
    technical = uniq(sum(categorized.values(), []))
    allowed = {s.lower() for s in technical}

    tech_details = [d for d in skill_details if d["category"] != "non_technical"]
    if tech_details:
        confidence["skills"] = round(sum(d["confidence"] for d in tech_details) / len(tech_details), 3)

    experience = parse_experience(_section_body(sections, "EXPERIENCE"), entities, find_skills)
    most_recent_role = next((x["designation"] for x in experience if x.get("designation")), None) \
        or next(iter(entity_values(entities, ["JOB_TITLE", "DESIGNATION"])), None)

    not_skills = {(r.get(k) or "").lower() for r in experience for k in ("company", "designation", "location")} - {""}
    if not_skills & allowed:
        dropped |= not_skills & allowed
        categorized = {k: [x for x in v if x.lower() not in not_skills] for k, v in categorized.items()}
        technical = [x for x in technical if x.lower() not in not_skills]
        skill_details = [d for d in skill_details if d["skill"].lower() not in not_skills]
        allowed -= not_skills

    analysis = experience_analysis(experience)
    stated = re.search(r"\b(\d+(?:\.\d+)?)\+?\s+years?(?:\s+and\s+\d+\s+months?)?\s+(?:of\s+)?experience\b", text, re.I)
    total_experience = None
    
    if stated:
        total_experience = stated.group(0)
        confidence["total_experience"] = 0.9
        evidence["total_experience"] = {"source": "pattern:stated", "text": total_experience}
    elif analysis["total_experience"]:
        total_experience = analysis["total_experience"]
        confidence["total_experience"] = round(0.7 * analysis["dated_entries"] / max(len(experience), 1), 3)
        evidence["total_experience"] = {"source": "computed:employment_dates",
                                        "text": f"{analysis['dated_entries']} dated entries, overlaps merged"}

    education, exams = parse_education(_section_body(sections, "EDUCATION"), entities)
    projects = parse_projects(_section_body(sections, "PROJECTS"), entities, find_skills)

    for record in experience:
        record["technologies_used"] = [s for s in record["technologies_used"] if s.lower() in allowed]
    for record in projects:
        record["technology_stack"] = [s for s in record["technology_stack"] if s.lower() in allowed]

    section_conf = {s["label"]: s.get("confidence", 0.0) for s in sections}
    for field_name, label, records, keys in (
            ("education", "EDUCATION", education, ("degree", "institution", "end_year")),
            ("work_experience", "EXPERIENCE", experience, ("company", "designation", "start_date")),
            ("projects", "PROJECTS", projects, ("name", "summary", "technology_stack"))):
        if records:
            filled = sum(bool(r.get(k)) for r in records for k in keys) / (len(records) * len(keys))
            confidence[field_name] = round(max(section_conf.get(label, 0.0), 0.5) * filled, 3)
    
    if summary:
        confidence["professional_summary"] = round(max(section_conf.get("SUMMARY", 0.0), 0.5), 3)
    if objective:
        confidence["career_objective"] = round(max(section_conf.get("CAREER_OBJECTIVE", 0.0), 0.5), 3)
    
    for field_name in ("full_name", "location", "email", "phone_number"):
        if field_name in evidence:
            evidence[field_name]["section"] = _section_of(sections, evidence[field_name]["text"])

    return {
        "candidate": {
            "full_name": name,
            "email": email,
            "phone_number": phone,
            "location": location,
            "linkedin": web["linkedin"],
            "github": web["github"],
            "portfolio": web["portfolio"],
        },
        "professional_information": {
            "professional_summary": summary,
            "career_objective": objective,
            "total_experience": total_experience,
            "current_or_most_recent_role": most_recent_role,
        },
        "skills": {
            "technical_skills": technical,
            "programming_languages": categorized["programming_languages"],
            "frameworks": categorized["frameworks"],
            "libraries": categorized["libraries"],
            "databases": categorized["databases"],
            "cloud_technologies": categorized["cloud"],
            "devops_infrastructure": categorized["devops_infrastructure"],
            "tools": categorized["tools"],
            "other_relevant_technologies": categorized["other"],
        },
        "education": education,
        "projects": projects,
        "work_experience": experience,
        "certifications": _clean_items(lines_of(_section_body(sections, "CERTIFICATIONS"))),
        "achievements": _clean_items(lines_of(_section_body(sections, "ACHIEVEMENTS"))) + exams,
        "volunteering": _clean_items(lines_of(_section_body(sections, "VOLUNTEERING"))),
        "extraction_metadata": {
            "entity_model_used": model is not None,
            "section_count": len(sections),
            "detected_sections": [s["label"] for s in sections],
            "sections": [{"label": s["label"], "heading": s.get("heading"), "method": s.get("method"),
                          "confidence": s.get("confidence")} for s in sections],
            "field_confidence": confidence,
            "evidence": evidence,
            "skill_normalization": {
                "raw_skills": uniq(raw_skills),
                "normalized_skills": technical,
                "details": skill_details,
                "rejected_unknown": sorted(dropped),
                "non_technical": [d["skill"] for d in skill_details if d["category"] == "non_technical"],
            },
            "experience_analysis": analysis,
        },
    }

def parse_resume(text, components=None, links=None):
    components = components or Components()
    result = parse_resume_text(text, model=components.model, section_classifier=components.section_classifier,
                               skill_matcher=components.skill_matcher, links=links)
    
    result["extraction_metadata"]["components"] = components.info
    return result

def public_view(result, include_metadata=False):
    keys = OUTPUT_KEYS + (("extraction_metadata",) if include_metadata else ())
    return {key: result[key] for key in keys if key in result}
