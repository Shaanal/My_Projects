"""uvicorn api.app:app --reload  ->  http://127.0.0.1:8000"""
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from inference.backend import APPROACH, load_components
from inference.parser import parse_resume, public_view
from preprocessing.ingest import SUPPORTED, clean_text, extract_links, extract_text

MAX_BYTES = 25 * 1024 * 1024
PAGE = Path(__file__).with_name("static") / "index.html"

app = FastAPI(title="Resume Parser", version="2.0.0",
              description=f"Upload a resume and receive structured JSON. Approach {APPROACH}.")
COMPONENTS = load_components()

@app.get("/", include_in_schema=False)
def page():
    return HTMLResponse(PAGE.read_text(encoding="utf-8"))

@app.get("/health")
def health():
    return {"status": "ok", "approach": APPROACH,
            "entity_model_loaded": COMPONENTS.model is not None,
            "section_classifier_loaded": COMPONENTS.section_classifier is not None,
            "components": COMPONENTS.info}

@app.post("/parse-resume")
async def parse_resume_endpoint(
        file: UploadFile = File(...),
        include_metadata: bool = Query(False, description="Add confidence, evidence and detected sections")):
    
    suffix = Path(file.filename or "resume.txt").suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(status_code=415, detail=f"Unsupported file extension: {suffix}")
    
    content = await file.read(MAX_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Upload exceeds 25 MB limit.")

    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            temp_name = tmp.name
        
        text = clean_text(extract_text(temp_name))
        if not text:
            raise HTTPException(status_code=422, detail="No text could be extracted from this resume.")
        
        result = parse_resume(text, COMPONENTS, links=extract_links(temp_name))
        
        return JSONResponse(public_view(result, include_metadata))
    
    except HTTPException:
        raise
    
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not parse resume: {exc}")
    
    finally:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)
