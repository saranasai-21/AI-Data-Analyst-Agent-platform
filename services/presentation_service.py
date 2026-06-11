"""
PresentationService -- executive-quality PowerPoint report generator.

Visual design:
  - Dark title stripe with small icon badge
  - Native PowerPoint bullets (fragments, not sentences)
  - Colored metric cards for Key Findings
  - Automatic overflow pagination
  - Junk-slide removal
"""

import os
import re

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from lxml import etree


# ═══════════════════════════════════════════════════════════════════════════
# Design tokens
# ═══════════════════════════════════════════════════════════════════════════

_BG               = RGBColor(248, 251, 255)
_TITLE_BAR        = RGBColor(18, 48, 74)
_TITLE_TEXT       = RGBColor(255, 255, 255)
_SUBTITLE_COLOR   = RGBColor(66, 97, 117)
_BULLET_COLOR     = RGBColor(31, 41, 55)
_ACCENT_FILL      = RGBColor(232, 247, 255)
_ACCENT_BORDER    = RGBColor(169, 215, 239)
_HIGHLIGHT        = RGBColor(22, 119, 201)

_FONT             = "Arial"
_TITLE_PT         = Pt(26)
_BULLET_PT        = Pt(18)
_CAPTION_PT       = Pt(13)
_SPACE_AFTER      = 8        # points between bullets
_MAX_BULLETS      = 6        # overflow threshold

# Card colours (rotate through these for visual variety)
_CARD_COLORS = [
    (RGBColor(232, 247, 255), RGBColor(22, 119, 201)),   # light-blue bg, blue text
    (RGBColor(230, 255, 237), RGBColor(21, 128, 61)),     # light-green bg, green text
    (RGBColor(254, 243, 199), RGBColor(180, 83, 9)),      # light-amber bg, amber text
    (RGBColor(237, 233, 254), RGBColor(109, 40, 217)),    # light-purple bg, purple text
    (RGBColor(255, 228, 230), RGBColor(190, 18, 60)),     # light-rose bg, rose text
    (RGBColor(224, 242, 254), RGBColor(3, 105, 161)),     # light-sky bg, sky text
]

# Section → icon path
_ICON_MAP = {
    "Executive Summary":         "assets/icon_summary.png",
    "Key Findings":              "assets/icon_findings.png",
    "Trends":                    "assets/icon_trends.png",
    "Opportunities":             "assets/icon_opportunities.png",
    "Risks":                     "assets/icon_risks.png",
    "Strategic Recommendations": "assets/icon_strategy.png",
    "Conclusion":                "assets/icon_conclusion.png",
}

# Junk markers for cleanup
_JUNK = [
    "no ai insights generated", "no ai recommendations generated",
    "no ai analysis generated", "generation failed",
    "temporarily unavailable", "traceback", "exception",
    "syntaxerror", "nameerror", "unterminated string", "is not defined",
]


# ═══════════════════════════════════════════════════════════════════════════
# Service
# ═══════════════════════════════════════════════════════════════════════════


