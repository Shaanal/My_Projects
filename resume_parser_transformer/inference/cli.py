"""python3 -m inference.cli resume.pdf [--output out.json] [--with-metadata] [--no-model]"""
import argparse
import json
from pathlib import Path

from inference.backend import load_components
from inference.parser import parse_resume, public_view
from preprocessing.ingest import clean_text, extract_links, extract_text

def main():
    p = argparse.ArgumentParser(description="Extract structured fields from a resume")
    p.add_argument("resume")
    p.add_argument("--model", default=None, help="NER model folder (default: this project's model)")
    p.add_argument("--section-model", default=None, help="Section classifier (default: this project's model)")
    p.add_argument("--no-model", action="store_true", help="Rules and skill ontology only")
    p.add_argument("--with-metadata", action="store_true", help="Also output confidence, evidence and sections")
    p.add_argument("--output", default=None)
    a = p.parse_args()

    components = load_components(ner_path=a.model, section_path=a.section_model,
                                 use_ner=not a.no_model, use_sections=not a.no_model)
    text = clean_text(extract_text(a.resume))
    result = public_view(parse_resume(text, components, links=extract_links(a.resume)), a.with_metadata)

    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if a.output:
        Path(a.output).write_text(rendered, encoding="utf-8")
    print(rendered)

if __name__ == "__main__":
    main()
