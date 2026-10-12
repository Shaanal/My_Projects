from dataclasses import dataclass, field, fields, is_dataclass
from typing import Optional, get_args, get_origin
import json

@dataclass
class Candidate:
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

@dataclass
class ProfessionalInformation:
    professional_summary: Optional[str] = None
    career_objective: Optional[str] = None
    total_experience: Optional[str] = None
    current_or_most_recent_role: Optional[str] = None

@dataclass
class Skills:
    technical_skills: list[str] = field(default_factory=list)
    programming_languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    libraries: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    cloud_technologies: list[str] = field(default_factory=list)
    devops_infrastructure: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    other_relevant_technologies: list[str] = field(default_factory=list)

@dataclass
class Education:
    degree: Optional[str] = None
    specialization: Optional[str] = None
    institution: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    grade: Optional[str] = None
    raw_text: Optional[str] = None

@dataclass
class Project:
    name: Optional[str] = None
    summary: Optional[str] = None
    technology_stack: list[str] = field(default_factory=list)
    role: Optional[str] = None
    responsibilities: list[str] = field(default_factory=list)

@dataclass
class WorkExperience:
    company: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsibilities: list[str] = field(default_factory=list)
    technologies_used: list[str] = field(default_factory=list)
    raw_text: Optional[str] = None

@dataclass
class Resume:
    candidate: Candidate = field(default_factory=Candidate)
    professional_information: ProfessionalInformation = field(default_factory=ProfessionalInformation)
    skills: Skills = field(default_factory=Skills)
    education: list[Education] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    work_experience: list[WorkExperience] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
    volunteering: list[str] = field(default_factory=list)
    extraction_metadata: dict = field(default_factory=dict)

# Only returned on request (API ?include_metadata=true, CLI/batch --with-metadata).
OPTIONAL = {"extraction_metadata"}

def validate(data, schema=Resume, path="resume"):
    problems = []
    if not isinstance(data, dict):
        return [f"{path}: expected an object"]
    
    expected = {f.name: f.type for f in fields(schema)}
    for key in expected.keys() - data.keys() - OPTIONAL:
        problems.append(f"{path}.{key}: missing")
    for key in data.keys() - expected.keys():
        problems.append(f"{path}.{key}: unexpected")
    
    for key, kind in expected.items():
        if key not in data:
            continue
        value, where = data[key], f"{path}.{key}"
        
        if is_dataclass(kind):
            problems += validate(value, kind, where)
        elif get_origin(kind) is list:
            if not isinstance(value, list):
                problems.append(f"{where}: expected a list")
                continue
            
            item = get_args(kind)[0]
            for i, entry in enumerate(value):
                if is_dataclass(item):
                    problems += validate(entry, item, f"{where}[{i}]")
                elif not isinstance(entry, item):
                    problems.append(f"{where}[{i}]: expected {item.__name__}")
        
        elif kind is dict and not isinstance(value, dict):
            problems.append(f"{where}: expected an object")
        elif get_origin(kind) is not None and value is not None and not isinstance(value, str):
            problems.append(f"{where}: expected a string or null")
    return problems

if __name__ == "__main__":
    import sys
    for name in sys.argv[1:] or ["sample_output.json"]:
        issues = validate(json.loads(open(name, encoding="utf-8").read()))
        print(f"{name}: {'OK' if not issues else issues}")
