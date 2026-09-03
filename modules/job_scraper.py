import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse

INVALID_DOMAINS = ["example.com", "placeholder.com", "test.com", "localhost", "127.0.0.1"]
EXECUTIVE_KEYWORDS = ["manager", "director", "head of", "vp ", "vice president", "chief", "executive", "recruiter", "accountant"]
NON_TECH_KEYWORDS = ["sales", "office assistant", "content reviewer", "copywriter", "writer", "steward", "technician", "customer support", "help desk", "qa engineer", "devops"]

def is_valid_url(url: str) -> bool:
    """Check if a URL is valid, non-placeholder, and properly formatted."""
    if not url or not isinstance(url, str):
        return False
    url_clean = url.strip().lower()
    if url_clean in ["#", "", "none"]:
        return False
    if any(domain in url_clean for domain in INVALID_DOMAINS):
        return False
    if not (url_clean.startswith("http://") or url_clean.startswith("https://")):
        return False
    try:
        parsed = urlparse(url_clean)
        return bool(parsed.netloc and "." in parsed.netloc)
    except Exception:
        return False

def is_executive_role(title: str) -> bool:
    """Check if job title indicates an executive, managerial, or non-engineering role."""
    t_lower = (title or "").lower()
    return any(word in t_lower for word in EXECUTIVE_KEYWORDS + NON_TECH_KEYWORDS)

def map_query_to_api_tags(query: str) -> list:
    """Map user search query to API tags for maximum active job retrieval."""
    q_lower = (query or "").lower().strip()
    tags = []
    
    if any(k in q_lower for k in ["machine learning", "ml", "ai", "artificial intelligence", "deep learning", "generative ai", "nlp", "llm"]):
        tags.extend(["ai", "python", "data", "dev"])
    elif any(k in q_lower for k in ["data science", "data analyst", "data engineer"]):
        tags.extend(["data", "python", "sql"])
    elif any(k in q_lower for k in ["react", "frontend", "front-end", "javascript", "ui"]):
        tags.extend(["react", "javascript", "dev"])
    elif any(k in q_lower for k in ["python", "backend", "django", "fastapi"]):
        tags.extend(["python", "dev", "backend"])
    else:
        words = [w for w in q_lower.split() if w not in ["intern", "internship", "junior", "developer", "engineer", "role"]]
        tags.append(words[0] if words else "dev")
        
    return list(dict.fromkeys(tags))

def is_role_relevant(query: str, title: str, description: str) -> bool:
    """Check if a job posting strictly matches the searched role and technical domain."""
    q_lower = (query or "").lower().strip()
    t_lower = (title or "").lower()
    d_lower = (description or "").lower()
    
    # 1. Filter out management & non-technical sales/support/QA roles
    if is_executive_role(title):
        return False
        
    # 2. Category matching
    # ML / AI / Data Science
    if any(k in q_lower for k in ["machine learning", "ml", "ai", "artificial intelligence", "data science", "deep learning", "generative ai", "python"]):
        ml_keywords = ["machine learning", "ml", "ai", "artificial intelligence", "data science", "deep learning", "generative ai", "llm", "python", "nlp", "computer vision", "data engineer", "data scientist", "ai engineer", "developer", "software"]
        if not (any(k in t_lower for k in ml_keywords) or any(k in d_lower for k in ml_keywords[:7])):
            return False
        if ("frontend" in t_lower or "react" in t_lower or "designer" in t_lower) and not ("ml" in t_lower or "ai" in t_lower or "python" in t_lower or "data" in t_lower):
            return False
        return True

    # React / Frontend
    if any(k in q_lower for k in ["react", "frontend", "front-end", "ui", "javascript"]):
        fe_keywords = ["react", "frontend", "front end", "javascript", "web developer", "ui developer", "html", "css", "js"]
        if not (any(k in t_lower for k in fe_keywords) or any(k in d_lower for k in fe_keywords[:5])):
            return False
        if ("machine learning" in t_lower or "data science" in t_lower) and not ("react" in t_lower):
            return False
        return True

    # General query fallback
    query_tokens = [tok for tok in q_lower.split() if tok not in ["intern", "internship", "junior", "developer", "engineer", "role"]]
    if query_tokens:
        return any(tok in t_lower or tok in d_lower for tok in query_tokens)
        
    return True

