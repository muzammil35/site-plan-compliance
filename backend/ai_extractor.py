"""Send PDF to Gemini and extract structured site plan measurements."""
import json
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

EXTRACTION_PROMPT = """You are analyzing an architectural site plan PDF. Extract the following measurements from the drawing.

For each field, return:
- value: the numeric value (null if not found)
- unit: the unit (e.g. "m", "ft", "m²")
- confidence: integer 0-100 (how confident you are in this reading)
- note: brief explanation of where/how you found it, or why you couldn't

IMPORTANT RULES:
- Read dimension labels and annotation text directly — do not estimate from pixel distances
- If units are ambiguous, note it and default to meters
- If a value cannot be reliably found, set value to null and confidence to 0
- Do not guess or interpolate missing values

Return ONLY valid JSON matching this exact schema:
{
  "lot_width": {"value": number|null, "unit": "m", "confidence": 0-100, "note": "..."},
  "lot_depth": {"value": number|null, "unit": "m", "confidence": 0-100, "note": "..."},
  "lot_area": {"value": number|null, "unit": "m²", "confidence": 0-100, "note": "..."},
  "building_width": {"value": number|null, "unit": "m", "confidence": 0-100, "note": "..."},
  "building_depth": {"value": number|null, "unit": "m", "confidence": 0-100, "note": "..."},
  "building_area": {"value": number|null, "unit": "m²", "confidence": 0-100, "note": "..."},
  "front_setback": {"value": number|null, "unit": "m", "confidence": 0-100, "note": "..."},
  "rear_setback": {"value": number|null, "unit": "m", "confidence": 0-100, "note": "..."},
  "side_setback_left": {"value": number|null, "unit": "m", "confidence": 0-100, "note": "..."},
  "side_setback_right": {"value": number|null, "unit": "m", "confidence": 0-100, "note": "..."},
  "building_height": {"value": number|null, "unit": "m", "confidence": 0-100, "note": "..."},
  "parking_spaces": {"value": number|null, "unit": "spaces", "confidence": 0-100, "note": "..."}
}"""


def extract_site_data(pdf_bytes: bytes) -> dict:
    """
    Send PDF to Gemini and return extracted measurements with confidence scores.
    Raises on API error; returns partial data if some fields are null.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=types.Content(parts=[
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            types.Part.from_text(text=EXTRACTION_PROMPT),
        ]),
    )

    raw = response.text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    extracted = json.loads(raw)

    # Derive lot_area and building_area from dimensions if not explicitly stated
    _fill_derived_fields(extracted)

    return extracted


def _fill_derived_fields(data: dict) -> None:
    """Compute area from width×depth if area not directly extracted."""
    for prefix in ("lot", "building"):
        area_field = f"{prefix}_area"
        w = data.get(f"{prefix}_width", {})
        d = data.get(f"{prefix}_depth", {})

        if (
            data.get(area_field, {}).get("value") is None
            and w.get("value") is not None
            and d.get("value") is not None
        ):
            derived = round(w["value"] * d["value"], 2)
            lower_conf = min(w["confidence"], d["confidence"])
            data[area_field] = {
                "value": derived,
                "unit": "m²",
                "confidence": lower_conf,
                "note": f"Derived from {prefix} width × depth ({w['value']} × {d['value']})",
            }
