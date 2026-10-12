import re
from inference.patterns import (ACTION_START, COURSE_START, DATE, DATE_RANGE, DATE_TEXT, DEGREE_ABBR,
                                DEGREE_WORDS, EXAM, INSTITUTION, LINK_TEXT, OPEN_END, PROJECT_TYPE,
                                ROLE_LINE, ROLE_WORDS, entity_values, is_date_line, join_wrapped,
                                mentions, month_index, strip_dates, title_like, uniq, years)
from preprocessing.normalize import classify_roles, lookup_skill, normalize_skill

PART_SPLIT = r"\s*[,|]\s*|\s+[–—-]\s+"

def skills_in(text, entities, find_skills):
    return uniq([normalize_skill(s) for s in find_skills(text, entities)])

# ---------- education ----------

def _is_degree(line):
    return bool(DEGREE_ABBR.search(line) or DEGREE_WORDS.search(line) or COURSE_START.match(line))

def _education_entries(body):
    merged = []
    for line in [t for t, _ in join_wrapped(body)]:
        if not line:
            continue
        continues_name = (merged and INSTITUTION.search(merged[-1]) and not merged[-1].endswith(",")
                          and len(line.split()) <= 3 and not re.search(r"\d", line) and title_like(line)
                          and not _is_degree(line) and not INSTITUTION.search(line))
        if continues_name:
            merged[-1] += " " + line
        else:
            merged.append(line)

    entries, current, has = [], None, set()
    for line in merged:
        kinds = set()
        if EXAM.search(line) and not _is_degree(line):
            kinds.add("exam")
        if _is_degree(line):
            kinds.add("degree")
        if INSTITUTION.search(DEGREE_WORDS.sub(" ", line)):  # "Higher Secondary School" is a degree
            kinds.add("institution")
        if DATE_RANGE.search(line) or is_date_line(line):
            kinds.add("date")

        repeats = kinds & has and kinds - {"date"} <= has
        after_exam = current and current[0] == "exam" and kinds & {"degree", "institution"}
        if current is None or "exam" in kinds or repeats or after_exam:
            current = ["exam" if "exam" in kinds else "degree", []]
            entries.append(current)
            has = set()
        current[1].append(line)
        has |= kinds
    return [(kind, lines) for kind, lines in entries if lines]

def _degree_of(lines, block, degrees):
    degree = next((d for d in degrees if mentions(block, d)), None)
    if degree is None:
        line = next((x for x in lines if _is_degree(x)), None)
        if line:
            parts = [p.strip() for p in re.split(PART_SPLIT, line) if p.strip()]
            degree = next((p for p in parts if _is_degree(p) and not DATE.fullmatch(p)), line)
            degree = re.sub(rf"^\W*{DATE_TEXT}\W*", "", degree, flags=re.I).strip() or None
    return degree

def _institution_of(lines, block, institutions, degree):
    institution = next((i for i in institutions if mentions(block, i)), None)
    if institution:
        full = next((p.strip() for x in lines for p in re.split(PART_SPLIT, x)
                     if institution.lower() in p.lower() and len(p) > len(institution)
                     and INSTITUTION.search(p) and not _is_degree(p) and not DATE.search(p)), None)
        return full or institution

    parts = [p.strip() for x in lines for p in re.split(PART_SPLIT, x) if p.strip()]
    candidates = [p for p in parts if INSTITUTION.search(DEGREE_WORDS.sub(" ", p)) and p != degree]
    candidates.sort(key=lambda p: not re.search(r"\b(?:University|College|Institute|IIT|IIIT|NIT)\b", p))
    return candidates[0] if candidates else None

def _specialization_of(block, degree, specializations):
    found = next((s for s in specializations if mentions(block, s)), None)
    if found:
        return found
    labelled = re.search(r"\bspeciali[sz]ation\b\s*[:\-]?\s*([^\n|;,]+)", block, re.I)
    if labelled:
        return labelled.group(1).strip()
    if degree: 
        field = re.search(r"\b(?:in|of)\s+([A-Z][A-Za-z &]+?)(?:\s*[,(|\-–]|\s+\d|$)", degree)
        if field and not re.match(r"(?:Science|Arts|Engineering|Technology)$", field.group(1).strip()):
            return field.group(1).strip()
    return None

