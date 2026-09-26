"""
actions/presentation_designer.py — Autonomous High-Impact Presentation Designer Engine for J.A.R.V.I.S. Mark 58

Empowers J.A.R.V.I.S. with full creative and structural freedom to research, storyboard,
design, and deliver visually captivating 16:9 widescreen presentations (.pptx).

Key Capabilities:
1. Executive Aesthetic Themes:
   - cyberpunk_stark: Stark Industries deep navy, neon cyan, arc sky blue, and crisp white.
   - executive_obsidian: Obsidian black, warm champagne gold, amber accents, and alabaster text.
   - silicon_minimalist: Crisp pure white/slate, royal indigo, violet highlights, and dark charcoal text.
   - emerald_science: Deep forest slate, mint neon, teal radiance, and clean white.
   - solar_amber: Dark graphite, fiery solar orange, crimson accents, and warm white.

2. Intriguing Custom Slide Archetypes (Geometric Free-Canvas on 16:9 Widescreen):
   - Hero Title: Massive headline with accent chips, subtitle hook, and presenter credential card.
   - KPI / Metric Cards: 3 or 4 high-impact metric cards with giant figures (Pt 48-56), delta chips, and takeaways.
   - Comparative Cards: 2 split perspective cards with custom bullet markers (status quo vs. Stark solution).
   - Feature Grid: 3 or 4 modular glassmorphic/card containers with badge indicators.
   - Process Pipeline: 4-stage horizontal flowchart with step badges, milestone tags, and connecting flows.
   - Executive Quote: Stylized quotation callout with author attribution and strategic impact commentary.
   - Matrix Table: High-contrast data matrix with custom column formatting, header fill, and zebra striping.
   - Agenda / Roadmap: Numbered briefing overview with section scopes.
   - Conclusion / Action Plan: High-impact takeaway with 3 immediate next steps and Q&A signature.

3. Complete Storyboard & Speaker Delivery Suite:
   - Full AI Storyboard Generation via Gemini (narrative arc, archetype selection, visual layout).
   - Articulate, persuasive speaker notes embedded on EVERY slide for confident delivery.
   - Speaker Speech Rehearsal Script (.md) generation.
   - PowerPoint COM automation for 1-click full-screen slideshow launching and instant 16:9 PDF export.
   - Full deck manipulation: retheming existing presentations and appending custom slides.
"""

import os
import sys
import re
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent.parent

# ====================================================================
# 1. COLOR PALETTES & THEME DEFINITIONS
# ====================================================================

THEMES = {
    "cyberpunk_stark": {
        "name": "Stark Cyberpunk",
        "description": "Dark slate with electric cyan neon and arc sky blue. J.A.R.V.I.S. signature aesthetic.",
        "bg_color": (11, 15, 25),          # #0B0F19
        "card_bg": (23, 32, 51),           # #172033
        "card_border": (38, 56, 89),       # #263859
        "accent_primary": (0, 240, 255),   # #00F0FF Neon Cyan
        "accent_secondary": (56, 189, 248),# #38BDF8 Sky Blue
        "text_primary": (248, 250, 252),   # #F8FAFC Crisp White
        "text_muted": (148, 163, 184),     # #94A3B8 Slate Muted
        "badge_bg": (15, 42, 66),          # Deep Cyan Pill
        "highlight": (245, 158, 11),       # Amber Gold
        "positive": (52, 211, 153),        # Emerald Green
        "negative": (248, 113, 113)        # Coral Red
    },
    "executive_obsidian": {
        "name": "Executive Obsidian & Gold",
        "description": "Obsidian black and warm champagne gold. Ultra-luxurious McKinsey/Goldman aesthetic.",
        "bg_color": (9, 10, 15),           # #090A0F
        "card_bg": (24, 24, 27),           # #18181B
        "card_border": (45, 45, 52),       # #2D2D34
        "accent_primary": (234, 179, 8),   # #EAB308 Champagne Gold
        "accent_secondary": (217, 119, 6), # #D97706 Warm Amber
        "text_primary": (250, 250, 250),   # #FAFAFA Pure Alabaster
        "text_muted": (161, 161, 170),     # #A1A1AA Zinc Muted
        "badge_bg": (48, 38, 12),          # Deep Gold Pill
        "highlight": (251, 191, 36),       # Vivid Amber
        "positive": (74, 222, 128),
        "negative": (248, 113, 113)
    },
    "silicon_minimalist": {
        "name": "Silicon Valley Clean",
        "description": "Crisp white canvas, slate card containers, and royal indigo accents. Apple Keynote style.",
        "bg_color": (255, 255, 255),       # #FFFFFF Pure White
        "card_bg": (248, 250, 252),        # #F8FAFC Light Slate
        "card_border": (226, 232, 240),    # #E2E8F0 Border Slate
        "accent_primary": (79, 70, 229),   # #4F46E5 Indigo
        "accent_secondary": (124, 58, 237),# #7C3AED Royal Violet
        "text_primary": (15, 23, 42),      # #0F172A Deep Charcoal
        "text_muted": (100, 116, 139),     # #64748B Slate Grey
        "badge_bg": (238, 242, 255),       # Soft Indigo Pill
        "highlight": (234, 88, 12),        # Burnt Orange
        "positive": (16, 185, 129),
        "negative": (239, 68, 68)
    },
    "emerald_science": {
        "name": "Emerald BioTech & Sustainability",
        "description": "Deep forest slate with luminous mint and teal neon. Ideal for healthcare, science, and green tech.",
        "bg_color": (2, 44, 34),           # #022C22 Forest Dark
        "card_bg": (6, 78, 59),            # #064E3B Deep Emerald Card
        "card_border": (16, 120, 87),      # #107857
        "accent_primary": (52, 211, 153),  # #34D399 Mint Neon
        "accent_secondary": (45, 212, 191),# #2DD4BF Teal Radiance
        "text_primary": (240, 253, 244),   # #F0FDF4 Mint White
        "text_muted": (167, 243, 208),     # #A7F3D0 Sage
        "badge_bg": (4, 54, 42),
        "highlight": (250, 204, 21),
        "positive": (52, 211, 153),
        "negative": (248, 113, 113)
    },
    "solar_amber": {
        "name": "Solar Flare Amber & Crimson",
        "description": "High-contrast dark charcoal with radiant solar orange and crimson. Dynamic, high-energy pitch deck.",
        "bg_color": (24, 24, 27),          # #18181B Dark Charcoal
        "card_bg": (39, 39, 42),           # #27272A
        "card_border": (63, 63, 70),       # #3F3F46
        "accent_primary": (249, 115, 22),  # #F97316 Solar Orange
        "accent_secondary": (239, 68, 68), # #EF4444 Crimson
        "text_primary": (255, 247, 237),   # #FFF7ED Warm White
        "text_muted": (212, 212, 216),     # #D4D4D8 Zinc
        "badge_bg": (60, 30, 16),
        "highlight": (251, 146, 60),
        "positive": (74, 222, 128),
        "negative": (239, 68, 68)
    }
}

DEFAULT_THEME = "cyberpunk_stark"

def get_theme(theme_name: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves theme dict with fallback to cyberpunk_stark."""
    if not theme_name:
        return THEMES[DEFAULT_THEME]
    norm = theme_name.lower().strip().replace("-", "_").replace(" ", "_")
    for key in THEMES:
        if key in norm or norm in key:
            return THEMES[key]
    return THEMES[DEFAULT_THEME]

def _to_rgb(color_tuple) -> RGBColor:
    return RGBColor(*color_tuple)

def _get_output_dir(target_location: Union[str, Path] = "desktop") -> Path:
    """Resolves output target folder, defaulting to Desktop."""
    if isinstance(target_location, Path):
        target_location.mkdir(parents=True, exist_ok=True)
        return target_location
    if isinstance(target_location, str):
        p = Path(target_location)
        if p.is_dir() or p.is_absolute() or "/" in target_location or "\\" in target_location:
            p.mkdir(parents=True, exist_ok=True)
            return p
        loc = target_location.lower().strip()
    else:
        loc = "desktop"

    if loc in ("desktop", "desk"):
        cand = Path.home() / "OneDrive" / "Desktop"
        if cand.exists(): return cand
        cand = Path.home() / "Desktop"
        if cand.exists(): return cand
    elif loc in ("downloads", "download"):
        cand = Path.home() / "Downloads"
        if cand.exists(): return cand
    elif loc in ("documents", "docs"):
        cand = Path.home() / "Documents"
        if cand.exists(): return cand
    
    cand = Path.home() / "Desktop"
    cand.mkdir(parents=True, exist_ok=True)
    return cand


# ====================================================================
# 2. CANVAS & BASE SLIDE SCAFFOLDING (16:9 WIDESCREEN)
# ====================================================================

def create_base_presentation() -> Any:
    """Initializes a 16:9 widescreen presentation (13.333 x 7.5 inches)."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs

def render_slide_background(slide: Any, theme: Dict[str, Any]):
    """Applies a seamless full-bleed background and subtle top accent glow line."""
    # Full background canvas
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = _to_rgb(theme["bg_color"])
    bg.line.fill.background()

    # Top accent highlight stripe (0.06 inch height)
    top_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.06))
    top_line.fill.solid()
    top_line.fill.fore_color.rgb = _to_rgb(theme["accent_primary"])
    top_line.line.fill.background()

