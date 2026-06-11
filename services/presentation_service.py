import os
import re

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE, PP_PARAGRAPH_ALIGNMENT
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
        query=None,
        dataset_summary=None,
        output_path="outputs/AI_Report.pptx"
    ):
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        base_name = os.path.splitext(file_name)[0].replace("_", " ").replace("-", " ").title()
        self._current_base_name = base_name

        from agents.report_agent import ReportAgent
        from core.config import GEMINI_API_KEY
        
        report_agent = ReportAgent(GEMINI_API_KEY)
        report_sections = report_agent.generate_full_report_sections(
            query=query or "", 
            dataset_summary=dataset_summary or "", 
            analysis_result=analysis_result or ""
        )

        self._add_title_slide(prs, file_name)

        # Executive Summary
        self._add_json_section_slides(prs, "Executive Summary", report_sections.get("Executive Summary", {}))
        
        # Key Findings
        self._add_json_section_slides(prs, "Key Findings", report_sections.get("Key Findings", {}))
        
        # Trends
        self._add_json_section_slides(prs, "Trends", report_sections.get("Trends", {}))
        
        # Opportunities
        self._add_json_section_slides(prs, "Opportunities", report_sections.get("Opportunities", {}))
        
        # Risks
        self._add_json_section_slides(prs, "Risks", report_sections.get("Risks", {}))
        
        # Recommendations
        self._add_json_section_slides(prs, "Recommendations", report_sections.get("Recommendations", {}))

        # Visual Evidence (Charts)
        if chart_items:
            # Add up to 3 charts max as requested "select only top 2-3 charts"
            self._add_visualization_slides(prs, chart_items[:3])

        # Conclusion
        self._add_json_section_slides(prs, "Conclusion", report_sections.get("Conclusion", {}))

        self._remove_empty_slides(prs)
        prs.save(output_path)
        return output_path

    def _add_json_section_slides(self, prs, section_name, section_data):
        if not section_data or "slides" not in section_data:
            return
            
        IMAGE_MAP = {
            "Executive Summary": "assets/executive.png",
            "Key Findings": "assets/findings.png",
            "Trends": "assets/trends.png",
            "Opportunities": "assets/opportunities.png",
            "Risks": "assets/risks.png",
            "Recommendations": "assets/strategy.png",
            "Conclusion": "assets/conclusion.png"
        }
            
        for slide_data in section_data["slides"]:
            title = slide_data.get("title", "")
            bullets = slide_data.get("bullets", [])
            
            # Ensure bullets have the proper prefix for _add_textbox_column
            formatted_bullets = []
            for b in bullets:
                if not b.startswith("- "):
                    formatted_bullets.append(f"- {b}")
                else:
                    formatted_bullets.append(b)
            
            slide = self._blank_slide(prs, title)
            
            image_path = IMAGE_MAP.get(section_name)
            
            if image_path and os.path.exists(image_path):
                # Layout Option 1: Image on left, text on right
                try:
                    slide.shapes.add_picture(
                        image_path,
                        Inches(0.5),
                        Inches(1.5),
                        width=Inches(3.8)
                    )
                    
                    self._add_textbox_column(
                        slide,
                        formatted_bullets,
                        left=Inches(4.6),
                        top=Inches(1.2),
                        width=Inches(8.0),
                        height=Inches(5.5),
                        computed_font_size=20,
                        space_after=0.25
                    )
                except Exception:
                    # Fallback if image corrupt
                    self._add_textbox_column(
                        slide,
                        formatted_bullets,
                        left=Inches(0.65),
                        top=Inches(1.2),
                        width=Inches(12.0),
                        height=Inches(5.5),
                        computed_font_size=20,
                        space_after=0.25
                    )
            else:
                self._add_textbox_column(
                    slide,
                    formatted_bullets,
                    left=Inches(0.65),
                    top=Inches(1.2),
                    width=Inches(12.0),
                    height=Inches(5.5),
                    computed_font_size=20,
                    space_after=0.25
                )

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
        # Clean title of any markdown artifacts
        clean_title = str(title)
        clean_title = re.sub(r"\*\*(.*?)\*\*", r"\1", clean_title)
        clean_title = re.sub(r"^#+\s*", "", clean_title).strip(":- ")
        p.text = clean_title
        p.font.size = Pt(28 if len(clean_title) <= 42 else 23)
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

    def _is_valid_content(self, text):
        if text is None:
            return False
            
        # Handle pandas DataFrame / Series safely to avoid truthiness errors
        if isinstance(text, (pd.DataFrame, pd.Series)):
            return not text.empty
            
        if isinstance(text, dict):
            text = text.get("result", "")
            
        # Re-check in case the dictionary returned a DataFrame or Series
        if isinstance(text, (pd.DataFrame, pd.Series)):
            return not text.empty
            
        if text is None:
            return False

        # If it's not a string, check if it's truthy, otherwise convert to string
        if not isinstance(text, str):
            try:
                # Try simple comparison, if it fails, default to True (meaning it exists)
                if not text:
                    return False
            except Exception:
                pass
            try:
                text = str(text)
            except Exception:
                return True
            
        lower_text = text.strip().lower()
        placeholders = [
            "no ai insights generated yet",
            "no ai recommendations generated yet",
            "no ai analysis generated yet",
            "no details were generated for this section",
            "generation failed",
            "temporarily unavailable",
            "name 'len' is not defined",
            "is not defined",
            "error during analysis",
            "none",
            "null",
            "traceback",
            "exception",
            "error",
            "unterminated string literal",
            "syntaxerror",
            "nameerror",
        ]
        for placeholder in placeholders:
            if placeholder in lower_text:
                return False
                
        cleaned = self._clean_text(text)
        if not cleaned:
            return False
            
        return True

    def _determine_slide_title(self, text, default_title):
        if text is None:
            return default_title
            
        # Handle pandas DataFrame / Series safely to avoid truthiness errors
        if isinstance(text, (pd.DataFrame, pd.Series)):
            return default_title
            
        if isinstance(text, dict):
            text = text.get("result", "")
            
        # Re-check in case the dictionary returned a DataFrame or Series
        if isinstance(text, (pd.DataFrame, pd.Series)):
            return default_title
            
        if text is None:
            return default_title
            
        if not isinstance(text, str):
            return default_title
            
        # Try to find a markdown header (# Header, ## Header, ### Header)
        match = re.search(r'^\s*#+\s*(.+)$', text, re.MULTILINE)
        if match:
            candidate = match.group(1).strip()
            candidate = re.sub(r"\*\*(.*?)\*\*", r"\1", candidate)
            candidate = re.sub(r"\*(.*?)\*", r"\1", candidate)
            candidate = re.sub(r"`([^`]*)`", r"\1", candidate)
            candidate = candidate.strip(":- ")
            if candidate and len(candidate) < 60:
                return candidate
                
        # If no markdown header, look at the first line of cleaned text
        cleaned_lines = self._clean_text(text)
        if cleaned_lines:
            first_line = cleaned_lines[0]
            if not first_line.startswith("-") and len(first_line) < 60:
                candidate = first_line.split(":", 1)[0].strip()
                if candidate and len(candidate) > 3 and len(candidate) < 50:
                    return candidate
                    
        return default_title

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

    def _add_textbox_column(self, slide, lines, left, top, width, height, computed_font_size, space_after):
        box = slide.shapes.add_textbox(left, top, width, height)
        frame = box.text_frame
        frame.clear()
        frame.word_wrap = True
        frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        frame.margin_left = Inches(0.08)
        frame.margin_right = Inches(0.08)
        frame.margin_top = Inches(0.05)
        frame.margin_bottom = Inches(0.05)

        for i, line in enumerate(lines):
            p_obj = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
            p_elem = p_obj._p

            # Clean any remaining markdown bold markers or headers
            clean_line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            clean_line = re.sub(r"^#+\s*", "", clean_line)

            is_bullet = clean_line.startswith("- ")
            if is_bullet:
                p_obj.text = clean_line[2:]
                p_obj.level = 0
                self._set_para_indent(
                    p_elem,
                    left_emu=Inches(0.35),
                    first_line_emu=-Inches(0.20),
                )
            else:
                p_obj.text = clean_line
                self._set_para_indent(
                    p_elem,
                    left_emu=Inches(0.15),
                    first_line_emu=0,
                )

            p_obj.font.name = "Arial"
            p_obj.font.size = Pt(computed_font_size)
            p_obj.font.color.rgb = RGBColor(31, 41, 55)
            if is_bullet:
                p_obj.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            else:
                p_obj.alignment = PP_PARAGRAPH_ALIGNMENT.JUSTIFY
                
            self._set_para_space_after(p_elem, pt_value=space_after)

            if not is_bullet and not clean_line.startswith("  ") and len(clean_line) < 58:
                p_obj.font.bold = True
                p_obj.font.color.rgb = RGBColor(22, 83, 126)

    def _add_body_lines(self, slide, lines, top=1.22, font_size=17, max_lines=14):
        # Truncate lines to prevent overflow
        lines = lines[:40]

        if len(lines) <= 8:
            # Single column layout for shorter text
            computed_font_size = 16
            space_after = 10
            self._add_textbox_column(
                slide,
                lines,
                left=Inches(0.85),
                top=Inches(top),
                width=Inches(11.7),
                height=Inches(5.35),
                computed_font_size=computed_font_size,
                space_after=space_after
            )
        else:
            # Group lines by heading to keep headings and their bullets in the same column
            groups = []
            current_group = []
            for line in lines:
                is_bullet = line.startswith("- ")
                is_heading = not is_bullet and not line.startswith("  ") and len(line) < 58
                
                if is_heading:
                    if current_group:
                        groups.append(current_group)
                    current_group = [line]
                else:
                    if current_group and not current_group[0].startswith("- "):
                        current_group.append(line)
                    else:
                        if current_group:
                            groups.append(current_group)
                        current_group = [line]
            if current_group:
                groups.append(current_group)

            # Balanced distribution between two columns
            col1 = []
            col2 = []
            for group in groups:
                if len(col1) <= len(col2):
                    col1.extend(group)
                else:
                    col2.extend(group)

            max_col_lines = max(len(col1), len(col2))
            if max_col_lines <= 8:
                computed_font_size = 15
                space_after = 8
            elif max_col_lines <= 12:
                computed_font_size = 13
                space_after = 6
            elif max_col_lines <= 18:
                computed_font_size = 11
                space_after = 4
            else:
                computed_font_size = 9.5
                space_after = 2

            self._add_textbox_column(
                slide,
                col1,
                left=Inches(0.85),
                top=Inches(top),
                width=Inches(5.6),
                height=Inches(5.35),
                computed_font_size=computed_font_size,
                space_after=space_after
            )
            if col2:
                self._add_textbox_column(
                    slide,
                    col2,
                    left=Inches(6.85),
                    top=Inches(top),
                    width=Inches(5.6),
                    height=Inches(5.35),
                    computed_font_size=computed_font_size,
                    space_after=space_after
                )

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

        if not self._is_valid_content(result_text):
            return

        base_name = getattr(self, "_current_base_name", "")
        analysis_default = f"{base_name} Analysis" if base_name else "Analysis Results"
        analysis_title = self._determine_slide_title(result_text, analysis_default)

        self._add_text_slides(prs, analysis_title, result_text)

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
                    Inches(2.16),
                    Inches(1.25),
                    width=Inches(9.0),
                )
            except Exception:
                continue

            cap = slide.shapes.add_textbox(
                Inches(1.0),
                Inches(6.45),
                Inches(11.3),
                Inches(0.55),
            )
            frame = cap.text_frame
            frame.clear()
            p = frame.paragraphs[0]
            display_caption = self._clean_text(caption)[0] if self._clean_text(caption) else str(title)
            display_caption = re.sub(r"\*\*(.*?)\*\*", r"\1", display_caption)
            display_caption = re.sub(r"^#+\s*", "", display_caption)
            p.text = display_caption
            p.font.size = Pt(13)
            p.font.color.rgb = RGBColor(66, 97, 117)
            p.alignment = PP_ALIGN.CENTER

    def _add_text_slides(self, prs, title, text):
        if not self._is_valid_content(text):
            return

        lines = self._clean_text(text)
        if not lines:
            return

        sections = []
        current_title = title
        current_lines = []

        heading_patterns = [
            r'^#{1,4}\s+(.+)$',
            r'^\*\*(.+?)\*\*$',
            r'^\*\*(.+?):\*\*$'
        ]

        def extract_heading(line):
            for pattern in heading_patterns:
                match = re.match(pattern, line)
                if match:
                    heading = match.group(1).strip()
                    if len(heading) < 80:
                        return heading
            return None

        for line in lines:
            heading = extract_heading(line)
            if heading:
                if current_lines:
                    sections.append((current_title, current_lines))
                current_title = heading
                current_lines = []
            else:
                # avoid duplicating the section title in the very first line of a section
                clean_line = re.sub(r'^#+\s*', '', line).strip(":- ")
                clean_line = re.sub(r"\*\*(.*?)\*\*", r"\1", clean_line)
                if not current_lines and (
                    clean_line.lower() == current_title.lower() or
                    current_title.lower() in clean_line.lower() or
                    clean_line.lower() in current_title.lower()
                ):
                    continue
                current_lines.append(line)

        if current_lines:
            sections.append((current_title, current_lines))

        for section_title, section_lines in sections:
            if not section_lines:
                continue

            chunks = self._split_section_into_chunks(section_lines, max_chars=1200)

            for idx, chunk in enumerate(chunks):
                slide_title = (
                    section_title
                    if idx == 0
                    else f"{section_title} (Continued)"
                )
                slide = self._blank_slide(prs, slide_title)
                self._add_body_lines(slide, chunk, top=1.22)

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

    def _split_section_into_chunks(self, lines, max_chars=1200):
        """
        Split a section into multiple slides only if it becomes too large.
        Keeps headings together.
        """
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line)

            if current_size + line_size > max_chars and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _remove_empty_slides(self, prs):
        slides_to_delete = []
        for idx, slide in enumerate(prs.slides):
            text_found = False
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    txt = shape.text.strip()
                    if len(txt) > 5:
                        text_found = True
                        break
            if not text_found:
                slides_to_delete.append(idx)

        for idx in reversed(slides_to_delete):
            slide_id = prs.slides._sldIdLst[idx]
            rel_id = slide_id.rId
            prs.part.drop_rel(rel_id)
            del prs.slides._sldIdLst[idx]
