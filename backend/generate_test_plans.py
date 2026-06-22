"""Generate sample site plan PDFs for testing the compliance checker."""
import fitz  # PyMuPDF
import os

W, H = 1190, 842  # A3 landscape in points

GRAY  = (0.85, 0.85, 0.85)
BLUE  = (0.18, 0.38, 0.65)
GREEN = (0.13, 0.55, 0.13)
RED   = (0.75, 0.10, 0.10)
BLACK = (0.0, 0.0, 0.0)
WHITE = (1.0, 1.0, 1.0)
LGRAY = (0.95, 0.95, 0.95)


def dim_line(page, p1, p2, text, color=BLACK, font_size=9):
    import math
    page.draw_line(p1, p2, color=color, width=0.8)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return
    nx, ny = -dy / length * 5, dx / length * 5
    for pt in (p1, p2):
        page.draw_line((pt[0]-nx, pt[1]-ny), (pt[0]+nx, pt[1]+ny), color=color, width=0.8)
    mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
    page.insert_text((mx - len(text)*3, my - 5), text, fontsize=font_size, color=color)


def title_block(page, title, subtitle, scale="1:200", date="2024-01-15"):
    r = fitz.Rect(30, 30, W-30, 80)
    page.draw_rect(r, color=BLUE, fill=BLUE)
    page.insert_text((40, 52), title, fontsize=18, color=WHITE, fontname="hebo")
    page.insert_text((40, 68), subtitle, fontsize=9, color=(0.8, 0.9, 1.0), fontname="helv")
    page.insert_text((W-280, 52), f"Scale: {scale}", fontsize=9, color=WHITE)
    page.insert_text((W-280, 66), f"Date: {date}", fontsize=9, color=WHITE)
    page.insert_text((W-280, 79), "Drawn by: Test Generator", fontsize=8, color=(0.7, 0.8, 0.9))


def north_arrow(page, cx, cy):
    page.draw_circle((cx, cy), 18, color=BLACK, width=1)
    page.draw_line((cx, cy+15), (cx, cy-15), color=BLACK, width=1.5)
    page.draw_line((cx-8, cy+5), (cx, cy-15), color=BLACK, width=1.5)
    page.draw_line((cx+8, cy+5), (cx, cy-15), color=BLACK, width=1.5)
    page.insert_text((cx-3, cy-22), "N", fontsize=10, color=BLACK, fontname="hebo")


def legend_box(page, items, x, y):
    lh, bw = 16, 160
    bh = len(items)*lh + 20
    page.draw_rect(fitz.Rect(x, y, x+bw, y+bh), color=BLACK, fill=WHITE, width=0.8)
    page.insert_text((x+8, y+14), "LEGEND", fontsize=8, color=BLACK, fontname="hebo")
    for i, (color, label) in enumerate(items):
        ry = y + 20 + i*lh
        page.draw_rect(fitz.Rect(x+8, ry, x+22, ry+10), fill=color, color=BLACK, width=0.5)
        page.insert_text((x+26, ry+9), label, fontsize=8, color=BLACK)