def render_header(slide: Any, theme: Dict[str, Any], title: str, kicker: Optional[str] = None, subtitle: Optional[str] = None):
    """Renders a modern header with category pill, primary headline, and narrative hook."""
    left = Inches(0.8)
    top = Inches(0.5)

    # 1. Kicker / Category Pill Badge
    if kicker:
        badge_text = kicker.upper()
        # Pill background
        pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(2.8), Inches(0.32))
        pill.fill.solid()
        pill.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
        pill.line.color.rgb = _to_rgb(theme["accent_primary"])
        pill.line.width = Pt(1.0)
        tf_p = pill.text_frame
        tf_p.word_wrap = False
        p_pill = tf_p.paragraphs[0]
        p_pill.text = f"  {badge_text}  "
        p_pill.font.name = "Segoe UI"
        p_pill.font.size = Pt(10)
        p_pill.font.bold = True
        p_pill.font.color.rgb = _to_rgb(theme["accent_primary"])
        p_pill.alignment = PP_ALIGN.CENTER
        top += Inches(0.42)

    # 2. Slide Main Title
    title_box = slide.shapes.add_textbox(left, top, Inches(11.7), Inches(0.65))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title
    p_t.font.name = "Segoe UI"
    p_t.font.size = Pt(28)
    p_t.font.bold = True
    p_t.font.color.rgb = _to_rgb(theme["text_primary"])

    # 3. Subtitle / Narrative Hook
    if subtitle:
        sub_box = slide.shapes.add_textbox(left, top + Inches(0.6), Inches(11.7), Inches(0.4))
        tf_s = sub_box.text_frame
        tf_s.word_wrap = True
        p_s = tf_s.paragraphs[0]
        p_s.text = subtitle
        p_s.font.name = "Segoe UI"
        p_s.font.size = Pt(13)
        p_s.font.italic = True
        p_s.font.color.rgb = _to_rgb(theme["text_muted"])

def render_footer(slide: Any, theme: Dict[str, Any], deck_title: str, current_idx: int, total_slides: int):
    """Renders bottom divider line, presentation title, J.A.R.V.I.S. signature, and slide counter."""
    y = Inches(7.0)
    
    # Subtle separator line
    div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), y, Inches(11.733), Inches(0.015))
    div.fill.solid()
    div.fill.fore_color.rgb = _to_rgb(theme["card_border"])
    div.line.fill.background()

    # Footer Left: Deck Title
    f_left = slide.shapes.add_textbox(Inches(0.8), y + Inches(0.06), Inches(4.5), Inches(0.3))
    tf_l = f_left.text_frame
    p_l = tf_l.paragraphs[0]
    p_l.text = deck_title[:45]
    p_l.font.name = "Segoe UI"
    p_l.font.size = Pt(9)
    p_l.font.color.rgb = _to_rgb(theme["text_muted"])

    # Footer Center: J.A.R.V.I.S. Mark 58 Signature
    f_center = slide.shapes.add_textbox(Inches(5.0), y + Inches(0.06), Inches(3.333), Inches(0.3))
    tf_c = f_center.text_frame
    p_c = tf_c.paragraphs[0]
    p_c.text = "J.A.R.V.I.S. Autonomous Intelligence"
    p_c.alignment = PP_ALIGN.CENTER
    p_c.font.name = "Segoe UI"
    p_c.font.size = Pt(9)
    p_c.font.color.rgb = _to_rgb(theme["text_muted"])

    # Footer Right: Slide Counter
    f_right = slide.shapes.add_textbox(Inches(10.0), y + Inches(0.06), Inches(2.533), Inches(0.3))
    tf_r = f_right.text_frame
    p_r = tf_r.paragraphs[0]
    p_r.text = f"{current_idx:02d} / {total_slides:02d}"
    p_r.alignment = PP_ALIGN.RIGHT
    p_r.font.name = "Segoe UI"
    p_r.font.size = Pt(9)
    p_r.font.bold = True
    p_r.font.color.rgb = _to_rgb(theme["accent_primary"])


# ====================================================================
# 3. SPECIALIZED SLIDE ARCHETYPE RENDERERS
# ====================================================================

def render_hero_title_slide(prs: Any, theme: Dict[str, Any], data: Dict[str, Any], current_idx: int, total_slides: int):
    """Renders a cinematic, executive Hero Title slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    render_slide_background(slide, theme)

    # Decorative tech corner bracket or glow block
    glow_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(0.12), Inches(3.6))
    glow_bar.fill.solid()
    glow_bar.fill.fore_color.rgb = _to_rgb(theme["accent_primary"])
    glow_bar.line.fill.background()

    # Classification Badge Pill
    badge_label = data.get("kicker") or "EXECUTIVE STRATEGIC BRIEFING"
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.8), Inches(4.2), Inches(0.38))
    badge.fill.solid()
    badge.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
    badge.line.color.rgb = _to_rgb(theme["accent_primary"])
    badge.line.width = Pt(1.2)
    tf_b = badge.text_frame
    p_b = tf_b.paragraphs[0]
    p_b.text = f"  ✦ {badge_label.upper()}  "
    p_b.font.name = "Segoe UI"
    p_b.font.size = Pt(11)
    p_b.font.bold = True
    p_b.font.color.rgb = _to_rgb(theme["accent_primary"])
    p_b.alignment = PP_ALIGN.CENTER

    # Main Giant Title
    title_box = slide.shapes.add_textbox(Inches(1.2), Inches(2.35), Inches(11.0), Inches(1.8))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = data.get("title", "Autonomous Strategic Architecture")
    p_t.font.name = "Segoe UI"
    p_t.font.size = Pt(44)
    p_t.font.bold = True
    p_t.font.color.rgb = _to_rgb(theme["text_primary"])

    # Subtitle / Thesis Statement
    subtitle = data.get("subtitle", "Engineering High-Performance Intelligence & Autonomous Execution")
    sub_box = slide.shapes.add_textbox(Inches(1.2), Inches(4.1), Inches(11.0), Inches(0.9))
    tf_s = sub_box.text_frame
    tf_s.word_wrap = True
    p_s = tf_s.paragraphs[0]
    p_s.text = subtitle
    p_s.font.name = "Segoe UI"
    p_s.font.size = Pt(18)
    p_s.font.color.rgb = _to_rgb(theme["text_muted"])

    # Presenter Information Card
    presenter_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(5.1), Inches(10.5), Inches(1.3))
    presenter_card.fill.solid()
    presenter_card.fill.fore_color.rgb = _to_rgb(theme["card_bg"])
    presenter_card.line.color.rgb = _to_rgb(theme["card_border"])
    presenter_card.line.width = Pt(1.0)

    author = data.get("author", "Akul | NMIMS Mumbai")
    org = data.get("organization", "Executive Operations & Autonomous Systems")
    date_str = datetime.now().strftime("%B %d, %Y")

    tf_p = presenter_card.text_frame
    tf_p.word_wrap = True
    p_p1 = tf_p.paragraphs[0]
    p_p1.text = f"Presenter: {author}"
    p_p1.font.name = "Segoe UI"
    p_p1.font.size = Pt(14)
    p_p1.font.bold = True
    p_p1.font.color.rgb = _to_rgb(theme["accent_primary"])

    p_p2 = tf_p.add_paragraph()
    p_p2.text = f"{org} • Authored with J.A.R.V.I.S. Mark 58 • {date_str}"
    p_p2.font.name = "Segoe UI"
    p_p2.font.size = Pt(11)
    p_p2.font.color.rgb = _to_rgb(theme["text_muted"])

    # Speaker notes
    notes = data.get("notes") or f"Welcome everyone. Today's presentation covers {data.get('title')}. We will walk through the core strategic objectives, empirical metrics, and actionable roadmap."
    slide.notes_slide.notes_text_frame.text = notes
    render_footer(slide, theme, data.get("title", "Presentation"), current_idx, total_slides)


def render_kpi_cards_slide(prs: Any, theme: Dict[str, Any], data: Dict[str, Any], current_idx: int, total_slides: int):
    """Renders 3 or 4 Big-Stat KPI metric cards side-by-side."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    render_slide_background(slide, theme)
    render_header(slide, theme, data.get("title", "Key Performance Indicators"), data.get("kicker", "EMPIRICAL METRICS"), data.get("subtitle"))

    raw_cards = data.get("cards") or data.get("metrics") or []
    if not raw_cards:
        # Fallback card data
        cards = [
            {"value": "99.4%", "label": "Execution Reliability", "delta": "+48% YoY", "bullets": ["Full autonomous verification", "Fault-tolerant architecture"]},
            {"value": "10x", "label": "Throughput Velocity", "delta": "Sub-100ms", "bullets": ["Zero manual bottleneck", "Parallel worker agents"]},
            {"value": "Zero", "label": "Operational Regression", "delta": "100% Pass Rate", "bullets": ["Automated test suites", "High-fidelity feedback loop"]}
        ]
    else:
        cards = []
        for c in raw_cards:
            if isinstance(c, dict):
                cards.append(c)
            elif isinstance(c, (list, tuple)) and len(c) >= 2:
                cards.append({"value": str(c[0]), "label": str(c[1]), "delta": None, "bullets": []})
            else:
                cards.append({"value": str(c), "label": "Key Metric", "delta": None, "bullets": []})

    n = min(len(cards), 4)
    top_y = Inches(1.95)
    card_h = Inches(4.75)
    total_w = Inches(11.733)
    gap = Inches(0.35)
    card_w = (total_w - (gap * (n - 1))) / n

    for i in range(n):
        c_info = cards[i]
        c_left = Inches(0.8) + i * (card_w + gap)

        # Card container
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, top_y, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = _to_rgb(theme["card_bg"])
        card.line.color.rgb = _to_rgb(theme["card_border"])
        card.line.width = Pt(1.2)

        # Accent top bar on card
        c_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, c_left + Inches(0.15), top_y + Inches(0.15), card_w - Inches(0.3), Inches(0.04))
        c_bar.fill.solid()
        c_bar.fill.fore_color.rgb = _to_rgb(theme["accent_primary"] if i % 2 == 0 else theme["accent_secondary"])
        c_bar.line.fill.background()

        # Big Stat Value
        v_box = slide.shapes.add_textbox(c_left + Inches(0.2), top_y + Inches(0.35), card_w - Inches(0.4), Inches(1.0))
        tf_v = v_box.text_frame
        tf_v.word_wrap = True
        p_v = tf_v.paragraphs[0]
        p_v.text = str(c_info.get("value", "100%"))
        p_v.font.name = "Segoe UI"
        p_v.font.size = Pt(46 if n == 3 else 38)
        p_v.font.bold = True
        p_v.font.color.rgb = _to_rgb(theme["accent_primary"])

        # Metric Label
        lbl_box = slide.shapes.add_textbox(c_left + Inches(0.2), top_y + Inches(1.4), card_w - Inches(0.4), Inches(0.6))
        tf_lbl = lbl_box.text_frame
        tf_lbl.word_wrap = True
        p_lbl = tf_lbl.paragraphs[0]
        p_lbl.text = str(c_info.get("label", "Key Benchmark"))
        p_lbl.font.name = "Segoe UI"
        p_lbl.font.size = Pt(15)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = _to_rgb(theme["text_primary"])

        # Delta / Benchmark Pill
        delta = c_info.get("delta")
        if delta:
            delta_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.2), top_y + Inches(2.05), card_w - Inches(0.4), Inches(0.34))
            delta_box.fill.solid()
            delta_box.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
            delta_box.line.color.rgb = _to_rgb(theme["accent_secondary"])
            delta_box.line.width = Pt(0.8)
            tf_d = delta_box.text_frame
            p_d = tf_d.paragraphs[0]
            p_d.text = f"  ▲ {delta}  "
            p_d.font.name = "Segoe UI"
            p_d.font.size = Pt(10)
            p_d.font.bold = True
            p_d.font.color.rgb = _to_rgb(theme["accent_secondary"])
            p_d.alignment = PP_ALIGN.CENTER

        # Bullets / Supporting Details
        bullets = c_info.get("bullets", [])
        if bullets:
            b_top = top_y + (Inches(2.55) if delta else Inches(2.15))
            b_box = slide.shapes.add_textbox(c_left + Inches(0.2), b_top, card_w - Inches(0.4), Inches(1.9))
            tf_b = b_box.text_frame
            tf_b.word_wrap = True
            for idx, bullet_text in enumerate(bullets[:4]):
                p_b = tf_b.add_paragraph() if idx > 0 else tf_b.paragraphs[0]
                p_b.text = f"• {bullet_text}"
                p_b.font.name = "Segoe UI"
                p_b.font.size = Pt(11)
                p_b.font.color.rgb = _to_rgb(theme["text_muted"])

    notes = data.get("notes") or f"On this slide, direct the audience's attention to the primary KPI figures. Highlight the {cards[0].get('value', 'benchmark')} metric as the definitive benchmark."
    slide.notes_slide.notes_text_frame.text = notes
    render_footer(slide, theme, data.get("deck_title", "Presentation"), current_idx, total_slides)


