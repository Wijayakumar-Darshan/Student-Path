"""
pdf_report.py  -  PDF generation for term reports, year summaries, and
                  the AI grade-prediction report.
"""

import io, os, tempfile
from fpdf import FPDF
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import prediction_ai as pai

def _safe(text):
    """Strip/replace chars outside latin-1 so fpdf core fonts don't raise."""
    return (str(text)
            .replace('\u2014', '-').replace('\u2013', '-')
            .replace('\u2018', "'").replace('\u2019', "'")
            .replace('\u201c', '"').replace('\u201d', '"')
            .replace('\u2022', '*').replace('\u2026', '...')
            .encode('latin-1', errors='replace').decode('latin-1'))


# ── helpers ────────────────────────────────────────────────────────────────

def _save_fig(fig):
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return tmp.name


def _bar_chart_image(labels, current_vals, cutoff_vals, title):
    fig, ax = plt.subplots(figsize=(6, 3.2))
    x = range(len(labels))
    w = 0.35
    ax.bar([i - w/2 for i in x], current_vals, w, label="Student Marks",  color="#4C72B0")
    ax.bar([i + w/2 for i in x], cutoff_vals,  w, label="Minimum Cutoff", color="#DD8452")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
    ax.set_ylim(0, 100); ax.set_ylabel("Marks"); ax.set_title(title, fontsize=10)
    ax.legend(fontsize=7)
    fig.tight_layout()
    return _save_fig(fig)


def _prediction_chart_image(prediction_results):
    """Grouped bar chart: current avg (blue) vs predicted avg (orange), coloured by status."""
    grades       = [r["grade"]         for r in prediction_results]
    labels       = [f"Gr {r['grade']}" for r in prediction_results]
    current_vals = [r["current_avg"]   if r["current_avg"]   is not None else 0 for r in prediction_results]
    pred_vals    = [r["predicted_avg"] if r["predicted_avg"] is not None else 0 for r in prediction_results]
    bar_colors   = [pai.RISK_COLORS.get(r["status"], "#aaaaaa") for r in prediction_results]

    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(labels))
    w = 0.38
    ax.bar(x - w/2, current_vals, w, label="Current Avg",   color="#4C72B0", alpha=0.85)
    ax.bar(x + w/2, pred_vals,    w, label="Predicted Avg", color=bar_colors, alpha=0.85)
    ax.axhline(75, color="#2fa66b", linestyle="--", linewidth=1, label="Strong (75)")
    ax.axhline(60, color="#4C72B0", linestyle=":",  linewidth=1, label="On Track (60)")
    ax.axhline(45, color="#f0a500", linestyle="-.", linewidth=1, label="Warning (45)")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 100); ax.set_ylabel("Average Marks")
    ax.set_title("Grade-wise Performance Prediction (All Grades 6-13)", fontsize=11)
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    return _save_fig(fig)


def _trend_lines_image(prediction_results):
    """Line chart with historical points + projected trend per grade."""
    grades_with_data = [r for r in prediction_results if r["data_points"] > 0]
    if not grades_with_data:
        return None
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = plt.cm.tab10.colors
    for i, r in enumerate(grades_with_data):
        col = colors[i % len(colors)]
        hist_years  = [h[0] for h in r["historical"]]
        hist_marks  = [h[1] for h in r["historical"]]
        proj_years  = [p[0] for p in r["projection_series"]]
        proj_marks  = [p[1] for p in r["projection_series"]]
        ax.scatter(hist_years, hist_marks, color=col, s=30, zorder=3)
        if len(proj_years) > 1:
            ax.plot(proj_years, proj_marks, color=col, linewidth=1.5,
                    label=f"Gr {r['grade']}", linestyle="--" if r["data_points"] == 1 else "-")
    ax.set_ylabel("Avg Marks"); ax.set_xlabel("Year")
    ax.set_title("Grade Performance Trend Lines", fontsize=11)
    ax.legend(fontsize=7, ncol=4, loc="lower right")
    ax.set_ylim(0, 100)
    fig.tight_layout()
    return _save_fig(fig)


# ── PDF classes ─────────────────────────────────────────────────────────────

class _Base(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 10, "Student Performance Report", ln=True, align="C")
    def footer(self):
        self.set_y(-15); self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


# ── public API ───────────────────────────────────────────────────────────────