def fetch_from_remotive(query: str) -> list:
    """Fetch live jobs from Remotive API."""
    jobs = []
    api_tags = map_query_to_api_tags(query)
    for tag in api_tags[:2]:
        try:
            url = f"https://remotive.com/api/remote-jobs?search={requests.utils.quote(tag)}&limit=30"
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("jobs", []):
                    title = item.get("title", "")
                    desc = item.get("description", "")
                    job_url = item.get("url", "")
                    
                    soup = BeautifulSoup(desc, "html.parser")
                    clean_desc = soup.get_text(separator="\n").strip()
                    
                    if is_valid_url(job_url) and is_role_relevant(query, title, clean_desc):
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
            print(f"Remotive API error for tag {tag}: {e}")
    return jobs

def fetch_from_jobicy(query: str) -> list:
    """Fetch live jobs from Jobicy API."""
    jobs = []
    api_tags = map_query_to_api_tags(query)
    for tag in api_tags[:2]:
        try:
            url = f"https://jobicy.com/api/v2/remote-jobs?count=25&tag={requests.utils.quote(tag)}"
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("jobs", []):
                    title = item.get("jobTitle", "")
                    desc = item.get("jobDescription", "")
                    job_url = item.get("url", "")
                    
                    soup = BeautifulSoup(desc, "html.parser")
                    clean_desc = soup.get_text(separator="\n").strip()
                    
                    if is_valid_url(job_url) and is_role_relevant(query, title, clean_desc):
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
            print(f"Jobicy API error for tag {tag}: {e}")
    return jobs

def fetch_from_arbeitnow(query: str) -> list:
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
                
                if is_valid_url(job_url) and is_role_relevant(query, title, clean_desc):
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
    Strictly filters out non-engineering/sales roles and non-working URLs.
    """
    query_clean = query.strip() if query else "Developer"
    
    raw_jobs = []
    raw_jobs.extend(fetch_from_remotive(query_clean))
    raw_jobs.extend(fetch_from_jobicy(query_clean))
    raw_jobs.extend(fetch_from_arbeitnow(query_clean))
    
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
    Handles LinkedIn restrictions and user profiles gracefully.
    """
    url_clean = (url or "").strip()
    if not url_clean:
        return {
            "status": "error",
            "message": "Please enter a valid URL."
        }
        
    if not (url_clean.lower().startswith("http://") or url_clean.lower().startswith("https://")):
        url_clean = "https://" + url_clean

    if not is_valid_url(url_clean):
        return {
            "status": "error",
            "message": f"'{url}' is an invalid URL. Please enter a valid http:// or https:// job posting link."
        }
        
    url_lower = url_clean.lower()
    
    if "linkedin.com" in url_lower:
        if "/in/" in url_lower:
            return {
                "status": "blocked",
                "message": f"The link '{url_clean}' is a LinkedIn User Profile, not a job posting! Please paste a LinkedIn job posting URL (e.g. linkedin.com/jobs/view/...) or paste the job description text directly in the box below."
            }
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        try:
            resp = requests.get(url_clean, headers=headers, timeout=6)
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
                    "url": url_clean,
                    "application_url": url_clean,
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
        resp = requests.get(url_clean, headers=headers, timeout=6)
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
                "url": url_clean,
                "application_url": url_clean,
                "source": "Verified Job Page",
                "posted_date": "Recently",
                "description": full_text[:3500],
                "required_skills": []
            }
    except Exception as e:
        print(f"Error scraping job URL {url_clean}: {e}")
        
    return {
        "status": "error",
        "message": "Could not automatically extract content from this URL. Please paste the job description text directly below."
    }
