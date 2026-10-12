import re
from datetime import date

from preprocessing.normalize import AMBIGUOUS_FORMS, VOCAB

# ---------- contact ----------
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)

PHONE = re.compile(r"(?<![\d+])(?:\+?\(?\d[\d \t().-]{7,}\d)(?!\w)")

URL = re.compile(r"(?:https?://)?(?:www\.)?(?:linkedin\.com/in/[\w-]+|github\.com/[\w-]+|"
                 r"[\w.-]+\.[a-z]{2,}(?:/[\w./-]*)?)", re.I)

ADDRESS = re.compile(r"^\d+\s+\w+.*\b(?:Ave|Avenue|St|Street|Rd|Road|Blvd|Lane|Ln|Drive|Dr|Way|Nagar|Colony)\b\.?"
                     r"|\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b|\b\d{6}\b")

# ---------- dates ----------
MONTH = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
         r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")

DATE_TEXT = (rf"(?:{MONTH}\.?,?\s*'?(?:19|20)\d{{2}}|(?:0?[1-9]|1[0-2])\s*[/.]\s*(?:19|20)\d{{2}}|"
             r"(?:19|20)\d{2})")

OPEN_END = r"present|current(?:ly)?|now|till\s+date|to\s+date|ongoing|today"

DATE = re.compile(rf"\b{DATE_TEXT}\b", re.I)

DATE_RANGE = re.compile(
    rf"\b(?P<start>{DATE_TEXT})\s*(?:-|–|—|to|till|until|through)\s*(?P<end>{DATE_TEXT}|{OPEN_END})\b", re.I)

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun",
                                      "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

# ---------- jobs, education, projects ----------
ROLE_WORDS = re.compile(
    r"\b(?:developer|engineer|analyst|manager|intern|consultant|designer|scientist|lead|architect|"
    r"specialist|officer|administrator|director|executive|coordinator|recruiter|accountant|assistant|"
    r"programmer|technician|head|founder|teacher|researcher|associate)\b", re.I)

ROLE_LINE = re.compile(
    r"^(?:senior\s+|junior\s+|lead\s+|full[- ]?stack\s+|web\s+|software\s+|frontend\s+|back[- ]?end\s+)?"
    r"(?:developer|engineer|designer|analyst|manager|consultant|intern|architect|administrator|specialist)\b", re.I)

ACTION_START = re.compile(
    r"^(?:developed|built|designed|implemented|created|led|managed|worked|supported|automated|"
    r"analyzed|analysed|responsible)\b", re.I)

SENTENCE_START = re.compile(r"^(?:[A-Z][a-z]+(?:ing|ed)|Responsible|Worked|Built|Led|Managed|Helped)\b")

# Degree abbreviations are case-sensitive ("BE" is a degree, "be" is not).

DEGREE_ABBR = re.compile(
    r"(?<![A-Za-z])(?:B\.?\s?Tech|M\.?\s?Tech|B\.?E\.|BE|M\.?E\.|B\.?Sc|M\.?Sc|B\.?S\.|BS|M\.?S\.|MS|B\.?A\.|BA|"
    r"M\.?A\.|MA|B\.?Com|M\.?Com|BBA|MBA|MCA|BCA|Ph\.?\s?D|HSC|SSC|CBSE|ICSE|1[02]th|Class\s+(?:XII|X|1[02]))(?![A-Za-z])")

DEGREE_WORDS = re.compile(
    r"\b(?:Bachelor|Master|Doctor(?:ate)?|Diploma|Associate Degree|(?:Higher|Senior) Secondary(?: School)?|"
    r"Secondary School|Intermediate|Matriculation|High School|A[- ]Levels?|O[- ]Levels?)\b", re.I)

COURSE_START = re.compile(r"^(?:\W*(?:19|20)\d{2}\W*)?(?:Advanced |Online |Professional |Short )?"
                          r"(?:Course|Certificate|Certification)\b", re.I)

EXAM = re.compile(r"\b(?:JEE|GATE|GRE|GMAT|TOEFL|IELTS|SAT|NEET|UPSC|KVPY|Olympiad)\b")

INSTITUTION = re.compile(r"\b(?:University|College|Institute|School|Academy|Polytechnic|Vidyalaya|"
                         r"IIT|IIIT|NIT|BITS)\b")

PROJECT_TYPE = re.compile(r"^(?:(?:academic|personal|course|college|team|group|individual|freelance|"
                          r"hackathon|research|side|open[- ]source)\s*)+(?:projects?|work)?$", re.I)

# ---------- line handling ----------

BULLET = re.compile(r"^\s*[•▪●◦·‣⁃\-–*]\s+")

CONNECTIVE_END = re.compile(r"(?:[,&(+/]|\b(?:and|or|of|with|using|for|to|the|a|an|in|on|at|by|via|from|"
                            r"under|including|such as))$", re.I)

LINK_TEXT = re.compile(r"^(?:the\s+)?(?:links?|live\s+demo|demo|source\s+code|repo(?:sitory)?|click\s+here|"
                       r"github\s+link|website\s+link)\b", re.I)

# ---------- skills ----------

SKILL_LABELS = {"SKILL", "PROGRAMMING_LANGUAGE", "FRAMEWORK", "DATABASE", "CLOUD_PLATFORM",
                "DEVOPS_TOOL", "PROJECT_TECHNOLOGY", "TOOL"}

CATEGORY_LABEL = re.compile(r"\b(?:based|related|oriented|skills?|tools?|technologies|languages|frameworks|"
                            r"libraries|databases|platforms|others?|misc)$", re.I)

