"""
Evaluate the AI extractor against known ground truth.

Usage:
  python eval.py                  # generated test plans + validation folder
  python eval.py --only generated # generated plans only
  python eval.py --only validation
"""

import json
import os
import sys
import glob
from dotenv import load_dotenv
from ai_extractor import extract_site_data

load_dotenv()

# ── Ground truth for the generated test plans ─────────────────────────────────
# null = field is intentionally not labelled on the drawing; AI should return null.
GENERATED_TRUTH = {
    "plan_compliant.pdf": {
        "lot_width":          18.0,
        "lot_depth":          38.0,
        "lot_area":           684.0,
        "building_width":     12.0,
        "building_depth":     14.0,
        "building_area":      168.0,
        "front_setback":      7.5,
        "rear_setback":       10.0,
        "side_setback_left":  2.0,
        "side_setback_right": 4.0,
        "building_height":    8.5,
        "parking_spaces":     2.0,
        "lot_coverage":       24.6,
    },
    "plan_failures.pdf": {
        "lot_width":          15.0,
        "lot_depth":          30.0,
        "lot_area":           450.0,
        "building_width":     12.5,
        "building_depth":     16.0,
        "building_area":      200.0,
        "front_setback":      4.5,
        "rear_setback":       5.0,
        "side_setback_left":  1.5,
        "side_setback_right": 1.0,
        "building_height":    11.2,
        "parking_spaces":     2.0,
        "lot_coverage":       44.4,
    },
    "plan_missing_height_rear.pdf": {
        "lot_width":          20.0,
        "lot_depth":          42.0,
        "lot_area":           840.0,
        "building_width":     11.0,
        "building_depth":     13.0,
        "building_area":      143.0,
        "front_setback":      6.5,
        "rear_setback":       None,   # not labelled
        "side_setback_left":  2.5,
        "side_setback_right": 3.0,
        "building_height":    None,   # not labelled
        "parking_spaces":     2.0,
        "lot_coverage":       17.0,
    },
    "plan_mostly_unlabelled.pdf": {
        "lot_width":          16.0,
        "lot_depth":          35.0,
        "lot_area":           None,   # not labelled
        "building_width":     None,   # not labelled
        "building_depth":     None,   # not labelled
        "building_area":      None,   # not labelled
        "front_setback":      None,   # not labelled
        "rear_setback":       None,   # not labelled
        "side_setback_left":  None,   # not labelled
        "side_setback_right": None,   # not labelled
        "building_height":    None,   # not labelled
        "parking_spaces":     None,   # not labelled
        "lot_coverage":       None,   # not labelled
    },
    "plan_setbacks_only.pdf": {
        "lot_width":          None,   # not labelled
        "lot_depth":          None,   # not labelled
        "lot_area":           None,   # not labelled
        "building_width":     None,   # not labelled
        "building_depth":     None,   # not labelled
        "building_area":      None,   # not labelled
        "front_setback":      6.0,
        "rear_setback":       7.5,
        "side_setback_left":  1.5,
        "side_setback_right": 2.5,
        "building_height":    None,   # not labelled
        "parking_spaces":     3.0,
        "lot_coverage":       None,   # not labelled
    },
}

TOLERANCE = 0.10  # 10% relative tolerance for numeric comparisons


def score_field(extracted_value, truth_value):
    """
    Returns one of: "correct", "missed", "false_positive", "wrong", "skip"
      skip         — truth is None AND model returned None (both agree nothing to find)
      correct      — both have a value within tolerance, or both None
      missed       — truth has a value but model returned None
      false_positive — truth is None but model returned a value
      wrong        — both have a value but outside tolerance
    """
    if truth_value is None and extracted_value is None:
        return "skip"
    if truth_value is None and extracted_value is not None:
        return "false_positive"
    if truth_value is not None and extracted_value is None:
        return "missed"
    # both have values
    rel_err = abs(extracted_value - truth_value) / max(abs(truth_value), 1e-9)
    return "correct" if rel_err <= TOLERANCE else "wrong"


def run_eval(pdf_path, truth):
    """Extract from a single PDF and score against truth dict. Returns result dict."""
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    try:
        extracted = extract_site_data(pdf_bytes)
    except Exception as e:
        return {"error": str(e)}

    fields = list(truth.keys()) if truth else list(extracted.keys())

    rows = []
    for field in fields:
        ext_field = extracted.get(field, {})
        ext_val   = ext_field.get("value") if isinstance(ext_field, dict) else None
        confidence = ext_field.get("confidence", 0) if isinstance(ext_field, dict) else 0
        truth_val = truth.get(field) if truth else "unknown"

        if truth is not None:
            outcome = score_field(ext_val, truth_val)
        else:
            outcome = "no_truth"

        rows.append({
            "field":      field,
            "truth":      truth_val,
            "extracted":  ext_val,
            "confidence": confidence,
            "outcome":    outcome,
        })

    return {"rows": rows}


