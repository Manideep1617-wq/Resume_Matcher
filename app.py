import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
from dotenv import load_dotenv

# Import internal modules
from modules.resume_parser import extract_text_from_file, parse_resume_with_gemini, fallback_parse_resume
from modules.job_scraper import search_live_jobs, scrape_job_from_url, is_valid_url
from modules.match_engine import analyze_resume_job_match, rank_jobs_for_candidate

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AI Job Scraper & Resume Matcher",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .stApp {
        background-color: #0B0F19;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
        border-radius: 16px;
        padding: 26px;
        margin-bottom: 25px;
        border: 1px solid rgba(99, 102, 241, 0.25);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .main-header h1 {
        color: #FFFFFF !important;
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
    }
    .main-header p {
        color: #C7D2FE !important;
        font-size: 1.0rem !important;
        margin-top: 6px !important;
        margin-bottom: 0 !important;
    }

    /* Metric Cards */
    .metric-card {
        background: #131C31;
        border-radius: 14px;
        padding: 18px;
        border: 1px solid #1E293B;
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38BDF8, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94A3B8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* Job Card Design */
    .job-card {
        background: #131C31;
        border-radius: 14px;
        padding: 22px;
        border: 1px solid #1E293B;
        margin-bottom: 16px;
    }
    .job-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    .job-title-text {
        color: #F8FAFC;
        font-size: 1.25rem;
        font-weight: 700;
    }
    .job-company-text {
        color: #38BDF8;
        font-weight: 600;
        font-size: 0.95rem;
        margin-top: 2px;
    }
    .source-badge {
        display: inline-block;
        background: #1E293B;
        color: #94A3B8;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .score-badge {
        background: linear-gradient(135deg, #059669, #10B981);
        color: #FFFFFF;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.0rem;
    }

    /* Chips */
    .chip-match {
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 10px;
        margin: 3px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .chip-missing {
        display: inline-block;
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 4px 10px;
        margin: 3px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .chip-role {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        color: #A5B4FC;
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 4px 12px;
        margin: 3px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if "resume_data" not in st.session_state:
    st.session_state.resume_data = None
if "resume_raw_text" not in st.session_state:
    st.session_state.resume_raw_text = ""
if "selected_job" not in st.session_state:
    st.session_state.selected_job = None
if "job_results" not in st.session_state:
    st.session_state.job_results = []
if "match_result" not in st.session_state:
    st.session_state.match_result = None
if "url_scrape_status" not in st.session_state:
    st.session_state.url_scrape_status = None

# Sidebar Setup
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/artificial-intelligence.png", width=55)
    st.markdown("### **AI Job Matcher**")
    st.caption("Real-world job search & resume analysis")
    
    st.markdown("---")
    st.markdown("⚡ **Quick Demo Sandbox**")
    st.caption("Test app features with sample candidate resume:")
    
    if st.button("🚀 Load Sample Resume", use_container_width=True):
        sample_resume_text = """
HARSHITA SHARMA
Generative AI & Machine Learning Intern
Email: harshita.ai@example.com | GitHub: github.com/harshita-ai | Location: Remote / India

SUMMARY:
Passionate Computer Science undergraduate specializing in Machine Learning, Generative AI, Large Language Models (LLMs), RAG pipelines, and Python development. Seeking a Machine Learning Intern or AI/ML Intern position.

TECHNICAL SKILLS:
- Languages: Python, SQL, C++, JavaScript
- AI/ML & Data Science: Machine Learning, PyTorch, TensorFlow, Scikit-learn, Pandas, NumPy, OpenCV, Natural Language Processing (NLP)
- Generative AI & LLMs: Google Gemini API, LangChain, RAG, ChromaDB, Hugging Face Transformers, Prompt Engineering
- Tools & Web: Streamlit, FastAPI, Git, Linux, REST APIs

PROJECTS:
- AI Resume Matcher & Job Scraper: Built an interactive web application matching candidate resumes with live job postings using Streamlit and Gemini API.
- RAG Document Q&A System: Implemented semantic search over unstructured PDFs using ChromaDB vector database.

EDUCATION:
Bachelor of Technology in Computer Science & Engineering (2022 - 2026) | GPA: 8.8 / 10.0
"""
        st.session_state.resume_raw_text = sample_resume_text.strip()
        with st.spinner("Extracting profile details..."):
            st.session_state.resume_data = parse_resume_with_gemini(sample_resume_text)
            st.session_state.job_results = []
            st.session_state.selected_job = None
            st.session_state.match_result = None
        st.toast("Sample Resume Loaded!", icon="🎉")

    st.markdown("---")
    st.caption("🏆 Generative AI Build Sprint MVP")

# Main Header Banner
st.markdown("""
<div class="main-header">
    <h1>🎯 Real-World AI Job Scraper & Resume Matcher</h1>
    <p>Upload your resume to discover real job/internship opportunities, rank matching scores, and apply directly.</p>
</div>
""", unsafe_allow_html=True)

# Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📄 1. Candidate Resume",
    "🔍 2. Real-World Job Search",
    "📊 3. Match & Gap Matrix",
    "✍️ 4. Resume Optimizer & Cover Letter"
])

# ==========================================
# TAB 1: CANDIDATE RESUME
# ==========================================
with tab1:
    col_input, col_profile = st.columns([1, 1])
    
    with col_input:
        st.markdown("### **Upload Candidate Resume**")
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            help="Upload your resume document"
        )
        
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            raw_text = extract_text_from_file(file_bytes, uploaded_file.name)
            st.session_state.resume_raw_text = raw_text
            if st.button("✨ Parse Uploaded File", type="primary", use_container_width=True):
                with st.spinner("Extracting candidate profile..."):
                    st.session_state.resume_data = parse_resume_with_gemini(raw_text)
                    st.toast("Resume parsed successfully!", icon="✅")
                    
        st.markdown("**Or Paste Resume Text:**")
        pasted_text = st.text_area(
            "Raw Resume Text",
            value=st.session_state.resume_raw_text,
            height=260,
            placeholder="Paste raw text from candidate resume..."
        )
        if st.button("✨ Parse Pasted Text", use_container_width=True):
            if pasted_text.strip():
                st.session_state.resume_raw_text = pasted_text
                with st.spinner("Analyzing resume content..."):
                    st.session_state.resume_data = parse_resume_with_gemini(pasted_text)
                    st.toast("Profile extracted!", icon="✅")
            else:
                st.warning("Please paste resume text first.")

    with col_profile:
        st.markdown("### **Extracted Candidate Profile**")
        if st.session_state.resume_data:
            r = st.session_state.resume_data
            
            st.markdown(f"#### **{r.get('candidate_name', 'Candidate')}**")
            st.markdown(f"🎓 **Level:** `{r.get('experience_level', 'Internship / Fresher')}` | 📧 `{r.get('email', 'N/A')}`")
            st.caption(f"🎓 **Education:** {r.get('education', 'N/A')}")
            
            st.markdown("**Summary:**")
            st.info(r.get("summary", "No summary text provided."))
            
            st.markdown("**Extracted Technical Skills:**")
            t_skills = r.get("technical_skills", [])
            t_html = "".join([f'<span class="chip-match">{s}</span>' for s in t_skills])
            st.markdown(t_html if t_html else "*No technical skills identified*", unsafe_allow_html=True)
            
            st.markdown("<br>**Recommended Suitable Roles:**", unsafe_allow_html=True)
            roles = r.get("suitable_roles", [])
            r_html = "".join([f'<span class="chip-role">💡 {role}</span>' for role in roles])
            st.markdown(r_html if r_html else "*General entry-level roles*", unsafe_allow_html=True)
        else:
            st.info("👈 Upload or paste a resume on the left (or click 'Load Sample Resume' in the sidebar) to parse candidate profile.")

# ==========================================
# TAB 2: REAL-WORLD JOB SEARCH
# ==========================================
with tab2:
    st.markdown("### **Search Active Real-World Opportunities**")
    
    # Auto-fill query based on resume if available
    default_query = "Machine Learning Intern"
    cand_level = "Internship / Fresher"
    if st.session_state.resume_data:
        cand_level = st.session_state.resume_data.get("experience_level", cand_level)
        s_roles = st.session_state.resume_data.get("suitable_roles", [])
        if s_roles:
            default_query = s_roles[0]

    col_q, col_loc, col_btn = st.columns([2.5, 2, 1.2])
    with col_q:
        job_query = st.text_input("Target Job Title or Technology", value=default_query)
    with col_loc:
        job_location = st.text_input("Location Preference", value="Remote")
    with col_btn:
        st.write("")
        st.write("")
        search_trigger = st.button("🔍 Search Jobs", type="primary", use_container_width=True)

    st.markdown("---")

    # Paste Job URL / LinkedIn section
    with st.expander("🌐 Option: Scrape directly from Job Posting URL or Raw Text", expanded=True if st.session_state.url_scrape_status else False):
        url_in = st.text_input("Paste Job Posting Web URL (e.g. LinkedIn, company career page)")
        if st.button("Fetch Job from URL"):
            if url_in:
                with st.spinner("Scraping webpage content..."):
                    res = scrape_job_from_url(url_in)
                    if res.get("status") in ["blocked", "error"]:
                        st.session_state.url_scrape_status = res.get("message")
                    else:
                        st.session_state.selected_job = res
                        st.session_state.url_scrape_status = None
                        st.success(f"Selected Job: {res['title']}")
            else:
                st.session_state.url_scrape_status = "Please enter a valid URL."
                
        if st.session_state.url_scrape_status:
            st.warning(f"⚠️ {st.session_state.url_scrape_status}")
                
        raw_job_text = st.text_area("Or Paste Target Job Description Text", height=140, placeholder="Paste job description text here...")
        if st.button("Set as Target Job"):
            if raw_job_text.strip():
                st.session_state.selected_job = {
                    "id": "custom_job",
                    "title": job_query or "Target Job Posting",
                    "company": "Target Employer",
                    "location": job_location or "Remote",
                    "url": "#",
                    "application_url": "",
                    "source": "Custom Description",
                    "posted_date": "Today",
                    "description": raw_job_text,
                    "required_skills": []
                }
                st.success("Target job description set successfully!")

    # Fetch Real Jobs
    if search_trigger or (not st.session_state.job_results and st.session_state.resume_data):
        with st.spinner(f"Scraping real-world listings for '{job_query}'..."):
            raw_jobs = search_live_jobs(job_query, job_location, cand_level)
            if st.session_state.resume_data:
                st.session_state.job_results = rank_jobs_for_candidate(st.session_state.resume_data, raw_jobs, job_query)
            else:
                st.session_state.job_results = raw_jobs

    results = st.session_state.job_results
    
    if results:
        st.markdown(f"#### Found **{len(results)}** Verified Real-World Opportunities")
        
        for idx, j in enumerate(results):
            score = j.get("match_score", 85)
            source = j.get("source", "Verified Job API")
            app_url = j.get("application_url", "")
            
            st.markdown(f"""
            <div class="job-card">
                <div class="job-header">
                    <div>
                        <div class="job-title-text">{j['title']}</div>
                        <div class="job-company-text">🏢 {j['company']} • 📍 {j['location']} &nbsp; <span class="source-badge">Source: {source}</span></div>
                    </div>
                    <div class="score-badge">Match Score: {score}%</div>
                </div>
                <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 12px; margin-bottom: 12px;">{j['description'][:280]}...</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Skills breakdown chips
            matched_skills = j.get("matching_skills", [])
            missing_skills = j.get("missing_skills", [])
            why_text = j.get("why_matches", "Relevant to candidate background.")
            
            c_col1, c_col2 = st.columns([3, 1.2])
            with c_col1:
                st.markdown("**Matching Skills:** " + ("".join([f'<span class="chip-match">✓ {s}</span>' for s in matched_skills]) if matched_skills else "*General fit*"), unsafe_allow_html=True)
                if missing_skills:
                    st.markdown("**Missing Skills:** " + "".join([f'<span class="chip-missing">✗ {s}</span>' for s in missing_skills[:4]]), unsafe_allow_html=True)
                st.markdown(f"💡 *Why it matches:* {why_text}")
                
            with c_col2:
                st.write("")
                if is_valid_url(app_url):
                    st.link_button("Apply Now →", app_url, use_container_width=True, type="primary")
                else:
                    st.caption("Application link unavailable.")
                    
                if st.button("🎯 Select for Match Analysis", key=f"sel_job_{idx}_{j['id']}", use_container_width=True):
                    st.session_state.selected_job = j
                    st.toast(f"Selected: {j['title']}", icon="🎯")
                    
            st.markdown("<hr style='border-color: #1E293B; margin: 12px 0 24px 0;'>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ No relevant jobs found. Try a broader job title or different location.")
        st.info("💡 Tip: Upload candidate resume in Tab 1 or click 'Load Sample Resume' in the sidebar to auto-generate candidate-matched searches.")

    if st.session_state.selected_job:
        sel = st.session_state.selected_job
        st.success(f"📌 **Currently Selected Target Job:** {sel['title']} at **{sel['company']}**")

# ==========================================
# TAB 3: MATCH & GAP MATRIX
# ==========================================
with tab3:
    st.markdown("### **AI Match & Skill Gap Analysis Matrix**")
    
    if not st.session_state.resume_data:
        st.warning("⚠️ Please parse a candidate resume in Tab 1 first.")
    elif not st.session_state.selected_job:
        st.warning("⚠️ Please select a target job posting in Tab 2.")
    else:
        c_res = st.session_state.resume_data
        c_job = st.session_state.selected_job
        
        st.markdown(f"Comparing Candidate **`{c_res.get('candidate_name', 'Candidate')}`** ⚡ Target Job **`{c_job['title']} ({c_job['company']})`**")
        
        if st.button("🚀 Run AI Match Analysis", type="primary", use_container_width=True):
            with st.spinner("Analyzing semantic fit, skill overlap, and missing keywords..."):
                m_res = analyze_resume_job_match(c_res, c_job['title'], c_job['description'])
                st.session_state.match_result = m_res
                st.toast("Analysis Complete!", icon="🎉")

        if st.session_state.match_result:
            m = st.session_state.match_result
            
            # Score Gauge & Metric Cards
            chart_col, metrics_col = st.columns([1.3, 2])
            
            with chart_col:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=m.get("overall_score", 85),
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Match Compatibility Score", 'font': {'size': 18, 'color': "#F8FAFC"}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
                        'bar': {'color': "#6366F1"},
                        'bgcolor': "#131C31",
                        'borderwidth': 2,
                        'bordercolor': "#1E293B",
                        'steps': [
                            {'range': [0, 50], 'color': '#7F1D1D'},
                            {'range': [50, 75], 'color': '#D97706'},
                            {'range': [75, 100], 'color': '#059669'}
                        ]
                    }
                ))
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font={'color': "#F8FAFC", 'family': "sans serif"},
                    height=260,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

            with metrics_col:
                st.markdown("<br>", unsafe_allow_html=True)
                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{m.get('technical_score', 85)}%</div>
                        <div class="metric-label">Technical Fit</div>
                    </div>
                    """, unsafe_allow_html=True)
                with mc2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{m.get('soft_skills_score', 80)}%</div>
                        <div class="metric-label">Soft Skills</div>
                    </div>
                    """, unsafe_allow_html=True)
                with mc3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{m.get('experience_relevance_score', 88)}%</div>
                        <div class="metric-label">Level Alignment</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            
            # Skills Overlap vs Missing Gaps
            g_col1, g_col2 = st.columns(2)
            
            with g_col1:
                st.markdown("#### ✅ **Matching Skills & Qualifications**")
                matched = m.get("matching_skills", [])
                m_html = "".join([f'<span class="chip-match">✓ {s}</span>' for s in matched])
                st.markdown(m_html if m_html else "*No direct skill matches detected*", unsafe_allow_html=True)
                
                st.markdown("<br><b>Candidate Strengths for this Role:</b>", unsafe_allow_html=True)
                for s in m.get("key_strengths", []):
                    st.markdown(f"- 🟢 {s}")

            with g_col2:
                st.markdown("#### ⚠️ **Missing Skill Gaps & Keywords**")
                missing = m.get("missing_skills", [])
                miss_html = "".join([f'<span class="chip-missing">✗ {s}</span>' for s in missing])
                st.markdown(miss_html if miss_html else "*No major skill gaps identified!*", unsafe_allow_html=True)
                
                st.markdown("<br><b>Targeted Action Items to Boost Fit:</b>", unsafe_allow_html=True)
                for imp in m.get("improvement_areas", []):
                    st.markdown(f"- 🟠 {imp}")

# ==========================================
# TAB 4: RESUME OPTIMIZER & COVER LETTER
# ==========================================
with tab4:
    st.markdown("### **AI Resume Bullet Optimizer & Customized Cover Letter**")
    
    if not st.session_state.match_result:
        st.info("💡 Run the Match Analysis in Tab 3 first to generate customized resume bullet points and cover letters.")
    else:
        m = st.session_state.match_result
        c_job = st.session_state.selected_job
        
        opt_col1, opt_col2 = st.columns(2)
        
        with opt_col1:
            st.markdown("#### 📄 **Tailored Resume Action Bullets**")
            st.caption("Incorporate these keyword-optimized bullets into your resume experience section:")
            
            bullets = m.get("tailored_resume_bullets", [])
            for b in bullets:
                st.text_area("Action Bullet", value=f"• {b}", height=75)
                
            st.download_button(
                "📥 Download Bullet Suggestions (.txt)",
                data="\n".join([f"• {b}" for b in bullets]),
                file_name="tailored_resume_bullets.txt",
                mime="text/plain"
            )

        with opt_col2:
            st.markdown("#### ✉️ **Customized Cover Letter**")
            cover_letter = st.text_area(
                "Edit your generated cover letter:",
                value=m.get("cover_letter", ""),
                height=340
            )
            
            st.download_button(
                "📥 Download Cover Letter (.txt)",
                data=cover_letter,
                file_name=f"cover_letter_{c_job.get('company', 'company').lower().replace(' ', '_')}.txt",
                mime="text/plain"
            )