def parse_education(body, entities):
    if not body:
        return [], []
    degrees = entity_values(entities, ["DEGREE"])
    institutions = entity_values(entities, ["INSTITUTION"])
    specializations = entity_values(entities, ["SPECIALIZATION"])

    output, exams, seen = [], [], set()
    for kind, lines in _education_entries(body):
        block = "\n".join(lines)
        if kind == "exam":
            exams.append(" | ".join(x for x in lines if not is_date_line(x)))
            continue

        degree = _degree_of(lines, block, degrees)
        institution = _institution_of(lines, block, institutions, degree)

        span = DATE_RANGE.search(block)
        if span:
            start_year = years(span.group("start"))[0]
            end = span.group("end")
            end_year = "Present" if re.fullmatch(OPEN_END, end, re.I) else years(end)[0]
        else:
            found = years(block)
            start_year, end_year = (found[0], found[-1]) if found else (None, None)

        key = ((degree or "").lower(), (institution or "").lower())
        if key in seen and any(key):
            continue  # same course listed twice
        seen.add(key)

        grade = re.search(r"\b(?:CGPA|GPA|percentage|score|grade|marks)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?\s*%?)",
                          block, re.I)
        output.append({
            "degree": degree,
            "specialization": _specialization_of(block, degree, specializations),
            "institution": institution,
            "start_year": start_year,
            "end_year": end_year,
            "grade": grade.group(1).strip() if grade else None,
            "raw_text": block.strip(),
        })
    return output, exams

# ---------- experience ----------

def _is_new_job(line, current, upcoming=()):
    line = line.strip()
    if not current or not line or line[0].islower(): 
        return False

    if ROLE_WORDS.search(line) and any(ROLE_WORDS.search(x) for x in current):
        clause = re.search(r",\s+[a-z]", line) or line.endswith(".")
        if len(line.split()) <= 8 and not ACTION_START.match(line) and not clause:
            return True
    if DATE.search(line) and any(DATE.search(x) for x in current):
        return True
    if not any(DATE.search(x) for x in current):
        return False
    if line.lower().startswith(("skills", "technologies", "tools used", "tech stack")):
        return False
    if ACTION_START.match(line) or len(line.split()) > 10:
        return False
    if not any(DATE.search(x) for x in upcoming[:2]):
        return False
    return bool(re.match(r"^[A-Za-z0-9][A-Za-z0-9&.,'()/ -]{0,80}$", line))

def _date_range(chunk):
    match = DATE_RANGE.search(chunk)
    if match:
        end = match.group("end")
        return match.group("start"), ("Present" if re.fullmatch(OPEN_END, end, re.I) else end)
    dates = DATE.findall(chunk)
    
    if not dates:
        return None, None
    if len(dates) > 1:
        return dates[0], dates[-1]
    return dates[0], ("Present" if re.search(r"\bpresent\b|\bcurrent\b", chunk, re.I) else None)

def _split_title_line(line):
    parts = [p.strip(" ,.") for p in re.split(r"\s+(?:at|@)\s+|\s+[–—-]\s+|\s*\|\s*|,\s+", line)
             if p.strip(" ,.")]
    parts = [p for p in parts if not DATE.search(p) and not re.fullmatch(OPEN_END, p, re.I)]
    role = next((p for p in parts if ROLE_WORDS.search(p)), None)
    
    company = next((p for p in parts if p != role and len(p.split()) <= 8), None)
    rest = [p for p in parts if p not in (role, company)]
    location = None
    
    if rest and len(rest[-1].split()) <= 3 and re.fullmatch(r"[A-Z][A-Za-z .'-]+", rest[-1]):
        location = rest[-1]
    return role, company, location

def _plausible_company(value, excluded):
    if not value:
        return False
    v = value.strip()
    
    return (len(v.split()) <= 6 and not v.endswith(".")
            and not re.fullmatch(OPEN_END, v, re.I) and not DATE.fullmatch(v)
            and not re.match(r"^[A-Za-z]+ed\b", v) and not ACTION_START.match(v)
            and v.lower() not in excluded and not lookup_skill(v))

def _location_from_date_line(line):
    rest = DATE_RANGE.sub("", line) if DATE_RANGE.search(line) else DATE.sub("", line)
    rest = re.sub(OPEN_END, "", rest, flags=re.I).strip(" ,|–—-()")
    if rest and len(rest.split()) <= 4 and re.fullmatch(r"[A-Z][A-Za-z .,'-]+", rest):
        return rest
    return None