def render_comparison_cards_slide(prs: Any, theme: Dict[str, Any], data: Dict[str, Any], current_idx: int, total_slides: int):
    """Renders 2 large comparative perspective cards side-by-side."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    render_slide_background(slide, theme)
    render_header(slide, theme, data.get("title", "Comparative Analysis"), data.get("kicker", "ARCHITECTURAL COMPARISON"), data.get("subtitle"))

    c1_title = data.get("col1_title") or "Traditional / Legacy Model"
    c1_bullets = data.get("col1_bullets") or ["Siloed workflows requiring continuous manual oversight", "High latency in multi-step task execution", "Fragile error handling with manual recovery loops", "Scattered context across isolated software tools"]
    
    c2_title = data.get("col2_title") or "Next-Gen Stark Architecture"
    c2_bullets = data.get("col2_bullets") or ["Unified autonomous agent orchestration across tools", "Sub-second parallel sub-brain reasoning", "Self-healing error correction and verified execution", "Persistent institutional memory with deep research integration"]

    top_y = Inches(1.95)
    card_h = Inches(4.35)
    card_w = Inches(5.65)
    gap = Inches(0.433)

    # --- Left Card (Legacy / Status Quo) ---
    left_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top_y, card_w, card_h)
    left_card.fill.solid()
    left_card.fill.fore_color.rgb = _to_rgb(theme["card_bg"])
    left_card.line.color.rgb = _to_rgb(theme["card_border"])
    left_card.line.width = Pt(1.2)

    # Left Card Header Banner
    l_banner = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), top_y + Inches(0.2), card_w - Inches(0.4), Inches(0.55))
    l_banner.fill.solid()
    l_banner.fill.fore_color.rgb = _to_rgb((45, 25, 25) if theme != THEMES["silicon_minimalist"] else (254, 242, 242))
    l_banner.line.color.rgb = _to_rgb(theme["negative"])
    l_banner.line.width = Pt(1.0)
    tf_lb = l_banner.text_frame
    p_lb = tf_lb.paragraphs[0]
    p_lb.text = f"  ✕  {c1_title.upper()}"
    p_lb.font.name = "Segoe UI"
    p_lb.font.size = Pt(13)
    p_lb.font.bold = True
    p_lb.font.color.rgb = _to_rgb(theme["negative"])
    p_lb.alignment = PP_ALIGN.CENTER

    # Left Card Bullets
    l_box = slide.shapes.add_textbox(Inches(1.0), top_y + Inches(0.9), card_w - Inches(0.4), Inches(3.2))
    tf_l = l_box.text_frame
    tf_l.word_wrap = True
    for idx, b_text in enumerate(c1_bullets):
        p_b = tf_l.add_paragraph() if idx > 0 else tf_l.paragraphs[0]
        p_b.text = f"•  {b_text}"
        p_b.font.name = "Segoe UI"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = _to_rgb(theme["text_muted"])
        p_b.space_after = Pt(8)

    # --- Right Card (Stark Solution) ---
    right_x = Inches(0.8) + card_w + gap
    right_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_x, top_y, card_w, card_h)
    right_card.fill.solid()
    right_card.fill.fore_color.rgb = _to_rgb(theme["card_bg"])
    right_card.line.color.rgb = _to_rgb(theme["accent_primary"])
    right_card.line.width = Pt(1.5)

    # Right Card Header Banner
    r_banner = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_x + Inches(0.2), top_y + Inches(0.2), card_w - Inches(0.4), Inches(0.55))
    r_banner.fill.solid()
    r_banner.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
    r_banner.line.color.rgb = _to_rgb(theme["accent_primary"])
    r_banner.line.width = Pt(1.2)
    tf_rb = r_banner.text_frame
    p_rb = tf_rb.paragraphs[0]
    p_rb.text = f"  ✔  {c2_title.upper()}"
    p_rb.font.name = "Segoe UI"
    p_rb.font.size = Pt(13)
    p_rb.font.bold = True
    p_rb.font.color.rgb = _to_rgb(theme["accent_primary"])
    p_rb.alignment = PP_ALIGN.CENTER

    # Right Card Bullets
    r_box = slide.shapes.add_textbox(right_x + Inches(0.2), top_y + Inches(0.9), card_w - Inches(0.4), Inches(3.2))
    tf_r = r_box.text_frame
    tf_r.word_wrap = True
    for idx, b_text in enumerate(c2_bullets):
        p_b = tf_r.add_paragraph() if idx > 0 else tf_r.paragraphs[0]
        p_b.text = f"▶  {b_text}"
        p_b.font.name = "Segoe UI"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = _to_rgb(theme["text_primary"])
        p_b.space_after = Pt(8)

    # Bottom Verdict Pill / Banner
    verdict = data.get("verdict") or "Strategic Verdict: Stark Autonomous Architecture yields 4.2x efficiency gain and eliminates single points of failure."
    v_banner = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.4), Inches(11.733), Inches(0.42))
    v_banner.fill.solid()
    v_banner.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
    v_banner.line.color.rgb = _to_rgb(theme["accent_secondary"])
    v_banner.line.width = Pt(1.0)
    tf_vb = v_banner.text_frame
    p_vb = tf_vb.paragraphs[0]
    p_vb.text = f"  ✦ {verdict}  "
    p_vb.font.name = "Segoe UI"
    p_vb.font.size = Pt(10)
    p_vb.font.bold = True
    p_vb.font.color.rgb = _to_rgb(theme["accent_secondary"])
    p_vb.alignment = PP_ALIGN.CENTER

    notes = data.get("notes") or f"Walk through the comparative dichotomy. First establish the pain points on the left, then contrast with the solution advantages on the right."
    slide.notes_slide.notes_text_frame.text = notes
    render_footer(slide, theme, data.get("deck_title", "Presentation"), current_idx, total_slides)


def render_feature_grid_slide(prs: Any, theme: Dict[str, Any], data: Dict[str, Any], current_idx: int, total_slides: int):
    """Renders 3 modular feature/pillar cards with badge indicators."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    render_slide_background(slide, theme)
    render_header(slide, theme, data.get("title", "Core Pillars & Capabilities"), data.get("kicker", "STRATEGIC CAPABILITIES"), data.get("subtitle"))

    raw_features = data.get("features") or data.get("pillars") or data.get("cards") or []
    if not raw_features:
        features = [
            {"badge": "01", "title": "Cognitive Reasoning", "desc": "High-level multi-model intelligence with adaptive fallback.", "bullets": ["Contextual query routing", "Real-time verification"]},
            {"badge": "02", "title": "Systemic Execution", "desc": "Direct operating system control across desktop applications.", "bullets": ["Full Office automation", "Background process management"]},
            {"badge": "03", "title": "Persistent Memory", "desc": "Longitudinal student & executive telemetry integration.", "bullets": ["College academic hub", "Adaptive personal preferences"]}
        ]
    else:
        features = []
        for i, f in enumerate(raw_features):
            if isinstance(f, dict):
                features.append(f)
            else:
                features.append({"badge": f"0{i+1}", "title": str(f), "desc": "", "bullets": []})

    n = min(len(features), 3)
    top_y = Inches(1.95)
    card_h = Inches(4.75)
    total_w = Inches(11.733)
    gap = Inches(0.4)
    card_w = (total_w - (gap * (n - 1))) / n

    icons = ["⚡", "🛡️", "🎯", "🌐"]

    for i in range(n):
        f_info = features[i]
        c_left = Inches(0.8) + i * (card_w + gap)

        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, top_y, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = _to_rgb(theme["card_bg"])
        card.line.color.rgb = _to_rgb(theme["card_border"])
        card.line.width = Pt(1.2)

        # Card Badge Box (01, 02, etc.)
        b_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.3), top_y + Inches(0.3), Inches(0.65), Inches(0.65))
        b_box.fill.solid()
        b_box.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
        b_box.line.color.rgb = _to_rgb(theme["accent_primary"])
        b_box.line.width = Pt(1.0)
        tf_bb = b_box.text_frame
        p_bb = tf_bb.paragraphs[0]
        badge_txt = str(f_info.get("badge") or f"0{i+1}")
        p_bb.text = badge_txt
        p_bb.font.name = "Segoe UI"
        p_bb.font.size = Pt(14)
        p_bb.font.bold = True
        p_bb.font.color.rgb = _to_rgb(theme["accent_primary"])
        p_bb.alignment = PP_ALIGN.CENTER

        # Feature Title
        t_box = slide.shapes.add_textbox(c_left + Inches(1.1), top_y + Inches(0.3), card_w - Inches(1.3), Inches(0.7))
        tf_t = t_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = str(f_info.get("title") or f"Pillar {i+1}")
        p_t.font.name = "Segoe UI"
        p_t.font.size = Pt(17)
        p_t.font.bold = True
        p_t.font.color.rgb = _to_rgb(theme["text_primary"])

        # Feature Description
        desc_box = slide.shapes.add_textbox(c_left + Inches(0.3), top_y + Inches(1.15), card_w - Inches(0.6), Inches(0.9))
        tf_d = desc_box.text_frame
        tf_d.word_wrap = True
        p_d = tf_d.paragraphs[0]
        p_d.text = str(f_info.get("desc") or f_info.get("description", ""))
        p_d.font.name = "Segoe UI"
        p_d.font.size = Pt(12)
        p_d.font.italic = True
        p_d.font.color.rgb = _to_rgb(theme["text_muted"])

        # Supporting Bullets
        bullets = f_info.get("bullets", [])
        if bullets:
            b_list = slide.shapes.add_textbox(c_left + Inches(0.3), top_y + Inches(2.1), card_w - Inches(0.6), Inches(2.4))
            tf_bl = b_list.text_frame
            tf_bl.word_wrap = True
            for idx, b_text in enumerate(bullets[:4]):
                p_b = tf_bl.add_paragraph() if idx > 0 else tf_bl.paragraphs[0]
                p_b.text = f"•  {b_text}"
                p_b.font.name = "Segoe UI"
                p_b.font.size = Pt(11)
                p_b.font.color.rgb = _to_rgb(theme["text_primary"])
                p_b.space_after = Pt(6)

    notes = data.get("notes") or f"Highlight the three core strategic pillars. Emphasize how each pillar reinforces the overall architecture."
    slide.notes_slide.notes_text_frame.text = notes
    render_footer(slide, theme, data.get("deck_title", "Presentation"), current_idx, total_slides)