def make_plan(path, config):
    """
    config keys:
      title, subtitle
      lot_w, lot_d          — lot dimensions in metres
      bld_w, bld_d          — building footprint in metres
      front, rear, sl, sr   — setbacks in metres
      height                — building height in metres
      parking               — number of spaces
      omit                  — set of label keys to skip:
                              "lot_dims", "bld_dims", "front", "rear",
                              "sl", "sr", "height", "parking", "lot_area",
                              "lot_coverage", "parking_label"
      notes                 — list of strings
    """
    omit = set(config.get("omit", []))

    doc = fitz.open()
    page = doc.new_page(width=W, height=H)

    page.draw_rect(fitz.Rect(0, 0, W, H), fill=LGRAY, color=None)
    page.draw_rect(fitz.Rect(28, 28, W-28, H-28), fill=WHITE, color=BLACK, width=1.5)

    title_block(page, config["title"], config["subtitle"])

    ox, oy = 120, 130
    draw_w, draw_h = 700, 580
    scale = min(draw_w / config["lot_w"], draw_h / config["lot_d"])

    lw = config["lot_w"] * scale
    ld = config["lot_d"] * scale
    bw = config["bld_w"] * scale
    bd = config["bld_d"] * scale
    fr = config["front"] * scale
    re = config["rear"] * scale
    sl = config["sl"] * scale
    sr = config["sr"] * scale

    # Lot
    lot_rect = fitz.Rect(ox, oy, ox+lw, oy+ld)
    page.draw_rect(lot_rect, color=BLACK, fill=(0.97, 0.97, 0.93), width=2.0)
    page.insert_text((ox + lw/2 - 30, oy-10), "FRONT (STREET)", fontsize=8, color=BLACK)

    # Building
    bx, by = ox+sl, oy+fr
    bld_rect = fitz.Rect(bx, by, bx+bw, by+bd)
    page.draw_rect(bld_rect, color=BLUE, fill=(0.82, 0.89, 0.97), width=1.5)
    page.insert_text((bx+bw/2-25, by+bd/2), "BUILDING", fontsize=9, color=BLUE, fontname="hebo")

    # Parking stalls
    pk_count = config["parking"]
    pk_w = max(20, 30*scale/10)
    pk_d = max(18, 25*scale/10)
    for i in range(pk_count):
        px = ox + lw - (pk_count-i)*(pk_w+2) - 10
        py = oy + ld - pk_d - 10
        page.draw_rect(fitz.Rect(px, py, px+pk_w, py+pk_d),
                       color=GREEN, fill=(0.85, 0.95, 0.85), width=1.0)
        page.insert_text((px+2, py+pk_d-4), "P", fontsize=7, color=GREEN)

    # --- Dimension labels (each guarded by omit) ---

    if "lot_dims" not in omit:
        dim_line(page, (ox, oy-30), (ox+lw, oy-30), f"LOT WIDTH = {config['lot_w']} m")
        page.draw_line((ox, oy-35), (ox, oy-25), color=BLACK, width=0.6)
        page.draw_line((ox+lw, oy-35), (ox+lw, oy-25), color=BLACK, width=0.6)

        dim_line(page, (ox+lw+30, oy), (ox+lw+30, oy+ld), f"LOT DEPTH = {config['lot_d']} m")
        page.draw_line((ox+lw+25, oy), (ox+lw+35, oy), color=BLACK, width=0.6)
        page.draw_line((ox+lw+25, oy+ld), (ox+lw+35, oy+ld), color=BLACK, width=0.6)

    if "front" not in omit:
        dim_line(page, (ox+lw*0.15, oy), (ox+lw*0.15, oy+fr),
                 f"FRONT SETBACK = {config['front']} m", color=RED)

    if "rear" not in omit:
        rear_y = oy + ld - re
        dim_line(page, (ox+lw*0.15, rear_y), (ox+lw*0.15, oy+ld),
                 f"REAR SETBACK = {config['rear']} m", color=RED)

    if "sl" not in omit:
        dim_line(page, (ox, oy+ld*0.5), (ox+sl, oy+ld*0.5),
                 f"SIDE (L) = {config['sl']} m", color=RED)

    if "sr" not in omit:
        right_x = ox + sl + bw
        dim_line(page, (right_x, oy+ld*0.5), (ox+lw, oy+ld*0.5),
                 f"SIDE (R) = {config['sr']} m", color=RED)

    if "bld_dims" not in omit:
        dim_line(page, (bx, by+bd+15), (bx+bw, by+bd+15),
                 f"BLDG WIDTH = {config['bld_w']} m", color=BLUE)
        dim_line(page, (bx-20, by), (bx-20, by+bd),
                 f"BLDG DEPTH = {config['bld_d']} m", color=BLUE)

    if "height" not in omit:
        page.insert_text((bx+6, by+bd/2+14),
                         f"HEIGHT = {config['height']} m", fontsize=8, color=BLUE)

    if "parking_label" not in omit:
        page.insert_text(
            (ox+lw-(pk_count*(pk_w+2))-12, oy+ld-pk_d-15),
            f"PARKING: {pk_count} SPACES", fontsize=8, color=GREEN
        )

    lot_area = round(config["lot_w"] * config["lot_d"], 1)
    bld_area = round(config["bld_w"] * config["bld_d"], 1)
    coverage = round(bld_area / lot_area * 100, 1)

    area_parts = []
    if "lot_area" not in omit:
        area_parts.append(f"LOT AREA = {lot_area} m²")
    if "bld_area" not in omit:
        area_parts.append(f"BUILDING AREA = {bld_area} m²")
    if "lot_coverage" not in omit:
        area_parts.append(f"LOT COVERAGE = {coverage}%")
    if area_parts:
        page.insert_text((ox+lw*0.3, oy+18), "    ".join(area_parts),
                         fontsize=8, color=(0.3, 0.3, 0.3))

    north_arrow(page, W-80, H-80)
    legend_box(page, [
        (BLUE, "Building footprint"),
        ((0.97, 0.97, 0.93), "Lot boundary"),
        (GREEN, "Parking space"),
    ], W-210, H-160)

    nx, ny = ox, H-115
    page.draw_rect(fitz.Rect(nx, ny, nx+520, H-35), color=BLACK, fill=WHITE, width=0.8)
    page.insert_text((nx+8, ny+14), "NOTES", fontsize=8, color=BLACK, fontname="hebo")
    for i, note in enumerate(config["notes"]):
        page.insert_text((nx+8, ny+26+i*13), f"  {i+1}. {note}", fontsize=7.5, color=BLACK)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.save(path)
    doc.close()
    print(f"Saved: {path}")


