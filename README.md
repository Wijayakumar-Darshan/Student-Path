# 🎓 Student Performance & Marks Management System

A Streamlit web app for schools to manage student marks, streams, career
dreams, and AI-powered career-readiness insights — with downloadable PDF
reports.

## Features

- **Login system** with two roles:
  - **Admin** — manage subjects per stream, manage career dreams & minimum
    cutoff marks, view any student's performance chart.
  - **Counselling Teacher** — add students (with registration number,
    stream, career dream), enter marks per term (3 terms/year), view AI
    insight, download reports.
- **Streams**: Art, Commerce, Maths, Bio, Technology, Vocational.
- **Career dream + minimum cutoff**: each career has a required minimum
  mark per subject. The small rule-based **AI advisor** compares the
  student's average marks against the cutoff and tells you, per subject,
  how much (%) improvement is needed, plus an overall readiness summary.
- **Charts**: bar chart of the student's marks vs. the minimum cutoff for
  their career dream (shown both on-screen and inside the PDF report).
- **3 terms per year** per student per subject — marks are entered/edited
  per term, then averaged automatically.
- **Downloadable reports**:
  - Single-term report (table + AI insight + chart) as PDF.
  - End-of-year overall summary report (Term 1/2/3 + yearly average + AI
    insight) as PDF.

## Project Structure

```
school-performance-app/
├── app.py            # Streamlit app (UI, login, routing)
├── database.py       # SQLite schema, seed data, query helpers
├── ai_advisor.py      # Rule-based AI improvement-plan engine
├── pdf_report.py      # PDF report generation (fpdf2 + matplotlib)
├── requirements.txt
├── data/              # SQLite DB file is created here at first run
└── README.md
```

## Setup

```bash
cd school-performance-app
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app will open at `http://localhost:8501`. The SQLite database
(`data/school.db`) is created automatically on first run, pre-seeded with:

- Default subjects for each of the 6 streams.
- A couple of example career dreams + cutoffs per stream (e.g. Doctor,
  Engineer, Accountant, Lawyer, Software Engineer, Entrepreneur...). Admin
  can add more from the **Manage Careers & Cutoffs** page.
- Two demo login accounts:

| Role    | Username | Password    |
|---------|----------|-------------|
| Admin   | admin    | admin123    |
| Teacher | teacher  | teacher123  |

> ⚠️ Change these passwords before using in production. The simplest way
> is to add a "change password" feature, or directly update the
> `users` table's `password_hash` column using
> `database.hash_password("your_new_password")`.

## How it works

1. **Admin** logs in → adds/edits subjects for a stream → adds career
   dreams and sets the minimum cutoff mark per subject for that career.
2. **Teacher** logs in → adds a student with registration number, name,
   stream, and career dream → selects Term (1/2/3) and Year → enters marks
   for each subject in that stream.
3. After at least one term of marks exists, the **Performance & AI
   Insight** page shows:
   - A bar chart of the student's average marks per subject.
   - If a career dream is set, a second bar chart comparing marks against
     the career's minimum cutoffs, plus a written AI insight per subject
     (✅ On Track / 🟡 Almost There / 🟠 Needs Improvement / 🔴 Critical).
4. **Downloadable Reports** page lets the teacher generate and download:
   - A PDF for any single term.
   - A PDF end-of-year summary once Term 1, 2 and 3 marks are filled in
     (works with partial data too — missing terms show as "-").

## Switching to MySQL (optional)

This build defaults to SQLite so it runs with zero external setup. If you
want to use MySQL instead (as in the original project), you only need to
change `database.py`:

- Replace `get_conn()` to return a `pymysql.connect(...)` connection.
- Replace SQLite-specific syntax (`INSERT OR IGNORE`, `ON CONFLICT...DO
  UPDATE`, `AUTOINCREMENT`) with MySQL equivalents
  (`INSERT IGNORE`, `ON DUPLICATE KEY UPDATE`, `AUTO_INCREMENT`).

Everything else (app.py, ai_advisor.py, pdf_report.py) stays unchanged
since they only call the helper functions in `database.py`.

## Notes / Possible Extensions

- The "AI" engine here is a transparent rule-based comparator (no external
  API key needed), so the whole project runs fully offline. It can later
  be swapped for a call to a real LLM/ML model by replacing
  `ai_advisor.build_improvement_plan()` while keeping its input/output
  shape the same.
- Add a "change password" / user-management screen for production use.
- Add CSV/Excel export alongside PDF if needed (pandas `.to_csv()` /
  `.to_excel()` can be added easily next to the existing download buttons).
