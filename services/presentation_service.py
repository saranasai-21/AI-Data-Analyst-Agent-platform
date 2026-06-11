import os
import re

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt, Emu
from lxml import etree


class PresentationService:

    def __init__(self):
        os.makedirs("outputs", exist_ok=True)
        os.makedirs("outputs/charts", exist_ok=True)

    def create_report(
        self,
        file_name,
        profile,
        quality_report,
        analysis_result,
        insights,
        recommendations,
        chart_items=None,
        output_path="outputs/AI_Report.pptx"
    ):
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        base_name = os.path.splitext(file_name)[0].replace("_", " ").replace("-", " ").title()
        insights_title = f"{base_name} Insights" if base_name else "Business Insights"
        recs_title = f"{base_name} Recommendations" if base_name else "Recommendations"

        self._add_title_slide(prs, file_name)
        self._add_dataset_overview(prs, profile)
        self._add_data_quality_slide(prs, quality_report)
        self._add_analysis_slide(prs, analysis_result)
        self._add_visualization_slides(prs, chart_items)
        self._add_text_slides(prs, insights_title, insights)
        self._add_text_slides(prs, recs_title, recommendations)
        self._add_conclusion_slide(prs)

        prs.save(output_path)
        return output_path

    def _blank_slide(self, prs, title):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        background = slide.background.fill
        background.solid()
        background.fore_color.rgb = RGBColor(248, 251, 255)

        title_box = slide.shapes.add_textbox(
            Inches(0.65),
            Inches(0.35),
            Inches(12),
            Inches(0.65),
        )
        frame = title_box.text_frame
        frame.clear()
        p = frame.paragraphs[0]
        p.text = str(title)
        p.font.size = Pt(28 if len(str(title)) <= 42 else 23)
        p.font.bold = True
        p.font.color.rgb = RGBColor(18, 48, 74)
        return slide

    def _clean_text(self, value):
        if value is None:
            text = ""
        elif isinstance(value, pd.DataFrame):
            text = value.head(20).to_string(index=True)
        elif isinstance(value, pd.Series):
            text = value.head(30).to_string()
        else:
            text = str(value)

        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"`([^`]*)`", r"\1", text)
        text = text.replace("Ã¢â‚¬Â¢", "-")
        text = text.replace("\u00e2\u0080\u0093", "-")
        text = text.replace("\u00e2\u0080\u0094", "-")
        text = text.replace("\u2022", "-")
        text = re.sub(
            r"(Insight|Recommendation|Finding)\s+generation failed:\s+503.*",
            (
                r"\1 generation is temporarily unavailable because the AI model "
                "endpoint is under high demand. Please retry this section."
            ),
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        lines = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            line = re.sub(r"^[\-\*\u2022]\s*", "- ", line)
            line = re.sub(r"^\d+[\.\)]\s*", "- ", line)
            lines.append(line)

        return lines

    def _title_from_caption(self, caption, fallback):
        cleaned = self._clean_text(caption)
        if not cleaned:
            return fallback

        title = cleaned[0].split(":", 1)[0].strip()
        return title[:74] or fallback

    def _wrapped_lines(self, lines, width=88):
        # Do not physically wrap — let PPTX word_wrap handle layout.
        return lines

    def _set_para_indent(self, para_elem, left_emu, first_line_emu=0):
        """Set left_indent and first_line_indent on a CT_P (lxml element)."""
        pPr = para_elem.find(qn("a:pPr"))
        if pPr is None:
            pPr = etree.SubElement(para_elem, qn("a:pPr"))
            para_elem.insert(0, pPr)
        pPr.set("marL", str(int(left_emu)))
        pPr.set("indent", str(int(first_line_emu)))

    def _set_para_space_after(self, para_elem, pt_value):
        """Set spaceAft on a CT_P element in hundredths of a point."""
        pPr = para_elem.find(qn("a:pPr"))
        if pPr is None:
            pPr = etree.SubElement(para_elem, qn("a:pPr"))
            para_elem.insert(0, pPr)
        spcAft = pPr.find(qn("a:spcAft"))
        if spcAft is None:
            spcAft = etree.SubElement(pPr, qn("a:spcAft"))
        spcPts = spcAft.find(qn("a:spcPts"))
        if spcPts is None:
            spcPts = etree.SubElement(spcAft, qn("a:spcPts"))
        # hundredths of a point
        spcPts.set("val", str(int(pt_value * 100)))

    def _add_body_lines(self, slide, lines, top=1.22, font_size=17, max_lines=14):
        box = slide.shapes.add_textbox(
            Inches(0.85),
            Inches(top),
            Inches(11.7),
            Inches(5.35),
        )
        frame = box.text_frame
        frame.clear()
        frame.word_wrap = True
        frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        frame.margin_left = Inches(0.08)
        frame.margin_right = Inches(0.08)
        frame.margin_top = Inches(0.05)
        frame.margin_bottom = Inches(0.05)

        for i, line in enumerate(lines[:max_lines]):
            # First paragraph already exists; add new ones for subsequent lines
            p_obj = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
            # p_obj is a pptx _Paragraph — get the underlying lxml element
            p_elem = p_obj._p

            is_bullet = line.startswith("- ")
            if is_bullet:
                p_obj.text = line[2:]
                self._set_para_indent(
                    p_elem,
                    left_emu=Inches(0.35),
                    first_line_emu=-Inches(0.20),
                )
            else:
                p_obj.text = line
                self._set_para_indent(
                    p_elem,
                    left_emu=Inches(0.15),
                    first_line_emu=0,
                )

            p_obj.font.size = Pt(font_size)
            p_obj.font.color.rgb = RGBColor(31, 41, 55)
            self._set_para_space_after(p_elem, pt_value=10)

            if not is_bullet and not line.startswith("  ") and len(line) < 58:
                p_obj.font.bold = True
                p_obj.font.color.rgb = RGBColor(22, 83, 126)

    def _add_title_slide(self, prs, file_name):
        slide = self._blank_slide(prs, "AI Data Analyst Report")
        subtitle = slide.shapes.add_textbox(
            Inches(0.9),
            Inches(1.55),
            Inches(11.4),
            Inches(0.7),
        )
        frame = subtitle.text_frame
        frame.clear()
        p = frame.paragraphs[0]
        p.text = f"Dataset: {file_name}"
        p.font.size = Pt(22)
        p.font.color.rgb = RGBColor(66, 97, 117)

        accent = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0.9),
            Inches(2.7),
            Inches(11.3),
            Inches(2.7),
        )
        accent.fill.solid()
        accent.fill.fore_color.rgb = RGBColor(232, 247, 255)
        accent.line.color.rgb = RGBColor(169, 215, 239)

        label = slide.shapes.add_textbox(
            Inches(1.25),
            Inches(3.25),
            Inches(10.6),
            Inches(1.3),
        )
        frame = label.text_frame
        frame.clear()
        p = frame.paragraphs[0]
        p.text = "Automated profile, insights, recommendations, and selected visual evidence"
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.color.rgb = RGBColor(22, 119, 201)
        p.alignment = PP_ALIGN.CENTER

    def _add_dataset_overview(self, prs, profile):
        slide = self._blank_slide(prs, "Dataset Overview")
        rows = profile.get("rows", 0)
        columns = profile.get("columns", 0)
        duplicates = profile.get("duplicates", 0)
        column_names = profile.get("column_names", [])
        lines = [
            f"Rows: {rows}",
            f"Columns: {columns}",
            f"Duplicate rows: {duplicates}",
            f"Important columns preview: {', '.join(column_names[:12])}",
        ]
        self._add_body_lines(slide, self._wrapped_lines(lines), font_size=17, max_lines=12)

    def _add_data_quality_slide(self, prs, quality_report):
        slide = self._blank_slide(prs, "Data Quality Assessment")
        duplicates = quality_report.get("duplicates", 0)
        constant_columns = len(quality_report.get("constant_columns", []))
        high_cardinality = len(quality_report.get("high_cardinality", {}))
        missing_values = sum(quality_report.get("missing_values", {}).values())
        lines = [
            f"Duplicate rows: {duplicates}",
            f"Missing values: {missing_values}",
            f"Constant columns: {constant_columns}",
            f"High-cardinality columns: {high_cardinality}",
        ]
        self._add_body_lines(slide, self._wrapped_lines(lines), font_size=17, max_lines=12)

    def _add_analysis_slide(self, prs, analysis_result):
        if isinstance(analysis_result, dict):
            result_text = analysis_result.get("result", "")
        else:
            result_text = analysis_result

        self._add_text_slides(prs, "Analysis Results", result_text)

    def _add_visualization_slides(self, prs, chart_items=None):
        if not chart_items:
            return

        for i, item in enumerate(chart_items[:6], start=1):
            try:
                path, title, caption = item
            except Exception:
                try:
                    path, caption = item
                    title = self._title_from_caption(caption, f"Visualization {i}")
                except Exception:
                    path = item
                    title = f"Visualization {i}"
                    caption = ""

            if not path or not os.path.exists(path):
                continue

            slide = self._blank_slide(prs, title)
            try:
                slide.shapes.add_picture(
                    path,
                    Inches(1.0),
                    Inches(1.15),
                    width=Inches(11.3),
                )
            except Exception:
                continue

            cap = slide.shapes.add_textbox(
                Inches(1.0),
                Inches(6.25),
                Inches(11.3),
                Inches(0.55),
            )
            frame = cap.text_frame
            frame.clear()
            p = frame.paragraphs[0]
            p.text = self._clean_text(caption)[0] if self._clean_text(caption) else str(title)
            p.font.size = Pt(13)
            p.font.color.rgb = RGBColor(66, 97, 117)
            p.alignment = PP_ALIGN.CENTER

    def _add_text_slides(self, prs, title, text):
        lines = self._clean_text(text)
        if not lines:
            lines = ["No details were generated for this section."]

        slide = self._blank_slide(prs, title)
        self._add_body_lines(slide, lines, font_size=17, max_lines=50)

    def _add_conclusion_slide(self, prs):
        slide = self._blank_slide(prs, "Conclusion")
        lines = [
            "This report was automatically generated by the AI Data Analyst Agent.",
            (
                "The workflow included data quality assessment, dataset profiling, "
                "AI-powered analysis, visualization, business insights, and strategic "
                "recommendations."
            ),
        ]
        self._add_body_lines(
            slide,
            self._wrapped_lines(lines),
            top=1.7,
            font_size=18,
            max_lines=7,
        )