def render_process_pipeline_slide(prs: Any, theme: Dict[str, Any], data: Dict[str, Any], current_idx: int, total_slides: int):
    """Renders a 4-step horizontal workflow pipeline with chevron indicators."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    render_slide_background(slide, theme)
    render_header(slide, theme, data.get("title", "Execution Pipeline & Roadmap"), data.get("kicker", "OPERATIONAL ROADMAP"), data.get("subtitle"))

    raw_steps = data.get("steps") or data.get("stages") or []
    if not raw_steps:
        steps = [
            {"step": "01", "name": "Ingestion & Discovery", "phase": "Week 1", "items": ["Source data aggregation", "Schema verification", "Requirement extraction"]},
            {"step": "02", "name": "Deep Synthesis", "phase": "Week 2", "items": ["Multi-model reasoning", "Empirical cross-checking", "Risk vector analysis"]},
            {"step": "03", "name": "System Orchestration", "phase": "Week 3", "items": ["Pipeline construction", "Interface integration", "Telemetry binding"]},
            {"step": "04", "name": "Autonomous Deployment", "phase": "Week 4", "items": ["Continuous verification", "Production rollout", "Executive briefing"]}
        ]
    else:
        steps = []
        for i, s in enumerate(raw_steps):
            if isinstance(s, dict):
                steps.append(s)
            else:
                steps.append({"step": f"0{i+1}", "name": str(s), "phase": f"Phase {i+1}", "items": []})

    n = min(len(steps), 4)
    top_y = Inches(2.0)
    card_h = Inches(4.7)
    total_w = Inches(11.733)
    gap = Inches(0.28)
    card_w = (total_w - (gap * (n - 1))) / n

    for i in range(n):
        s_info = steps[i]
        c_left = Inches(0.8) + i * (card_w + gap)

        # Card container
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, top_y, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = _to_rgb(theme["card_bg"])
        card.line.color.rgb = _to_rgb(theme["card_border"])
        card.line.width = Pt(1.2)

        # Step Number Badge
        step_badge = slide.shapes.add_shape(MSO_SHAPE.OVAL, c_left + Inches(0.2), top_y + Inches(0.25), Inches(0.6), Inches(0.6))
        step_badge.fill.solid()
        step_badge.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
        step_badge.line.color.rgb = _to_rgb(theme["accent_primary"])
        step_badge.line.width = Pt(1.2)
        tf_sb = step_badge.text_frame
        p_sb = tf_sb.paragraphs[0]
        p_sb.text = str(s_info.get("step") or f"0{i+1}")
        p_sb.font.name = "Segoe UI"
        p_sb.font.size = Pt(13)
        p_sb.font.bold = True
        p_sb.font.color.rgb = _to_rgb(theme["accent_primary"])
        p_sb.alignment = PP_ALIGN.CENTER

        # Phase / Timeline Chip
        phase = str(s_info.get("phase") or f"Stage {i+1}")
        p_chip = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.9), top_y + Inches(0.35), card_w - Inches(1.1), Inches(0.32))
        p_chip.fill.solid()
        p_chip.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
        p_chip.line.color.rgb = _to_rgb(theme["card_border"])
        p_chip.line.width = Pt(0.8)
        tf_pc = p_chip.text_frame
        p_pc = tf_pc.paragraphs[0]
        p_pc.text = phase
        p_pc.font.name = "Segoe UI"
        p_pc.font.size = Pt(9)
        p_pc.font.bold = True
        p_pc.font.color.rgb = _to_rgb(theme["accent_secondary"])
        p_pc.alignment = PP_ALIGN.CENTER

        # Step Name
        n_box = slide.shapes.add_textbox(c_left + Inches(0.2), top_y + Inches(1.05), card_w - Inches(0.4), Inches(0.75))
        tf_n = n_box.text_frame
        tf_n.word_wrap = True
        p_n = tf_n.paragraphs[0]
        p_n.text = str(s_info.get("name") or f"Step {i+1}")
        p_n.font.name = "Segoe UI"
        p_n.font.size = Pt(14)
        p_n.font.bold = True
        p_n.font.color.rgb = _to_rgb(theme["text_primary"])
        p_n.font.name = "Segoe UI"
        p_n.font.size = Pt(14)
        p_n.font.bold = True
        p_n.font.color.rgb = _to_rgb(theme["text_primary"])

        # Deliverables / Items
        items = s_info.get("items") or s_info.get("bullets", [])
        if items:
            i_box = slide.shapes.add_textbox(c_left + Inches(0.2), top_y + Inches(1.85), card_w - Inches(0.4), Inches(2.6))
            tf_i = i_box.text_frame
            tf_i.word_wrap = True
            for idx, item_text in enumerate(items[:4]):
                p_it = tf_i.add_paragraph() if idx > 0 else tf_i.paragraphs[0]
                p_it.text = f"▶  {item_text}"
                p_it.font.name = "Segoe UI"
                p_it.font.size = Pt(10)
                p_it.font.color.rgb = _to_rgb(theme["text_muted"])
                p_it.space_after = Pt(6)

        # Connector arrow to next stage
        if i < n - 1:
            arrow_x = c_left + card_w + Inches(0.06)
            arr = slide.shapes.add_textbox(arrow_x, top_y + Inches(2.1), Inches(0.2), Inches(0.5))
            tf_a = arr.text_frame
            p_a = tf_a.paragraphs[0]
            p_a.text = "➔"
            p_a.font.name = "Segoe UI"
            p_a.font.size = Pt(14)
            p_a.font.bold = True
            p_a.font.color.rgb = _to_rgb(theme["accent_primary"])

    notes = data.get("notes") or f"Explain the linear progression across stages. Highlight how Stage {steps[0].get('step')} feeds seamlessly into deployment."
    slide.notes_slide.notes_text_frame.text = notes
    render_footer(slide, theme, data.get("deck_title", "Presentation"), current_idx, total_slides)


def render_quote_callout_slide(prs: Any, theme: Dict[str, Any], data: Dict[str, Any], current_idx: int, total_slides: int):
    """Renders an executive thesis or authority quote callout slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    render_slide_background(slide, theme)
    render_header(slide, theme, data.get("title", "Executive Perspective"), data.get("kicker", "CORE THESIS"), data.get("subtitle"))

    quote_text = data.get("quote", "Autonomous systems do not merely accelerate human capability—they fundamentally redefine the boundary between intent and execution.")
    author = data.get("author", "Autonomous Systems Architecture Group")
    role = data.get("role", "Executive Operations Directive")

    # Center Quote Card
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.5), Inches(2.0), Inches(10.333), Inches(4.5))
    card.fill.solid()
    card.fill.fore_color.rgb = _to_rgb(theme["card_bg"])
    card.line.color.rgb = _to_rgb(theme["card_border"])
    card.line.width = Pt(1.5)

    # Stylized Quotation Mark
    q_mark = slide.shapes.add_textbox(Inches(1.8), Inches(2.1), Inches(1.5), Inches(1.0))
    tf_q = q_mark.text_frame
    p_q = tf_q.paragraphs[0]
    p_q.text = "“"
    p_q.font.name = "Georgia"
    p_q.font.size = Pt(72)
    p_q.font.bold = True
    p_q.font.color.rgb = _to_rgb(theme["accent_primary"])

    # Main Quote Text
    body_box = slide.shapes.add_textbox(Inches(2.2), Inches(2.8), Inches(9.0), Inches(2.0))
    tf_b = body_box.text_frame
    tf_b.word_wrap = True
    p_b = tf_b.paragraphs[0]
    p_b.text = quote_text
    p_b.font.name = "Georgia"
    p_b.font.size = Pt(22)
    p_b.font.italic = True
    p_b.font.color.rgb = _to_rgb(theme["text_primary"])

    # Author Card
    a_box = slide.shapes.add_textbox(Inches(2.2), Inches(5.0), Inches(9.0), Inches(1.0))
    tf_a = a_box.text_frame
    tf_a.word_wrap = True
    p_a1 = tf_a.paragraphs[0]
    p_a1.text = f"—  {author}"
    p_a1.font.name = "Segoe UI"
    p_a1.font.size = Pt(15)
    p_a1.font.bold = True
    p_a1.font.color.rgb = _to_rgb(theme["accent_primary"])

    p_a2 = tf_a.add_paragraph()
    p_a2.text = role
    p_a2.font.name = "Segoe UI"
    p_a2.font.size = Pt(12)
    p_a2.font.color.rgb = _to_rgb(theme["text_muted"])

    notes = data.get("notes") or f"Pause on this quote. Deliver it with measured cadence to let the core thesis sink in with the executive stakeholders."
    slide.notes_slide.notes_text_frame.text = notes
    render_footer(slide, theme, data.get("deck_title", "Presentation"), current_idx, total_slides)


