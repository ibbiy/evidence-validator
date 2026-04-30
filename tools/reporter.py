"""
Evidence Integrity Validator - PDF Report Generator
Generates court-ready forensic integrity reports.
"""

import os
from datetime import datetime
from pathlib import Path


def generate_report(report_data: dict, output_path: str = None) -> str:
    """
    Generate a professional forensic integrity report.
    Returns the path to the generated report.
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"reports/evidence_report_{timestamp}.pdf"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        _generate_pdf_report(report_data, output_path)
    except ImportError:
        output_path = output_path.replace(".pdf", ".txt")
        _generate_txt_report(report_data, output_path)

    return output_path


def _generate_pdf_report(data: dict, output_path: str):
    """Generate a professional PDF report using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm, cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=2.5*cm,
        rightMargin=2.5*cm,
        title="Evidence Integrity Report",
        author=data.get("examiner", "Evidence Validator"),
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        name="Title_Report",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    ))
    styles.add(ParagraphStyle(
        name="SubTitle",
        fontName="Helvetica",
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor("#555555"),
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=18,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor("#1a1a2e"),
        borderPadding=(0, 0, 4, 0),
    ))
    styles.add(ParagraphStyle(
        name="FieldLabel",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#333333"),
    ))
    styles.add(ParagraphStyle(
        name="FieldValue",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#555555"),
    ))
    styles.add(ParagraphStyle(
        name="HashValue",
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#2d2d2d"),
        backColor=colors.HexColor("#f5f5f5"),
        leftIndent=4,
        rightIndent=4,
        spaceBefore=2,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="Footer",
        fontName="Helvetica",
        fontSize=7,
        textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="MetaKey",
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#444444"),
    ))
    styles.add(ParagraphStyle(
        name="MetaValue",
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#666666"),
    ))

    elements = []

    # === HEADER ===
    elements.append(Paragraph("EVIDENCE INTEGRITY REPORT", styles["Title_Report"]))
    elements.append(Paragraph("Forensic File Validation & Integrity Check", styles["SubTitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e")))
    elements.append(Spacer(1, 12))

    # === CASE INFO ===
    elements.append(Paragraph("Case Information", styles["SectionHeader"]))
    case_info = [
        ["Case Reference:", data.get("case_ref", "N/A")],
        ["Examiner:", data.get("examiner", "N/A")],
        ["Agency/Company:", data.get("agency", "N/A")],
        ["Examination Date:", data.get("exam_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))],
        ["Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
    ]
    t = Table(case_info, colWidths=[120, 350])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#333333")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#555555")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 8))

    # === CHAIN OF CUSTODY ===
    elements.append(Paragraph("Chain of Custody", styles["SectionHeader"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    elements.append(Spacer(1, 4))

    coc = data.get("chain_of_custody", [])
    if not coc:
        coc = [{"action": "File acquired for analysis", "by": data.get("examiner", "N/A"),
                "date": data.get("exam_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}]

    coc_data = [["#", "Action", "By", "Date/Time"]]
    for i, entry in enumerate(coc, 1):
        coc_data.append([
            str(i),
            entry.get("action", ""),
            entry.get("by", ""),
            entry.get("date", ""),
        ])

    t2 = Table(coc_data, colWidths=[30, 220, 120, 120])
    t2.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
        ("FONTNAME", (1, 1), (-1, -1), "Helvetica"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 12))

    # === FILES ===
    files = data.get("files", [])
    for idx, file_data in enumerate(files, 1):
        elements.append(Paragraph(f"File #{idx}: {file_data.get('filename', 'Unknown')}", styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        elements.append(Spacer(1, 4))

        # File info
        file_info = [
            ["File Path:", file_data.get("filepath", "N/A")],
            ["File Size:", file_data.get("filesize_hr", str(file_data.get("filesize", "N/A")))],
            ["Last Modified:", file_data.get("modified", "N/A")],
            ["Algorithm:", file_data.get("algorithm", "SHA256")],
        ]
        t3 = Table(file_info, colWidths=[100, 390])
        t3.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#333333")),
            ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#555555")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(t3)
        elements.append(Spacer(1, 4))

        # Hash value
        hash_val = file_data.get("hash", "")
        if hash_val:
            elements.append(Paragraph(
                f'<b>Hash ({file_data.get("algorithm", "SHA256")}):</b>',
                styles["FieldLabel"]
            ))
            elements.append(Paragraph(
                f'<font face="Courier" size="8" color="#2d2d2d">{hash_val}</font>',
                styles["HashValue"]
            ))
            elements.append(Spacer(1, 4))

        # Verification result
        if "expected" in file_data:
            match = file_data.get("match", False)
            status = "✅ MATCH - Integrity Verified" if match else "❌ MISMATCH - File has been modified"
            color = "#2e7d32" if match else "#c62828"
            elements.append(Paragraph(
                f'<font color="{color}"><b>{status}</b></font>',
                styles["FieldLabel"]
            ))
            elements.append(Spacer(1, 2))

        # Metadata
        meta = file_data.get("metadata", {})
        if meta:
            elements.append(Paragraph(f"<b>Extracted Metadata:</b>", styles["FieldLabel"]))
            elements.append(Spacer(1, 2))
            meta_items = _flatten_metadata(meta)
            for k, v in meta_items[:20]:
                elements.append(Paragraph(
                    f'<font face="Courier" size="7.5" color="#444444">{k}:</font>  '
                    f'<font size="7.5" color="#666666">{v}</font>',
                    styles["MetaKey"]
                ))
            if len(meta_items) > 20:
                elements.append(Paragraph(
                    f'<i>... and {len(meta_items) - 20} more metadata fields</i>',
                    styles["MetaValue"]
                ))

        elements.append(Spacer(1, 8))

        if idx < len(files):
            elements.append(HRFlowable(width="30%", thickness=0.3, color=colors.HexColor("#dddddd")))

    # === CERTIFICATION ===
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e")))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Certification", styles["SectionHeader"]))
    elements.append(Paragraph(
        "I, the undersigned, certify that the file hashes and metadata contained in this report "
        "were accurately computed using the Evidence Integrity Validator tool at the date and time "
        "indicated. To the best of my knowledge, the examination was conducted in accordance with "
        "digital forensic best practices and industry standards for evidence handling.",
        ParagraphStyle("CertText", fontSize=9, leading=14, textColor=colors.HexColor("#333333"),
                       spaceAfter=12)
    ))

    sig_data = [
        ["", ""],
        ["", ""],
        ["Examiner Signature:", "____________________________"],
        ["Date:", datetime.now().strftime("%Y-%m-%d")],
    ]
    t4 = Table(sig_data, colWidths=[140, 200])
    t4.setStyle(TableStyle([
        ("FONTNAME", (0, 2), (0, 3), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("SPACE", (0, 0), (-1, 1), 20),
    ]))
    elements.append(t4)

    # Build
    doc.build(elements)


def _flatten_metadata(meta: dict, prefix: str = "") -> list:
    """Flatten nested metadata dict into list of (key, value) pairs."""
    items = []
    for key, value in meta.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            items.extend(_flatten_metadata(value, full_key))
        elif isinstance(value, list):
            items.append((full_key, ", ".join(str(v) for v in value[:5])))
        else:
            items.append((full_key, str(value)))
    return items


def _generate_txt_report(data: dict, output_path: str):
    """Fallback text report if ReportLab is not available."""
    lines = []
    lines.append("=" * 70)
    lines.append("EVIDENCE INTEGRITY REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Case Reference: {data.get('case_ref', 'N/A')}")
    lines.append(f"Examiner: {data.get('examiner', 'N/A')}")
    lines.append(f"Agency: {data.get('agency', 'N/A')}")
    lines.append(f"Date: {data.get('exam_date', 'N/A')}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("CHAIN OF CUSTODY")
    lines.append("-" * 70)

    coc = data.get("chain_of_custody", [])
    for entry in coc:
        lines.append(f"  {entry.get('date', '')} - {entry.get('action', '')} by {entry.get('by', '')}")
    lines.append("")

    for idx, fdata in enumerate(data.get("files", []), 1):
        lines.append(f"FILE #{idx}: {fdata.get('filename', 'Unknown')}")
        lines.append(f"  Path: {fdata.get('filepath', 'N/A')}")
        lines.append(f"  Size: {fdata.get('filesize_hr', 'N/A')}")
        lines.append(f"  Modified: {fdata.get('modified', 'N/A')}")
        lines.append(f"  {fdata.get('algorithm', 'SHA256')}: {fdata.get('hash', 'N/A')}")
        if "expected" in fdata:
            status = "✅ VERIFIED" if fdata.get("match") else "❌ MISMATCH"
            lines.append(f"  Verification: {status}")
        lines.append("")

    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append(f"Generated by Evidence Integrity Validator")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path