def print_result(filename, result, truth_available):
    bar = "─" * 72
    print(f"\n{'━'*72}")
    print(f"  {filename}")
    print(f"{'━'*72}")

    if "error" in result:
        print(f"  ERROR: {result['error']}")
        return

    rows = result["rows"]

    # Header
    print(f"  {'Field':<24} {'Truth':>8}  {'Extracted':>10}  {'Conf':>5}  Outcome")
    print(f"  {bar}")

    counts = {"correct": 0, "missed": 0, "false_positive": 0, "wrong": 0, "skip": 0}

    for r in rows:
        truth_str = "—" if r["truth"] is None else str(r["truth"])
        ext_str   = "—" if r["extracted"] is None else str(r["extracted"])
        conf_str  = f"{r['confidence']}%" if r["extracted"] is not None else "  —"

        outcome = r["outcome"]
        if outcome == "correct":
            marker = "✓"
        elif outcome == "missed":
            marker = "✗ MISSED"
        elif outcome == "false_positive":
            marker = "! EXTRA"
        elif outcome == "wrong":
            marker = "✗ WRONG"
        elif outcome == "skip":
            marker = "· (both null)"
        else:
            marker = "? (no ground truth)"

        print(f"  {r['field']:<24} {truth_str:>8}  {ext_str:>10}  {conf_str:>5}  {marker}")

        if outcome in counts:
            counts[outcome] += 1

    if truth_available:
        total_scoreable = counts["correct"] + counts["missed"] + counts["false_positive"] + counts["wrong"]
        if total_scoreable > 0:
            pct = counts["correct"] / total_scoreable * 100
        else:
            pct = 100.0
        print(f"\n  {'─'*50}")
        print(f"  Score: {counts['correct']}/{total_scoreable} fields correct  ({pct:.0f}%)")
        print(f"         missed={counts['missed']}  wrong={counts['wrong']}  "
              f"false_positive={counts['false_positive']}  both-null={counts['skip']}")


def main():
    only = None
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        only = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

    base = os.path.dirname(__file__)
    plans_dir = os.path.join(base, "test_plans")
    val_dir   = os.path.join(plans_dir, "validation")
    val_truth_path = os.path.join(val_dir, "ground_truth.json")

    # Load validation ground truth if present
    val_truth = {}
    if os.path.exists(val_truth_path):
        with open(val_truth_path) as f:
            raw = json.load(f)
        val_truth = {k: v for k, v in raw.items() if not k.startswith("_")}

    results_summary = []

    # ── Generated plans ───────────────────────────────────────────────────────
    if only in (None, "generated"):
        print("\n" + "="*72)
        print("  GENERATED TEST PLANS  (known ground truth)")
        print("="*72)

        for filename, truth in GENERATED_TRUTH.items():
            path = os.path.join(plans_dir, filename)
            if not os.path.exists(path):
                print(f"\n  [skipping {filename} — file not found]")
                continue
            print(f"\nRunning extraction on {filename} ...")
            result = run_eval(path, truth)
            print_result(filename, result, truth_available=True)

            if "rows" in result:
                scoreable = [r for r in result["rows"] if r["outcome"] not in ("skip", "no_truth")]
                correct   = [r for r in scoreable if r["outcome"] == "correct"]
                pct = len(correct) / len(scoreable) * 100 if scoreable else 100
                results_summary.append((filename, f"{pct:.0f}%", len(correct), len(scoreable)))

    # ── Validation plans ──────────────────────────────────────────────────────
    if only in (None, "validation"):
        print("\n\n" + "="*72)
        print("  VALIDATION PLANS  (real PDFs)")
        print("="*72)

        val_pdfs = sorted(glob.glob(os.path.join(val_dir, "*.pdf")))
        if not val_pdfs:
            print("  No PDFs found in test_plans/validation/")
        else:
            for path in val_pdfs:
                filename = os.path.basename(path)
                truth = val_truth.get(filename)
                truth_available = truth is not None and any(v is not None for v in truth.values())
                print(f"\nRunning extraction on {filename} ...")
                result = run_eval(path, truth)
                print_result(filename, result, truth_available=truth_available)

                if truth_available and "rows" in result:
                    scoreable = [r for r in result["rows"] if r["outcome"] not in ("skip", "no_truth")]
                    correct   = [r for r in scoreable if r["outcome"] == "correct"]
                    pct = len(correct) / len(scoreable) * 100 if scoreable else 100
                    results_summary.append((filename, f"{pct:.0f}%", len(correct), len(scoreable)))

    # ── Summary table ─────────────────────────────────────────────────────────
    if results_summary:
        print("\n\n" + "="*72)
        print("  SUMMARY")
        print("="*72)
        for name, pct, correct, total in results_summary:
            bar_len = int(correct / max(total, 1) * 30)
            bar = "#" * bar_len + "." * (30 - bar_len)
            print(f"  [{bar}] {pct:>4}   {name}")
        print()


if __name__ == "__main__":
    main()