class PresentationService:
    """Builds executive-quality PPTX reports from structured JSON."""

    def __init__(self):
        os.makedirs("outputs", exist_ok=True)
        os.makedirs("outputs/charts", exist_ok=True)

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    def create_report(
        self,
        file_name: str,
        profile: dict,
        quality_report: dict,
        analysis_result,
        insights,
        recommendations,
        chart_items=None,
        query: str | None = None,
        dataset_summary: str | None = None,
        output_path: str = "outputs/AI_Report.pptx",
    ) -> str:
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        self._base_name = (
            os.path.splitext(file_name)[0]
            .replace("_", " ").replace("-", " ").title()
        )

        # -- Generate structured JSON via ReportAgent --
        from agents.report_agent import ReportAgent
        from core.config import GEMINI_API_KEY

        sections = ReportAgent(GEMINI_API_KEY).generate_full_report_sections(
            query=query or "",
            dataset_summary=dataset_summary or "",
            analysis_result=str(analysis_result) if analysis_result else "",
        )

        # -- Assemble deck --
        self._title_slide(prs, file_name)

        for name in [
            "Executive Summary", "Key Findings", "Trends",
            "Opportunities", "Risks", "Strategic Recommendations",
        ]:
            self._section_slides(prs, name, sections.get(name, {}))

        if chart_items:
            self._chart_slides(prs, chart_items[:3])

        self._section_slides(prs, "Conclusion", sections.get("Conclusion", {}))

        self._remove_junk(prs)
        prs.save(output_path)
        return output_path

    # ──────────────────────────────────────────────────────────────────
    # Section → slides
    # ──────────────────────────────────────────────────────────────────

    def _section_slides(self, prs, section_name: str, data: dict):
        if not data or "slides" not in data:
            return

        for slide_obj in data["slides"]:
            title = _clean(slide_obj.get("title", section_name))

            # Card-based slide (Key Findings)
            cards = slide_obj.get("cards")
            if cards:
                slide = self._make_slide(prs, title, section_name)
                self._render_cards(slide, cards)
                continue

            # Bullet-based slide
            bullets = _clean_bullets(slide_obj.get("bullets", []))
            if not bullets:
                continue

            chunks = [bullets[i:i + _MAX_BULLETS] for i in range(0, len(bullets), _MAX_BULLETS)]
            for page, chunk in enumerate(chunks):
                t = title if page == 0 else f"{title} (Continued)"
                slide = self._make_slide(prs, t, section_name)
                self._render_bullets(slide, chunk)

    # ──────────────────────────────────────────────────────────────────
    # Slide factory
    # ──────────────────────────────────────────────────────────────────

    def _make_slide(self, prs, title: str, section_name: str = ""):
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # Background
        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = _BG

        # Title bar
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0), Inches(0), Inches(13.333), Inches(1.0),
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = _TITLE_BAR
        bar.line.fill.background()

        # Icon badge in title bar
        icon_path = _ICON_MAP.get(section_name)
        icon_left = Inches(0.45)
        text_left = Inches(0.65)

        if icon_path and os.path.exists(icon_path):
            try:
                slide.shapes.add_picture(
                    icon_path,
                    Inches(0.35), Inches(0.12),
                    width=Inches(0.75),
                )
                text_left = Inches(1.25)
            except Exception:
                pass

        # Title text
        tbox = slide.shapes.add_textbox(text_left, Inches(0.15), Inches(11.5), Inches(0.7))
        tf = tbox.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = _TITLE_PT
        p.font.bold = True
        p.font.color.rgb = _TITLE_TEXT
        p.font.name = _FONT

        return slide

    # ──────────────────────────────────────────────────────────────────
    # Bullet renderer
    # ──────────────────────────────────────────────────────────────────

    def _render_bullets(self, slide, bullets: list[str]):
        box = slide.shapes.add_textbox(
            Inches(1.0), Inches(1.4), Inches(11.3), Inches(5.5),
        )
        tf = box.text_frame
        tf.clear()
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        tf.margin_left = Inches(0.15)
        tf.margin_right = Inches(0.15)
        tf.margin_top = Inches(0.1)
        tf.margin_bottom = Inches(0.1)

        for idx, text in enumerate(bullets):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.text = text
            p.level = 0
            p.alignment = PP_ALIGN.LEFT
            p.font.name = _FONT
            p.font.size = _BULLET_PT
            p.font.color.rgb = _BULLET_COLOR
            _set_indent(p._p, Inches(0.4), -Inches(0.25))
            _set_spacing(p._p, _SPACE_AFTER)

    # ──────────────────────────────────────────────────────────────────
    # Metric card renderer
    # ──────────────────────────────────────────────────────────────────

    def _render_cards(self, slide, cards: list[dict]):
        """Render colored metric cards in a responsive grid."""
        n = len(cards)
        cols = 3 if n > 4 else 2
        rows = (n + cols - 1) // cols

        card_w = Inches(3.4)
        card_h = Inches(1.6)
        gap_x = Inches(0.4)
        gap_y = Inches(0.35)

        grid_w = cols * card_w + (cols - 1) * gap_x
        start_x = (Inches(13.333) - grid_w) / 2
        start_y = Inches(1.5)

        for i, card in enumerate(cards):
            row = i // cols
            col = i % cols

            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)

            bg_color, text_color = _CARD_COLORS[i % len(_CARD_COLORS)]

            # Card shape
            rect = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, int(x), int(y), int(card_w), int(card_h),
            )
            rect.fill.solid()
            rect.fill.fore_color.rgb = bg_color
            rect.line.color.rgb = text_color
            rect.line.width = Pt(1.5)

            # Label
            label_box = slide.shapes.add_textbox(
                int(x + Inches(0.2)),
                int(y + Inches(0.2)),
                int(card_w - Inches(0.4)),
                int(Inches(0.55)),
            )
            tf = label_box.text_frame
            tf.clear()
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = card.get("label", "")
            p.font.size = Pt(14)
            p.font.bold = True
            p.font.color.rgb = _SUBTITLE_COLOR
            p.font.name = _FONT
            p.alignment = PP_ALIGN.LEFT

            # Value
            val_box = slide.shapes.add_textbox(
                int(x + Inches(0.2)),
                int(y + Inches(0.7)),
                int(card_w - Inches(0.4)),
                int(Inches(0.7)),
            )
            tf = val_box.text_frame
            tf.clear()
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = card.get("value", "")
            p.font.size = Pt(28)
            p.font.bold = True
            p.font.color.rgb = text_color
            p.font.name = _FONT
            p.alignment = PP_ALIGN.LEFT

    # ──────────────────────────────────────────────────────────────────
    # Title slide
    # ──────────────────────────────────────────────────────────────────

    def _title_slide(self, prs, file_name: str):
        slide = self._make_slide(prs, "AI Data Analyst Report")

        sub = slide.shapes.add_textbox(
            Inches(0.9), Inches(1.55), Inches(11.4), Inches(0.7),
        )
        tf = sub.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = f"Dataset: {file_name}"
        p.font.size = Pt(22)
        p.font.color.rgb = _SUBTITLE_COLOR
        p.font.name = _FONT

        accent = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0.9), Inches(2.7), Inches(11.3), Inches(2.7),
        )
        accent.fill.solid()
        accent.fill.fore_color.rgb = _ACCENT_FILL
        accent.line.color.rgb = _ACCENT_BORDER

        lbl = slide.shapes.add_textbox(
            Inches(1.25), Inches(3.25), Inches(10.6), Inches(1.3),
        )
        tf = lbl.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = (
            "Automated profiling, insights, recommendations, "
            "and selected visual evidence"
        )
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.color.rgb = _HIGHLIGHT
        p.font.name = _FONT
        p.alignment = PP_ALIGN.CENTER

    # ──────────────────────────────────────────────────────────────────
    # Chart slides
    # ──────────────────────────────────────────────────────────────────

    def _chart_slides(self, prs, items: list):
        for i, item in enumerate(items, 1):
            path, title, caption = _unpack_chart(item, i)
            if not path or not os.path.exists(path):
                continue

            slide = self._make_slide(prs, title, "")
            try:
                slide.shapes.add_picture(
                    path, Inches(2.16), Inches(1.25), width=Inches(9.0),
                )
            except Exception:
                continue

            cap = slide.shapes.add_textbox(
                Inches(1.0), Inches(6.45), Inches(11.3), Inches(0.55),
            )
            tf = cap.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            p.text = _clean(caption) if caption else title
            p.font.size = _CAPTION_PT
            p.font.color.rgb = _SUBTITLE_COLOR
            p.font.name = _FONT
            p.alignment = PP_ALIGN.CENTER

    # ──────────────────────────────────────────────────────────────────
    # Junk removal
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _remove_junk(prs):
        to_delete: list[int] = []
        for idx, slide in enumerate(prs.slides):
            texts = " ".join(
                s.text.strip() for s in slide.shapes if hasattr(s, "text")
            ).lower()

            meaningful = sum(
                1 for s in slide.shapes
                if hasattr(s, "text") and len(s.text.strip()) > 5
            )
            if meaningful == 0:
                to_delete.append(idx)
                continue
            if any(m in texts for m in _JUNK):
                to_delete.append(idx)

        for idx in reversed(to_delete):
            sid = prs.slides._sldIdLst[idx]
            prs.part.drop_rel(sid.rId)
            del prs.slides._sldIdLst[idx]