SKILL_FILLER = re.compile(r"^(?:familiar|knowledge|experience|experienced|excellent|good|strong|proficient|"
                          r"working|basic|expert|hands|ability|able|skilled|understanding)\b", re.I)

# Every unambiguous ontology form in one pattern, longest first ("react native" before "react").

VOCAB_PATTERN = re.compile(r"(?<![a-z0-9+#.])(?:" + "|".join(re.escape(v).replace(r"\ ", r"\s+") for v in VOCAB)                           + r")(?![a-z0-9+#]|\.[a-z0-9])", re.I)

# Ambiguous names (C, R, Go, Spring) only inside a list: (strict separators, loose separators).
AMBIGUOUS_PATTERNS = {
    skill: tuple(re.compile(rf"(?:^|{sep})\s*{re.escape(skill)}\s*(?={sep}|$)", re.M)
                 for sep in (r"[,|/;:•·()\n]", r"[,|/;:•·()\n\s]"))
    for skill in sorted(AMBIGUOUS_FORMS)  # sorted: same order on every run
}

# ---------- list-section clean-up ----------
JUNK_LINE = re.compile(r"\b(?:resume templates?|build this template|powered by|page \d+|curriculum vitae)\b", re.I)

COUNTRIES = {"united states", "usa", "united kingdom", "uk", "india", "canada", "australia", "germany",
             "france", "israel", "united arab emirates", "uae"}

LINK_WORDS = {"linkedin", "github", "portfolio", "website", "twitter", "behance", "dribbble", "email", "phone"}

# ---------- helpers ----------

def uniq(items):
    result, seen = [], set()
    for item in items:
        item = item.strip(" \t•-*|")
        if item and item.lower() not in seen:
            result.append(item)
            seen.add(item.lower())
    return result

def mentions(text, value):
    value = (value or "").strip()
    pattern = r"(?<![A-Za-z0-9])" + re.escape(value) + r"(?![A-Za-z0-9])"
    return len(value) >= 2 and re.search(pattern, text, re.I) is not None

def entity_values(entities, labels):
    labels = {x.upper() for x in labels}
    return uniq([e["text"] for e in entities if e.get("label", "").upper() in labels])

def years(text):
    return re.findall(r"\b(?:19|20)\d{2}\b", text)

def is_date_line(text):
    if not DATE.search(text):
        return False
    rest = re.sub(OPEN_END, " ", DATE.sub(" ", DATE_RANGE.sub(" ", text)), flags=re.I)
    return len(re.findall(r"[A-Za-z]{2,}", rest)) <= 3

def strip_dates(text):
    text = DATE_RANGE.sub(" ", text)
    text = re.sub(rf"^\W*{DATE_TEXT}\W*", "", text, flags=re.I)
    return " ".join(text.split()).strip(" ,|–—-")

def title_like(text):
    words = text.split()
    if not words or len(words) > 8 or text.endswith((".", ",")):
        return False
    if ROLE_WORDS.search(text):
        return True
    small = {"and", "of", "for", "in", "the", "a", "with", "&", "-", "–", "|", "on", "at", "to"}
    return all(w[:1].isupper() or w[:1].isdigit() or w.lower() in small for w in words)

def lines_of(body):
    return [x.strip(" \t•-*|") for x in (body or "").splitlines() if x.strip()]

def join_wrapped(body):
    raw_lines = [x for x in (body or "").splitlines() if x.strip()]
    raw_lines = [x for x in raw_lines if not LINK_TEXT.match(BULLET.sub("", x).strip())]

    out = []
    for index, raw in enumerate(raw_lines):
        bullet = bool(BULLET.match(raw))
        text = BULLET.sub("", raw).strip(" \t•*|")
        if not text:
            continue

        upcoming = BULLET.sub("", raw_lines[index + 1]).strip() if index + 1 < len(raw_lines) else ""
        is_title = is_date_line(upcoming) and len(text.split()) > 2
        if out and not bullet and not is_date_line(text) and not is_title:
            prev, prev_bullet = out[-1]
            unfinished = not prev.endswith((".", ":", ";", "!", "?", ")"))
            sentence = prev_bullet or SENTENCE_START.match(prev) and len(prev.split()) >= 4
            lone_name = len(text.split()) <= 2 and prev.split()[-1][:1].isupper()  # "...Kamal" / "Karlapalem"
            if (text[0].islower() or CONNECTIVE_END.search(prev)
                    or sentence and unfinished and (not title_like(text) or lone_name)):
                out[-1] = (prev + " " + text, prev_bullet)
                continue
        out.append((text, bullet))
    return out

def month_index(value, today=None):
    if not value:
        return None
    today = today or date.today()
    v = value.strip().lower()
    if re.fullmatch(OPEN_END, v):
        return today.year * 12 + today.month - 1
    year = re.search(r"(?:19|20)\d{2}", v)
    if not year:
        return None

    month = 1
    name = re.match(r"([a-z]{3})", v)
    numeric = re.match(r"(\d{1,2})\s*[/.]", v)
    if name and name.group(1) in MONTHS:
        month = MONTHS[name.group(1)]
    elif numeric:
        month = int(numeric.group(1))
    return int(year.group()) * 12 + month - 1

def find_phone(text):
    for match in PHONE.finditer(text):
        value = match.group(0).strip()
        if not 9 <= len(re.sub(r"\D", "", value)) <= 15:
            continue
        if re.fullmatch(r"(?:(?:19|20)\d{2}[\s.\-–/]*){2,}", value):
            continue
        return value
    return None
