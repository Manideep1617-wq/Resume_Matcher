import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
from dotenv import load_dotenv

# Import internal modules
from modules.resume_parser import extract_text_from_file, parse_resume_with_gemini, fallback_parse_resume
from modules.job_scraper import search_live_jobs, scrape_job_from_url, DEMO_JOBS
from modules.match_engine import analyze_resume_job_match

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AI Job Scraper & Resume Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Styling
st.markdown("""
<style>
    /* Metric Cards */
    .metric-card {
        background-color: #1E293B;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #334155;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #38BDF8;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Skill Badges */
    .skill-badge-match {
        display: inline-block;
        background-color: #065F46;
        color: #34D399;
        border: 1px solid #059669;
        padding: 4px 10px;
        margin: 3px;
        border-radius: 20px;
        font-weight: 500;
        font-size: 0.85rem;
    }
    .skill-badge-missing {
        display: inline-block;
        background-color: #7F1D1D;
        color: #FCA5A5;
        border: 1px solid #DC2626;
        padding: 4px 10px;
        margin: 3px;
        border-radius: 20px;
        font-weight: 500;
        font-size: 0.85rem;
    }
    
    /* Section Container */
    .content-box {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #334155;
        margin-bottom: 20px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #F8FAFC !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if "resume_data" not in st.session_state:
    st.session_state.resume_data = None
if "resume_raw_text" not in st.session_state:
    st.session_state.resume_raw_text = ""
if "selected_job" not in st.session_state:
    st.session_state.selected_job = DEMO_JOBS[0]
if "match_result" not in st.session_state:
    st.session_state.match_result = None

# Sidebar Setup
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/artificial-intelligence.png", width=70)
    st.title("Settings & Config")
    
    # API Key Configuration
    default_key = os.getenv("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=default_key,
        type="password",
        help="Paste your Gemini API key here or leave default if configured in environment."
    )
    api_key = api_key_input.strip() if api_key_input else default_key
    
    if api_key:
        st.success("✅ Gemini API Connected", icon="🔑")
    else:
        st.info("ℹ️ Running in Smart Fallback Mode (Rule-based matching active).", icon="💡")

    st.markdown("---")
    st.subheader("⚡ Quick Demo Loader")
    st.write("Test the app immediately with sample data:")
    if st.button("🚀 Load Sample Resume & Job"):
        sample_resume_text = """
HARSHITA SHARMA
Generative AI Developer & Software Engineer
Email: harshita@example.com | Phone: +91 9876543210 | GitHub: github.com/harshita-ai

PROFESSIONAL SUMMARY:
Proactive Software Engineer specializing in Generative AI, Large Language Models (LLMs), RAG systems, and Full Stack Python development. Passionate about building autonomous AI agents and interactive web solutions.

TECHNICAL SKILLS:
- Languages: Python, JavaScript, SQL, C++
- AI/ML & LLM: Google Gemini API, LangChain, OpenAI, RAG, Vector Databases (ChromaDB), Hugging Face
- Frameworks: Streamlit, FastAPI, Flask, React
- Tools & Cloud: Git, Docker, REST APIs, Linux, AWS

WORK EXPERIENCE:
AI Developer Intern | Tech Innovations (2025 - Present)
- Developed an interactive Resume Matcher and Job Scraper web application using Streamlit and Gemini API.
- Implemented Retrieval-Augmented Generation (RAG) pipelines for semantic search over unstructured PDFs.
- Optimized API latency by 35% through smart caching and batch processing.

EDUCATION:
Bachelor of Technology in Computer Science & Engineering (2022 - 2026)
GPA: 8.8 / 10.0
"""
        st.session_state.resume_raw_text = sample_resume_text.strip()
        with st.spinner("Parsing sample resume..."):
            st.session_state.resume_data = parse_resume_with_gemini(sample_resume_text, api_key)
        st.session_state.selected_job = DEMO_JOBS[0]
        st.session_state.match_result = None
        st.toast("Sample Resume & Job loaded successfully!", icon="🎉")

    st.markdown("---")
    st.caption("🏆 Built for Build Sprint MVP Submission")

# App Main Header
st.title("🎯 AI Job Scraper & Resume Matcher")
st.markdown("#### *Smart Resume Parsing • Live Job Scraping • AI Match Analysis • Cover Letter Generator*")
st.markdown("---")

# Main Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📄 1. Resume Parser",
    "🔍 2. Job Scraper & Search",
    "🎯 3. Match & Gap Analysis",
    "📝 4. Tailor & Cover Letter"
])

# ==========================================
# TAB 1: RESUME PARSER
# ==========================================
with tab1:
    st.subheader("Upload or Paste Candidate Resume")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            help="Upload your latest resume document"
        )
        
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            raw_text = extract_text_from_file(file_bytes, uploaded_file.name)
            st.session_state.resume_raw_text = raw_text
            
            if st.button("✨ Parse Uploaded Resume", type="primary"):
                with st.spinner("Extracting profile details using AI..."):
                    st.session_state.resume_data = parse_resume_with_gemini(raw_text, api_key)
                    st.toast("Resume parsed successfully!", icon="✅")
                    
        st.markdown("**Or Paste Raw Resume Text:**")
        pasted_text = st.text_area(
            "Resume Text",
            value=st.session_state.resume_raw_text,
            height=220,
            placeholder="Paste raw text from resume here..."
        )
        if st.button("✨ Parse Pasted Text"):
            if pasted_text.strip():
                st.session_state.resume_raw_text = pasted_text
                with st.spinner("Parsing resume text..."):
                    st.session_state.resume_data = parse_resume_with_gemini(pasted_text, api_key)
                    st.toast("Resume parsed successfully!", icon="✅")
            else:
                st.warning("Please paste resume text first.")

    with col2:
        st.subheader("Extracted Candidate Profile")
        if st.session_state.resume_data:
            r_data = st.session_state.resume_data
            
            st.markdown(f"### **{r_data.get('candidate_name', 'Candidate Profile')}**")
            st.markdown(f"📧 **Email:** {r_data.get('email', 'N/A')} | 📞 **Phone:** {r_data.get('phone', 'N/A')}")
            st.markdown(f"🎓 **Education:** {r_data.get('education', 'N/A')}")
            st.markdown(f"⏳ **Experience:** {r_data.get('experience_years', 'N/A')}")
            
            st.markdown("#### **Summary:**")
            st.info(r_data.get('summary', 'No summary available.'))
            
            st.markdown("#### **Technical Skills:**")
            tech_skills = r_data.get("technical_skills", [])
            badges_html = "".join([f'<span class="skill-badge-match">{s}</span>' for s in tech_skills])
            st.markdown(badges_html if badges_html else "*No technical skills detected*", unsafe_allow_html=True)
            
            st.markdown("#### **Soft Skills:**")
            soft_skills = r_data.get("soft_skills", [])
            soft_html = "".join([f'<span class="skill-badge-match">{s}</span>' for s in soft_skills])
            st.markdown(soft_html if soft_html else "*No soft skills detected*", unsafe_allow_html=True)
        else:
            st.info("👈 Upload or paste a resume on the left, or click 'Load Sample Resume & Job' in the sidebar to begin.")

# ==========================================
# TAB 2: JOB SCRAPER & SEARCH
# ==========================================
with tab2:
    st.subheader("Scrape & Search Live Job Postings")
    
    search_col1, search_col2, search_col3 = st.columns([2, 2, 1])
    with search_col1:
        job_query = st.text_input("Job Title / Role", value="Generative AI Developer")
    with search_col2:
        job_location = st.text_input("Location", value="Remote")
    with search_col3:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 Search Jobs", use_container_width=True, type="primary")
        
    st.markdown("---")
    
    # Custom Job URL Scraper section
    with st.expander("🌐 Option: Scrape directly from Job Posting URL or Raw Text"):
        url_input = st.text_input("Paste Job Posting URL (e.g. Indeed, LinkedIn, Glassdoor page)")
        if st.button("Scrape Job from URL"):
            if url_input:
                with st.spinner("Scraping webpage content..."):
                    scraped_job = scrape_job_from_url(url_input)
                    st.session_state.selected_job = scraped_job
                    st.success(f"Scraped job: {scraped_job['title']}")
            else:
                st.warning("Please enter a valid URL.")
                
        custom_desc = st.text_area("Or Paste Target Job Description Text", height=150)
        if st.button("Set as Target Job Description"):
            if custom_desc:
                st.session_state.selected_job = {
                    "id": "custom_pasted",
                    "title": "Custom Target Job",
                    "company": "Target Employer",
                    "location": "Custom",
                    "url": "#",
                    "posted_date": "Today",
                    "description": custom_desc,
                    "required_skills": []
                }
                st.success("Target job description set successfully!")

    # Display Search Results / Available Jobs
    if search_btn or "job_results" not in st.session_state:
        with st.spinner(f"Scraping live job listings for '{job_query}'..."):
            st.session_state.job_results = search_live_jobs(job_query, job_location)

    jobs_list = st.session_state.get("job_results", DEMO_JOBS)
    
    st.markdown(f"### Found {len(jobs_list)} Job Opportunities")
    
    for idx, j in enumerate(jobs_list):
        with st.container():
            col_info, col_act = st.columns([4, 1])
            with col_info:
                st.markdown(f"#### **{j['title']}** — *{j['company']}* ({j['location']})")
                st.caption(f"📅 Posted: {j['posted_date']} | 🔗 [View Job Source]({j['url']})")
                st.text(j['description'][:280] + "...")
            with col_act:
                st.write("")
                if st.button(f"🎯 Select Job", key=f"select_job_{idx}_{j['id']}", use_container_width=True):
                    st.session_state.selected_job = j
                    st.toast(f"Selected: {j['title']}", icon="🎯")
            st.markdown("---")

    # Display Selected Target Job Box
    if st.session_state.selected_job:
        sel = st.session_state.selected_job
        st.info(f"📌 **Currently Selected Target Job:** {sel['title']} at {sel['company']}")

# ==========================================
# TAB 3: MATCH & GAP ANALYSIS
# ==========================================
with tab3:
    st.subheader("AI Match & Skill Gap Analysis Dashboard")
    
    if not st.session_state.resume_data:
        st.warning("⚠️ Please parse a resume in Tab 1 first or click 'Load Sample Resume & Job' in the sidebar.")
    elif not st.session_state.selected_job:
        st.warning("⚠️ Please select a target job in Tab 2.")
    else:
        current_job = st.session_state.selected_job
        current_resume = st.session_state.resume_data
        
        st.markdown(f"**Comparing Candidate:** `{current_resume.get('candidate_name', 'Candidate')}` ⚡ **Target Role:** `{current_job['title']} ({current_job['company']})`")
        
        if st.button("🚀 Run AI Semantic Match Analysis", type="primary", use_container_width=True):
            with st.spinner("Analyzing skill overlap, semantic fit, and missing keywords using AI..."):
                match_res = analyze_resume_job_match(
                    current_resume,
                    current_job['title'],
                    current_job['description'],
                    api_key
                )
                st.session_state.match_result = match_res
                st.toast("Analysis Complete!", icon="🎉")

        if st.session_state.match_result:
            res = st.session_state.match_result
            
            # Overview Metrics & Plotly Gauge Chart
            score_col1, score_col2 = st.columns([1.2, 2])
            
            with score_col1:
                # Plotly Gauge Chart
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=res.get("overall_score", 75),
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Overall Match Score", 'font': {'size': 20, 'color': "#F8FAFC"}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
                        'bar': {'color': "#4F46E5"},
                        'bgcolor': "#1E293B",
                        'borderwidth': 2,
                        'bordercolor': "#334155",
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
                    height=280,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

            with score_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{res.get('technical_score', 80)}%</div>
                        <div class="metric-label">Technical Match</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m_col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{res.get('soft_skills_score', 85)}%</div>
                        <div class="metric-label">Soft Skills</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m_col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{res.get('experience_relevance_score', 78)}%</div>
                        <div class="metric-label">Domain Relevance</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            
            # Skills Breakdown
            skills_col1, skills_col2 = st.columns(2)
            with skills_col1:
                st.markdown("### ✅ Matching Skills & Strengths")
                matching = res.get("matching_skills", [])
                match_html = "".join([f'<span class="skill-badge-match">✓ {s}</span>' for s in matching])
                st.markdown(match_html if match_html else "None identified", unsafe_allow_html=True)
                
                st.markdown("<br><b>Key Strengths:</b>", unsafe_allow_html=True)
                for s in res.get("key_strengths", []):
                    st.markdown(f"- 🟢 {s}")

            with skills_col2:
                st.markdown("### ⚠️ Skill Gaps & Missing Keywords")
                missing = res.get("missing_skills", [])
                missing_html = "".join([f'<span class="skill-badge-missing">✗ {s}</span>' for s in missing])
                st.markdown(missing_html if missing_html else "No major skill gaps!", unsafe_allow_html=True)
                
                st.markdown("<br><b>Improvement Recommendations:</b>", unsafe_allow_html=True)
                for area in res.get("improvement_areas", []):
                    st.markdown(f"- 🟠 {area}")

# ==========================================
# TAB 4: RESUME OPTIMIZER & COVER LETTER
# ==========================================
with tab4:
    st.subheader("AI Resume Optimization & Tailored Cover Letter")
    
    if not st.session_state.match_result:
        st.info("💡 Run the AI Semantic Match Analysis in Tab 3 first to generate tailored suggestions and cover letters.")
    else:
        res = st.session_state.match_result
        current_job = st.session_state.selected_job
        current_resume = st.session_state.resume_data
        
        col_res, col_let = st.columns(2)
        
        with col_res:
            st.markdown("### 📄 Tailored Resume Bullets")
            st.write("Incorporate these AI-optimized bullet points into your resume experience section:")
            
            bullets = res.get("tailored_resume_bullets", [])
            for b in bullets:
                st.text_area("Bullet Point", value=f"• {b}", height=75)
                
            st.download_button(
                "📥 Download Resume Suggestions (.txt)",
                data="\n".join([f"• {b}" for b in bullets]),
                file_name="tailored_resume_bullets.txt",
                mime="text/plain"
            )

        with col_let:
            st.markdown("### ✉️ Customized Cover Letter")
            cover_letter_text = st.text_area(
                "Edit your generated cover letter:",
                value=res.get("cover_letter", "Cover letter text will appear here."),
                height=350
            )
            
            st.download_button(
                "📥 Download Cover Letter (.txt)",
                data=cover_letter_text,
                file_name=f"cover_letter_{current_job.get('company', 'company').lower().replace(' ', '_')}.txt",
                mime="text/plain"
            )