def _job_chunks(items):
    lines = [t for t, _ in items]
    chunks, current = [], []
    
    for index, (line, bullet) in enumerate(items):
        next_line = lines[index + 1] if index + 1 < len(lines) else None
        project_style = current and not bullet and is_project_start(line, next_line)
        if not bullet and _is_new_job(line, [t for t, _ in current], lines[index + 1:index + 3]) or project_style:
            chunks.append(current)
            current = []
        current.append((line, bullet))
    
    if current:
        chunks.append(current)
    return chunks

def parse_experience(body, entities, find_skills):
    if not body:
        return []
    companies = entity_values(entities, ["COMPANY", "ORG"])
    titles = entity_values(entities, ["JOB_TITLE", "DESIGNATION"])
    locations = entity_values(entities, ["LOCATION", "GPE"])
    excluded = {x.lower() for x in locations + entity_values(entities, ["PERSON"])}

    result = []
    for items in _job_chunks(join_wrapped(body)):
        lines = [t for t, _ in items]
        if not lines:
            continue
        chunk = "\n".join(lines)
        start_date, end_date = _date_range(chunk)
        company = next((x for x in companies if mentions(chunk, x)), None)
        title = next((x for x in titles if mentions(chunk, x)), None)

        title_line = next((x for x in lines[:3] if ROLE_WORDS.search(x) and not ACTION_START.match(x)
                           and len(x.split()) <= 12), None)
        split_location = None
        if title_line:
            split_role, split_company, split_location = _split_title_line(title_line)
            if title is None or split_role and title.lower() in split_role.lower() and len(split_role) > len(title):
                title = split_role  # keep the full title
            if company is None and _plausible_company(split_company, excluded):
                company = split_company
        title = (classify_roles([title]) or [title])[0] if title else title
        if company is None:
            company = next((x for x in lines[:3] if x != title and x != title_line and not DATE.search(x)
                            and _plausible_company(x, excluded) and not re.search(r",\s*[A-Z]{2}$", x)), None)

        header_area = "\n".join(x for x in lines if len(x.split()) <= 8 or is_date_line(x))
        location = next((x for x in locations if mentions(header_area, x)), None)
        if location is None:
            location = next((loc for loc in (_location_from_date_line(x) for x in lines[:4] if DATE.search(x))
                             if loc), None)
        location = location or split_location

        header_lines = {title_line, company}
        action_words = ("improved", "spearheaded", "directed", "acted", "boosted", "initiated",
                        "collaborated", "joined", "configured", "installed", "maintained")
        
        responsibilities = [t for t, b in items if t not in header_lines and len(t.split()) >= 4
                            and (b or ACTION_START.match(t) or t.lower().startswith(action_words))]
        if not responsibilities:  # no bullets: use the description lines
            responsibilities = [t for t in lines if t not in header_lines and len(t.split()) >= 4
                                and not is_date_line(t) and not ROLE_WORDS.search(t[:40])
                                or t not in header_lines and len(t.split()) >= 8]

        record = {
            "company": company,
            "designation": title,
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "responsibilities": responsibilities,
            "technologies_used": skills_in(chunk, entities, find_skills),
            "raw_text": chunk,
        }
        
        if result and not (company or title or start_date):
            previous = result[-1]
            previous["responsibilities"] += [r for r in responsibilities if r not in previous["responsibilities"]]
            previous["technologies_used"] = uniq(previous["technologies_used"] + record["technologies_used"])
            previous["raw_text"] += "\n" + chunk
            continue
        result.append(record)
    
    return result

def experience_analysis(experience):
    intervals = []
    for index, item in enumerate(experience):
        start = month_index(item.get("start_date"))
        end = month_index(item.get("end_date")) if item.get("end_date") else start
        if start is not None and end is not None and end >= start:
            intervals.append((start, end + 1, index))

    merged = []
    for start, end, _ in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    total = sum(end - start for start, end in merged)

    overlaps, duplicates = [], []
    for i, (s1, e1, a) in enumerate(intervals):
        for s2, e2, b in intervals[i + 1:]:
            months = min(e1, e2) - max(s1, s2)
            if months <= 0:
                continue
            first, second = experience[a], experience[b]
            same_company = (first.get("company") or "").lower() == (second.get("company") or "").lower()
            same_role = (first.get("designation") or "").lower() == (second.get("designation") or "").lower()
            pair = {"entries": [a, b], "overlap_months": months}
            (duplicates if same_company and same_role and first.get("company") else overlaps).append(pair)

    def as_text(m):
        y, rest = divmod(max(m, 0), 12)
        parts = ([f"{y} year{'s' if y != 1 else ''}"] if y else []) + \
                ([f"{rest} month{'s' if rest != 1 else ''}"] if rest else [])
        return " ".join(parts) or "0 months"

    return {
        "total_months": total if intervals else None,
        "total_experience": as_text(total) if intervals else None,
        "dated_entries": len(intervals),
        "overlapping_entries": overlaps,
        "duplicate_entries": duplicates,
    }

