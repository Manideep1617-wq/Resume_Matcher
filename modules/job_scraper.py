import requests
from bs4 import BeautifulSoup
import re
import json

DEMO_JOBS = [
    {
        "id": "job_01",
        "title": "Generative AI Developer Intern",
        "company": "DeepMind Innovations",
        "location": "Remote / Bengaluru, India",
        "url": "https://example.com/jobs/genai-intern",
        "posted_date": "2026-09-01",
        "description": """
About the Role:
We are looking for a passionate Generative AI Developer Intern to build cutting-edge LLM applications, RAG pipelines, and AI agent workflows.

Key Responsibilities:
- Design and deploy LLM applications using LangChain, LlamaIndex, and Google Gemini / OpenAI APIs.
- Build clean, interactive web user interfaces using Streamlit, Gradio, or React.
- Implement Retrieval-Augmented Generation (RAG) with vector databases like ChromaDB, FAISS, or Pinecone.
- Perform prompt engineering, fine-tuning, and performance optimization.
- Write clean, maintainable Python code with unit tests and documentation.

Required Skills & Qualifications:
- Strong proficiency in Python 3.x, OOP, and RESTful APIs.
- Hands-on experience with LLM APIs (Gemini, GPT-4, Anthropic) and Prompt Engineering.
- Experience with web scraping (BeautifulSoup, Selenium, Scrapy) or API integrations.
- Familiarity with Vector Databases (ChromaDB, Pinecone, FAISS).
- Knowledge of Git, Docker, and CI/CD pipelines.
- Good problem-solving mindset and communication skills.
""",
        "required_skills": ["Python", "Generative AI", "Gemini API", "LangChain", "RAG", "Streamlit", "Vector DB", "Prompt Engineering", "Git"]
    },
    {
        "id": "job_02",
        "title": "AI/ML Engineer - NLP & Agents",
        "company": "TechCorp Global",
        "location": "Hybrid / San Francisco, CA",
        "url": "https://example.com/jobs/aiml-engineer",
        "posted_date": "2026-08-28",
        "description": """
About TechCorp:
TechCorp is scaling its next-generation AI platforms. We need an AI/ML Engineer focused on NLP and Autonomous Agent workflows.

Responsibilities:
- Build enterprise AI agent architectures with multi-agent orchestration.
- Fine-tune transformer models (Llama 3, Mistral, BERT) for specialized industry domains.
- Optimize inference speed, context length, and token usage costs.
- Integrate cloud infrastructure (AWS/GCP, Docker, Kubernetes) with ML pipelines.

Requirements:
- Master's or Bachelor's in CS, AI, or Data Science.
- 2+ years experience in Python, PyTorch, TensorFlow, and HuggingFace Transformers.
- Expertise in NLP, Tokenization, Embeddings, and Vector Search.
- Experience with FastAPI, Docker, and AWS SageMaker.
- Solid background in Data Structures and Algorithms.
""",
        "required_skills": ["Python", "PyTorch", "NLP", "HuggingFace", "AI Agents", "FastAPI", "Docker", "AWS", "Transformers"]
    },
    {
        "id": "job_03",
        "title": "Full Stack Python & AI Developer",
        "company": "NextGen Software",
        "location": "Remote",
        "url": "https://example.com/jobs/fullstack-python",
        "posted_date": "2026-08-30",
        "description": """
Position Overview:
NextGen Software is searching for a Full Stack Python Developer with AI/ML integration skills to lead new product features.

What You Will Do:
- Develop scalable backend microservices using Python, FastAPI, and PostgreSQL.
- Build clean frontend interfaces using React / Next.js or Streamlit dashboards.
- Integrate AI features including automatic summary generation, resume parsing, and semantic search.
- Manage Docker deployments and automated CI/CD deployments.

What We Look For:
- Strong core Python, Django or FastAPI backend experience.
- Experience with JavaScript / TypeScript, React, and HTML/CSS.
- Knowledge of relational databases (PostgreSQL, MySQL) and ORMs (SQLAlchemy).
- Familiarity with AI services (OpenAI, Gemini, Azure AI).
""",
        "required_skills": ["Python", "FastAPI", "React", "PostgreSQL", "JavaScript", "Docker", "REST API", "SQL", "Gemini"]
    }
]

def search_live_jobs(query: str, location: str = "Remote") -> list:
    """
    Search active jobs using public open APIs (Remotive API, etc.).
    Falls back to custom search / demo jobs if external requests fail or return empty.
    """
    jobs = []
    
    # 1. Query Remotive Job Search API
    try:
        url = f"https://remotive.com/api/remote-jobs?search={requests.utils.quote(query)}&limit=10"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            remotive_jobs = data.get("jobs", [])
            for index, item in enumerate(remotive_jobs[:8]):
                # Clean HTML tags from job description
                raw_desc = item.get("description", "")
                soup = BeautifulSoup(raw_desc, "html.parser")
                clean_desc = soup.get_text(separator="\n").strip()
                
                jobs.append({
                    "id": f"remotive_{item.get('id', index)}",
                    "title": item.get("title", query),
                    "company": item.get("company_name", "Remote Company"),
                    "location": item.get("candidate_required_location", location or "Remote"),
                    "url": item.get("url", "#"),
                    "posted_date": item.get("publication_date", "Recently")[:10],
                    "description": clean_desc if len(clean_desc) > 100 else f"Job title: {item.get('title')}. Category: {item.get('category')}",
                    "required_skills": item.get("tags", [])
                })
    except Exception as e:
        print(f"Error fetching from Remotive API: {e}")

    # 2. If no jobs found online or query matches demo jobs, merge demo jobs
    query_lower = query.lower()
    matching_demos = [
        job for job in DEMO_JOBS
        if any(word in job["title"].lower() or word in job["description"].lower() for word in query_lower.split())
    ]
    
    # Prepend matched demo jobs so user always gets instant relevant results
    all_jobs = matching_demos + jobs
    
    # If still empty, return all demo jobs
    if not all_jobs:
        return DEMO_JOBS
        
    return all_jobs

def scrape_job_from_url(url: str) -> dict:
    """
    Scrape job description directly from a job posting URL.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            
            # Remove scripts, styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
                
            title = soup.title.string if soup.title else "Scraped Job Posting"
            text_lines = [line.strip() for line in soup.get_text().splitlines() if line.strip()]
            full_text = "\n".join(text_lines)
            
            return {
                "id": "scraped_url_job",
                "title": title[:80],
                "company": "Online Employer",
                "location": "See posting",
                "url": url,
                "posted_date": "Today",
                "description": full_text[:4000],
                "required_skills": []
            }
    except Exception as e:
        print(f"Error scraping job from URL: {e}")
        
    return {
        "id": "scraped_url_job",
        "title": "Job Posting from URL",
        "company": "Web Employer",
        "location": "Remote",
        "url": url,
        "posted_date": "Today",
        "description": f"Failed to auto-extract full page layout from {url}. Please copy and paste the job description text directly into the text box.",
        "required_skills": []
    }