def generate_term_report(student, term, year, marks_rows, ai_plan=None, ai_summary=None):
    pdf = _Base(); pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Term {term} Report - Year {year}", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for label, val in [
        ("Registration No", student["reg_no"]),
        ("Name",           student["name"]),
        ("Grade",          student.get("grade", "-")),
        ("Stream",         student.get("stream_name", "-")),
        ("Career Dream",   student.get("career_name", "-")),
    ]:
        pdf.cell(0, 7, f"{label}: {val}", ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(90, 8, "Subject", border=1); pdf.cell(40, 8, "Marks", border=1, align="C", ln=True)
    pdf.set_font("Helvetica", "", 11)
    total = 0
    for r in marks_rows:
        pdf.cell(90, 8, r["subject_name"], border=1)
        pdf.cell(40, 8, str(r["marks"]), border=1, align="C", ln=True)
        total += r["marks"]
    if marks_rows:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(90, 8, "Average", border=1)
        pdf.cell(40, 8, str(round(total / len(marks_rows), 2)), border=1, align="C", ln=True)

    if ai_plan:
        pdf.ln(5); pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "AI Career-Readiness Insight", ln=True)
        pdf.set_font("Helvetica", "", 10)
        if ai_summary: pdf.multi_cell(0, 6, _safe(ai_summary))
        pdf.ln(2)
        img = _bar_chart_image(
            [p["subject"] for p in ai_plan],
            [p["current"] for p in ai_plan],
            [p["cutoff"]  for p in ai_plan],
            "Marks vs Career Minimum Cutoff",
        )
        pdf.image(img, x=15, w=180); os.unlink(img)
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10)
        for h, w in [("Subject",70),("Current",30),("Target",30),("Status",30)]:
            pdf.cell(w, 7, h, border=1, align="C")
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for p in ai_plan:
            pdf.cell(70, 7, p["subject"], border=1)
            pdf.cell(30, 7, str(p["current"]), border=1, align="C")
            pdf.cell(30, 7, str(p["cutoff"]),  border=1, align="C")
            pdf.cell(30, 7, p["status"],       border=1, align="C", ln=True)

    return bytes(pdf.output(dest="S"))


def generate_year_summary_report(student, year, subject_term_avgs, overall_avg,
                                  ai_plan=None, ai_summary=None):
    pdf = _Base(); pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"End-of-Year Summary - {year}", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for label, val in [
        ("Registration No", student["reg_no"]),
        ("Name",           student["name"]),
        ("Grade",          student.get("grade", "-")),
        ("Stream",         student.get("stream_name", "-")),
        ("Career Dream",   student.get("career_name", "-")),
    ]:
        pdf.cell(0, 7, f"{label}: {val}", ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    for h, w in [("Subject",60),("Term 1",30),("Term 2",30),("Term 3",30),("Average",30)]:
        pdf.cell(w, 8, h, border=1, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 10)
    for row in subject_term_avgs:
        pdf.cell(60, 8, row["subject_name"], border=1)
        for k in ["term1","term2","term3","average"]:
            pdf.cell(30, 8, str(row.get(k, "-")), border=1, align="C")
        pdf.ln()
    pdf.ln(3); pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Overall Yearly Average: {overall_avg}", ln=True)

    if ai_plan:
        pdf.ln(5); pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "AI Career-Readiness Insight (Yearly)", ln=True)
        pdf.set_font("Helvetica", "", 10)
        if ai_summary: pdf.multi_cell(0, 6, _safe(ai_summary))
        pdf.ln(2)
        img = _bar_chart_image(
            [p["subject"] for p in ai_plan],
            [p["current"] for p in ai_plan],
            [p["cutoff"]  for p in ai_plan],
            "Yearly Average vs Career Minimum Cutoff",
        )
        pdf.image(img, x=15, w=180); os.unlink(img)

    return bytes(pdf.output(dest="S"))


def generate_prediction_report(prediction_results, ol_summary, generated_date):
    """Full AI grade-prediction report with bar chart + trend lines + grade table."""
    pdf = _Base(); pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "AI Grade Performance Prediction Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Generated: {generated_date}", ln=True, align="C")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "O/L Risk Summary (Grade 10 & 11)", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, _safe(ol_summary))
    pdf.ln(4)

    # Bar chart
    img1 = _prediction_chart_image(prediction_results)
    pdf.image(img1, x=10, w=190); os.unlink(img1)
    pdf.ln(3)

    # Trend lines
    img2 = _trend_lines_image(prediction_results)
    if img2:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Grade Trend Lines (Historical + Projected)", ln=True)
        pdf.image(img2, x=10, w=190); os.unlink(img2)
        pdf.ln(3)

    # Table
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Grade-by-Grade Prediction Details", ln=True)
    pdf.set_font("Helvetica", "B", 9)
    for h, w in [("Grade",20),("Data Yrs",22),("Current",25),("Predicted",25),
                 ("Trend/yr",25),("Status",28),("Confidence",28)]:
        pdf.cell(w, 8, h, border=1, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for r in prediction_results:
        pdf.cell(20, 8, str(r["grade"]),       border=1, align="C")
        pdf.cell(22, 8, str(r["data_points"]), border=1, align="C")
        pdf.cell(25, 8, str(r["current_avg"]   or "-"), border=1, align="C")
        pdf.cell(25, 8, str(r["predicted_avg"] or "-"), border=1, align="C")
        pdf.cell(25, 8, str(r["trend_slope"]   or "-"), border=1, align="C")
        pdf.cell(28, 8, r["status"],     border=1, align="C")
        pdf.cell(28, 8, r["confidence"], border=1, align="C", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Grade-level Messages", ln=True)
    pdf.set_font("Helvetica", "", 9)
    for r in prediction_results:
        if r["data_points"] > 0:
            pdf.multi_cell(180, 6, _safe(f"* {r['message']}"))
            pdf.ln(1)

    return bytes(pdf.output(dest="S"))
