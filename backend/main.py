"""FastAPI backend for PlotPrefect compliance analysis."""
import os
from dataclasses import asdict
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from ai_extractor import extract_site_data
from compliance_engine import evaluate
from pdf_annotator import annotate_pdf

load_dotenv()

app = FastAPI(title="PlotPrefect API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_PDF_MB = 20


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Only PDF files are accepted.")

    pdf_bytes = await file.read()

    if len(pdf_bytes) > MAX_PDF_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_PDF_MB} MB limit.")

    if len(pdf_bytes) < 100:
        raise HTTPException(400, "File appears to be empty or corrupt.")

    try:
        extracted = extract_site_data(pdf_bytes)
    except Exception as e:
        raise HTTPException(502, f"Extraction failed: {str(e)}")

    results = evaluate(extracted)

    try:
        annotated_pdf_b64 = annotate_pdf(pdf_bytes, results)
    except Exception:
        annotated_pdf_b64 = None

    return JSONResponse({
        "extracted": extracted,
        "compliance": [asdict(r) for r in results],
        "annotated_pdf": annotated_pdf_b64,
        "summary": {
            "total": len(results),
            "pass": sum(1 for r in results if r.status == "PASS"),
            "fail": sum(1 for r in results if r.status == "FAIL"),
            "unknown": sum(1 for r in results if r.status == "UNKNOWN"),
        },
    })
