"""
app.py  –  Streamlit Student Performance & Marks Management System
"""

import datetime
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import database as db
import ai_advisor
import pdf_report
import prediction_ai as pai

st.set_page_config(page_title="Student Performance System", page_icon="🎓", layout="wide")
db.init_db()

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: linear-gradient(180deg,#f6f8fc 0%,#eef1f8 100%); }
#MainMenu, header[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#1f2a44 0%,#161d33 100%);
}
section[data-testid="stSidebar"] * { color: #f1f3fb !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.15); }

h1,h2,h3 { font-family:'Poppins',sans-serif; font-weight:600; color:#1f2a44; }

div[data-testid="stForm"] {
    background:#fff; padding:1.4rem 1.6rem;
    border-radius:16px; box-shadow:0 4px 18px rgba(31,42,68,.08);
    border:1px solid #ecedf5;
}
div[data-testid="stExpander"] {
    background:#fff; border-radius:14px;
    border:1px solid #ecedf5; box-shadow:0 2px 10px rgba(31,42,68,.05);
    margin-bottom:.6rem;
}
.stButton > button, .stFormSubmitButton > button {
    background:linear-gradient(135deg,#4C72B0 0%,#3a5a92 100%);
    color:white; border:none; border-radius:10px;
    padding:.5rem 1.2rem; font-weight:600;
    transition:transform .15s ease, box-shadow .15s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    transform:translateY(-1px);
    box-shadow:0 6px 14px rgba(76,114,176,.35); color:white;
}
.stDownloadButton > button {
    background:linear-gradient(135deg,#2fa66b 0%,#1f7a4d 100%);
    color:white; border:none; border-radius:10px; font-weight:600;
}
.stDownloadButton > button:hover {
    transform:translateY(-1px);
    box-shadow:0 6px 14px rgba(47,166,107,.35);
}
div[data-testid="stMetric"] {
    background:#fff; border-radius:14px; padding:.8rem 1rem;
    border:1px solid #ecedf5; box-shadow:0 2px 10px rgba(31,42,68,.05);
}
div[data-testid="stDataFrame"], div[data-testid="stTable"] {
    border-radius:12px; overflow:hidden; border:1px solid #ecedf5;
}
button[data-baseweb="tab"] { font-weight:600; border-radius:10px 10px 0 0; }
div[data-testid="stAlert"] { border-radius:12px; }

.app-banner {
    background:linear-gradient(135deg,#4C72B0 0%,#2c3e6b 100%);
    padding:1.6rem 2rem; border-radius:18px; color:white;
    margin-bottom:1.2rem; box-shadow:0 8px 24px rgba(31,42,68,.18);
}
.app-banner h1 { color:white !important; margin:0; font-size:1.8rem; }
.app-banner p  { color:#d7e0f5; margin:.2rem 0 0 0; }

.login-card {
    background:#fff; border-radius:20px; padding:2.2rem 2.4rem;
    box-shadow:0 12px 32px rgba(31,42,68,.12); border:1px solid #ecedf5;
}

.risk-card {
    border-radius:14px; padding:.9rem 1.2rem; margin-bottom:.5rem;
    font-weight:500; border-left:5px solid;
}
</style>
""", unsafe_allow_html=True)

# ── Session ───────────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None


def logout():
    st.session_state.user = None
    st.rerun()


def _banner(icon, title, subtitle):
    st.markdown(
        f'<div class="app-banner"><h1>{icon} {title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def _sidebar_user(icon, role_label):
    st.sidebar.markdown(
        f"""<div style="text-align:center;padding:.6rem 0 1rem 0;">
            <div style="font-size:2.2rem;">{icon}</div>
            <div style="font-weight:600;font-size:1.05rem;">{st.session_state.user['full_name']}</div>
            <div style="opacity:.7;font-size:.85rem;">Role: {role_label}</div>
            </div><hr/>""",
        unsafe_allow_html=True,
    )


# ── LOGIN ─────────────────────────────────────────────────────────────────────
def login_screen():
    _banner("🎓", "Student Performance & Marks System",
            "Login as Admin or Counselling Teacher to continue")
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("#### 🔐 Sign in")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                user = db.verify_login(username.strip(), password)
                if user:
                    st.session_state.user = dict(user)
                    st.rerun()
                else:
                    st.error("Invalid username or password.")


# ── ADMIN ─────────────────────────────────────────────────────────────────────
def admin_dashboard():
    _sidebar_user("🛡️", "Admin")
    page = st.sidebar.radio("Navigate", [
        "📚 Manage Subjects",
        "🎯 Manage Careers & Cutoffs",
        "📊 Student Performance Charts",
        "👥 All Students",
        "🤖 AI Grade Predictions",
    ])
    st.sidebar.markdown("<br/>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()

    _banner("🛡️", "Admin Dashboard",
            "Manage subjects, careers, student performance and AI predictions")

    streams      = db.get_streams()
    stream_names = [s["name"] for s in streams]

    # ── Manage Subjects ────────────────────────────────────────────────────
    if page == "📚 Manage Subjects":
        st.header("📚 Manage Subjects")
        chosen_stream = st.selectbox("Stream", stream_names)
        stream_id     = db.get_stream_id(chosen_stream)

        with st.form("add_subject_form"):
            new_subject = st.text_input("New subject name")
            if st.form_submit_button("➕ Add Subject"):
                if new_subject.strip():
                    db.add_subject(new_subject.strip(), stream_id)
                    st.success(f"Added '{new_subject}' to {chosen_stream}.")
                    st.rerun()

        subs = db.get_subjects_by_stream(stream_id)
        st.subheader(f"Subjects in {chosen_stream}")
        if not subs:
            st.info("No subjects yet for this stream.")
        else:
            for sub in subs:
                with st.expander(f"✏️ {sub['name']}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        with st.form(f"edit_sub_{sub['id']}"):
                            edited = st.text_input("Subject name", value=sub["name"])
                            if st.form_submit_button("💾 Save"):
                                if edited.strip():
                                    db.update_subject(sub["id"], edited.strip())
                                    st.success("Updated."); st.rerun()
                    with col2:
                        mc, cc = db.subject_usage_counts(sub["id"])
                        if mc or cc:
                            st.caption(f"⚠️ {mc} marks, {cc} cutoffs")
                        if st.checkbox("Confirm delete", key=f"cd_{sub['id']}"):
                            if st.button("🗑️ Delete", key=f"ds_{sub['id']}"):
                                db.delete_subject(sub["id"], cascade=True)
                                st.success("Deleted."); st.rerun()

    # ── Manage Careers ─────────────────────────────────────────────────────
    elif page == "🎯 Manage Careers & Cutoffs":
        st.header("🎯 Manage Career Dreams & Minimum Cutoffs")
        tab_view, tab_add, tab_update, tab_delete = st.tabs(
            ["📋 View All", "➕ Add Career", "✏️ Update Career", "🗑️ Delete Career"]
        )

        with tab_view:
            all_careers = db.get_all_careers()
            if not all_careers:
                st.info("No careers added yet.")
            else:
                df = pd.DataFrame(all_careers).rename(columns={
                    "name":"Career","stream_name":"Stream",
                    "cutoff_count":"Subjects w/ Cutoffs","student_count":"Students Assigned"})
                st.dataframe(df[["Career","Stream","Subjects w/ Cutoffs","Students Assigned"]],
                             use_container_width=True, hide_index=True)
                st.markdown("##### Drill into a career's cutoffs")
                opts = {f"{c['name']} ({c['stream_name']})": c for c in all_careers}
                sel  = st.selectbox("Select career", list(opts.keys()), key="view_c")
                rows = db.get_career_cutoffs(opts[sel]["id"])
                if rows:
                    st.table(pd.DataFrame(rows)[["subject_name","min_marks"]]
                             .rename(columns={"subject_name":"Subject","min_marks":"Cutoff"}))
                else:
                    st.caption("No cutoffs set yet.")

        with tab_add:
            chosen_stream = st.selectbox("Stream", stream_names, key="add_c_stream")
            stream_id     = db.get_stream_id(chosen_stream)
            subs          = db.get_subjects_by_stream(stream_id)
            if not subs:
                st.warning("Add subjects for this stream first.")
            else:
                career_name   = st.text_input("Career dream name", key="add_c_name")
                st.caption("Pick only subjects this career actually requires — students may take different combinations.")
                subj_opts     = {s["name"]: s["id"] for s in subs}
                sel_names     = st.multiselect("Subjects required", list(subj_opts.keys()), key="add_c_subs")
                with st.form("add_career_form"):
                    cutoffs = {}
                    if sel_names:
                        st.write("Minimum cutoff marks:")
                        cols = st.columns(2)
                        for i, nm in enumerate(sel_names):
                            with cols[i % 2]:
                                cutoffs[subj_opts[nm]] = st.number_input(
                                    nm, 0, 100, 50, key=f"ac_{subj_opts[nm]}")
                    else:
                        st.info("Select subjects above first.")
                    if st.form_submit_button("➕ Save Career"):
                        if not career_name.strip():
                            st.error("Career name required.")
                        elif not cutoffs:
                            st.error("Select at least one subject.")
                        else:
                            db.add_career(career_name.strip(), stream_id, cutoffs)
                            st.success(f"Saved '{career_name}'."); st.rerun()

        with tab_update:
            chosen_stream_u = st.selectbox("Stream", stream_names, key="upd_c_stream")
            stream_id_u     = db.get_stream_id(chosen_stream_u)
            subs_u          = db.get_subjects_by_stream(stream_id_u)
            careers_u       = db.get_careers_by_stream(stream_id_u)
            if not careers_u:
                st.info(f"No careers in {chosen_stream_u} yet.")
            elif not subs_u:
                st.warning("Add subjects first.")
            else:
                sel_c = st.selectbox("Career to update", [c["name"] for c in careers_u], key="upd_c_sel")
                c     = next(x for x in careers_u if x["name"] == sel_c)
                rows  = db.get_career_cutoffs(c["id"])
                ex    = {r["subject_id"]: r["min_marks"] for r in rows}
                edited_name = st.text_input("Career name", value=c["name"], key=f"ucn_{c['id']}")
                st.caption("Add/remove subjects; only selected ones will be kept after saving.")
                subj_opts_u  = {s["name"]: s["id"] for s in subs_u}
                cur_names    = [s["name"] for s in subs_u if s["id"] in ex]
                sel_names_u  = st.multiselect("Subjects required", list(subj_opts_u.keys()),
                                               default=cur_names, key=f"ucs_{c['id']}")
                with st.form(f"upd_c_{c['id']}"):
                    new_cutoffs = {}
                    if sel_names_u:
                        st.write("Minimum cutoff marks:")
                        cols = st.columns(2)
                        for i, nm in enumerate(sel_names_u):
                            sid2 = subj_opts_u[nm]
                            with cols[i % 2]:
                                new_cutoffs[sid2] = st.number_input(
                                    nm, 0, 100, int(ex.get(sid2, 50)), key=f"uc_{c['id']}_{sid2}")
                    else:
                        st.info("Select subjects above.")
                    if st.form_submit_button("💾 Save Changes"):
                        if not edited_name.strip():
                            st.error("Name required.")
                        elif not new_cutoffs:
                            st.error("Select at least one subject.")
                        else:
                            db.update_career(c["id"], edited_name.strip(), new_cutoffs, replace=True)
                            st.success("Updated."); st.rerun()

        with tab_delete:
            chosen_stream_d = st.selectbox("Stream", stream_names, key="del_c_stream")
            stream_id_d     = db.get_stream_id(chosen_stream_d)
            careers_d       = db.get_careers_by_stream(stream_id_d)
            if not careers_d:
                st.info(f"No careers in {chosen_stream_d}.")
            else:
                sel_d = st.selectbox("Career to delete", [c["name"] for c in careers_d], key="del_c_sel")
                c     = next(x for x in careers_d if x["name"] == sel_d)
                n     = db.career_usage_counts(c["id"])
                if n:
                    st.warning(f"⚠️ '{c['name']}' is assigned to {n} student(s). "
                               "Deleting will clear their career dream.")
                if st.checkbox(f"Confirm delete '{c['name']}'", key=f"conf_d_{c['id']}"):
                    if st.button("🗑️ Delete Career", key=f"del_c_{c['id']}"):
                        db.delete_career(c["id"], cascade=True)
                        st.success("Deleted."); st.rerun()

    # ── Student Charts ─────────────────────────────────────────────────────
    elif page == "📊 Student Performance Charts":
        st.header("📊 Student Performance Charts")
        students = db.get_all_students()
        if not students:
            st.info("No students added yet.")
            return
        opts    = {f"Gr{s['grade']} | {s['reg_no']} - {s['name']} ({s['stream_name']})": s for s in students}
        chosen  = st.selectbox("Select Student", list(opts.keys()))
        render_student_chart_and_ai(opts[chosen])

    # ── All Students ───────────────────────────────────────────────────────
    elif page == "👥 All Students":
        st.header("👥 All Students")
        grade_filter  = st.selectbox("Filter by Grade", ["All"] + [f"Grade {g}" for g in db.GRADES])
        stream_filter = st.selectbox("Filter by Stream", ["All"] + [s["name"] for s in db.get_streams()])
        g = int(grade_filter.split()[-1]) if grade_filter != "All" else None
        s = db.get_stream_id(stream_filter) if stream_filter != "All" else None
        students = db.get_all_students(stream_id=s, grade=g)
        if students:
            st.dataframe(
                pd.DataFrame(students)[["reg_no","name","grade","stream_name","career_name"]].rename(
                    columns={"reg_no":"Reg No","name":"Name","grade":"Grade",
                             "stream_name":"Stream","career_name":"Career Dream"}),
                use_container_width=True, hide_index=True,
            )
            st.metric("Total Students", len(students))
        else:
            st.info("No students found.")

    # ── AI Grade Predictions ───────────────────────────────────────────────
    elif page == "🤖 AI Grade Predictions":
        render_prediction_page()


# ── AI Prediction Page (shared between admin & teacher) ──────────────────────
def render_prediction_page():
    st.header("🤖 AI Grade Performance Prediction")
    st.caption(
        "This model uses linear regression trained on all historical marks in the system. "
        "Prediction accuracy improves as more years of data are fed in. "
        "Grades 10 & 11 are highlighted as O/L critical years."
    )

    rows = db.get_grade_year_averages()
    if not rows:
        st.warning("No marks data in the system yet. Add student marks first to enable predictions.")
        return

    results    = pai.predict_grade_performance(rows, predict_years=2)
    ol_summary = pai.ol_risk_summary(results)

    # O/L banner
    st.info(f"📌 {ol_summary}")
    st.markdown("---")

    # Metric cards row
    grades_with_data = [r for r in results if r["data_points"] > 0]
    col_sets = st.columns(min(len(grades_with_data), 4))
    for i, r in enumerate(grades_with_data[:4]):
        with col_sets[i]:
            color = pai.RISK_COLORS[r["status"]]
            st.markdown(
                f"<div class='risk-card' style='border-color:{color};background:{color}18;'>"
                f"<b>Grade {r['grade']}</b><br/>"
                f"<span style='font-size:1.4rem;color:{color};'>{r['predicted_avg']}</span><br/>"
                f"<small>{r['status']} · {r['confidence']} confidence</small></div>",
                unsafe_allow_html=True,
            )
    if len(grades_with_data) > 4:
        col_sets2 = st.columns(min(len(grades_with_data) - 4, 4))
        for i, r in enumerate(grades_with_data[4:8]):
            with col_sets2[i]:
                color = pai.RISK_COLORS[r["status"]]
                st.markdown(
                    f"<div class='risk-card' style='border-color:{color};background:{color}18;'>"
                    f"<b>Grade {r['grade']}</b><br/>"
                    f"<span style='font-size:1.4rem;color:{color};'>{r['predicted_avg']}</span><br/>"
                    f"<small>{r['status']} · {r['confidence']} confidence</small></div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # Bar chart: current vs predicted
    st.subheader("Current Average vs Predicted Average by Grade")
    fig, ax = plt.subplots(figsize=(10, 4))
    x      = np.arange(8)
    labels = [f"Gr {r['grade']}" for r in results]
    cur    = [r["current_avg"]   if r["current_avg"]   is not None else 0 for r in results]
    pred   = [r["predicted_avg"] if r["predicted_avg"] is not None else 0 for r in results]
    bar_c  = [pai.RISK_COLORS.get(r["status"], "#aaa") for r in results]
    w      = 0.38
    ax.bar(x - w/2, cur,  w, label="Current Avg",   color="#4C72B0", alpha=0.85)
    ax.bar(x + w/2, pred, w, label="Predicted Avg", color=bar_c,     alpha=0.85)
    ax.axhline(75, color="#2fa66b", linestyle="--", linewidth=1.2, label="Strong (75)")
    ax.axhline(60, color="#4C72B0", linestyle=":",  linewidth=1.2, label="On Track (60)")
    ax.axhline(45, color="#f0a500", linestyle="-.", linewidth=1.2, label="Warning (45)")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylim(0, 100); ax.set_ylabel("Average Marks")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Trend line chart
    st.subheader("Historical Trend Lines + Projected (per Grade)")
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    colors = plt.cm.tab10.colors
    for i, r in enumerate(grades_with_data):
        col       = colors[i % len(colors)]
        proj_y    = [p[0] for p in r["projection_series"]]
        proj_m    = [p[1] for p in r["projection_series"]]
        hist_y    = [h[0] for h in r["historical"]]
        hist_m    = [h[1] for h in r["historical"]]
        ax2.scatter(hist_y, hist_m, color=col, s=40, zorder=3)
        if len(proj_y) > 1:
            ax2.plot(proj_y, proj_m, color=col, linewidth=2,
                     linestyle="--" if r["data_points"] == 1 else "-",
                     label=f"Grade {r['grade']}")
    ax2.set_ylabel("Avg Marks"); ax2.set_xlabel("Year")
    ax2.set_ylim(0, 100)
    ax2.legend(fontsize=8, ncol=4, loc="lower right")
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    # Detail table
    st.subheader("Grade-by-Grade Details")
    table_rows = []
    for r in results:
        table_rows.append({
            "Grade":       r["grade"],
            "Data Years":  r["data_points"],
            "Current Avg": r["current_avg"] or "-",
            "Predicted":   r["predicted_avg"] or "-",
            "Trend/yr":    r["trend_slope"] or "-",
            "Status":      r["status"],
            "Confidence":  r["confidence"],
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    # Messages
    st.subheader("AI Insights by Grade")
    for r in results:
        if r["data_points"] > 0:
            color = pai.RISK_COLORS[r["status"]]
            st.markdown(
                f"<div class='risk-card' style='border-color:{color};background:{color}12;'>"
                f"{r['message']}</div>",
                unsafe_allow_html=True,
            )

    # Download
    today = datetime.date.today().strftime("%d %B %Y")
    pdf_b = pdf_report.generate_prediction_report(results, ol_summary, today)
    st.download_button(
        "⬇️ Download AI Prediction Report (PDF)",
        data=pdf_b,
        file_name=f"grade_prediction_{datetime.date.today()}.pdf",
        mime="application/pdf",
    )


# ── Shared: per-student chart + career AI ────────────────────────────────────
def render_student_chart_and_ai(student, year_filter=None):
    marks_rows = db.get_marks_for_student(student["reg_no"], year=year_filter)
    if not marks_rows:
        st.info("No marks recorded yet for this student.")
        return None, None

    avg_marks = ai_advisor.average_marks_by_subject(marks_rows)
    st.subheader("Average Marks by Subject")
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(list(avg_marks.keys()), list(avg_marks.values()), color="#4C72B0")
    ax.set_ylim(0, 100); ax.set_ylabel("Marks")
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    st.pyplot(fig); plt.close(fig)

    ai_plan = ai_summary = None
    if student.get("career_id"):
        cutoffs = db.get_career_cutoffs(student["career_id"])
        if cutoffs:
            ai_plan    = ai_advisor.build_improvement_plan(avg_marks, cutoffs)
            ai_summary = ai_advisor.overall_summary(ai_plan)
            st.subheader(f"🤖 AI Career-Readiness — {student.get('career_name','')}")
            st.info(ai_summary)

            fig2, ax2 = plt.subplots(figsize=(7, 3.5))
            labels = [p["subject"] for p in ai_plan]
            x = range(len(labels)); w = 0.35
            ax2.bar([i - w/2 for i in x], [p["current"] for p in ai_plan], w,
                    label="Student Marks", color="#4C72B0")
            ax2.bar([i + w/2 for i in x], [p["cutoff"]  for p in ai_plan], w,
                    label="Min Cutoff", color="#DD8452")
            ax2.set_xticks(list(x)); ax2.set_xticklabels(labels, rotation=20, ha="right")
            ax2.set_ylim(0, 100); ax2.legend()
            fig2.tight_layout()
            st.pyplot(fig2); plt.close(fig2)

            for p in ai_plan:
                icon = {"On Track":"✅","Almost There":"🟡","Needs Improvement":"🟠","Critical":"🔴"}[p["status"]]
                st.write(f"{icon} **{p['subject']}** — {p['message']}")
        else:
            st.warning("No cutoffs configured for this student's career dream yet.")
    else:
        st.caption("No career dream assigned yet.")

    return ai_plan, ai_summary


# ── TEACHER ───────────────────────────────────────────────────────────────────
def teacher_dashboard():
    _sidebar_user("🧑‍🏫", "Counselling Teacher")
    page = st.sidebar.radio("Navigate", [
        "➕ Add / Update Student",
        "📝 Enter Marks",
        "📊 Performance & AI Insight",
        "⬇️ Downloadable Reports",
        "🤖 AI Grade Predictions",
    ])
    st.sidebar.markdown("<br/>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()

    _banner("🧑‍🏫", "Teacher Dashboard",
            "Add students, record marks per term and track AI career-readiness")

    streams      = db.get_streams()
    stream_names = [s["name"] for s in streams]

    # ── Add / Update Student ───────────────────────────────────────────────
    if page == "➕ Add / Update Student":
        st.header("➕ Add / Update Student")

        # FIX: stream selection OUTSIDE the form so career list refreshes dynamically
        col1, col2 = st.columns(2)
        with col1:
            stream_choice = st.selectbox("Stream", stream_names, key="stu_stream")
        with col2:
            grade_choice  = st.selectbox("Grade", [f"Grade {g}" for g in db.GRADES], key="stu_grade")

        stream_id = db.get_stream_id(stream_choice)
        grade_val = int(grade_choice.split()[-1])

        # Careers now fetched fresh from DB based on the selected stream
        careers       = db.get_careers_by_stream(stream_id)
        career_names  = ["-- none --"] + [c["name"] for c in careers]

        with st.form("student_form"):
            reg_no        = st.text_input("Student Registration Number")
            name          = st.text_input("Student Name")
            career_choice = st.selectbox("Career Dream", career_names)

            if st.form_submit_button("💾 Save Student"):
                if reg_no.strip() and name.strip():
                    career_id = None
                    if career_choice != "-- none --":
                        career_id = next(c["id"] for c in careers if c["name"] == career_choice)
                    db.upsert_student(reg_no.strip(), name.strip(), grade_val, stream_id, career_id)
                    st.success(f"✅ Saved: {name} (Reg: {reg_no}, Grade {grade_val}, {stream_choice})")
                else:
                    st.error("Registration number and name are required.")

        # Show existing student info if reg no typed
        st.markdown("---")
        st.caption("🔍 Look up an existing student to pre-fill the form:")
        lookup = st.text_input("Enter registration number to look up", key="lookup_reg")
        if lookup.strip():
            existing = db.get_student(lookup.strip())
            if existing:
                st.json({k: v for k, v in existing.items() if k != "password_hash"})
            else:
                st.info("No student found with that registration number.")

    # ── Enter Marks ────────────────────────────────────────────────────────
    elif page == "📝 Enter Marks":
        st.header("📝 Enter Marks (per Term)")

        # Grade filter to narrow student list
        grade_f = st.selectbox("Filter students by Grade",
                               ["All"] + [f"Grade {g}" for g in db.GRADES], key="marks_grade_f")
        g_val   = int(grade_f.split()[-1]) if grade_f != "All" else None
        students = db.get_all_students(grade=g_val)

        if not students:
            st.info("No students found. Add a student first.")
            return

        opts    = {f"Gr{s['grade']} | {s['reg_no']} - {s['name']} ({s['stream_name']})": s
                   for s in students}
        chosen  = st.selectbox("Select Student", list(opts.keys()))
        student = opts[chosen]

        col1, col2, col3 = st.columns(3)
        term = col1.selectbox("Term", [1, 2, 3])
        year = col2.number_input("Year", 2000, 2100, 2026, step=1)
        # Grade in this particular year (defaults to student's registered grade)
        grade_for_marks = col3.selectbox(
            "Grade (this year)",
            [f"Grade {g}" for g in db.GRADES],
            index=db.GRADES.index(student["grade"]) if student["grade"] in db.GRADES else 4,
        )
        grade_int = int(grade_for_marks.split()[-1])

        subjects = db.get_subjects_by_stream(student["stream_id"])
        if not subjects:
            st.warning("No subjects configured for this stream. Ask Admin to add subjects.")
            return

        existing = {
            m["subject_id"]: m["marks"]
            for m in db.get_marks_for_student(student["reg_no"], year=year)
            if m["term"] == term
        }

        with st.form("marks_form"):
            entries = {}
            cols    = st.columns(2)
            for i, sub in enumerate(subjects):
                with cols[i % 2]:
                    entries[sub["id"]] = st.number_input(
                        sub["name"], 0.0, 100.0,
                        float(existing.get(sub["id"], 0.0)), step=1.0,
                        key=f"mk_{sub['id']}_{term}_{year}",
                    )
            if st.form_submit_button(f"💾 Save Term {term} Marks"):
                for subject_id, mark_val in entries.items():
                    db.save_mark(student["reg_no"], subject_id, term, year, grade_int, mark_val)
                st.success(f"Term {term} marks saved for {student['name']} — Grade {grade_int} ({year}).")

    # ── Performance & AI ───────────────────────────────────────────────────
    elif page == "📊 Performance & AI Insight":
        st.header("📊 Performance & AI Career-Readiness Insight")
        students = db.get_all_students()
        if not students:
            st.info("No students added yet."); return
        opts    = {f"Gr{s['grade']} | {s['reg_no']} - {s['name']} ({s['stream_name']})": s for s in students}
        chosen  = st.selectbox("Select Student", list(opts.keys()))
        render_student_chart_and_ai(opts[chosen])

    # ── Downloadable Reports ───────────────────────────────────────────────
    elif page == "⬇️ Downloadable Reports":
        st.header("⬇️ Downloadable Student Reports")
        students = db.get_all_students()
        if not students:
            st.info("No students added yet."); return
        opts    = {f"Gr{s['grade']} | {s['reg_no']} - {s['name']} ({s['stream_name']})": s for s in students}
        chosen  = st.selectbox("Select Student", list(opts.keys()))
        student = opts[chosen]

        tab1, tab2 = st.tabs(["📄 Single Term Report", "📑 Year Summary Report"])

        with tab1:
            c1, c2 = st.columns(2)
            term = c1.selectbox("Term", [1, 2, 3], key="rpt_term")
            year = c2.number_input("Year", 2000, 2100, 2026, step=1, key="rpt_year")
            marks_rows = [m for m in db.get_marks_for_student(student["reg_no"], year=year)
                          if m["term"] == term]
            if not marks_rows:
                st.info("No marks for this term/year yet.")
            else:
                st.dataframe(pd.DataFrame(marks_rows)[["subject_name","marks"]],
                             use_container_width=True, hide_index=True)
                ai_plan = ai_summary = None
                if student.get("career_id"):
                    avg = {r["subject_name"]: r["marks"] for r in marks_rows}
                    cuts = db.get_career_cutoffs(student["career_id"])
                    if cuts:
                        ai_plan    = ai_advisor.build_improvement_plan(avg, cuts)
                        ai_summary = ai_advisor.overall_summary(ai_plan)
                full_stu = {**student, "stream_name": student.get("stream_name",""),
                            "career_name": student.get("career_name","")}
                pdf_b = pdf_report.generate_term_report(full_stu, term, year, marks_rows, ai_plan, ai_summary)
                st.download_button("⬇️ Download Term PDF", pdf_b,
                                   f"{student['reg_no']}_term{term}_{year}.pdf", "application/pdf")

        with tab2:
            year2 = st.number_input("Year", 2000, 2100, 2026, step=1, key="sum_year")
            all_m = db.get_marks_for_student(student["reg_no"], year=year2)
            if not all_m:
                st.info("No marks for this year yet.")
            else:
                df    = pd.DataFrame(all_m)
                pivot = df.pivot_table(index="subject_name", columns="term", values="marks", aggfunc="mean")
                pivot = pivot.reindex(columns=[1,2,3])
                pivot["average"] = pivot.mean(axis=1, skipna=True).round(2)
                pivot = pivot.round(2)
                st.dataframe(pivot, use_container_width=True)

                sta_rows = [{"subject_name": subj,
                             "term1": row.get(1,"-"), "term2": row.get(2,"-"),
                             "term3": row.get(3,"-"), "average": row["average"]}
                            for subj, row in pivot.iterrows()]
                overall = round(pivot["average"].mean(), 2)
                st.metric("Overall Yearly Average", overall)

                ai_plan = ai_summary = None
                if student.get("career_id"):
                    avg  = {r["subject_name"]: r["average"] for r in sta_rows}
                    cuts = db.get_career_cutoffs(student["career_id"])
                    if cuts:
                        ai_plan    = ai_advisor.build_improvement_plan(avg, cuts)
                        ai_summary = ai_advisor.overall_summary(ai_plan)
                        st.info(ai_summary)

                full_stu = {**student, "stream_name": student.get("stream_name",""),
                            "career_name": student.get("career_name","")}
                pdf_b = pdf_report.generate_year_summary_report(
                    full_stu, year2, sta_rows, overall, ai_plan, ai_summary)
                st.download_button("⬇️ Download Year Summary PDF", pdf_b,
                                   f"{student['reg_no']}_{year2}_summary.pdf", "application/pdf")

    # ── AI Grade Predictions (teacher view) ───────────────────────────────
    elif page == "🤖 AI Grade Predictions":
        render_prediction_page()


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.user:
        login_screen()
    elif st.session_state.user["role"] == "admin":
        admin_dashboard()
    else:
        teacher_dashboard()


if __name__ == "__main__":
    main()
