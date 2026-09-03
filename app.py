import streamlit as st
import plotly.graph_objects as go
import os
import json
from dotenv import load_dotenv

from modules.resume_parser import extract_text_from_file, parse_resume_with_gemini, fallback_parse_resume
from modules.job_scraper import search_jobs_for_resume, scrape_job_from_url, is_valid_url
from modules.match_engine import analyze_resume_job_match, rank_jobs_for_candidate

load_dotenv()

st.set_page_config(
    page_title="AI Job & Internship Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0B0F19; font-family: 'Inter', system-ui, sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
        border-radius: 16px; padding: 26px; margin-bottom: 22px;
        border: 1px solid rgba(99,102,241,0.25);
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
    }
    .main-header h1 { color:#FFF!important; font-size:2rem!important; font-weight:800!important; margin:0!important; }
    .main-header p  { color:#C7D2FE!important; font-size:1rem!important; margin-top:6px!important; }

    .metric-card { background:#131C31; border-radius:14px; padding:18px; border:1px solid #1E293B; text-align:center; }
    .metric-value { font-size:2.2rem; font-weight:800; background:linear-gradient(135deg,#38BDF8,#818CF8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
    .metric-label { font-size:.85rem; color:#94A3B8; font-weight:600; text-transform:uppercase; letter-spacing:.08em; }

    .job-card { background:#131C31; border-radius:14px; padding:20px; border:1px solid #1E293B; margin-bottom:14px; }
    .job-title-t { color:#F8FAFC; font-size:1.2rem; font-weight:700; }
    .job-co { color:#38BDF8; font-weight:600; font-size:.9rem; margin-top:2px; }
    .score-badge { background:linear-gradient(135deg,#059669,#10B981); color:#FFF; padding:6px 14px; border-radius:20px; font-weight:800; font-size:1rem; white-space:nowrap; }
    .src-badge { background:#1E293B; color:#94A3B8; padding:3px 9px; border-radius:10px; font-size:.75rem; font-weight:600; }

    .chip-ok   { display:inline-block; background:rgba(16,185,129,.15); color:#34D399; border:1px solid rgba(16,185,129,.3); padding:4px 10px; margin:3px; border-radius:16px; font-size:.8rem; font-weight:600; }
    .chip-no   { display:inline-block; background:rgba(239,68,68,.15); color:#F87171; border:1px solid rgba(239,68,68,.3); padding:4px 10px; margin:3px; border-radius:16px; font-size:.8rem; font-weight:600; }
    .chip-role { display:inline-block; background:rgba(99,102,241,.15); color:#A5B4FC; border:1px solid rgba(99,102,241,.3); padding:4px 12px; margin:3px; border-radius:16px; font-size:.8rem; font-weight:600; }

    [data-testid="stSidebar"] { background-color:#0F172A; border-right:1px solid #1E293B; }
</style>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────────────────────────────
for k, v in {
    "resume_data": None, "resume_raw_text": "", "selected_job": None,
    "job_results": [], "match_result": None, "url_scrape_msg": None
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def do_parse_and_search(raw_text: str):
    """Parse resume then immediately fetch matched jobs & auto-select first result."""
    st.session_state.resume_data = parse_resume_with_gemini(raw_text)
    st.session_state.match_result = None
    with st.spinner("Finding India-eligible jobs/internships matched to your resume…"):
        raw_jobs = search_jobs_for_resume(st.session_state.resume_data)
        r_data = st.session_state.resume_data
        if raw_jobs and r_data:
            st.session_state.job_results = rank_jobs_for_candidate(r_data, raw_jobs)
        else:
            st.session_state.job_results = raw_jobs
        # Auto-select top job so Tab 3 & 4 are immediately usable
        if st.session_state.job_results:
            st.session_state.selected_job = st.session_state.job_results[0]


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/artificial-intelligence.png", width=55)
    st.markdown("### **AI Job Matcher**")
    st.caption("Resume-aware Indian job/internship search")
    st.markdown("---")
    st.markdown("⚡ **Quick Demo Sandbox**")
    st.caption("Load a sample candidate profile and auto-search jobs:")
    if st.button("🚀 Load Sample Resume", use_container_width=True):
        sample = """
HARSHITA SHARMA  — Generative AI & ML Intern Candidate
Email: harshita@example.com | GitHub: github.com/harshita-ai | Location: Bengaluru, India

SUMMARY: B.Tech Computer Science undergraduate (2022-2026) specialising in Machine Learning,
Generative AI, LLMs, RAG pipelines, and Python development. Seeking ML / AI Intern role in India.

TECHNICAL SKILLS: Python, Machine Learning, PyTorch, TensorFlow, Scikit-learn, Pandas, NumPy,
NLP, LangChain, Gemini API, RAG, ChromaDB, Streamlit, FastAPI, Git, Linux, REST APIs

PROJECTS:
- AI Resume Matcher & Job Scraper using Streamlit + Gemini API
- RAG Document Q&A System using ChromaDB vector database

EDUCATION: B.Tech CSE (2022-2026) | GPA 8.8 / 10.0
"""
        st.session_state.resume_raw_text = sample.strip()
        with st.spinner("Parsing resume and searching India jobs…"):
            do_parse_and_search(sample)
        st.toast("Loaded! Jobs auto-fetched in Tab 2.", icon="🎉")
    st.markdown("---")
    st.caption("🏆 Generative AI Build Sprint MVP")


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🎯 AI Job & Internship Matcher — India</h1>
  <p>Upload your resume → we auto-detect your level → fetch real India-eligible jobs matched to your skills.</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "📄 1. Candidate Resume",
    "🔍 2. Matched Job Listings",
    "📊 3. Match & Gap Matrix",
    "✍️ 4. Resume Optimizer & Cover Letter"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RESUME
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("### **Upload Your Resume**")
        uploaded = st.file_uploader("PDF / DOCX / TXT", type=["pdf", "docx", "txt"])
        if uploaded:
            file_bytes = uploaded.read()
            raw = extract_text_from_file(file_bytes, uploaded.name)
            st.session_state.resume_raw_text = raw
            if st.button("✨ Parse & Find Jobs", type="primary", use_container_width=True):
                with st.spinner("Parsing resume and searching matched India jobs…"):
                    do_parse_and_search(raw)
                st.toast("Done! Check Tab 2 for your matched jobs.", icon="✅")

        st.markdown("**— or paste resume text below —**")
        pasted = st.text_area("Resume Text", value=st.session_state.resume_raw_text, height=250,
                               placeholder="Paste raw text from your resume here…")
        if st.button("✨ Parse & Find Jobs", key="parse_paste", use_container_width=True):
            if pasted.strip():
                st.session_state.resume_raw_text = pasted
                with st.spinner("Parsing resume and searching matched India jobs…"):
                    do_parse_and_search(pasted)
                st.toast("Done! Check Tab 2 for your matched jobs.", icon="✅")
            else:
                st.warning("Please paste your resume text first.")

    with c2:
        st.markdown("### **Extracted Profile**")
        if st.session_state.resume_data:
            r = st.session_state.resume_data
            st.markdown(f"#### **{r.get('candidate_name', 'Candidate')}**")
            st.markdown(f"🎓 **Level:** `{r.get('experience_level', 'Internship / Fresher')}` | 📧 `{r.get('email', 'N/A')}`")
            st.caption(f"🎓 {r.get('education', 'N/A')}")
            st.info(r.get("summary", ""))

            st.markdown("**Technical Skills:**")
            t_html = "".join(f'<span class="chip-ok">{s}</span>' for s in r.get("technical_skills", []))
            st.markdown(t_html or "*None detected*", unsafe_allow_html=True)

            st.markdown("<br>**Suitable Roles:**", unsafe_allow_html=True)
            r_html = "".join(f'<span class="chip-role">💡 {role}</span>' for role in r.get("suitable_roles", []))
            st.markdown(r_html or "*General tech roles*", unsafe_allow_html=True)
        else:
            st.info("👈 Upload / paste your resume and click **Parse & Find Jobs** to begin.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MATCHED JOB LISTINGS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.resume_data:
        st.warning("⚠️ Please parse your resume in Tab 1 first — jobs are auto-fetched based on your profile.")
    else:
        r = st.session_state.resume_data
        level = r.get("experience_level", "Internship / Fresher")
        skills = r.get("technical_skills", [])

        st.markdown(f"### Matched Opportunities for **{r.get('candidate_name', 'Candidate')}**")
        st.caption(f"Level: `{level}` | Skills: {', '.join(skills[:5])}")

        # Refresh button
        if st.button("🔄 Refresh Job Listings", use_container_width=False):
            with st.spinner("Re-fetching latest India-eligible jobs matched to your resume…"):
                raw_jobs = search_jobs_for_resume(r)
                st.session_state.job_results = rank_jobs_for_candidate(r, raw_jobs) if raw_jobs else []
                if st.session_state.job_results:
                    st.session_state.selected_job = st.session_state.job_results[0]
                st.session_state.match_result = None

        st.markdown("---")

        # ── URL / Paste section ────────────────────────────────────────────────
        with st.expander("🌐 Analyze a Specific Job Posting (URL or Paste)", expanded=bool(st.session_state.url_scrape_msg)):
            url_in = st.text_input("Job Posting URL (LinkedIn, Naukri, Internshala, company career page…)")
            if st.button("Fetch Job from URL"):
                if url_in:
                    with st.spinner("Fetching job posting…"):
                        res = scrape_job_from_url(url_in)
                        if res.get("status") in ["blocked", "error"]:
                            st.session_state.url_scrape_msg = res.get("message")
                        else:
                            st.session_state.selected_job = res
                            st.session_state.url_scrape_msg = None
                            st.success(f"Selected: {res['title']}")
                else:
                    st.session_state.url_scrape_msg = "Please enter a URL."
            if st.session_state.url_scrape_msg:
                st.warning(f"⚠️ {st.session_state.url_scrape_msg}")

            paste_jd = st.text_area("— or Paste Job Description Text —", height=130,
                                     placeholder="Paste the full job description text here…")
            if st.button("Set Pasted JD as Target Job"):
                if paste_jd.strip():
                    st.session_state.selected_job = {
                        "id": "custom_jd", "title": "Pasted Job Description",
                        "company": "Target Employer", "location": "India",
                        "url": "#", "application_url": "",
                        "source": "Pasted by User", "posted_date": "Today",
                        "description": paste_jd, "required_skills": []
                    }
                    st.session_state.url_scrape_msg = None
                    st.success("Target job set! Go to Tab 3 to run match analysis.")

        # ── Job Cards ──────────────────────────────────────────────────────────
        results = st.session_state.job_results
        if results:
            selected_id = st.session_state.selected_job.get("id") if st.session_state.selected_job else None
            st.markdown(f"#### Found **{len(results)}** India-Eligible Opportunities Matched to Your Resume")

            for idx, j in enumerate(results):
                score = j.get("match_score", 75)
                app_url = j.get("application_url", "")
                selected_mark = " ← **Currently Selected**" if j["id"] == selected_id else ""

                st.markdown(f"""
                <div class="job-card">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                    <div>
                      <div class="job-title-t">{j['title']}</div>
                      <div class="job-co">🏢 {j['company']} &nbsp;•&nbsp; 📍 {j['location']} &nbsp;
                        <span class="src-badge">Source: {j['source']}</span>
                      </div>
                    </div>
                    <div class="score-badge">Match: {score}%</div>
                  </div>
                  <p style="color:#94A3B8;font-size:.9rem;margin:12px 0 8px;">{j['description'][:260]}…</p>
                </div>
                """, unsafe_allow_html=True)

                matched = j.get("matching_skills", [])
                missing = j.get("missing_skills", [])
                why = j.get("why_matches", "Skills in your resume align with this role.")
                if matched:
                    st.markdown("✅ " + " ".join(f'<span class="chip-ok">✓ {s}</span>' for s in matched[:6]),
                                unsafe_allow_html=True)
                if missing:
                    st.markdown("⚠️ " + " ".join(f'<span class="chip-no">✗ {s}</span>' for s in missing[:4]),
                                unsafe_allow_html=True)
                st.caption(f"💡 {why}")

                btn_col1, btn_col2 = st.columns([1, 1])
                with btn_col1:
                    if is_valid_url(app_url):
                        st.link_button("Apply Now →", app_url, use_container_width=True, type="primary")
                    else:
                        st.caption("Application link unavailable.")
                with btn_col2:
                    label = "✅ Selected" if j["id"] == selected_id else "🎯 Select for Analysis"
                    if st.button(label, key=f"sel_{idx}_{j['id']}", use_container_width=True):
                        st.session_state.selected_job = j
                        st.session_state.match_result = None
                        st.toast(f"Selected: {j['title']}", icon="🎯")

                st.markdown("<hr style='border-color:#1E293B;margin:10px 0 20px;'>", unsafe_allow_html=True)

            if st.session_state.selected_job:
                sel = st.session_state.selected_job
                st.success(f"📌 **Selected Job:** {sel['title']} at **{sel['company']}** — go to Tab 3 to run match analysis.")
        else:
            st.warning("⚠️ No matching jobs found right now. Try refreshing or paste a job description manually above.")
            st.info("💡 Make sure you've parsed your resume in Tab 1 first.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — MATCH & GAP MATRIX
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### **AI Match & Skill Gap Analysis**")
    if not st.session_state.resume_data:
        st.warning("⚠️ Parse your resume in Tab 1 first.")
    elif not st.session_state.selected_job:
        st.warning("⚠️ Select a job in Tab 2 first (top job is auto-selected after parsing).")
    else:
        c_res = st.session_state.resume_data
        c_job = st.session_state.selected_job
        st.markdown(f"**Candidate:** `{c_res.get('candidate_name','Candidate')}` ⚡ **Role:** `{c_job['title']} @ {c_job['company']}`")

        if st.button("🚀 Run AI Match Analysis", type="primary", use_container_width=True):
            with st.spinner("Analysing semantic fit, skill overlap and missing keywords…"):
                st.session_state.match_result = analyze_resume_job_match(
                    c_res, c_job["title"], c_job["description"]
                )
            st.toast("Analysis complete!", icon="🎉")

        if st.session_state.match_result:
            m = st.session_state.match_result

            ch_col, me_col = st.columns([1.3, 2])
            with ch_col:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=m.get("overall_score", 80),
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Match Score", "font": {"size": 18, "color": "#F8FAFC"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#94A3B8"},
                        "bar": {"color": "#6366F1"}, "bgcolor": "#131C31",
                        "borderwidth": 2, "bordercolor": "#1E293B",
                        "steps": [
                            {"range": [0, 50], "color": "#7F1D1D"},
                            {"range": [50, 75], "color": "#D97706"},
                            {"range": [75, 100], "color": "#059669"}
                        ]
                    }
                ))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font={"color": "#F8FAFC"}, height=260, margin=dict(l=20,r=20,t=40,b=20))
                st.plotly_chart(fig, use_container_width=True)

            with me_col:
                st.markdown("<br>", unsafe_allow_html=True)
                mc1, mc2, mc3 = st.columns(3)
                for col, val, lbl in [
                    (mc1, m.get("technical_score", 85), "Technical Fit"),
                    (mc2, m.get("soft_skills_score", 80), "Soft Skills"),
                    (mc3, m.get("experience_relevance_score", 88), "Level Alignment"),
                ]:
                    col.markdown(f"""<div class="metric-card"><div class="metric-value">{val}%</div><div class="metric-label">{lbl}</div></div>""", unsafe_allow_html=True)

            st.markdown("---")
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("#### ✅ Matching Skills")
                matched = m.get("matching_skills", [])
                st.markdown("".join(f'<span class="chip-ok">✓ {s}</span>' for s in matched) or "*None detected*", unsafe_allow_html=True)
                st.markdown("<br><b>Strengths:</b>", unsafe_allow_html=True)
                for s in m.get("key_strengths", []):
                    st.markdown(f"- 🟢 {s}")
            with g2:
                st.markdown("#### ⚠️ Missing Skills / Gaps")
                missing = m.get("missing_skills", [])
                st.markdown("".join(f'<span class="chip-no">✗ {s}</span>' for s in missing) or "*No major gaps!*", unsafe_allow_html=True)
                st.markdown("<br><b>Action Items:</b>", unsafe_allow_html=True)
                for imp in m.get("improvement_areas", []):
                    st.markdown(f"- 🟠 {imp}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — RESUME OPTIMIZER & COVER LETTER
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### **AI Resume Optimizer & Cover Letter**")
    if not st.session_state.match_result:
        if st.session_state.selected_job and st.session_state.resume_data:
            st.info("💡 Go to **Tab 3** and click **Run AI Match Analysis** to generate personalized bullets and cover letter.")
        else:
            st.info("💡 Parse your resume in Tab 1, then run Match Analysis in Tab 3 to unlock this tab.")
    else:
        m = st.session_state.match_result
        c_job = st.session_state.selected_job
        o1, o2 = st.columns(2)

        with o1:
            st.markdown("#### 📄 Tailored Resume Bullets")
            st.caption("Add these AI-optimized bullets to your experience section:")
            for b in m.get("tailored_resume_bullets", []):
                st.text_area("Bullet", value=f"• {b}", height=70, label_visibility="collapsed")
            st.download_button("📥 Download (.txt)", "\n".join(f"• {b}" for b in m.get("tailored_resume_bullets", [])),
                               file_name="resume_bullets.txt", mime="text/plain")

        with o2:
            st.markdown("#### ✉️ Cover Letter")
            cl = st.text_area("Edit your cover letter:", value=m.get("cover_letter", ""), height=340)
            company_slug = (c_job.get("company") or "company").lower().replace(" ", "_")
            st.download_button("📥 Download (.txt)", cl,
                               file_name=f"cover_letter_{company_slug}.txt", mime="text/plain")