# ---------- projects ----------

def is_project_start(line, next_line=None):
    line = line.strip()
    if not line:
        return False
    if re.match(r"^(?:\d+[\.)]?\s*)?(?:projects?|project)\b", line, re.I):
        return True
    
    if (next_line and ROLE_LINE.match(next_line.strip()) and len(line.split()) <= 8 and len(line) <= 80
            and re.match(r"^[A-Za-z][A-Za-z0-9&.'()/ -]{1,79}$", line) and not ACTION_START.match(line)):
        return True
    if line[0].islower() or DATE.search(line):
        return False
    
    return bool(re.match(r"^(?:\d+[\.)]?\s*)?[A-Za-z][A-Za-z0-9&.,'()/ -]{1,60}?(?:\s*:\s+|\s+[-–—]\s+).*$", line)
                and len(line.split()) <= 12)

def _project_chunks(items):
    items = [(t, b) for t, b in items if not LINK_TEXT.match(t)]
    chunks, current = [], []
    
    for index, (text, bullet) in enumerate(items):
        upcoming = [t for t, _ in items[index + 1:index + 3]]
        title_then_date = (not bullet and len(text.split()) <= 10 and not text.endswith((".", ","))
                           and not is_date_line(text) and any(is_date_line(u) for u in upcoming))
        titled_bullet = (bullet and re.match(r"^[A-Z][\w .&'+/-]{1,50}?:\s*\S", text) is not None
                         and not re.match(r"^(?:tech|tools|stack|role|skills|languages|team|duration|link|"
                                          r"frameworks|libraries|platform|environment|result|impact)", text, re.I))
        
        explicit = not bullet and is_project_start(text, upcoming[0] if upcoming else None)
        starts = explicit or title_then_date or titled_bullet

        has_body = any(b or len(t.split()) >= 5 for t, b in current[1:]) or titled_bullet and current
        
        if current and starts and has_body:
            chunks.append(current)
            current = []
        current.append((text, bullet))
    
    if current:
        chunks.append(current)
    return chunks

def parse_projects(body, entities, find_skills):
    if not body:
        return []
    project_names = entity_values(entities, ["PROJECT_NAME"])

    output = []
    for items in _project_chunks(join_wrapped(body)):
        lines = [t for t, _ in items]
        if not lines or all(is_date_line(x) for x in lines[1:]) and len(lines) <= 2 and not items[0][1]:
            continue  
        chunk = "\n".join(lines)
        first_line = lines[0]

        name = next((x for x in project_names if mentions(chunk, x)), None)
        if name is None:
            if re.match(r"^(?:\d+[\.)]?\s*)?(?:projects?|project)\b", first_line, re.I):
                name = first_line.split(":", 1)[-1].strip() or first_line
            else:
                name = re.split(r"\s*:\s*", first_line, maxsplit=1)[0]  # title before the colon
        name = strip_dates(name) or name

        role = next((x for x in lines[1:] if len(x.split()) <= 5 and not x.endswith((".", ","))
                     and "," not in x and ROLE_LINE.match(x)), None)
        
        body_lines = lines[lines.index(role) + 1 if role else 1:]
        if body_lines and PROJECT_TYPE.match(body_lines[0].strip()):
            body_lines = body_lines[1:]  # "Academic Projects" / "Personal Project"
        
        summary = [strip_dates(x) for x in body_lines
                   if not is_date_line(x) and not re.match(r"^(technologies|tech stack|tools used)\s*[:\-]", x, re.I)]
        summary = [x for x in summary if x]
        
        inline = re.split(r"\s*:\s*", first_line, maxsplit=1)
        if len(inline) == 2 and inline[0] == name:
            summary.insert(0, inline[1])

        role = role or next((e["text"] for e in entities
                             if e.get("label", "").upper() in {"ROLE", "JOB_TITLE"} and mentions(chunk, e["text"])),
                            None)
        bullets = [strip_dates(t) for t, b in items[1:] if b]

        output.append({
            "name": name,
            "summary": " ".join(summary) or None,
            "technology_stack": skills_in(chunk, entities, find_skills),
            "role": role,
            "responsibilities": bullets or [x for x in summary if ACTION_START.match(x)],
        })
    return output