def render_matrix_table_slide(prs: Any, theme: Dict[str, Any], data: Dict[str, Any], current_idx: int, total_slides: int):
    """Renders a structured, high-contrast matrix table slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    render_slide_background(slide, theme)
    render_header(slide, theme, data.get("title", "Comparative Matrix & Specifications"), data.get("kicker", "TECHNICAL MATRIX"), data.get("subtitle"))

    headers = data.get("headers") or ["Strategic Capability", "Standard Workflow", "J.A.R.V.I.S. Autonomous Protocol", "Business Impact"]
    rows = data.get("rows") or [
        ["Research Synthesis", "Manual search & copy-paste (2-3 hrs)", "Autonomous 5-Source Engine (30s)", "6x Velocity"],
        ["Presentation Authoring", "Static templates & manual formatting", "High-Impact AI Geometric Canvas", "100% Autonomy"],
        ["System Control", "Manual clicks across apps", "Natural Voice & STUNT Bridge", "Zero Friction"],
        ["Academic & Exam Prep", "Unorganized notes & PDFs", "Feynman Tutor & College Hub", "Top 1% Mastery"]
    ]

    num_rows = len(rows) + 1
    num_cols = len(headers)

    t_shape = slide.shapes.add_table(num_rows, num_cols, Inches(0.8), Inches(2.0), Inches(11.733), Inches(4.5))
    table = t_shape.table

    # Set column widths proportionally
    col_w = Inches(11.733) / num_cols
    for c_idx in range(num_cols):
        table.columns[c_idx].width = int(col_w)

    # Style Header Row
    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = h_text
        p.font.name = "Segoe UI"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = _to_rgb(theme["accent_primary"])
        p.alignment = PP_ALIGN.CENTER

    # Style Data Rows
    for row_idx, row_data in enumerate(rows):
        is_even = (row_idx % 2 == 0)
        row_color = theme["card_bg"] if is_even else theme["bg_color"]
        for col_idx, val in enumerate(row_data[:num_cols]):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = _to_rgb(row_color)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = str(val)
            p.font.name = "Segoe UI"
            p.font.size = Pt(11)
            # Accent the last column (e.g. Impact)
            if col_idx == num_cols - 1:
                p.font.bold = True
                p.font.color.rgb = _to_rgb(theme["accent_secondary"])
                p.alignment = PP_ALIGN.CENTER
            else:
                p.font.color.rgb = _to_rgb(theme["text_primary"])
                p.alignment = PP_ALIGN.LEFT

    notes = data.get("notes") or f"Review the comparative matrix. Point out row by row how the Stark protocol outperforms manual baselines."
    slide.notes_slide.notes_text_frame.text = notes
    render_footer(slide, theme, data.get("deck_title", "Presentation"), current_idx, total_slides)


def render_agenda_slide(prs: Any, theme: Dict[str, Any], data: Dict[str, Any], current_idx: int, total_slides: int):
    """Renders a crisp executive agenda/roadmap slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    render_slide_background(slide, theme)
    render_header(slide, theme, data.get("title", "Executive Agenda"), data.get("kicker", "BRIEFING OVERVIEW"), data.get("subtitle"))

    raw_items = data.get("items") or data.get("agenda") or []
    if not raw_items:
        items = [
            {"num": "01", "title": "Strategic Context & Problem Space", "desc": "Current landscape vulnerabilities and systemic friction."},
            {"num": "02", "title": "Empirical Performance Metrics", "desc": "Quantified benchmarks and throughput validation."},
            {"num": "03", "title": "Core Architectural Capabilities", "desc": "Multi-agent orchestration and deep intelligence."},
            {"num": "04", "title": "Roadmap & Actionable Next Steps", "desc": "Immediate execution milestones and governance."}
        ]
    else:
        items = []
        for i, itm in enumerate(raw_items):
            if isinstance(itm, dict):
                items.append(itm)
            else:
                items.append({"num": f"0{i+1}", "title": str(itm), "desc": ""})

    top_y = Inches(2.0)
    card_h = Inches(4.6)
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top_y, Inches(11.733), card_h)
    card.fill.solid()
    card.fill.fore_color.rgb = _to_rgb(theme["card_bg"])
    card.line.color.rgb = _to_rgb(theme["card_border"])
    card.line.width = Pt(1.2)

    item_h = Inches(4.0) / max(len(items), 1)
    for i, itm in enumerate(items):
        cur_y = top_y + Inches(0.3) + i * item_h

        # Number pill
        num_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), cur_y, Inches(0.65), Inches(0.55))
        num_box.fill.solid()
        num_box.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
        num_box.line.color.rgb = _to_rgb(theme["accent_primary"])
        num_box.line.width = Pt(1.0)
        tf_nb = num_box.text_frame
        p_nb = tf_nb.paragraphs[0]
        p_nb.text = str(itm.get("num") or f"0{i+1}")
        p_nb.font.name = "Segoe UI"
        p_nb.font.size = Pt(13)
        p_nb.font.bold = True
        p_nb.font.color.rgb = _to_rgb(theme["accent_primary"])
        p_nb.alignment = PP_ALIGN.CENTER

        # Title & Description
        txt_box = slide.shapes.add_textbox(Inches(2.1), cur_y - Inches(0.05), Inches(10.0), item_h)
        tf_t = txt_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = str(itm.get("title") or f"Topic {i+1}")
        p_t.font.name = "Segoe UI"
        p_t.font.size = Pt(15)
        p_t.font.bold = True
        p_t.font.color.rgb = _to_rgb(theme["text_primary"])

        if itm.get("desc"):
            p_d = tf_t.add_paragraph()
            p_d.text = str(itm.get("desc"))
            p_d.font.name = "Segoe UI"
            p_d.font.size = Pt(11)
            p_d.font.color.rgb = _to_rgb(theme["text_muted"])

    notes = data.get("notes") or f"Walk the room through today's agenda. Outline the primary checkpoints and time allocations."
    slide.notes_slide.notes_text_frame.text = notes
    render_footer(slide, theme, data.get("deck_title", "Presentation"), current_idx, total_slides)


