import os
import re
import html
import datetime
import pandas as pd

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    Preformatted
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically calculate the total page count
    and render running headers and footers with page numbers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        # Cover page (page 1) has no header or footer
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header
        self.drawString(54, 750, "AI DATA ANALYST PLATFORM REPORT")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)

        # Footer
        self.setFont("Helvetica", 9)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        self.drawString(54, 40, "Confidential - Automated Analysis Report")
        self.line(54, 52, 558, 52)

        self.restoreState()


class PDFService:

    def create_report(
        self,
        file_name,
        profile,
        quality_report,
        analysis_result,
        insights,
        recommendations,
        output_path="outputs/report.pdf"
    ):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Standard letter size, margins set to 0.75in (54pt) on left/right and 1.0in (72pt) on top/bottom
        # Content stays between y=72 and y=720, ensuring no overlap with header/footer
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=72,
            bottomMargin=72
        )

        styles = getSampleStyleSheet()

        # Define custom typography and layout styles
        title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=30,
            leading=36,
            textColor=colors.HexColor('#4f46e5'),
            alignment=0, # Left-aligned title
            spaceAfter=15
        )

        subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=15,
            leading=20,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=40
        )

        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1e1b4b'),
            spaceBefore=15,
            spaceAfter=10,
            keepWithNext=True
        )

        normal_style = ParagraphStyle(
            'Body',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155'),
            spaceAfter=8
        )

        normal_bold_style = ParagraphStyle(
            'BodyBold',
            parent=normal_style,
            fontName='Helvetica-Bold'
        )

        bullet_style = ParagraphStyle(
            'BulletText',
            parent=normal_style,
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=4
        )

        custom_styles = {
            "BodyText": normal_style,
            "BodyTextBold": normal_bold_style,
            "Heading1": heading_style,
            "Heading2": ParagraphStyle(
                'SubSectionHeading',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=13,
                leading=16,
                textColor=colors.HexColor('#1e1b4b'),
                spaceBefore=10,
                spaceAfter=6,
                keepWithNext=True
            ),
            "Heading3": ParagraphStyle(
                'SubSubSectionHeading',
                parent=styles['Heading3'],
                fontName='Helvetica-Bold',
                fontSize=11,
                leading=14,
                textColor=colors.HexColor('#1e1b4b'),
                spaceBefore=8,
                spaceAfter=4,
                keepWithNext=True
            ),
            "Bullet": bullet_style,
            "Normal": styles['Normal']
        }

        # Table Styles
        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=colors.white
        )

        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            textColor=colors.HexColor('#1e293b')
        )

        table_cell_bold_style = ParagraphStyle(
            'TableCellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=colors.HexColor('#1e293b')
        )

        # Helpers for parsing and layouts
        def format_number(value):
            try:
                number = float(value)
                if abs(number) >= 1_000_000_000:
                    return f"{number / 1_000_000_000:.1f}B"
                if abs(number) >= 1_000_000:
                    return f"{number / 1_000_000:.1f}M"
                if abs(number) >= 1_000:
                    return f"{number / 1_000:.1f}K"
                if number.is_integer():
                    return f"{int(number):,}"
                return f"{number:,.2f}"
            except Exception:
                return str(value)

        def format_inline_markdown(txt):
            # Escape HTML characters first to avoid XML parser errors
            txt = html.escape(str(txt))
            # Bold markdown: **text** -> <b>text</b>
            txt = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', txt)
            # Italic markdown: *text* -> <i>text</i>
            txt = re.sub(r'\*(.*?)\*', r'<i>\1</i>', txt)
            # Inline code: `text` -> monospace font with colored text
            txt = re.sub(r'`(.*?)`', r'<font face="Courier" size="9" color="#4f46e5"><b>\1</b></font>', txt)
            return txt

        def markdown_to_flowables(text, styles_dict):
            flowables = []
            lines = str(text).split("\n")
            in_code_block = False
            code_lines = []

            for line in lines:
                stripped = line.strip()

                # Handle code block boundaries
                if stripped.startswith("```"):
                    if in_code_block:
                        code_content = "\n".join(code_lines)
                        code_style = ParagraphStyle(
                            'CodeStyle',
                            parent=styles_dict['Normal'],
                            fontName='Courier',
                            fontSize=8.5,
                            leading=11,
                            textColor=colors.HexColor('#0f172a'),
                            backColor=colors.HexColor('#f1f5f9'),
                            borderColor=colors.HexColor('#e2e8f0'),
                            borderWidth=0.5,
                            borderPadding=6,
                            spaceAfter=8
                        )
                        flowables.append(Preformatted(html.escape(code_content), code_style))
                        code_lines = []
                        in_code_block = False
                    else:
                        in_code_block = True
                    continue

                if in_code_block:
                    code_lines.append(line)
                    continue

                # Headings
                if stripped.startswith("# "):
                    flowables.append(Spacer(1, 10))
                    flowables.append(Paragraph(format_inline_markdown(stripped[2:]), styles_dict["Heading1"]))
                    flowables.append(Spacer(1, 6))
                    continue
                elif stripped.startswith("## "):
                    flowables.append(Spacer(1, 8))
                    flowables.append(Paragraph(format_inline_markdown(stripped[3:]), styles_dict["Heading2"]))
                    flowables.append(Spacer(1, 4))
                    continue
                elif stripped.startswith("### "):
                    flowables.append(Spacer(1, 6))
                    flowables.append(Paragraph(format_inline_markdown(stripped[4:]), styles_dict["Heading3"]))
                    flowables.append(Spacer(1, 4))
                    continue

                # Bullet points
                if stripped.startswith("* ") or stripped.startswith("- ") or stripped.startswith("• "):
                    bullet_text = stripped[2:]
                    flowables.append(Paragraph(f"• {format_inline_markdown(bullet_text)}", styles_dict["Bullet"]))
                    continue

                # Numbered list items
                num_list_match = re.match(r'^(\d+)\.\s+(.*)$', stripped)
                if num_list_match:
                    num = num_list_match.group(1)
                    num_text = num_list_match.group(2)
                    flowables.append(Paragraph(f"{num}. {format_inline_markdown(num_text)}", styles_dict["Bullet"]))
                    continue

                # Empty spacer lines
                if not stripped:
                    flowables.append(Spacer(1, 6))
                    continue

                # Normal Paragraph Text
                flowables.append(Paragraph(format_inline_markdown(line), styles_dict["BodyText"]))

            return flowables

        def make_pdf_table(df, styles_dict):
            # Limit dimension columns/rows to avoid breaking page layout boundaries
            df_limited = df.iloc[:25, :8]
            headers = [str(c) for c in df_limited.columns]
            
            data = [[Paragraph(html.escape(h), table_header_style) for h in headers]]
            
            for _, row in df_limited.iterrows():
                row_data = []
                for val in row:
                    if pd.isnull(val):
                        val_str = "NaN"
                    elif isinstance(val, float):
                        val_str = f"{val:,.2f}"
                    elif isinstance(val, int):
                        val_str = f"{val:,}"
                    else:
                        val_str = str(val)
                    row_data.append(Paragraph(html.escape(val_str), table_cell_style))
                data.append(row_data)

            available_width = 504 # 612 letter width - 108 margin width
            num_cols = len(headers)
            col_width = available_width / num_cols if num_cols > 0 else available_width
            col_widths = [col_width] * num_cols

            t = Table(data, colWidths=col_widths, repeatRows=1)
            t_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ])

            for i in range(1, len(data)):
                if i % 2 == 0:
                    t_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc'))

            t.setStyle(t_style)
            return t

        def format_value_to_flowables(value, styles_dict):
            if value is None:
                return [Paragraph("No result returned.", styles_dict["BodyText"])]
            if isinstance(value, pd.DataFrame):
                return [make_pdf_table(value, styles_dict)]
            if isinstance(value, pd.Series):
                return [make_pdf_table(value.reset_index(), styles_dict)]
            if isinstance(value, dict):
                try:
                    rows = []
                    for k, v in value.items():
                        if isinstance(v, dict):
                            rows.append([Paragraph(f"<b>{html.escape(str(k))}</b>", table_cell_bold_style), Paragraph("", table_cell_style)])
                            for subk, subv in v.items():
                                rows.append([Paragraph(f"  • {html.escape(str(subk))}", table_cell_style), Paragraph(html.escape(str(subv)), table_cell_style)])
                        else:
                            rows.append([Paragraph(f"<b>{html.escape(str(k))}</b>", table_cell_bold_style), Paragraph(html.escape(str(v)), table_cell_style)])
                    if rows:
                        t = Table(rows, colWidths=[200, 304])
                        t.setStyle(TableStyle([
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ]))
                        return [t]
                except Exception:
                    pass
                return markdown_to_flowables(str(value), styles_dict)
            if isinstance(value, (list, tuple)):
                flowables = []
                for item in value:
                    flowables.extend(format_value_to_flowables(item, styles_dict))
                return flowables
            return markdown_to_flowables(str(value), styles_dict)

        # ----------------------------------
        # Cover Page Layout
        # ----------------------------------
        content = []
        content.append(Spacer(1, 120))
        content.append(Paragraph("AI Data Analyst Report", title_style))
        content.append(Paragraph("Automated Data Profiling, Quality Inspection, and Agentic Insights", subtitle_style))
        content.append(Spacer(1, 80))

        # Metadata Card block
        meta_html = f"""
        <b>Dataset Name:</b> {html.escape(file_name)}<br/>
        <b>Date Generated:</b> {datetime.datetime.now().strftime("%B %d, %Y")}<br/>
        <b>System Version:</b> Multi-Agent Analysis Pipeline v1.2.0<br/>
        """
        content.append(Paragraph(meta_html, normal_style))
        content.append(PageBreak())

        # ----------------------------------
        # Dataset Overview Page
        # ----------------------------------
        content.append(Paragraph("Dataset Overview", heading_style))
        content.append(Spacer(1, 10))

        # Key Metrics Table
        overview_data = [
            [Paragraph("<b>Metric</b>", table_header_style), Paragraph("<b>Value</b>", table_header_style)],
            [Paragraph("Total Records (Rows)", table_cell_bold_style), Paragraph(format_number(profile.get('rows', 0)), table_cell_style)],
            [Paragraph("Total Fields (Columns)", table_cell_bold_style), Paragraph(format_number(profile.get('columns', 0)), table_cell_style)],
            [Paragraph("Duplicate Rows Detected", table_cell_bold_style), Paragraph(format_number(profile.get('duplicates', 0)), table_cell_style)]
        ]
        t_overview = Table(overview_data, colWidths=[200, 304])
        t_overview.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(t_overview)
        content.append(Spacer(1, 20))

        column_names = profile.get("column_names", [])
        if column_names:
            content.append(Paragraph("<b>Columns List:</b>", normal_bold_style))
            content.append(Spacer(1, 6))
            content.append(Paragraph(", ".join(map(str, column_names)), normal_style))

        content.append(PageBreak())

        # ----------------------------------
        # Data Quality Assessment Page
        # ----------------------------------
        content.append(Paragraph("Data Quality Assessment", heading_style))
        content.append(Spacer(1, 10))

        quality_data = [
            [Paragraph("<b>Quality Attribute</b>", table_header_style), Paragraph("<b>Observation</b>", table_header_style)],
            [Paragraph("Duplicate Rows Count", table_cell_bold_style), Paragraph(format_number(quality_report.get('duplicates', 0)), table_cell_style)],
            [Paragraph("Constant Fields (Zero Variance)", table_cell_bold_style), Paragraph(format_number(len(quality_report.get('constant_columns', []))), table_cell_style)],
            [Paragraph("High Cardinality Columns", table_cell_bold_style), Paragraph(format_number(len(quality_report.get('high_cardinality', {}))), table_cell_style)]
        ]
        t_quality = Table(quality_data, colWidths=[200, 304])
        t_quality.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9488')), # Teal header for Data Quality
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(t_quality)
        content.append(Spacer(1, 20))

        missing_values = quality_report.get("missing_values", {})
        if missing_values:
            content.append(Paragraph("<b>Missing Values Scan (Top Fields):</b>", normal_bold_style))
            content.append(Spacer(1, 6))
            
            missing_rows = [[Paragraph("<b>Column Name</b>", table_header_style), Paragraph("<b>Missing Cell Count</b>", table_header_style)]]
            for col, val in list(missing_values.items())[:15]:
                missing_rows.append([
                    Paragraph(html.escape(str(col)), table_cell_bold_style),
                    Paragraph(format_number(val), table_cell_style)
                ])
            t_missing = Table(missing_rows, colWidths=[250, 254])
            t_missing.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9488')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            content.append(t_missing)

        content.append(PageBreak())

        # ----------------------------------
        # Analysis Page
        # ----------------------------------
        content.append(Paragraph("Analysis Results", heading_style))
        content.append(Spacer(1, 10))

        if isinstance(analysis_result, dict):
            generated_code = analysis_result.get("generated_code", "")
            result = analysis_result.get("result", "")

            if generated_code:
                content.append(Paragraph("<b>Generated Analysis Code:</b>", normal_bold_style))
                content.append(Spacer(1, 6))
                
                code_style = ParagraphStyle(
                    'CodeBlock',
                    parent=styles['Normal'],
                    fontName='Courier',
                    fontSize=8,
                    leading=10,
                    textColor=colors.HexColor('#0f172a'),
                    backColor=colors.HexColor('#f1f5f9'),
                    borderColor=colors.HexColor('#e2e8f0'),
                    borderWidth=0.5,
                    borderPadding=6,
                    spaceAfter=10
                )
                content.append(Preformatted(html.escape(str(generated_code)), code_style))
                content.append(Spacer(1, 10))

            content.append(Paragraph("<b>Analysis Output:</b>", normal_bold_style))
            content.append(Spacer(1, 6))
            content.extend(format_value_to_flowables(result, custom_styles))
        else:
            content.extend(format_value_to_flowables(analysis_result, custom_styles))

        content.append(PageBreak())

        # ----------------------------------
        # Insights Page
        # ----------------------------------
        content.append(Paragraph("Business Insights", heading_style))
        content.append(Spacer(1, 10))
        content.extend(markdown_to_flowables(insights, custom_styles))
        content.append(PageBreak())

        # ----------------------------------
        # Recommendations Page
        # ----------------------------------
        content.append(Paragraph("Recommendations", heading_style))
        content.append(Spacer(1, 10))
        content.extend(markdown_to_flowables(recommendations, custom_styles))
        content.append(PageBreak())

        # ----------------------------------
        # Executive Summary Page
        # ----------------------------------
        content.append(Paragraph("Executive Summary", heading_style))
        content.append(Spacer(1, 10))

        summary_text = """
        This report was automatically generated using a Multi-Agent AI Data Analyst Platform. 
        The workflow includes automated data quality assessment, profiling, analysis execution, 
        insights extraction, and strategic recommendation generation using LLM-powered agents. 
        All code execution results were run inside secure sandboxed environments to verify accuracy.
        """
        content.append(Paragraph(summary_text, normal_style))

        # Build document with NumberedCanvas to trigger page numbers
        doc.build(content, canvasmaker=NumberedCanvas)

        return output_path