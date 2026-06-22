"""Annotate PDF pages with failure callouts using PyMuPDF."""
import base64
import fitz  # PyMuPDF
from compliance_engine import ComplianceResult

RED = (0.85, 0.1, 0.1)
ORANGE = (1.0, 0.55, 0.0)
GREEN = (0.1, 0.65, 0.1)
WHITE = (1.0, 1.0, 1.0)

# Where to place the summary callout box on the first page (relative to page)
CALLOUT_X_FRAC = 0.02
CALLOUT_Y_FRAC = 0.02


def annotate_pdf(pdf_bytes: bytes, results: list[ComplianceResult]) -> str:
    """
    Add a compliance summary overlay to the first page of the PDF.
    Returns base64-encoded annotated PDF.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    pw, ph = page.rect.width, page.rect.height

    failures = [r for r in results if r.status == "FAIL"]
    unknowns = [r for r in results if r.status == "UNKNOWN"]
    passes = [r for r in results if r.status == "PASS"]

    _draw_summary_box(page, pw, ph, failures, unknowns, passes)

    if failures:
        _draw_failure_banner(page, pw, ph, failures)

    out = doc.tobytes(deflate=True)
    doc.close()
    return base64.b64encode(out).decode("utf-8")


def _draw_summary_box(page, pw, ph, failures, unknowns, passes):
    """Draw a compliance summary legend in the top-left corner."""
    x0 = pw * CALLOUT_X_FRAC
    y0 = ph * CALLOUT_Y_FRAC
    box_w = min(220, pw * 0.35)
    line_h = 14
    padding = 8

    all_results = failures + unknowns + passes
    box_h = padding * 2 + line_h * (len(all_results) + 1) + 4

    # Background
    rect = fitz.Rect(x0, y0, x0 + box_w, y0 + box_h)
    page.draw_rect(rect, color=(0.2, 0.2, 0.2), fill=WHITE, width=1.5)

    # Title
    title_rect = fitz.Rect(x0, y0, x0 + box_w, y0 + line_h + padding)
    page.draw_rect(title_rect, color=None, fill=(0.15, 0.15, 0.15))
    page.insert_text(
        (x0 + padding, y0 + line_h),
        "COMPLIANCE SUMMARY",
        fontsize=8,
        color=WHITE,
        fontname="helv",
    )

    y = y0 + line_h + padding + 4
    for r in all_results:
        color = RED if r.status == "FAIL" else (ORANGE if r.status == "UNKNOWN" else GREEN)
        status_tag = f"[{r.status}]"
        text = f"{status_tag} {r.label}"
        if r.deficiency and r.deficiency > 0:
            text += f"  (-{r.deficiency}{_unit_suffix(r.rule_key)})"
        page.insert_text(
            (x0 + padding, y + line_h - 2),
            text,
            fontsize=7,
            color=color,
            fontname="helv",
        )
        y += line_h


def _draw_failure_banner(page, pw, ph, failures):
    """Draw a red warning banner at the bottom of the page."""
    banner_h = 18 + len(failures) * 13
    y0 = ph - banner_h - 10
    rect = fitz.Rect(pw * 0.25, y0, pw * 0.75, y0 + banner_h)
    page.draw_rect(rect, color=RED, fill=(1.0, 0.93, 0.93), width=1.5)

    page.insert_text(
        (pw * 0.25 + 8, y0 + 13),
        f"{len(failures)} COMPLIANCE FAILURE{'S' if len(failures) > 1 else ''}",
        fontsize=9,
        color=RED,
        fontname="helv",
    )

    y = y0 + 24
    for r in failures:
        msg = f"• {r.label}: {r.actual} (required {r.required})"
        if r.deficiency:
            msg += f" — deficient by {r.deficiency}{_unit_suffix(r.rule_key)}"
        page.insert_text((pw * 0.25 + 8, y), msg, fontsize=7.5, color=RED, fontname="helv")
        y += 13


def _unit_suffix(rule_key: str) -> str:
    if "setback" in rule_key or "height" in rule_key:
        return "m"
    if "coverage" in rule_key:
        return "%"
    return ""