# ═══════════════════════════════════════════════════════════════════════════
# Module-level helpers (no state, easily testable)
# ═══════════════════════════════════════════════════════════════════════════


def _clean(text: str) -> str:
    t = re.sub(r"\*\*(.*?)\*\*", r"\1", str(text))
    t = re.sub(r"^#+\s*", "", t)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    return t.strip(":- ") or ""


def _clean_bullets(raw: list) -> list[str]:
    out: list[str] = []
    for b in raw:
        t = _clean(str(b))
        t = re.sub(r"^[\-\*\u2022]\s*", "", t)
        t = re.sub(r"^\d+[.)]\s*", "", t)
        if not t:
            continue
        if any(m in t.lower() for m in _JUNK):
            continue
        out.append(t)
    return out


def _unpack_chart(item, idx: int):
    try:
        p, t, c = item
    except (ValueError, TypeError):
        try:
            p, c = item
            t = f"Visualization {idx}"
        except (ValueError, TypeError):
            p, t, c = item, f"Visualization {idx}", ""
    return p, t, c


def _set_indent(p_elem, left_emu, indent_emu=0):
    pPr = p_elem.find(qn("a:pPr"))
    if pPr is None:
        pPr = etree.SubElement(p_elem, qn("a:pPr"))
        p_elem.insert(0, pPr)
    pPr.set("marL", str(int(left_emu)))
    pPr.set("indent", str(int(indent_emu)))


def _set_spacing(p_elem, after_pt: float):
    pPr = p_elem.find(qn("a:pPr"))
    if pPr is None:
        pPr = etree.SubElement(p_elem, qn("a:pPr"))
        p_elem.insert(0, pPr)
    spcAft = pPr.find(qn("a:spcAft"))
    if spcAft is None:
        spcAft = etree.SubElement(pPr, qn("a:spcAft"))
    spcPts = spcAft.find(qn("a:spcPts"))
    if spcPts is None:
        spcPts = etree.SubElement(spcAft, qn("a:spcPts"))
    spcPts.set("val", str(int(after_pt * 100)))