# ── 1. Fully compliant, all labels present ───────────────────────────────────
make_plan("test_plans/plan_compliant.pdf", {
    "title": "SITE PLAN — 142 Maple Avenue",
    "subtitle": "Residential Zone RF1 | Fully Compliant",
    "lot_w": 18.0, "lot_d": 38.0,
    "bld_w": 12.0, "bld_d": 14.0,
    "front": 7.5, "rear": 10.0, "sl": 2.0, "sr": 4.0,
    "height": 8.5, "parking": 2,
    "notes": [
        "All setbacks comply with RF1 zoning bylaw minimums.",
        "Lot coverage = 168.0 m2 / 684.0 m2 = 24.6% (max 45% — compliant).",
        "Building height measured to ridge from finished grade.",
        "Two parking stalls provided per bylaw requirement.",
    ],
})

# ── 2. Multiple failures, all labels present ─────────────────────────────────
make_plan("test_plans/plan_failures.pdf", {
    "title": "SITE PLAN — 77 Birch Street",
    "subtitle": "Residential Zone RF1 | Non-Compliant — Review Required",
    "lot_w": 15.0, "lot_d": 30.0,
    "bld_w": 12.5, "bld_d": 16.0,
    "front": 4.5,   # FAIL: min 6.0 m
    "rear": 5.0,    # FAIL: min 7.5 m
    "sl": 1.5,
    "sr": 1.0,      # FAIL: min 1.5 m
    "height": 11.2, # FAIL: max 10.0 m
    "parking": 2,
    "notes": [
        "Front setback 4.5 m is deficient by 1.5 m (min 6.0 m required).",
        "Rear setback 5.0 m is deficient by 2.5 m (min 7.5 m required).",
        "Right side setback 1.0 m is deficient by 0.5 m (min 1.5 m required).",
        "Building height 11.2 m exceeds maximum of 10.0 m by 1.2 m.",
    ],
})

# ── 3. Missing height and rear setback labels ─────────────────────────────────
make_plan("test_plans/plan_missing_height_rear.pdf", {
    "title": "SITE PLAN — 33 Cedar Lane",
    "subtitle": "Residential Zone RF1 | Preliminary — Height & Rear Setback Not Shown",
    "lot_w": 20.0, "lot_d": 42.0,
    "bld_w": 11.0, "bld_d": 13.0,
    "front": 6.5, "rear": 9.0, "sl": 2.5, "sr": 3.0,
    "height": 9.0,  # drawn but NOT labelled
    "parking": 2,
    "omit": ["height", "rear"],
    "notes": [
        "Building height not shown on this sheet — refer to elevation drawings.",
        "Rear setback dimension to be confirmed in final submission.",
        "All other dimensions as shown.",
    ],
})

# ── 4. Missing almost everything except lot outline ───────────────────────────
make_plan("test_plans/plan_mostly_unlabelled.pdf", {
    "title": "SITE PLAN — 19 Elm Drive",
    "subtitle": "Residential Zone RF1 | Concept Only — Dimensions Not Confirmed",
    "lot_w": 16.0, "lot_d": 35.0,
    "bld_w": 10.0, "bld_d": 12.0,
    "front": 7.0, "rear": 8.5, "sl": 2.0, "sr": 4.0,
    "height": 7.5,
    "parking": 2,
    "omit": ["front", "rear", "sl", "sr", "height", "bld_dims",
             "lot_area", "bld_area", "lot_coverage", "parking_label"],
    "notes": [
        "CONCEPT DRAWING ONLY — no dimensions confirmed.",
        "Lot width and depth shown for reference; all other dimensions TBD.",
        "Do not use for permit submission.",
    ],
})

# ── 5. Only setbacks labelled, no building or lot dimensions ──────────────────
make_plan("test_plans/plan_setbacks_only.pdf", {
    "title": "SITE PLAN — 88 Oak Crescent",
    "subtitle": "Residential Zone RF1 | Setback Study",
    "lot_w": 17.5, "lot_d": 36.0,
    "bld_w": 11.5, "bld_d": 15.0,
    "front": 6.0, "rear": 7.5, "sl": 1.5, "sr": 2.5,
    "height": 9.5,
    "parking": 3,
    "omit": ["lot_dims", "bld_dims", "height",
             "lot_area", "bld_area", "lot_coverage"],
    "notes": [
        "Only setback dimensions shown for zoning review purposes.",
        "Lot and building dimensions to be added in architectural drawings.",
        "Parking: 3 spaces provided (2 required).",
    ],
})

print("\nAll test plans generated in backend/test_plans/")
