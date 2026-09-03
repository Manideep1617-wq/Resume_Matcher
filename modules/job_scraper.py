import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse

INVALID_DOMAINS = ["example.com", "placeholder.com", "test.com", "localhost", "127.0.0.1", "none", "#", ""]
SENIOR_KEYWORDS = ["senior", "sr.", "sr ", "lead", "principal", "architect", "manager", "director", "head of", "vp ", "vice president"]

def is_valid_url(url: str) -> bool:
    """Check if a URL is valid, non-placeholder, and properly formatted."""
    if not url or not isinstance(url, str):
        return False
    url_clean = url.strip().lower()
    if any(domain in url_clean for domain in INVALID_DOMAINS):
        return False
    if not (url_clean.startswith("http://") or url_clean.startswith("https://")):
        return False
    try:
        parsed = urlparse(url_clean)
        return bool(parsed.netloc and "." in parsed.netloc)
    except Exception:
        return False

def is_senior_role(title: str) -> bool:
    """Check if job title indicates a senior or leadership role."""
    title_lower = (title or "").lower()
    return any(word in title_lower for word in SENIOR_KEYWORDS)

def extract_api_search_term(query: str) -> str:
    """Extract primary tech/domain tag for API endpoint queries."""
    q_lower = (query or "").lower().strip()
    if any(k in q_lower for k in ["machine learning", "ml"]):
        return "machine learning"
    if any(k in q_lower for k in ["ai", "artificial intelligence", "generative ai"]):
        return "ai"
    if "data science" in q_lower:
        return "data science"
    if "react" in q_lower:
        return "react"
    if "python" in q_lower:
        return "python"
    if any(k in q_lower for k in ["frontend", "front-end"]):
        return "frontend"
    if any(k in q_lower for k in ["backend", "back-end"]):
        return "backend"
        
    # Strip modifier words
    words = [w for w in q_lower.split() if w not in ["intern", "internship", "junior", "developer", "engineer", "role", "jobs"]]
    return words[0] if words else query

def is_role_relevant(query: str, title: str, description: str, is_intern_candidate: bool = True) -> bool:
    """Strict relevance and seniority filter for search results."""
    q_lower = (query or "").lower().strip()
    t_lower = (title or "").lower()
    d_lower = (description or "").lower()
    
    # 1. Exclude Senior roles if candidate is Intern/Fresher
    if is_intern_candidate and is_senior_role(title):
        return False
        
    # 2. Category matching
    if any(k in q_lower for k in ["machine learning", "ml", "ai", "artificial intelligence", "data science", "deep learning", "generative ai"]):
        ml_keywords = ["machine learning", "ml", "ai", "artificial intelligence", "data science", "deep learning", "generative ai", "llm", "python", "nlp", "computer vision", "data"]
        if not (any(k in t_lower for k in ml_keywords) or any(k in d_lower for k in ml_keywords[:6])):
            return False
        if ("frontend" in t_lower or "react" in t_lower or "designer" in t_lower) and not ("ml" in t_lower or "ai" in t_lower or "python" in t_lower):
            return False
        return True

    if any(k in q_lower for k in ["react", "frontend", "front-end", "ui", "javascript"]):
        fe_keywords = ["react", "frontend", "front end", "javascript", "web developer", "ui developer", "html", "css", "js"]
        if not (any(k in t_lower for k in fe_keywords) or any(k in d_lower for k in fe_keywords[:5])):
            return False
        if ("machine learning" in t_lower or "data science" in t_lower) and not ("react" in t_lower):
            return False
        return True

    query_tokens = [tok for tok in q_lower.split() if tok not in ["intern", "internship", "junior", "developer", "engineer"]]
    if query_tokens:
        return any(tok in t_lower or tok in d_lower for tok in query_tokens)
        
    return True