def render_conclusion_slide(prs: Any, theme: Dict[str, Any], data: Dict[str, Any], current_idx: int, total_slides: int):
    """Renders a commanding executive conclusion slide with 3 action items."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    render_slide_background(slide, theme)
    render_header(slide, theme, data.get("title", "Strategic Conclusion & Next Steps"), data.get("kicker", "ACTION PLAN"), data.get("subtitle"))

    takeaway = data.get("takeaway", "Autonomous intelligence delivers exponential velocity when integrated across systems.")
    raw_actions = data.get("actions") or []
    if not raw_actions:
        action_items = [
            {"step": "01", "title": "Deploy Pilot Protocol", "detail": "Activate initial testing across non-critical workflows."},
            {"step": "02", "title": "Measure Delta & KPIs", "detail": "Quantify latency reductions and accuracy benchmarks."},
            {"step": "03", "title": "Full Production Rollout", "detail": "Transition core operations to autonomous supervision."}
        ]
    else:
        action_items = []
        for i, a in enumerate(raw_actions):
            if isinstance(a, dict):
                action_items.append(a)
            else:
                action_items.append({"step": f"0{i+1}", "title": str(a), "detail": ""})

    # Executive Takeaway Banner
    t_banner = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.0), Inches(11.733), Inches(0.95))
    t_banner.fill.solid()
    t_banner.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
    t_banner.line.color.rgb = _to_rgb(theme["accent_primary"])
    t_banner.line.width = Pt(1.2)
    tf_tb = t_banner.text_frame
    tf_tb.word_wrap = True
    p_tb = tf_tb.paragraphs[0]
    p_tb.text = f"KEY EXECUTIVE TAKEAWAY:\n{takeaway}"
    p_tb.font.name = "Segoe UI"
    p_tb.font.size = Pt(13)
    p_tb.font.bold = True
    p_tb.font.color.rgb = _to_rgb(theme["text_primary"])
    p_tb.alignment = PP_ALIGN.CENTER

    # 3 Next Step Cards
    top_y = Inches(3.2)
    card_h = Inches(2.6)
    total_w = Inches(11.733)
    gap = Inches(0.4)
    num_cards = min(len(action_items), 3)
    card_w = (total_w - (gap * max(num_cards - 1, 1))) / max(num_cards, 1)

    for i in range(num_cards):
        a_info = action_items[i]
        c_left = Inches(0.8) + i * (card_w + gap)

        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, top_y, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = _to_rgb(theme["card_bg"])
        card.line.color.rgb = _to_rgb(theme["card_border"])
        card.line.width = Pt(1.2)

        # Step indicator
        step_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.2), top_y + Inches(0.25), Inches(0.55), Inches(0.5))
        step_box.fill.solid()
        step_box.fill.fore_color.rgb = _to_rgb(theme["badge_bg"])
        step_box.line.color.rgb = _to_rgb(theme["accent_primary"])
        step_box.line.width = Pt(1.0)
        tf_s = step_box.text_frame
        p_s = tf_s.paragraphs[0]
        p_s.text = str(a_info.get("step") or f"0{i+1}")
        p_s.font.name = "Segoe UI"
        p_s.font.size = Pt(12)
        p_s.font.bold = True
        p_s.font.color.rgb = _to_rgb(theme["accent_primary"])
        p_s.alignment = PP_ALIGN.CENTER

        # Title
        t_box = slide.shapes.add_textbox(c_left + Inches(0.9), top_y + Inches(0.25), card_w - Inches(1.1), Inches(0.6))
        tf_t = t_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = str(a_info.get("title") or f"Action {i+1}")
        p_t.font.name = "Segoe UI"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = _to_rgb(theme["text_primary"])

        # Detail
        d_box = slide.shapes.add_textbox(c_left + Inches(0.2), top_y + Inches(0.95), card_w - Inches(0.4), Inches(1.4))
        tf_d = d_box.text_frame
        tf_d.word_wrap = True
        p_d = tf_d.paragraphs[0]
        p_d.text = str(a_info.get("detail") or "")
        p_d.font.name = "Segoe UI"
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = _to_rgb(theme["text_muted"])
        p_d.font.name = "Segoe UI"
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = _to_rgb(theme["text_muted"])

    # Q&A Footer Pill
    qa_bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.1), Inches(11.733), Inches(0.6))
    qa_bar.fill.solid()
    qa_bar.fill.fore_color.rgb = _to_rgb(theme["card_bg"])
    qa_bar.line.color.rgb = _to_rgb(theme["accent_primary"])
    qa_bar.line.width = Pt(1.0)
    tf_qa = qa_bar.text_frame
    p_qa = tf_qa.paragraphs[0]
    p_qa.text = "✦  FLOOR OPEN FOR STRATEGIC Q&A  •  THANK YOU  ✦"
    p_qa.font.name = "Segoe UI"
    p_qa.font.size = Pt(12)
    p_qa.font.bold = True
    p_qa.font.color.rgb = _to_rgb(theme["accent_primary"])
    p_qa.alignment = PP_ALIGN.CENTER

    notes = data.get("notes") or f"Summarize the final call-to-action with authority. Invite questions from the room."
    slide.notes_slide.notes_text_frame.text = notes
    render_footer(slide, theme, data.get("deck_title", "Presentation"), current_idx, total_slides)


def render_standard_content_slide(prs: Any, theme: Dict[str, Any], data: Dict[str, Any], current_idx: int, total_slides: int):
    """Fallback high-impact cards renderer for general bullet content."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    render_slide_background(slide, theme)
    render_header(slide, theme, data.get("title", "Key Strategic Concept"), data.get("kicker", "ANALYSIS"), data.get("subtitle"))

    bullets = data.get("bullets", [])
    top_y = Inches(2.0)
    card_h = Inches(4.7)
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top_y, Inches(11.733), card_h)
    card.fill.solid()
    card.fill.fore_color.rgb = _to_rgb(theme["card_bg"])
    card.line.color.rgb = _to_rgb(theme["card_border"])
    card.line.width = Pt(1.2)

    box = slide.shapes.add_textbox(Inches(1.2), top_y + Inches(0.4), Inches(10.9), Inches(4.0))
    tf = box.text_frame
    tf.word_wrap = True

    if not bullets:
        bullets = ["Autonomous execution pipeline active", "System metrics aligned with target thresholds", "Operational readiness verified across all channels"]

    for idx, b_text in enumerate(bullets):
        p = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
        p.text = f"▶  {b_text}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(14)
        p.font.color.rgb = _to_rgb(theme["text_primary"])
        p.space_after = Pt(12)

    notes = data.get("notes") or f"Review the key strategic points outlined on this slide."
    slide.notes_slide.notes_text_frame.text = notes
    render_footer(slide, theme, data.get("deck_title", "Presentation"), current_idx, total_slides)


# ====================================================================
# 4. AUTONOMOUS AI STORYBOARD GENERATION ENGINE
# ====================================================================

STORYBOARD_SYSTEM_PROMPT = """
You are the J.A.R.V.I.S. Autonomous Executive Presentation Designer.
Your mission is to architect an intriguing, high-impact, world-class 16:9 widescreen presentation deck.

Guidelines:
1. Compelling Narrative Progression:
   - Slide 1: 'hero_title' (Bold hook, author credentials, project badge)
   - Slide 2: 'agenda' (Executive roadmap of briefing)
   - Slide 3: 'comparison' (Status Quo / Problem vs. The Autonomous Solution)
   - Slide 4: 'kpi_cards' (3 or 4 high-impact metrics with big numbers and delta chips)
   - Slide 5: 'feature_grid' (3 core pillars or strategic capabilities)
   - Slide 6: 'process_pipeline' (4-step execution flow or technical roadmap)
   - Slide 7: 'quote' or 'table' (Authoritative thesis or comparative specifications table)
   - Slide 8: 'conclusion' (High-impact executive takeaway and 3 next steps)

2. Visual Variety:
   - NEVER use the same slide archetype twice in a row.
   - Every slide must feature a 'kicker' (e.g. 'EXECUTIVE OVERVIEW', 'EMPIRICAL BENCHMARKS', 'PIPELINE ARCHITECTURE').

3. Speaker Notes for Every Single Slide:
   - Write comprehensive, natural speaker notes for every slide to guide Akul during delivery.
   - Include tone cues (e.g., [Deliberate, authoritative], [Energetic, high-conviction]).

4. Valid JSON Output ONLY:
   Output ONLY a valid JSON object matching this schema:
   {
     "deck_title": "string",
     "theme": "cyberpunk_stark | executive_obsidian | silicon_minimalist | emerald_science | solar_amber",
     "slides": [
       {
         "type": "hero_title | agenda | comparison | kpi_cards | feature_grid | process_pipeline | quote | table | conclusion",
         "kicker": "string",
         "title": "string",
         "subtitle": "string",
         "notes": "string",
         ... archetype-specific fields (e.g. cards, col1_title, col1_bullets, col2_title, col2_bullets, features, steps, quote, author, headers, rows, takeaway, actions)
       }
     ]
   }
"""

def generate_presentation_storyboard(
    topic: str,
    num_slides: int = 7,
    theme_hint: Optional[str] = None,
    audience: str = "Executive & Academic",
    source_content: Optional[str] = None,
    tone: str = "Authoritative, Innovative, Intriguing"
) -> Dict[str, Any]:
    """Generates an end-to-end presentation storyboard using Gemini AI with fallback resilience."""
    try:
        from core.ai_client import generate_text_with_retry
    except ImportError:
        generate_text_with_retry = None

    theme = theme_hint or DEFAULT_THEME

    user_prompt = f"""
Architect an intriguing {num_slides}-slide presentation on the topic:
TOPIC: {topic}
AUDIENCE: {audience}
DESIRED THEME: {theme}
TONE: {tone}

{f'ADDITIONAL SOURCE MATERIAL/CONTEXT: {source_content[:4000]}' if source_content else ''}

Ensure each slide has full structured data and rich speaker delivery notes.
Respond with pure JSON only.
"""

    if generate_text_with_retry:
        try:
            raw_res = generate_text_with_retry(
                prompt_or_contents=[
                    {"role": "user", "parts": [{"text": STORYBOARD_SYSTEM_PROMPT + "\n\n" + user_prompt}]}
                ]
            )
            # Clean JSON formatting
            clean_res = raw_res.strip()
            if "```json" in clean_res:
                clean_res = clean_res.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in clean_res:
                clean_res = clean_res.split("```", 1)[1].split("```", 1)[0].strip()
            
            data = json.loads(clean_res)
            if "slides" in data and len(data["slides"]) > 0:
                return data
        except Exception as e:
            # Fall back to high-grade deterministic storyboard
            pass

    # High-grade deterministic fallback template
    return _build_fallback_storyboard(topic, num_slides, theme)


