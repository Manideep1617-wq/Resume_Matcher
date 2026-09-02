# 🎯 AI Job Scraper & Resume Matcher MVP

An interactive, AI-powered application built for the **1-Week Build Sprint** (Generative AI Developer Intern role).

This application allows job seekers and candidates to parse resumes (PDF, DOCX, TXT), search and scrape live job postings across web job feeds, compute semantic match scores using Google Gemini AI, identify missing skill gaps, and generate tailored cover letters and resume bullet points.

---

## 🌟 Key Features

1. **📄 Multi-format Resume Parser**
   - Extracts structured details (Candidate Name, Summary, Technical Skills, Soft Skills, Experience, Education) from PDF, DOCX, or plain text using **Google Gemini API** (`gemini-2.5-flash`).
   - Includes a robust NLP regex fallback parser for zero-downtime operation even without an API key.

2. **🔍 Live Job Scraper & Searcher**
   - Real-time searching of remote/active job listings using public job APIs (Remotive API) and BeautifulSoup web scrapers.
   - Paste direct Job Posting URLs to scrape page content automatically.
   - Pre-loaded with realistic demo job listings for instant 1-click evaluation.

3. **🎯 AI Match Engine & Visual Gap Dashboard**
   - Semantic match calculation producing an **Overall Match Score (0 – 100%)** via interactive Plotly gauge charts.
   - Categorized metric breakdown: Technical Match, Soft Skills Fit, and Domain Relevance.
   - Visual badges highlighting **Matching Skills** (Green) vs. **Skill Gaps / Missing Keywords** (Red).

4. **📝 Resume Tailor & Cover Letter Generator**
   - Generates action-oriented, keyword-optimized bullet points tailored for the target job.
   - Auto-generates a personalized 3-paragraph Cover Letter ready to edit, copy, or download.

5. **⚡ Quick Demo Mode**
   - Sidebar 1-click button ("🚀 Load Sample Resume & Job") to test all features instantly without uploading any file.

---

## 📐 Architecture & Workflow

```
┌─────────────────┐       ┌─────────────────┐
│ Candidate Resume│       │  Job Listings   │
│  (PDF / DOCX)   │       │  (Scraped/API)  │
└────────┬────────┘       └────────┬────────┘
         │                         │
         ▼                         ▼
┌───────────────────────────────────────────┐
│     Google Gemini AI Parsing Engine       │
└────────────────────┬──────────────────────┘
                     │
                     ▼
┌───────────────────────────────────────────┐
│     Semantic Match & Skill Gap Engine     │
└────────────────────┬──────────────────────┘
                     │
                     ▼
┌───────────────────────────────────────────┐
│        Streamlit Interactive UI           │
│  - Plotly Match Gauge Score (0-100%)      │
│  - Skill Overlap vs Missing Keywords      │
│  - Customized Cover Letter & Bullets      │
└───────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack & Technologies Used

- **Frontend & Web Framework**: [Streamlit](https://streamlit.io/)
- **Generative AI & LLM**: Google Gemini API (`google-genai` SDK, Model: `gemini-2.5-flash`)
- **Data & Data Visualization**: `Plotly`, `Pandas`
- **Document Extractors**: `pdfplumber`, `python-docx`
- **Job Scraping & HTTP**: `BeautifulSoup4`, `Requests`
- **Environment Management**: `python-dotenv`

---

## 🚀 Live Deployment Guide

You can deploy this application live for free on **Streamlit Community Cloud** or **Hugging Face Spaces**:

### Deploying to Streamlit Community Cloud (Recommended)
1. Push this repository to your GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and click **"New app"**.
3. Select your GitHub repository, branch (`main`), and set Main file path to `app.py`.
4. (Optional) Under **Advanced settings**, add your `GEMINI_API_KEY = "your_key_here"` under Secrets.
5. Click **Deploy!** Your app will receive a public live URL (e.g. `https://your-app.streamlit.app`).

---

## 💻 Local Quickstart Setup

### Prerequisites
- Python 3.10 or higher installed.

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/your-username/Resume_Matcher.git
cd Resume_Matcher

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set up Environment Variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 5. Launch Application
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📁 Repository Structure

```
Resume_Matcher/
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Project Python dependencies
├── README.md                   # Project documentation & deployment guide
├── .env.example                # Environment variable template
├── .streamlit/
│   └── config.toml             # Custom UI theme configuration
├── modules/
│   ├── __init__.py
│   ├── resume_parser.py        # PDF/DOCX extractor & Gemini parser
│   ├── job_scraper.py         # Live job search API & web scraper
│   └── match_engine.py         # Semantic match scoring & cover letter generator
```

---

## 🤝 Submission Information

- **Role Applied For**: Generative AI Developer Intern
- **Assignment**: AI Job Scraper & Resume Matcher MVP (Build Sprint)
- **Developer**: Harshita Sharma