def fetch_from_remotive(query: str, is_intern_candidate: bool = True) -> list:
    """Fetch live jobs from Remotive API."""
    jobs = []
    api_term = extract_api_search_term(query)
    try:
        url = f"https://remotive.com/api/remote-jobs?search={requests.utils.quote(api_term)}&limit=30"
        resp = requests.get(url, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("jobs", []):
                title = item.get("title", "")
                desc = item.get("description", "")
                job_url = item.get("url", "")
                
                soup = BeautifulSoup(desc, "html.parser")
                clean_desc = soup.get_text(separator="\n").strip()
                
                if is_valid_url(job_url) and is_role_relevant(query, title, clean_desc, is_intern_candidate):
                    jobs.append({
                        "id": f"remotive_{item.get('id')}",
                        "title": title,
                        "company": item.get("company_name", "Tech Employer"),
                        "location": item.get("candidate_required_location", "Remote"),
                        "url": job_url,
                        "application_url": job_url,
                        "source": "Remotive",
                        "posted_date": item.get("publication_date", "")[:10] or "Active Listing",
                        "description": clean_desc[:2500],
                        "required_skills": item.get("tags", [])
                    })
    except Exception as e:
        print(f"Remotive API error: {e}")
    return jobs

def fetch_from_jobicy(query: str, is_intern_candidate: bool = True) -> list:
    """Fetch live jobs from Jobicy API."""
    jobs = []
    api_term = extract_api_search_term(query)
    try:
        url = f"https://jobicy.com/api/v2/remote-jobs?count=25&tag={requests.utils.quote(api_term)}"
        resp = requests.get(url, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("jobs", []):
                title = item.get("jobTitle", "")
                desc = item.get("jobDescription", "")
                job_url = item.get("url", "")
                
                soup = BeautifulSoup(desc, "html.parser")
                clean_desc = soup.get_text(separator="\n").strip()
                
                if is_valid_url(job_url) and is_role_relevant(query, title, clean_desc, is_intern_candidate):
                    jobs.append({
                        "id": f"jobicy_{item.get('id')}",
                        "title": title,
                        "company": item.get("companyName", "Tech Employer"),
                        "location": item.get("jobGeo", "Remote"),
                        "url": job_url,
                        "application_url": job_url,
                        "source": "Jobicy",
                        "posted_date": item.get("pubDate", "")[:10] or "Active Listing",
                        "description": clean_desc[:2500],
                        "required_skills": item.get("jobIndustry", []) if isinstance(item.get("jobIndustry"), list) else [query]
                    })
    except Exception as e:
        print(f"Jobicy API error: {e}")
    return jobs

def fetch_from_arbeitnow(query: str, is_intern_candidate: bool = True) -> list:
    """Fetch live jobs from Arbeitnow API."""
    jobs = []
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        resp = requests.get(url, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", []):
                title = item.get("title", "")
                desc = item.get("description", "")
                job_url = item.get("url", "")
                
                soup = BeautifulSoup(desc, "html.parser")
                clean_desc = soup.get_text(separator="\n").strip()
                
                if is_valid_url(job_url) and is_role_relevant(query, title, clean_desc, is_intern_candidate):
                    jobs.append({
                        "id": f"arbeit_{item.get('slug')}",
                        "title": title,
                        "company": item.get("company_name", "Tech Company"),
                        "location": item.get("location", "Remote"),
                        "url": job_url,
                        "application_url": job_url,
                        "source": "Arbeitnow",
                        "posted_date": "Active Listing",
                        "description": clean_desc[:2500],
                        "required_skills": item.get("tags", [])
                    })
    except Exception as e:
        print(f"Arbeitnow API error: {e}")
    return jobs

def search_live_jobs(query: str, location: str = "Remote", candidate_level: str = "Internship / Fresher") -> list:
    """
    Search active real-world job listings using verified job APIs.
    Strictly filters out irrelevant roles, senior roles for interns, and non-working URLs.
    """
    query_clean = query.strip() if query else "Developer"
    is_intern = any(w in candidate_level.lower() or w in query_clean.lower() for w in ["intern", "fresher", "junior", "student"])
    
    raw_jobs = []
    raw_jobs.extend(fetch_from_remotive(query_clean, is_intern))
    raw_jobs.extend(fetch_from_jobicy(query_clean, is_intern))
    raw_jobs.extend(fetch_from_arbeitnow(query_clean, is_intern))
    
    seen = set()
    unique_jobs = []
    for j in raw_jobs:
        key = (j["title"].lower(), j["company"].lower())
        if key not in seen and is_valid_url(j.get("application_url")):
            seen.add(key)
            unique_jobs.append(j)
            
    return unique_jobs

def scrape_job_from_url(url: str) -> dict:
    """
    Scrape job description directly from a job posting web URL.
    Handles LinkedIn restrictions gracefully with fallback guidance.
    """
    if not is_valid_url(url):
        return {
            "status": "error",
            "message": "Invalid URL format. Please enter a valid http:// or https:// job posting link."
        }
        
    url_lower = url.lower()
    
    if "linkedin.com" in url_lower:
        if "/in/" in url_lower:
            return {
                "status": "blocked",
                "message": "The pasted link appears to be a LinkedIn user profile rather than a job posting. Please paste a LinkedIn job posting URL (e.g., linkedin.com/jobs/view/...) or paste the job description text directly below."
            }
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=6)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                title = soup.find("h1") or soup.title
                title_str = title.get_text().strip() if title else "LinkedIn Job Posting"
                
                if "sign in" in title_str.lower() or "authwall" in resp.url.lower():
                    return {
                        "status": "blocked",
                        "message": "LinkedIn restricts automated public access for this listing. Please copy and paste the job description text into the box below to analyze this job."
                    }
                    
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text_lines = [line.strip() for line in soup.get_text().splitlines() if line.strip()]
                full_text = "\n".join(text_lines)
                
                return {
                    "status": "success",
                    "id": "linkedin_job",
                    "title": title_str[:80],
                    "company": "LinkedIn Listing",
                    "location": "See Posting",
                    "url": url,
                    "application_url": url,
                    "source": "LinkedIn",
                    "posted_date": "Recently",
                    "description": full_text[:3500],
                    "required_skills": []
                }
            else:
                return {
                    "status": "blocked",
                    "message": f"LinkedIn restricts automated access (HTTP Status {resp.status_code}). Please copy and paste the job description text into the box below to analyze this job."
                }
        except Exception as e:
            return {
                "status": "blocked",
                "message": "LinkedIn restricts automated access for this link. Please copy and paste the job description text into the box below to analyze this job."
            }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            title = soup.title.string if soup.title else "Web Job Posting"
            text_lines = [line.strip() for line in soup.get_text().splitlines() if line.strip()]
            full_text = "\n".join(text_lines)
            
            return {
                "status": "success",
                "id": "scraped_web_job",
                "title": title[:80],
                "company": "Web Employer",
                "location": "See Posting",
                "url": url,
                "application_url": url,
                "source": "Verified Job Page",
                "posted_date": "Recently",
                "description": full_text[:3500],
                "required_skills": []
            }
    except Exception as e:
        print(f"Error scraping job URL {url}: {e}")
        
    return {
        "status": "error",
        "message": "Could not automatically extract content from this URL. Please paste the job description text directly below."
    }