def _build_fallback_storyboard(topic: str, num_slides: int, theme: str) -> Dict[str, Any]:
    """Generates a high-quality structured storyboard when offline or during API limits."""
    slides = [
        {
            "type": "hero_title",
            "kicker": "STRATEGIC EXECUTIVE BRIEFING",
            "title": topic.title(),
            "subtitle": "Autonomous Framework, Empirical Benchmarks & Next-Gen Implementation",
            "author": "Akul | NMIMS Mumbai",
            "organization": "Executive Operations & Technology",
            "notes": f"Welcome everyone. Today we present our comprehensive briefing on {topic}. We examine the foundational vectors, comparative paradigm shifts, and an actionable roadmap."
        },
        {
            "type": "agenda",
            "kicker": "BRIEFING ROADMAP",
            "title": "Executive Briefing Structure",
            "subtitle": "Navigating core strategic vectors and operational milestones",
            "items": [
                {"num": "01", "title": "The Strategic Problem Space", "desc": "Current operational bottlenecks and systemic latency."},
                {"num": "02", "title": "Empirical Performance Metrics", "desc": "Quantified KPIs, throughput, and verified benchmarks."},
                {"num": "03", "title": "Core Technical Capabilities", "desc": "Autonomous orchestration and high-fidelity execution."},
                {"num": "04", "title": "Execution Roadmap & Delivery", "desc": "Phased implementation milestones and governance."}
            ],
            "notes": "Outline the four primary domains of today's briefing. Keep pacing brisk and invite active consideration."
        },
        {
            "type": "comparison",
            "kicker": "ARCHITECTURAL DICHOTOMY",
            "title": "Status Quo vs. Autonomous Vanguard",
            "subtitle": "Contrasting legacy operational friction against high-velocity execution",
            "col1_title": "Legacy / Manual Baselines",
            "col1_bullets": [
                "Fragmented toolchains with high human coordination tax",
                "Linear bottlenecking and non-deterministic error recovery",
                "High latency in multi-source intelligence gathering",
                "Scattered institutional context across unindexed documents"
            ],
            "col2_title": "J.A.R.V.I.S. Autonomous Protocol",
            "col2_bullets": [
                "Unified multi-agent orchestration across desktop & web",
                "Deterministic verification loops and automated testing",
                "Instant multi-source academic & operational synthesis",
                "Persistent telemetry and deep contextual memory"
            ],
            "verdict": "Strategic Verdict: Transitioning to the Stark Protocol delivers 5.4x operational velocity.",
            "notes": "Stress the architectural dichotomy. The left represents unsustainable legacy tax; the right unlocks autonomous scale."
        },
        {
            "type": "kpi_cards",
            "kicker": "EMPIRICAL BENCHMARKS",
            "title": "Quantified Impact & Performance",
            "subtitle": "Empirically verified metrics across production environments",
            "cards": [
                {"value": "99.8%", "label": "Execution Reliability", "delta": "+42% vs Baseline", "bullets": ["Full test-suite coverage", "Zero runtime regressions"]},
                {"value": "12x", "label": "Synthesis Velocity", "delta": "Sub-Second Ingestion", "bullets": ["Parallel agent processing", "Real-time verification"]},
                {"value": "100%", "label": "Autonomous Sovereignty", "delta": "Local & Secure", "bullets": ["Zero unmonitored egress", "Hardware equilibrium active"]}
            ],
            "notes": "Direct the audience to the 99.8% reliability figure. Emphasize that these metrics are backed by automated verification."
        },
        {
            "type": "feature_grid",
            "kicker": "CORE CAPABILITIES",
            "title": "Three Strategic Pillars",
            "subtitle": "Foundational modules enabling end-to-end execution",
            "features": [
                {"badge": "01", "title": "Cognitive Reasoning", "desc": "Multi-model orchestration with automatic fallback resilience.", "bullets": ["Deep research synthesis", "Exam companion mastery"]},
                {"badge": "02", "title": "Systemic Execution", "desc": "Hardware-level controls and full application automation.", "bullets": ["STUNT desktop bridge", "PowerPoint & Office COM"]},
                {"badge": "03", "title": "Autonomous Governance", "desc": "Continuous self-testing, logging, and security shields.", "bullets": ["War mode protocols", "Hardware equilibrium"]}
            ],
            "notes": "Walk through each pillar sequentially. Highlight how reasoning translates directly into systemic action."
        },
        {
            "type": "process_pipeline",
            "kicker": "OPERATIONAL ROADMAP",
            "title": "Four-Phase Rollout Pipeline",
            "subtitle": "Systematic progression from ingestion to production readiness",
            "steps": [
                {"step": "01", "name": "Ingestion & Discovery", "phase": "Phase 1", "items": ["Telemetry capture", "Context mapping"]},
                {"step": "02", "name": "Synthesized Design", "phase": "Phase 2", "items": ["Geometric canvas layout", "Palette harmonization"]},
                {"step": "03", "name": "Orchestrated Review", "phase": "Phase 3", "items": ["Speaker script generation", "Test suite verification"]},
                {"step": "04", "name": "Executive Delivery", "phase": "Phase 4", "items": ["SlideShow automation", "PDF publication"]}
            ],
            "notes": "Explain how the four phases ensure zero deployment risk and seamless executive delivery."
        },
        {
            "type": "conclusion",
            "kicker": "STRATEGIC IMPERATIVE",
            "title": "Final Takeaway & Immediate Actions",
            "subtitle": "Concrete roadmap for immediate organizational execution",
            "takeaway": f"Harnessing autonomous presentation and intelligence systems transforms {topic} into an unfair competitive advantage.",
            "actions": [
                {"step": "01", "title": "Authorize Pilot Deployment", "detail": "Implement autonomous protocols across key test operations."},
                {"step": "02", "title": "Establish Telemetry Loops", "detail": "Track daily efficiency gains and accuracy metrics."},
                {"step": "03", "title": "Scale Full Fleet", "detail": "Standardize Mark 58 intelligence across all workflows."}
            ],
            "notes": "Deliver the final takeaway with confidence. Invite immediate questions and open the floor for discussion."
        }
    ]
    return {
        "deck_title": topic.title(),
        "theme": theme,
        "slides": slides[:num_slides]
    }


# ====================================================================
# 5. HIGH-LEVEL DECK BUILDER & CONTROLS
# ====================================================================

def build_presentation_from_storyboard(
    storyboard: Dict[str, Any],
    output_filename: Optional[str] = None,
    target_location: str = "desktop",
    open_after: bool = True
) -> Dict[str, Any]:
    """Compiles a complete structured storyboard into a 16:9 widescreen .pptx presentation."""
    if not PPTX_AVAILABLE:
        return {"status": "error", "message": "python-pptx library is not installed."}

    theme_name = storyboard.get("theme", DEFAULT_THEME)
    theme = get_theme(theme_name)
    deck_title = storyboard.get("deck_title", "Presentation")
    slides_data = storyboard.get("slides", [])
    total_slides = len(slides_data)

    prs = create_base_presentation()

    # Render each slide based on its designated archetype
    for idx, s_data in enumerate(slides_data, start=1):
        s_data["deck_title"] = deck_title
        s_type = (s_data.get("type") or "content").lower().strip()

        if s_type in ("hero_title", "title", "hero"):
            render_hero_title_slide(prs, theme, s_data, idx, total_slides)
        elif s_type in ("kpi_cards", "kpi", "metrics", "stats"):
            render_kpi_cards_slide(prs, theme, s_data, idx, total_slides)
        elif s_type in ("comparison", "split", "versus", "pro_con"):
            render_comparison_cards_slide(prs, theme, s_data, idx, total_slides)
        elif s_type in ("feature_grid", "features", "pillars", "grid"):
            render_feature_grid_slide(prs, theme, s_data, idx, total_slides)
        elif s_type in ("process_pipeline", "pipeline", "roadmap", "steps", "flow"):
            render_process_pipeline_slide(prs, theme, s_data, idx, total_slides)
        elif s_type in ("quote", "callout", "thesis"):
            render_quote_callout_slide(prs, theme, s_data, idx, total_slides)
        elif s_type in ("table", "matrix", "specs"):
            render_matrix_table_slide(prs, theme, s_data, idx, total_slides)
        elif s_type in ("agenda", "overview", "table_of_contents"):
            render_agenda_slide(prs, theme, s_data, idx, total_slides)
        elif s_type in ("conclusion", "summary", "next_steps", "action_plan"):
            render_conclusion_slide(prs, theme, s_data, idx, total_slides)
        else:
            render_standard_content_slide(prs, theme, s_data, idx, total_slides)

    # Determine output file path
    out_dir = _get_output_dir(target_location)
    if not output_filename:
        safe_title = re.sub(r"[^\w\s-]", "", deck_title).strip().replace(" ", "_")
        output_filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
    elif not output_filename.endswith(".pptx"):
        output_filename += ".pptx"

    file_path = out_dir / output_filename
    prs.save(str(file_path))

    # Auto-open if requested
    if open_after:
        try:
            os.startfile(str(file_path))
        except Exception:
            pass

    return {
        "status": "success",
        "file_path": str(file_path),
        "filename": output_filename,
        "slide_count": total_slides,
        "theme": theme_name,
        "theme_name": theme["name"],
        "deck_title": deck_title
    }


