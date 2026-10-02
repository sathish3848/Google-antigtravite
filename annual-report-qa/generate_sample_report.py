"""
Helper script to generate a realistic, multi-page sample Annual Report PDF
for Tata Consultancy Services (TCS) FY2024 with rich financial data,
page-numbered metadata, and structured sections.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas
import config

class NumberedCanvas(canvas.Canvas):
    """Canvas that adds clean page numbers and headers to every page."""
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1A365D"))
        # Header
        self.drawString(54, 755, "Tata Consultancy Services Limited — Annual Report FY 2023-2024")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawRightString(558, 755, "Financial & Operational Extract")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(54, 747, 558, 747)

        # Footer
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawString(54, 32, "Confidential & Proprietary — For Internal Analysis & Q&A")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


def create_sample_annual_report(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'MainBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=8
    )
    highlight_style = ParagraphStyle(
        'Highlight',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#1A365D")
    )

    story = []

    # ================= PAGE 1 =================
    story.append(Paragraph("TATA CONSULTANCY SERVICES LIMITED", title_style))
    story.append(Paragraph("<b>Annual Report FY2023–24: Performance Overview & Highlights</b>", h2_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Tata Consultancy Services (TCS) delivered a resilient performance in Financial Year 2023–2024 "
        "amidst macroeconomic volatility and heightened enterprise caution across major western markets. "
        "Our robust client relationships, differentiated full-services portfolio, and disciplined operational "
        "execution drove steady financial performance and industry-leading margins.",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Key Financial Highlights (Consolidated):", h2_style))
    summary_data = [
        ["Financial Metric", "FY2024 (INR Crores)", "FY2023 (INR Crores)", "YoY Growth"],
        ["Total Revenue from Operations", "₹240,893", "₹225,458", "+6.8%"],
        ["Operating Profit (EBIT)", "₹59,314", "₹54,237", "+9.4%"],
        ["Operating Margin", "24.6%", "24.1%", "+50 bps"],
        ["Net Profit (Profit After Tax)", "₹46,099", "₹42,303", "+9.0%"],
        ["Net Margin", "19.1%", "18.8%", "+30 bps"],
        ["Earnings Per Share (EPS)", "₹125.88", "₹115.19", "+9.3%"],
        ["Free Cash Flow", "₹44,282", "₹41,200", "+7.5%"]
    ]
    t1 = Table(summary_data, colWidths=[170, 110, 110, 80])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t1)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Executive Summary on Revenue:</b> What was the total revenue in FY2024? Total revenue in FY2024 reached "
        "<b>₹240,893 crore</b> ($29.1 billion), demonstrating an organic revenue expansion of 6.8% over the previous fiscal year.",
        body_style
    ))
    story.append(PageBreak())

    # ================= PAGE 2 =================
    story.append(Paragraph("MANAGEMENT DISCUSSION AND ANALYSIS", title_style))
    story.append(Paragraph("<b>Market Landscape and Growth Vectors</b>", h2_style))
    story.append(Paragraph(
        "During FY2024, our clients accelerated their digital transformation initiatives focusing on cost optimization, "
        "cloud migration, and AI integration. TCS participated in major deal renewals and strategic vendor consolidation "
        "mandates, closing an all-time high Total Contract Value (TCV) of $42.7 billion in orders.",
        body_style
    ))
    story.append(Paragraph("Industry Vertical Performance:", h2_style))
    vertical_data = [
        ["Industry Vertical", "% of Revenue", "FY2024 Performance Drivers"],
        ["Banking, Financial Services & Insurance (BFSI)", "32.0%", "Resilient wealth management, regulatory tech, Core banking modernize"],
        ["Consumer Business & Retail", "15.8%", "Supply chain resilience, omni-channel commerce platforms"],
        ["Life Sciences & Healthcare", "11.2%", "Clinical trial analytics, cloud-first drug discovery systems"],
        ["Manufacturing", "10.4%", "Industry 4.0, smart factory automation, connected vehicle platforms"],
        ["Technology & Services", "8.9%", "Platform engineering, enterprise SaaS implementation"],
        ["Communication & Media", "6.7%", "5G network rollouts, operational digitization"]
    ]
    t2 = Table(vertical_data, colWidths=[150, 80, 240])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Artificial Intelligence and GenAI:</b> TCS established a dedicated AI.Cloud business unit, training over 300,000 employees "
        "in AI essentials and launching TCS AI WisdomNext, an aggregator platform helping clients orchestrate enterprise GenAI models.",
        body_style
    ))
    story.append(PageBreak())

    # ================= PAGE 3 =================
    story.append(Paragraph("RISK MANAGEMENT & ENTERPRISE GOVERNANCE", title_style))
    story.append(Paragraph("<b>Main Risks Mentioned by Management</b>", h2_style))
    story.append(Paragraph(
        "The Board and Enterprise Risk Management (ERM) committee conduct regular reviews to identify and mitigate "
        "strategic, operational, cyber, financial, and compliance risks. The principal risks identified by management in FY2024 include:",
        body_style
    ))

    risks = [
        "<b>1. Macroeconomic Uncertainty & Discretionary IT Spend:</b> Continued softness in discretionary spending across North America and Europe, particularly in the banking and telecom sectors, may postpone customer decision cycles and contract execution.",
        "<b>2. Rapid Advances in Generative AI:</b> Accelerating adoption of Generative AI could disrupt traditional IT labor-based billing models. TCS is actively counteracting this by embedding AI-assisted coding and automated service delivery into its engagement frameworks.",
        "<b>3. Cybersecurity & Data Privacy Risks:</b> Threat actors increasingly target distributed enterprise networks and software supply chains. Unmitigated security vulnerabilities or unauthorized data access could lead to regulatory penalties and reputational loss.",
        "<b>4. Geopolitical Conflicts & Cross-Border Delivery:</b> Ongoing geopolitical friction in Eastern Europe and the Middle East, along with potential trade barriers and visa regulation shifts in key geographies, could disrupt international delivery centers.",
        "<b>5. Foreign Exchange & Currency Volatility:</b> Significant volatility in foreign currency exchange rates (principally USD, EUR, and GBP against INR) poses direct translation and realization risks to operating revenue and margins.",
        "<b>6. Talent Retention & Wage Inflation:</b> Intense competition for specialized engineering talent in cloud, cybersecurity, and artificial intelligence puts pressure on compensation structures and employee retention."
    ]
    for r in risks:
        story.append(Paragraph(r, body_style))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Management Response:</b> TCS mitigates these through active hedging policies, comprehensive security operations centers (SOC), "
        "and aggressive reskilling of its global talent pool.",
        body_style
    ))
    story.append(PageBreak())

    # ================= PAGE 4 =================
    story.append(Paragraph("OUR PEOPLE & HUMAN CAPITAL", title_style))
    story.append(Paragraph("<b>Workforce Metrics and Talent Development</b>", h2_style))
    story.append(Paragraph(
        "Our employees are the core differentiator of TCS. We maintain a diverse, skilled, and global workforce "
        "committed to delivering customer success across all delivery locations.",
        body_style
    ))

    people_data = [
        ["Human Capital Metric", "Metric Value as of March 31, 2024", "Notes & Industry Context"],
        ["Total Number of Employees", "601,546 employees", "Global full-time workforce headcount"],
        ["Women Professionals", "35.6% (214,150+ women)", "One of the world's largest employers of women"],
        ["Nationalities Represented", "152 nationalities", "Operating across 55 countries"],
        ["Annual Training Hours", "51 million learning hours", "Average 85+ learning hours per associate"],
        ["AI-Trained Associates", "300,000+ employees", "Certified in foundational & advanced AI competencies"],
        ["Attrition Rate (LTM)", "12.5%", "Moderated from 20.1% in the prior year"]
    ]
    t3 = Table(people_data, colWidths=[150, 160, 160])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t3)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Employee Count Answer:</b> How many employees does the company have? As of March 31, 2024, TCS has a total workforce of "
        "<b>601,546 employees</b>.",
        body_style
    ))
    story.append(PageBreak())

    # ================= PAGE 5 =================
    story.append(Paragraph("SHAREHOLDER INFORMATION & DIVIDEND POLICY", title_style))
    story.append(Paragraph("<b>Dividend per Share and Capital Allocation</b>", h2_style))
    story.append(Paragraph(
        "TCS follows a disciplined capital return strategy, returning between 80% to 100% of free cash flow to equity "
        "shareholders through dividends and buybacks.",
        body_style
    ))

    div_data = [
        ["Dividend Distribution", "Amount per Share (INR)", "Record / Payment Date"],
        ["First Interim Dividend", "₹9.00 per equity share", "July 2023"],
        ["Second Interim Dividend", "₹9.00 per equity share", "October 2023"],
        ["Third Interim Dividend", "₹9.00 per equity share", "January 2024"],
        ["Special Dividend", "₹18.00 per equity share", "January 2024"],
        ["Final Dividend (Recommended)", "₹28.00 per equity share", "Subject to AGM approval (June 2024)"],
        ["Total Dividend for FY2024", "₹73.00 per equity share", "Combined distribution for the year"]
    ]
    t4 = Table(div_data, colWidths=[160, 160, 150])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t4)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Dividend Answer:</b> What is the dividend per share? The total dividend per share for FY2024 was <b>₹73.00</b> "
        "(including ₹27 across three interim dividends, ₹18 special dividend, and ₹28 final dividend recommended by the Board).",
        body_style
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>Share Buyback:</b> In addition to dividends, TCS completed a ₹17,000 crore share buyback in December 2023, repurchasing "
        "40,963,855 equity shares at ₹4,150 per share.",
        body_style
    ))
    story.append(PageBreak())

    # ================= PAGE 6 =================
    story.append(Paragraph("CONSOLIDATED FINANCIAL STATEMENTS", title_style))
    story.append(Paragraph("<b>Balance Sheet and Cash Position (As of March 31, 2024)</b>", h2_style))
    story.append(Paragraph(
        "TCS maintained an unencumbered balance sheet with zero long-term debt and strong liquidity reserves. "
        "All figures are presented in INR Crores under Ind AS guidelines.",
        body_style
    ))

    bs_data = [
        ["Balance Sheet Line Item", "As at March 31, 2024 (₹ Cr)", "As at March 31, 2023 (₹ Cr)"],
        ["Non-Current Assets (Property, Plant & Equipment, Intangibles)", "₹38,245", "₹36,110"],
        ["Cash and Cash Equivalents + Investments", "₹48,150", "₹49,820"],
        ["Trade Receivables and Other Current Assets", "₹56,105", "₹52,140"],
        ["Total Assets", "₹142,500", "₹138,070"],
        ["Total Equity (Share Capital + Reserves)", "₹98,450", "₹95,200"],
        ["Total Borrowings / Long-term Debt", "₹0 (Zero Debt)", "₹0 (Zero Debt)"],
        ["Current Liabilities and Provisions", "₹44,050", "₹42,870"],
        ["Total Equity and Liabilities", "₹142,500", "₹138,070"]
    ]
    t5 = Table(bs_data, colWidths=[200, 140, 130])
    t5.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t5)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Sample annual report created successfully at: {output_path}")

if __name__ == "__main__":
    out_file = config.DATA_DIR / "TCS_Annual_Report_FY2024_Sample.pdf"
    create_sample_annual_report(out_file)
