import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
from dotenv import load_dotenv

# Import internal modules
from modules.resume_parser import extract_text_from_file, parse_resume_with_gemini, fallback_parse_resume
from modules.job_scraper import search_live_jobs, scrape_job_from_url
from modules.match_engine import analyze_resume_job_match

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AI Job Scraper & Resume Matcher",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Modern CSS Styling
st.markdown("""
<style>
    /* Global Styling */
    .stApp {
        background-color: #0B0F19;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Gradient Banner */
    .main-header {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 25px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .main-header h1 {
        color: #FFFFFF !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        letter-spacing: -0.02em;
    }
    .main-header p {
        color: #C7D2FE !important;
        font-size: 1.05rem !important;
        margin-top: 6px !important;
        margin-bottom: 0 !important;
    }

    /* Metric Cards */
    .metric-card {
        background: #131C31;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #1E293B;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: transform 0.2s ease;
    }
    .metric-value {
        font-size: 2.4rem;
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
        margin-top: 4px;
    }
    
    /* Dynamic Skill Tags */
    .skill-chip-match {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.12);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 6px 14px;
        margin: 4px;
        border-radius: 24px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .skill-chip-gap {
        display: inline-flex;
        align-items: center;
        background: rgba(239, 68, 68, 0.12);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 6px 14px;
        margin: 4px;
        border-radius: 24px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .skill-chip-neutral {
        display: inline-flex;
        align-items: center;
        background: rgba(99, 102, 241, 0.12);
        color: #A5B4FC;
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 6px 14px;
        margin: 4px;
        border-radius: 24px;
        font-weight: 500;
        font-size: 0.85rem;
    }

    /* Job Card Container */
    .job-card {
        background: #131C31;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #1E293B;
        margin-bottom: 16px;
    }
    .job-title {
        color: #F8FAFC;
        font-size: 1.2rem;
        font-weight: 700;
    }
    .job-company {
        color: #38BDF8;
        font-weight: 600;
        font-size: 0.95rem;
    }

    /* Sidebar Clean styling */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
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

# Sidebar Setup (Clean, minimal, no manual key input)
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/artificial-intelligence.png", width=60)
    st.markdown("### **AI Resume Matcher**")
    st.caption("Real-world job search & instant match engine")
    
    st.markdown("---")
    st.markdown("#### ⚡ **Quick Demo Sandbox**")
    st.write("Load sample candidate resume and target role with 1 click:")
    
    if st.button("🚀 Load Sample Candidate", use_container_width=True):
        sample_resume_text = """
HARSHITA SHARMA
Generative AI Engineer & Full Stack Developer
Email: harshita.ai@example.com | GitHub: github.com/harshita-ai | Location: Remote / Bengaluru

SUMMARY:
Results-driven AI Developer specializing in Generative AI, Large Language Models (LLMs), RAG pipelines, and Full Stack Python application development. Proven track record building production-grade web interfaces and deploying microservices.

TECHNICAL SKILLS:
- Languages: Python, JavaScript, TypeScript, SQL, HTML/CSS
- Generative AI & ML: Google Gemini API, OpenAI, LangChain, RAG, ChromaDB, Hugging Face Transformers, PyTorch
- Web & Backend: Streamlit, FastAPI, Flask, React, REST APIs
- DevOps & Tools: Docker, Git, Linux, PostgreSQL, AWS

WORK EXPERIENCE:
AI Engineer Intern | Tech Innovations Inc. (2025 - Present)
- Architected an AI-powered Resume Matcher & Job Scraper application using Streamlit and Gemini LLM.
- Engineered RAG vector search pipelines reducing resume parsing latency by 40%.
- Developed RESTful FastAPI services integrated with PostgreSQL database.

EDUCATION:
B.Tech in Computer Science & Engineering (2022 - 2026) | GPA: 8.8/10
"""
        st.session_state.resume_raw_text = sample_resume_text.strip()
        with st.spinner("Extracting profile details..."):
            st.session_state.resume_data = parse_resume_with_gemini(sample_resume_text)
            # Fetch live jobs matching candidate title
            st.session_state.job_results = search_live_jobs("Generative AI Developer")
            if st.session_state.job_results:
                st.session_state.selected_job = st.session_state.job_results[0]
            st.session_state.match_result = None
        st.toast("Sample Candidate & Live Jobs Loaded!", icon="🎉")

    st.markdown("---")
    st.caption("🏆 Generative AI Build Sprint MVP")

# Top Header Banner
st.markdown("""
<div class="main-header">
    <h1>🎯 AI Job Scraper & Resume Matcher</h1>
    <p>Search active real-world opportunities, analyze skill gap fit, and generate optimized resume content.</p>
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
        st.markdown("### **Upload or Paste Resume**")
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            help="Supported formats: PDF, DOCX, TXT"
        )
        
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            raw_text = extract_text_from_file(file_bytes, uploaded_file.name)
            st.session_state.resume_raw_text = raw_text
            if st.button("✨ Parse Uploaded File", type="primary", use_container_width=True):
                with st.spinner("Extracting profile details using AI..."):
                    st.session_state.resume_data = parse_resume_with_gemini(raw_text)
                    st.toast("Resume parsed successfully!", icon="✅")
                    
        st.markdown("**Or Paste Resume Text:**")
        pasted_text = st.text_area(
            "Raw Resume Text",
            value=st.session_state.resume_raw_text,
            height=260,
            placeholder="Paste text from candidate resume..."
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
            st.caption(f"📧 {r.get('email', 'N/A')} | 📞 {r.get('phone', 'N/A')} | 🎓 {r.get('education', 'N/A')}")
            
            st.markdown("**Professional Summary:**")
            st.info(r.get("summary", "No summary text provided."))
            
            st.markdown("**Extracted Technical Skills:**")
            t_skills = r.get("technical_skills", [])
            t_html = "".join([f'<span class="skill-chip-neutral">{s}</span>' for s in t_skills])
            st.markdown(t_html if t_html else "*No technical skills identified*", unsafe_allow_html=True)
            
            st.markdown("<br>**Soft Skills:**", unsafe_allow_html=True)
            s_skills = r.get("soft_skills", [])
            s_html = "".join([f'<span class="skill-chip-neutral">{s}</span>' for s in s_skills])
            st.markdown(s_html if s_html else "*No soft skills identified*", unsafe_allow_html=True)
        else:
            st.info("👈 Upload or paste a resume on the left (or click 'Load Sample Candidate' in the sidebar) to parse candidate profile.")

# ==========================================
# TAB 2: REAL-WORLD JOB SEARCH
# ==========================================
with tab2:
    st.markdown("### **Search Active Real-World Job Postings**")
    
    col_q, col_loc, col_btn = st.columns([2.5, 2, 1.2])
    with col_q:
        job_query = st.text_input("Target Job Title or Technology", value="Generative AI Developer")
    with col_loc:
        job_location = st.text_input("Location Preference", value="Remote")
    with col_btn:
        st.write("")
        st.write("")
        search_trigger = st.button("🔍 Search Jobs", type="primary", use_container_width=True)
        
    st.markdown("---")
    
    with st.expander("🌐 Option: Scrape directly from Job Posting URL or Raw Text"):
        url_in = st.text_input("Paste Job Posting Web URL")
        if st.button("Fetch Job from URL"):
            if url_in:
                with st.spinner("Scraping job post page..."):
                    scraped = scrape_job_from_url(url_in)
                    st.session_state.selected_job = scraped
                    st.success(f"Selected Job: {scraped['title']}")
            else:
                st.warning("Please enter a valid URL.")
                
        raw_job_text = st.text_area("Or Paste Target Job Description Text", height=140)
        if st.button("Set as Target Job"):
            if raw_job_text:
                st.session_state.selected_job = {
                    "id": "custom_job",
                    "title": "Custom Target Role",
                    "company": "Target Company",
                    "location": "Remote",
                    "url": "#",
                    "posted_date": "Today",
                    "description": raw_job_text,
                    "required_skills": []
                }
                st.success("Target job description updated!")

    # Fetch Jobs dynamically
    if search_trigger or not st.session_state.job_results:
        with st.spinner(f"Scraping live active jobs for '{job_query}'..."):
            st.session_state.job_results = search_live_jobs(job_query, job_location)

    results = st.session_state.job_results
    st.markdown(f"#### Found **{len(results)}** Live Active Opportunities")
    
    for idx, j in enumerate(results):
        st.markdown(f"""
        <div class="job-card">
            <div class="job-title">{j['title']}</div>
            <div class="job-company">🏢 {j['company']} • 📍 {j['location']}</div>
            <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 8px;">{j['description'][:280]}...</p>
        </div>
        """, unsafe_allow_html=True)
        
        act_col1, act_col2 = st.columns([4, 1])
        with act_col1:
            st.caption(f"📅 Posted: {j['posted_date']} | 🔗 [Source Listing]({j['url']})")
        with act_col2:
            if st.button("🎯 Select This Job", key=f"job_select_{idx}_{j['id']}", use_container_width=True):
                st.session_state.selected_job = j
                st.toast(f"Selected target role: {j['title']}", icon="🎯")
        st.markdown("<hr style='border-color: #1E293B; margin: 10px 0 20px 0;'>", unsafe_allow_html=True)

    if st.session_state.selected_job:
        sel = st.session_state.selected_job
        st.success(f"📌 **Active Target Job Selected:** {sel['title']} at **{sel['company']}**")

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
        
        if st.button("🚀 Analyze Candidate Match Fit", type="primary", use_container_width=True):
            with st.spinner("Computing semantic fit, skill overlap, and missing gaps..."):
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
                    value=m.get("overall_score", 75),
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
                        <div class="metric-value">{m.get('technical_score', 80)}%</div>
                        <div class="metric-label">Technical Fit</div>
                    </div>
                    """, unsafe_allow_html=True)
                with mc2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{m.get('soft_skills_score', 85)}%</div>
                        <div class="metric-label">Soft Skills</div>
                    </div>
                    """, unsafe_allow_html=True)
                with mc3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{m.get('experience_relevance_score', 78)}%</div>
                        <div class="metric-label">Domain Alignment</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            
            # Dynamic Skills Overlap vs Missing Gaps
            g_col1, g_col2 = st.columns(2)
            
            with g_col1:
                st.markdown("#### ✅ **Matching Skills & Qualifications**")
                matched = m.get("matching_skills", [])
                m_html = "".join([f'<span class="skill-chip-match">✓ {s}</span>' for s in matched])
                st.markdown(m_html if m_html else "*No direct skill matches detected*", unsafe_allow_html=True)
                
                st.markdown("<br><b>Candidate Strengths for this Role:</b>", unsafe_allow_html=True)
                for s in m.get("key_strengths", []):
                    st.markdown(f"- 🟢 {s}")

            with g_col2:
                st.markdown("#### ⚠️ **Missing Skill Gaps & Keywords**")
                missing = m.get("missing_skills", [])
                miss_html = "".join([f'<span class="skill-chip-gap">✗ {s}</span>' for s in missing])
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