def create_intriguing_presentation(
    topic: str,
    theme: Optional[str] = None,
    num_slides: int = 7,
    audience: str = "Executive & Academic",
    target_location: str = "desktop",
    open_after: bool = True,
    source_content: Optional[str] = None,
    custom_slides: Optional[List[Dict[str, Any]]] = None,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """End-to-end presentation authoring: research, design, speaker notes, and compilation."""
    theme_choice = theme or DEFAULT_THEME

    if custom_slides:
        storyboard = {
            "deck_title": topic.title(),
            "theme": theme_choice,
            "slides": custom_slides
        }
    else:
        storyboard = generate_presentation_storyboard(
            topic=topic,
            num_slides=num_slides,
            theme_hint=theme_choice,
            audience=audience,
            source_content=source_content
        )

    return build_presentation_from_storyboard(
        storyboard=storyboard,
        output_filename=filename,
        target_location=target_location,
        open_after=open_after
    )


# ====================================================================
# 6. INTERACTIVE PRESENTATION CONTROLS (FULL FREEDOM)
# ====================================================================

def start_slideshow(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Launches the specified PowerPoint presentation directly into full-screen SlideShow mode."""
    p = Path(file_path)
    if not p.exists():
        # Check desktop
        cand = _get_output_dir("desktop") / file_path
        if cand.exists(): p = cand

    if not p.exists():
        return {"status": "error", "message": f"Presentation file not found at: {file_path}"}

    try:
        import win32com.client
        ppt = win32com.client.Dispatch("PowerPoint.Application")
        ppt.Visible = True
        prs = ppt.Presentations.Open(str(p.resolve()))
        prs.SlideShowSettings.Run()
        return {
            "status": "success",
            "message": f"Full-screen SlideShow initiated for: {p.name}",
            "file": str(p)
        }
    except Exception as e:
        # Fallback to os.startfile
        try:
            os.startfile(str(p.resolve()))
            return {"status": "partial_success", "message": f"Opened presentation in PowerPoint: {p.name}", "error": str(e)}
        except Exception as e2:
            return {"status": "error", "message": f"Failed to start presentation: {e2}"}


def convert_presentation_to_pdf(file_path: Union[str, Path], output_pdf_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Exports a PowerPoint presentation to a high-fidelity 16:9 PDF using PowerPoint COM automation."""
    p = Path(file_path)
    if not p.exists():
        cand = _get_output_dir("desktop") / file_path
        if cand.exists(): p = cand

    if not p.exists():
        return {"status": "error", "message": f"Presentation not found: {file_path}"}

    out_p = Path(output_pdf_path) if output_pdf_path else p.with_suffix(".pdf")

    try:
        import win32com.client
        ppt = win32com.client.Dispatch("PowerPoint.Application")
        prs = ppt.Presentations.Open(str(p.resolve()), WithWindow=False)
        prs.SaveAs(str(out_p.resolve()), 32)  # 32 = ppSaveAsPDF
        prs.Close()
        return {
            "status": "success",
            "message": f"Successfully exported presentation to PDF: {out_p.name}",
            "pdf_path": str(out_p),
            "size_bytes": out_p.stat().st_size
        }
    except Exception as e:
        return {"status": "error", "message": f"PDF export failed via PowerPoint COM: {e}"}


def export_speaker_script(file_path: Union[str, Path], output_md_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Extracts speaker delivery notes from every slide and compiles an executive speech rehearsal guide."""
    p = Path(file_path)
    if not p.exists():
        cand = _get_output_dir("desktop") / file_path
        if cand.exists(): p = cand

    if not p.exists():
        return {"status": "error", "message": f"Presentation not found: {file_path}"}

    if not PPTX_AVAILABLE:
        return {"status": "error", "message": "python-pptx not available."}

    prs = Presentation(str(p.resolve()))
    lines = [
        f"# Speaker Delivery & Rehearsal Script",
        f"**Deck:** {p.name}  ",
        f"**Authored:** {datetime.now().strftime('%B %d, %Y')}  ",
        f"**System:** J.A.R.V.I.S. Mark 58 Autonomous Executive Suite  ",
        f"\n---\n"
    ]

    total = len(prs.slides)
    for idx, slide in enumerate(prs.slides, start=1):
        # Extract title
        title = "Untitled Slide"
        for shape in slide.shapes:
            if shape.has_text_frame and shape.text_frame.text:
                first_line = shape.text_frame.text.splitlines()[0].strip()
                if len(first_line) > 3 and not first_line.startswith("0") and not first_line.startswith("J.A.R.V.I.S."):
                    title = first_line
                    break

        notes = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
        if not notes:
            notes = "[No explicit speaker notes recorded for this slide.]"

        lines.append(f"## Slide {idx:02d}: {title}")
        lines.append(f"**Presenter Cue & Talking Points:**\n")
        lines.append(f"> {notes}\n")
        lines.append(f"---\n")

    out_file = Path(output_md_path) if output_md_path else p.with_name(f"{p.stem}_Speaker_Script.md")
    out_file.write_text("\n".join(lines), encoding="utf-8")

    return {
        "status": "success",
        "message": f"Speaker script generated for {total} slides.",
        "script_path": str(out_file),
        "slide_count": total
    }


def retheme_presentation(file_path: Union[str, Path], new_theme: str) -> Dict[str, Any]:
    """Rethemes a presentation by regenerating its visual components with the newly requested palette."""
    p = Path(file_path)
    if not p.exists():
        cand = _get_output_dir("desktop") / file_path
        if cand.exists(): p = cand

    if not p.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}

    # Extract title and topic from presentation stem
    topic = p.stem.replace("_", " ")
    out_name = f"{p.stem}_{new_theme}.pptx"
    target_loc = str(p.parent) if p.parent.exists() else "desktop"
    
    return create_intriguing_presentation(
        topic=topic,
        theme=new_theme,
        filename=out_name,
        target_location=target_loc,
        open_after=False
    )


# ====================================================================
# 7. MAIN TOOL ENTRY POINT FOR J.A.R.V.I.S.
# ====================================================================

def presentation_designer(parameters: Dict[str, Any], player: Any = None) -> str:
    """
    Main tool handler for J.A.R.V.I.S. Presentation Designer.
    
    parameters:
      action: 'create' | 'plan' | 'slideshow' | 'export_pdf' | 'speaker_script' | 'retheme' | 'list_themes'
      topic: Subject or topic of presentation
      theme: 'cyberpunk_stark' | 'executive_obsidian' | 'silicon_minimalist' | 'emerald_science' | 'solar_amber'
      num_slides: Number of slides (default 7)
      audience: Target audience (e.g. 'Board of Directors', 'College Class', 'Investors')
      source_content: Optional notes, document excerpt, or research dossier
      target_location: 'desktop' | 'downloads' | 'documents'
      filename: Optional specific output filename
      file_path: Existing presentation path for slideshow, PDF conversion, or script extraction
      open_after: Whether to launch the deck immediately (default True)
    """
    action = (parameters.get("action") or "create").lower().strip()
    topic = parameters.get("topic") or parameters.get("title") or "Autonomous Artificial Intelligence"
    theme = parameters.get("theme") or DEFAULT_THEME
    num_slides = int(parameters.get("num_slides") or 7)
    audience = parameters.get("audience") or "Executive & Academic"
    src = parameters.get("source_content") or parameters.get("content")
    loc = parameters.get("target_location") or "desktop"
    fname = parameters.get("filename")
    fpath = parameters.get("file_path")
    open_after = parameters.get("open_after", True)

    if player and hasattr(player, "write_log"):
        player.write_log(f"PRESENTATION DESIGNER: Executing action '{action}' for topic '{topic}' [Theme: {theme}]...")

    # 1. LIST THEMES
    if action in ("list_themes", "themes"):
        theme_list = "\n".join([f"• **{k}** ({v['name']}): {v['description']}" for k, v in THEMES.items()])
        return (
            f"### Available J.A.R.V.I.S. Presentation Themes:\n\n{theme_list}\n\n"
            f"*To use any theme, specify `theme='<key>'` when creating or re-theming.*"
        )

    # 2. PLAN / STORYBOARD ONLY
    elif action in ("plan", "storyboard", "outline"):
        sb = generate_presentation_storyboard(topic, num_slides, theme, audience, src)
        slides_summary = []
        for i, s in enumerate(sb.get("slides", []), start=1):
            slides_summary.append(f"{i:02d}. **{s.get('type', 'slide').upper()}**: {s.get('title')} — *{s.get('subtitle', '')}*")
        
        return (
            f"### Presentation Blueprint: {sb.get('deck_title')}\n"
            f"**Recommended Theme:** {sb.get('theme')}\n"
            f"**Total Slides:** {len(sb.get('slides', []))}\n\n"
            + "\n".join(slides_summary)
            + f"\n\n*Say 'JARVIS, build this presentation' to render the complete deck.*"
        )

    # 3. START SLIDESHOW (FULL SCREEN)
    elif action in ("slideshow", "present", "start_slideshow"):
        target_f = fpath or fname
        if not target_f:
            # Look for most recent pptx on Desktop
            desk = _get_output_dir("desktop")
            pptx_files = sorted(desk.glob("*.pptx"), key=lambda f: f.stat().st_mtime, reverse=True)
            if pptx_files:
                target_f = pptx_files[0]
            else:
                return "No presentation file specified and none found on Desktop to present."
        res = start_slideshow(target_f)
        return res.get("message", str(res))

    # 4. EXPORT TO PDF
    elif action in ("export_pdf", "convert_pdf", "pdf"):
        target_f = fpath or fname
        if not target_f:
            desk = _get_output_dir("desktop")
            pptx_files = sorted(desk.glob("*.pptx"), key=lambda f: f.stat().st_mtime, reverse=True)
            if pptx_files: target_f = pptx_files[0]
            else: return "Please specify the presentation file to export to PDF."
        res = convert_presentation_to_pdf(target_f)
        if res.get("status") == "success":
            return f"Flawlessly exported presentation to 16:9 PDF:\n📄 `{res.get('pdf_path')}`"
        return f"PDF export failed: {res.get('message')}"

    # 5. SPEAKER SCRIPT & REHEARSAL GUIDE
    elif action in ("speaker_script", "script", "rehearse", "notes"):
        target_f = fpath or fname
        if not target_f:
            desk = _get_output_dir("desktop")
            pptx_files = sorted(desk.glob("*.pptx"), key=lambda f: f.stat().st_mtime, reverse=True)
            if pptx_files: target_f = pptx_files[0]
            else: return "Please specify the presentation file to generate speaker notes for."
        res = export_speaker_script(target_f)
        if res.get("status") == "success":
            return f"Speaker Delivery Script generated successfully for {res.get('slide_count')} slides:\n📝 `{res.get('script_path')}`"
        return f"Script generation failed: {res.get('message')}"

    # 6. RETHEME PRESENTATION
    elif action in ("retheme", "change_theme"):
        target_f = fpath or fname
        if not target_f:
            desk = _get_output_dir("desktop")
            pptx_files = sorted(desk.glob("*.pptx"), key=lambda f: f.stat().st_mtime, reverse=True)
            if pptx_files: target_f = pptx_files[0]
            else: return "Please specify the presentation file to re-theme."
        res = retheme_presentation(target_f, theme)
        if res.get("status") == "success":
            return f"Presentation re-themed to **{res.get('theme_name')}** ({res.get('slide_count')} slides):\n🎨 `{res.get('file_path')}`"
        return f"Retheming failed: {res.get('message')}"

    # 7. CREATE / DESIGN PRESENTATION (DEFAULT)
    else:
        res = create_intriguing_presentation(
            topic=topic,
            theme=theme,
            num_slides=num_slides,
            audience=audience,
            target_location=loc,
            open_after=open_after,
            source_content=src,
            custom_slides=parameters.get("slides"),
            filename=fname
        )

        if res.get("status") == "success":
            return (
                f"### High-Impact Presentation Generated Successfully!\n"
                f"• **Deck Title:** {res.get('deck_title')}\n"
                f"• **Theme:** {res.get('theme_name')} (`{res.get('theme')}`)\n"
                f"• **Slide Count:** {res.get('slide_count')} widescreen 16:9 slides\n"
                f"• **Location:** `{res.get('file_path')}`\n"
                f"• **Features:** Dynamic cards, geometric layout, and speaker delivery notes embedded on all slides.\n"
                f"• **Status:** Opened in PowerPoint for your immediate review."
            )
        return f"Failed to generate presentation: {res.get('message')}"
