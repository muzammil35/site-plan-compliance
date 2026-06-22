"""Evaluate extracted site data against zoning rules. Pure Python, no AI."""
from dataclasses import dataclass
from typing import Optional

RULES = {
    "front_setback":      {"min": 6.0,  "unit": "m",  "label": "Front Setback"},
    "rear_setback":       {"min": 7.5,  "unit": "m",  "label": "Rear Setback"},
    "side_setback_left":  {"min": 1.5,  "unit": "m",  "label": "Side Setback (Left)"},
    "side_setback_right": {"min": 1.5,  "unit": "m",  "label": "Side Setback (Right)"},
    "lot_coverage":       {"max": 45.0, "unit": "%",  "label": "Lot Coverage"},
    "building_height":    {"max": 10.0, "unit": "m",  "label": "Building Height"},
    "parking_spaces":     {"min": 2,    "unit": "spaces", "label": "Parking Spaces"},
}


@dataclass
class ComplianceResult:
    rule_key: str
    label: str
    required: str
    actual: Optional[str]
    status: str          # "PASS" | "FAIL" | "UNKNOWN"
    confidence: int
    note: str
    deficiency: Optional[float] = None   # positive = how much short of minimum


def evaluate(extracted: dict) -> list[ComplianceResult]:
    """Run all rules against extracted data and return results."""
    results = []

    # Compute derived lot_coverage if we have the pieces
    extracted = _inject_lot_coverage(extracted)

    for key, rule in RULES.items():
        field = extracted.get(key, {})
        value = field.get("value")
        confidence = field.get("confidence", 0)
        note = field.get("note", "")
        label = rule["label"]

        if value is None:
            results.append(ComplianceResult(
                rule_key=key,
                label=label,
                required=_fmt_required(rule),
                actual=None,
                status="UNKNOWN",
                confidence=0,
                note=note or "Value could not be extracted from the drawing.",
            ))
            continue

        if "min" in rule:
            passed = value >= rule["min"]
            deficiency = round(rule["min"] - value, 2) if not passed else None
        else:
            passed = value <= rule["max"]
            deficiency = round(value - rule["max"], 2) if not passed else None

        unit = rule["unit"]
        results.append(ComplianceResult(
            rule_key=key,
            label=label,
            required=_fmt_required(rule),
            actual=f"{value} {unit}",
            status="PASS" if passed else "FAIL",
            confidence=confidence,
            note=note,
            deficiency=deficiency,
        ))

    return results


def _fmt_required(rule: dict) -> str:
    unit = rule["unit"]
    if "min" in rule:
        return f"≥ {rule['min']} {unit}"
    return f"≤ {rule['max']} {unit}"


def _inject_lot_coverage(extracted: dict) -> dict:
    """Compute lot coverage % if not present but building_area and lot_area are."""
    if extracted.get("lot_coverage", {}).get("value") is not None:
        return extracted

    b = extracted.get("building_area", {})
    l = extracted.get("lot_area", {})

    if b.get("value") and l.get("value") and l["value"] > 0:
        coverage = round((b["value"] / l["value"]) * 100, 1)
        conf = min(b.get("confidence", 0), l.get("confidence", 0))
        extracted = dict(extracted)
        extracted["lot_coverage"] = {
            "value": coverage,
            "unit": "%",
            "confidence": conf,
            "note": f"Computed: {b['value']}m² ÷ {l['value']}m² = {coverage}%",
        }

    return extracted
