import argparse
import json
import re
from pathlib import Path

from inference.backend import load_components
from inference.parser import parse_resume, public_view
from preprocessing.ingest import SUPPORTED, clean_text, extract_links, extract_text

def safe_id(path, index):
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", path.stem).strip("_") or "resume"
    return f"{stem}_{path.suffix.lower().lstrip('.') or 'file'}_{index:04d}"

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", default="data/input")
    p.add_argument("--text-output", default="data/extracted")
    p.add_argument("--json-output", default="data/parsed")
    p.add_argument("--model", default=None, help="NER model folder, or 'none' for the rules baseline")
    p.add_argument("--with-metadata", action="store_true", help="Keep extraction_metadata in the saved JSON")
    a = p.parse_args()

    input_dir, text_dir, json_dir = Path(a.input), Path(a.text_output), Path(a.json_output)
    files = sorted(x for x in input_dir.rglob("*") if x.is_file() and x.suffix.lower() in SUPPORTED)
    if not files:
        raise SystemExit(f"No supported documents found in {input_dir}")
    text_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

    baseline = (a.model or "").lower() == "none"
    components = load_components(ner_path=None if baseline else a.model, use_ner=not baseline, use_sections=not baseline)
    print(f"Components: {components.info}")

    manifest, successes = [], 0
    for index, path in enumerate(files, 1):
        rid = safe_id(path, index)
        item = {"resume_id": rid, "source_file": str(path), "status": "error", "characters": 0, "error": None}
        try:
            text = clean_text(extract_text(str(path)))
            if not text:
                raise ValueError("No text extracted")
            (text_dir / f"{rid}.txt").write_text(text, encoding="utf-8")
            result = public_view(parse_resume(text, components, links=extract_links(str(path))), a.with_metadata)
            (json_dir / f"{rid}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            item.update(status="success", characters=len(text))
            successes += 1
        except Exception as exc:
            item["error"] = str(exc)
        manifest.append(item)
        print(f"[{item['status'].upper()}] {path.name}" + (f" - {item['error']}" if item["error"] else ""))

    (text_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Completed {successes}/{len(files)}")

if __name__ == "__main__":
    main()
