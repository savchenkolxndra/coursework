"""
export.py — функції експорту даних у CSV, Excel та PDF
"""
import io
import os
import pandas as pd
from datetime import datetime

from config import (
    FONT_PATHS, FONT_BOLD_PATHS,
    DARK_GREEN, MID_GREEN, LIGHT_GREEN, BG_GREEN, PALE_GREEN,
    GOLD, GOLD_LIGHT, GOLD_MID,
)
# Аліаси
VIO1, VIO2, VIO3, VIO4 = MID_GREEN, DARK_GREEN, BG_GREEN, LIGHT_GREEN
PINK1, PINK2, PINK3, PINK4 = GOLD, GOLD_LIGHT, GOLD_MID, GOLD_MID
TEAL = LIGHT_GREEN


def export_csv(df: pd.DataFrame) -> bytes:
    """Експортує датафрейм у CSV з підтримкою кирилиці."""
    return df.to_csv(index=False).encode("utf-8-sig")


def export_excel(df: pd.DataFrame) -> bytes:
    """
    Експортує датафрейм у Excel з трьома аркушами:
    Оцінки, По групах, По темах.
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Оцінки")

        by_group = df.groupby("group_name")["grade"].agg(
            ["mean", "median", "min", "max", "count"]
        ).round(2)
        by_group.columns = ["Середнє", "Медіана", "Мін", "Макс", "Кількість"]
        by_group.to_excel(writer, sheet_name="По групах")

        by_topic = df.groupby("topic")["grade"].agg(
            ["mean", "median", "min", "max", "count"]
        ).round(2)
        by_topic.columns = ["Середнє", "Медіана", "Мін", "Макс", "Кількість"]
        by_topic.to_excel(writer, sheet_name="По темах")

    return buf.getvalue()


def export_pdf(df: pd.DataFrame) -> bytes:
    """
    Генерує PDF-звіт із загальною статистикою, таблицями
    по групах, темах і деталями оцінок. Зелена палітра.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rlc
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import cm

    # ── Шрифти ────────────────────────────────────────────────────────────────
    font_reg  = next((p for p in FONT_PATHS if os.path.exists(p)), None)
    font_bold = next((p for p in FONT_BOLD_PATHS if os.path.exists(p)), None)

    fn      = "MyFont"      if font_reg  else "Helvetica"
    fn_bold = "MyFont-Bold" if font_bold else "Helvetica-Bold"

    if font_reg:
        pdfmetrics.registerFont(TTFont("MyFont", font_reg))
    if font_bold:
        pdfmetrics.registerFont(TTFont("MyFont-Bold", font_bold))

    # ── Кольори (зелена палітра) ──────────────────────────────────────────────
    C_DARK   = rlc.HexColor("#1B5E20")
    C_MID    = rlc.HexColor("#388E3C")
    C_LIGHT  = rlc.HexColor("#E8F5E9")
    C_XLIGHT = rlc.HexColor("#F1F8E9")
    C_GOLD   = rlc.HexColor("#F9A825")

    def _table_style(header_color, grid_color, row_colors):
        return TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), header_color),
            ("TEXTCOLOR",     (0, 0), (-1, 0), rlc.white),
            ("FONTNAME",      (0, 0), (-1, 0), fn_bold),
            ("FONTNAME",      (0, 1), (-1, -1), fn),
            ("FONTSIZE",      (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), row_colors),
            ("GRID",          (0, 0), (-1, -1), 0.5, grid_color),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ])

    def sty(name, **kw):
        return ParagraphStyle(name, fontName=kw.pop("font", fn), **kw)

    # ── Документ ─────────────────────────────────────────────────────────────
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    story = []

    story.append(Paragraph(
        "Аналітика успішності студентів",
        sty("h1", font=fn_bold, fontSize=18, textColor=C_DARK, spaceAfter=4)
    ))
    story.append(Paragraph(
        f"Сформовано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        sty("sub", fontSize=10, textColor=C_GOLD, spaceAfter=16)
    ))

    # Загальна статистика
    story.append(Paragraph(
        "Загальна статистика",
        sty("h2", font=fn_bold, fontSize=13, textColor=C_DARK, spaceAfter=6)
    ))
    stats_data = [
        ["Показник", "Значення"],
        ["Кількість оцінок",   str(len(df))],
        ["Середній бал",       f"{df['grade'].mean():.2f}"],
        ["Медіана",            f"{df['grade'].median():.1f}"],
        ["Мінімум",            str(int(df['grade'].min()))],
        ["Максимум",           str(int(df['grade'].max()))],
        ["Відмінники (90+)",   f"{(df['grade'] >= 90).sum()} ({(df['grade'] >= 90).mean()*100:.0f}%)"],
        ["Незадовільно (<60)", f"{(df['grade'] < 60).sum()} ({(df['grade'] < 60).mean()*100:.0f}%)"],
    ]
    t1 = Table(stats_data, colWidths=[9*cm, 7*cm])
    t1.setStyle(_table_style(C_DARK, C_MID, [C_LIGHT, rlc.white]))
    story += [t1, Spacer(1, 0.5*cm)]

    # По групах
    story.append(Paragraph(
        "Середній бал по групах",
        sty("h2", font=fn_bold, fontSize=13, textColor=C_DARK, spaceAfter=6)
    ))
    by_group = df.groupby("group_name")["grade"].agg(["mean", "count"]).reset_index()
    grp_data = [["Група", "Середній бал", "Кількість оцінок"]]
    for _, row in by_group.iterrows():
        grp_data.append([row["group_name"], f"{row['mean']:.2f}", str(int(row["count"]))])
    t2 = Table(grp_data, colWidths=[6*cm, 6*cm, 5*cm])
    t2.setStyle(_table_style(C_MID, C_MID, [C_XLIGHT, rlc.white]))
    story += [t2, Spacer(1, 0.5*cm)]

    # По темах
    story.append(Paragraph(
        "Середній бал по темах",
        sty("h2", font=fn_bold, fontSize=13, textColor=C_DARK, spaceAfter=6)
    ))
    by_topic = df.groupby("topic")["grade"].agg(["mean", "count"]).reset_index().sort_values("mean", ascending=False)
    topic_data = [["Тема", "Середній бал", "Кількість оцінок"]]
    for _, row in by_topic.iterrows():
        topic_data.append([row["topic"], f"{row['mean']:.2f}", str(int(row["count"]))])
    t3 = Table(topic_data, colWidths=[7*cm, 5*cm, 5*cm])
    t3.setStyle(_table_style(C_DARK, C_MID, [C_LIGHT, rlc.white]))
    story += [t3, Spacer(1, 0.5*cm)]

    # Деталі оцінок
    story.append(Paragraph(
        "Деталі оцінок",
        sty("h2", font=fn_bold, fontSize=13, textColor=C_DARK, spaceAfter=6)
    ))
    det_data = [["Група", "Студент", "Тема", "Оцінка"]]
    for _, row in df.sort_values("grade", ascending=False).iterrows():
        det_data.append([
            row["group_name"], row["student_name"],
            row["topic"], str(int(row["grade"]))
        ])
    t4 = Table(det_data, colWidths=[3*cm, 6.5*cm, 4.5*cm, 3*cm])
    t4.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_MID),
        ("TEXTCOLOR",     (0, 0), (-1, 0), rlc.white),
        ("FONTNAME",      (0, 0), (-1, 0), fn_bold),
        ("FONTNAME",      (0, 1), (-1, -1), fn),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_XLIGHT, rlc.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, C_MID),
        ("ALIGN",         (3, 0), (3, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(t4)

    doc.build(story)
    return buf.getvalue()