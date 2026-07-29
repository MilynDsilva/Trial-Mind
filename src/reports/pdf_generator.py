import os
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from src.models.patient import PatientRecord
from src.models.trial import TrialProtocol
from src.models.match import MatchReport, MatchStatus


class PDFReportExporter:
    """Generates printable, executive PDF match reports for clinicians."""

    @staticmethod
    def generate_pdf(
        report: MatchReport,
        patient: PatientRecord,
        trial: TrialProtocol,
        output_filename: str = "match_report.pdf",
    ) -> str:
        doc = SimpleDocTemplate(
            output_filename,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        
        # Custom Paragraph Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=6,
        )
        
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=12,
        )

        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=12,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.whitesmoke,
            fontName="Helvetica-Bold",
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1e293b"),
        )

        story = []

        # 1. Header
        story.append(Paragraph("🏥 TrialMind — Clinical Trial Matching Report", title_style))
        story.append(Paragraph("Automated Clinical Decision Support & Audit Summary", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

        # 2. Patient & Trial Info Header Block
        meta_data = [
            [
                Paragraph(f"<b>Patient ID:</b> {patient.anonymized_id}", body_style),
                Paragraph(f"<b>Trial ID:</b> {trial.nct_id}", body_style),
            ],
            [
                Paragraph(f"<b>Condition:</b> {patient.diagnosis.condition_name} ({patient.diagnosis.stage or 'N/A'})", body_style),
                Paragraph(f"<b>Trial Phase:</b> {trial.phase or 'Phase 2'}", body_style),
            ],
            [
                Paragraph(f"<b>Primary Mutation:</b> {', '.join([f'{b.gene_mutation} {b.variant_or_status}' for b in patient.biomarkers]) or 'None'}", body_style),
                Paragraph(f"<b>Target Condition:</b> {trial.target_condition}", body_style),
            ],
        ]

        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(meta_table)
        story.append(Spacer(1, 12))

        # 3. Overall Eligibility Status Banner
        status_color_hex = "#16a34a" if report.overall_status == MatchStatus.ELIGIBLE else ("#d97706" if report.overall_status == MatchStatus.POTENTIALLY_ELIGIBLE else "#dc2626")
        status_bg_hex = "#f0fdf4" if report.overall_status == MatchStatus.ELIGIBLE else ("#fffbeb" if report.overall_status == MatchStatus.POTENTIALLY_ELIGIBLE else "#fef2f2")

        status_text = f"<font size=14 color='{status_color_hex}'><b>MATCH STATUS: {report.overall_status.value}</b></font> (Confidence Score: {report.confidence_score*100:.1f}%)"
        
        status_data = [[Paragraph(status_text, body_style)]]
        status_table = Table(status_data, colWidths=[540])
        status_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(status_bg_hex)),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(status_color_hex)),
                    ("PADDING", (0, 0), (-1, -1), 10),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(status_table)
        story.append(Spacer(1, 10))

        # 4. Executive Summary
        story.append(Paragraph("Executive Summary", section_heading))
        story.append(Paragraph(report.summary, body_style))
        story.append(Spacer(1, 10))

        # 5. Criteria Evaluation Matrix Table
        story.append(Paragraph("Eligibility Criteria Line-by-Line Evaluation", section_heading))

        eval_table_data = [
            [
                Paragraph("Rule ID", table_header_style),
                Paragraph("Type", table_header_style),
                Paragraph("Criterion Description", table_header_style),
                Paragraph("Status", table_header_style),
                Paragraph("Clinical Evidence & Reasoning", table_header_style),
            ]
        ]

        for ev in report.evaluations:
            ev_color = "#16a34a" if ev.status == "MET" else ("#dc2626" if ev.status == "NOT_MET" else "#d97706")
            status_p = Paragraph(f"<font color='{ev_color}'><b>{ev.status}</b></font>", table_cell_style)
            
            reasoning_text = ev.reasoning
            if ev.evidence_quote:
                reasoning_text += f"<br/><i>Quote: \"{ev.evidence_quote}\"</i>"
            if ev.page_citation:
                reasoning_text += f" <font color='#64748b'>({ev.page_citation})</font>"

            eval_table_data.append(
                [
                    Paragraph(ev.criterion_id, table_cell_style),
                    Paragraph(ev.rule_type, table_cell_style),
                    Paragraph(ev.criterion_text, table_cell_style),
                    status_p,
                    Paragraph(reasoning_text, table_cell_style),
                ]
            )

        eval_table = Table(eval_table_data, colWidths=[45, 65, 175, 65, 190])
        eval_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("PADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(eval_table)
        story.append(Spacer(1, 12))

        # 6. Action Items
        if report.action_items:
            story.append(Paragraph("Recommended Clinical Action Items", section_heading))
            for item in report.action_items:
                story.append(Paragraph(f"• {item}", body_style))
            story.append(Spacer(1, 10))

        # 7. Disclaimer Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=12, spaceAfter=8))
        disclaimer_p = Paragraph(
            "<b>Disclaimer:</b> TrialMind is an AI decision-support tool built for clinical research assistance. "
            "It does not provide formal medical diagnoses or replace physician judgment. All trial eligibility determinations "
            "must be verified by a licensed clinician.",
            ParagraphStyle("Disclaimer", parent=body_style, fontSize=7.5, leading=9, textColor=colors.HexColor("#94a3b8")),
        )
        story.append(disclaimer_p)

        doc.build(story)
        return output_filename
