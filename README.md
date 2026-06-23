# PlotPerfect — Zoning Compliance Checker

PlotPerfect lets users upload a residential site plan PDF, automatically extracts key measurements using an AI vision model, evaluates them against zoning bylaw rules, and returns an annotated PDF highlighting any compliance failures.

---

## Setup Instructions

### Prerequisites

- Python 3.12+
- Node.js 18+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

### Backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set: GEMINI_API_KEY=your_key_here

# Start the API server
uvicorn main:app --reload
# Runs on http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

Open `http://localhost:3000`, drag and drop a site plan PDF, and the results will appear within a few seconds.

### Evaluating the AI Extractor

To run accuracy tests against the generated and validation test plans:

```bash
cd backend
python generate_test_plans.py     # generate synthetic test PDFs
python eval.py                    # run extraction + score results
python eval.py --only generated   # generated plans only
```

---

## Assumptions

- **Units are metres.** All zoning rules are evaluated in metres. If a PDF uses feet or other units, the AI is instructed to note the ambiguity, but conversion is not automatic.
- **Site plans are single-page or the relevant drawing is on page 1.** The annotator overlays the first page only.
- **Dimension labels are readable text.** The AI reads annotation text directly from the PDF — it does not estimate measurements from pixel distances. Scanned/rasterised PDFs with no selectable text will produce lower confidence scores.
- **A single fixed zoning district.** The compliance rules are currently hardcoded to one RF1-style residential standard (see `backend/compliance_engine.py`). There is no multi-zone selector.
- **Lot coverage is derived when not labelled.** If lot coverage is not stated explicitly, it is computed from building area ÷ lot area when both are available.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  Browser (Next.js / React)                          │
│                                                     │
│  PDFUpload ──► page.tsx ──► DefectWindow            │
│                         └──► AnnotatedPDF           │
└───────────────────┬─────────────────────────────────┘
                    │  POST /api/analyze (multipart PDF)
                    ▼
┌─────────────────────────────────────────────────────┐
│  FastAPI Backend                                    │
│                                                     │
│  main.py                                            │
│    │                                                │
│    ├── ai_extractor.py                              │
│    │     Sends PDF to Gemini 2.5 Flash              │
│    │     Returns structured JSON (value/unit/       │
│    │     confidence/note per field)                 │
│    │                                                │
│    ├── compliance_engine.py                         │
│    │     Pure-Python rule evaluation                │
│    │     Computes PASS / FAIL / UNKNOWN per rule    │
│    │                                                │
│    └── pdf_annotator.py                             │
│          Overlays compliance summary + failure      │
│          banner onto the original PDF (PyMuPDF)     │
│          Returns base64-encoded annotated PDF       │
└─────────────────────────────────────────────────────┘
```

**Data flow:**
1. User uploads a PDF via the drag-and-drop interface.
2. The frontend POSTs it to `/api/analyze`.
3. The backend sends the PDF to Gemini 2.5 Flash, which returns structured extraction JSON.
4. The compliance engine evaluates each extracted value against the hardcoded rules.
5. PyMuPDF annotates the original PDF with a summary overlay and failure banner.
6. The response (extracted values, compliance results, summary counts, annotated PDF as base64) is returned to the frontend.
7. The frontend renders the compliance table and an inline PDF preview with a download button.

---

## Limitations

- **Single zoning district.** Rules are hardcoded for one residential zone. Different municipalities, zones, or bylaw versions are not supported without editing `compliance_engine.py`.
- **No unit conversion.** Drawings in imperial units will produce incorrect compliance results unless the AI correctly identifies and notes the discrepancy.
- **First page only.** Multi-sheet drawing sets (site plan, elevations, grading plan) are not supported. Only the first page is analysed and annotated.
- **AI extraction is probabilistic.** The model may miss, misread, or hallucinate dimensions, particularly on low-resolution scans, hand-annotated drawings, or densely labelled plans. Confidence scores indicate reliability but are not guarantees.
- **No authentication or file storage.** Each request is stateless — results are not saved, and there is no user account system.
- **20 MB file size limit.** Enforced by the backend. Very high-resolution PDFs may need to be compressed before upload.
- **Reliance on model without any way to properly verify reliability and accuracy.**
- **Annotated site plan only gives a complinace summary at the moment rather than annotating specific errors.**

---

## Future Improvements

- **Multi-zone support.** Allow users to select their zoning district or municipality from a dropdown, loading the appropriate rule set from a config file or database.
- **Multi-page / multi-sheet support.** Detect and extract from elevation drawings to reliably determine building height, and grading plans for finished grade references.
- **Unit detection and conversion.** Automatically detect imperial units and convert before compliance evaluation.
- **Streaming progress updates.** Use server-sent events to show extraction and evaluation progress steps rather than a single spinner.
- **Report export.** Generate a downloadable compliance report PDF summarising all findings, extracted values, and rule references.
- **User accounts and history.** Save past analyses so users can revisit, compare revisions, or share results with a reviewer.
- **Build a custom OCR+CAD model to reduce reliance on unauditable vision model.** Given this project was a 3-day MVP, I opted to go for the faster route by plugging into the gemini API, but a more mature project would make use of a parsing engine that could relay the results into a CAD model. Additionally, it might be beneficial to take the site plans generated from user, turn it into a DWG file (AutoCAD), then model the architecture in AUTOCAD so that there is no reliance on the vision LLM to make guesses.
- **Confidence-weighted review flags.** Automatically flag low-confidence extractions for manual review rather than treating them as UNKNOWN failures.
- **Admin rule editor.** A UI for configuring zoning rules without editing source code, enabling non-developer administrators to maintain the rule set.
