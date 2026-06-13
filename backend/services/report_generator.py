from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

NAVY = colors.HexColor('#0A1628')
BLUE = colors.HexColor('#1E6FFF')
GREEN = colors.HexColor('#00C896')
LIGHT_GRAY = colors.HexColor('#F4F6FA')
RED = colors.HexColor('#FF4D6D')
ORANGE = colors.HexColor('#FF9800')


def get_grade(score: float) -> str:
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    else:
        return "D"


def generate_pdf_report(analysis_result: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=NAVY,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=BLUE,
        spaceBefore=16,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=NAVY,
        spaceAfter=6,
        leading=14
    )
    small_style = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        spaceAfter=4
    )

    story = []
    story.append(Paragraph("ATS Resume Analysis Report", title_style))
    story.append(Paragraph("Powered by AI-Enhanced Analysis", small_style))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=16))

    overall = analysis_result.get('overall_score', 0)
    grade = get_grade(overall)
    grade_color = GREEN if overall >= 70 else (ORANGE if overall >= 50 else RED)

    score_data = [
        ['Overall ATS Score', f'{overall:.1f}%', f'Grade: {grade}'],
    ]
    score_table = Table(score_data, colWidths=[3*inch, 2*inch, 2*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [NAVY]),
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Category Score Breakdown", heading_style))
    categories = analysis_result.get('categories', {})
    cat_rows = [['Category', 'Score', 'Status']]
    cat_map = [
        ('keyword_match', 'Keyword Match'),
        ('skills_match', 'Skills Match'),
        ('experience_relevance', 'Experience Relevance'),
        ('education_match', 'Education Match'),
        ('formatting_readability', 'Formatting & Readability'),
    ]
    for key, label in cat_map:
        val = categories.get(key, 0)
        pct = f"{val * 100:.1f}%"
        status = "✓ Good" if val >= 0.7 else ("△ Fair" if val >= 0.5 else "✗ Needs Work")
        cat_rows.append([label, pct, status])

    cat_table = Table(cat_rows, colWidths=[3*inch, 1.5*inch, 2.5*inch])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("AI Assessment", heading_style))
    assessment = analysis_result.get('ai_analysis', {}).get('overall_assessment', 'N/A')
    story.append(Paragraph(assessment, body_style))

    strengths = analysis_result.get('ai_analysis', {}).get('strengths', [])
    if strengths:
        story.append(Paragraph("Key Strengths", heading_style))
        for s in strengths:
            story.append(Paragraph(f"• {s}", body_style))

    gaps = analysis_result.get('ai_analysis', {}).get('critical_gaps', [])
    if gaps:
        story.append(Paragraph("Critical Gaps", heading_style))
        for g in gaps:
            story.append(Paragraph(f"• {g}", body_style))

    suggestions = analysis_result.get('ai_analysis', {}).get('top_suggestions', [])
    if suggestions:
        story.append(Paragraph("Top 5 Actionable Recommendations", heading_style))
        for i, sug in enumerate(suggestions[:5], 1):
            priority = sug.get('priority', 'Medium')
            p_color = '#FF4D6D' if priority == 'High' else ('#FF9800' if priority == 'Medium' else '#00C896')
            story.append(Paragraph(
                f"<b>{i}. {sug.get('title', '')}</b> "
                f"<font color='{p_color}'>[{priority} Priority]</font>",
                body_style
            ))
            story.append(Paragraph(sug.get('description', ''), small_style))
            story.append(Spacer(1, 4))

    matched_kws = analysis_result.get('keyword_details', {}).get('matched', [])
    missing_kws = analysis_result.get('keyword_details', {}).get('missing', [])

    if matched_kws or missing_kws:
        story.append(Paragraph("Keyword Analysis", heading_style))
        max_rows = max(len(matched_kws[:10]), len(missing_kws[:10]))
        kw_rows = [['✓ Matched Keywords', '✗ Missing Keywords']]
        for i in range(max_rows):
            m = matched_kws[i] if i < len(matched_kws) else ''
            miss = missing_kws[i] if i < len(missing_kws) else ''
            kw_rows.append([m, miss])

        kw_table = Table(kw_rows, colWidths=[3.5*inch, 3.5*inch])
        kw_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), GREEN),
            ('BACKGROUND', (1, 0), (1, 0), RED),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(kw_table)

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
    story.append(Paragraph("Generated by ATS Resume Scorer | Powered by Claude AI", small_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
