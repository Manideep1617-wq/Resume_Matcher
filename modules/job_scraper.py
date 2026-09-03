import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

INVALID_DOMAINS = ["example.com", "placeholder.com", "test.com", "localhost", "127.0.0.1"]

def is_valid_url(url: str) -> bool:
    """Check if a URL is valid and non-placeholder."""
    if not url or not isinstance(url, str):
        return False
    url_clean = url.strip().lower()
    if url_clean in ["#", "", "none", "null"]:
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

EXCLUDE_TITLE_WORDS = [
    "manager", "director", "head of", "vp ", "vice president", "chief", "executive",
    "recruiter", "accountant", "sales", "marketing", "copywriter", "writer",
    "office assistant", "customer support", "help desk", "devops", "qa engineer",
    "network engineer", "security engineer", "sre", "site reliability"
]

def is_role_match_for_level(title: str, skills: list, level: str) -> bool:
    """Check if a job title/role is appropriate for the candidate's level and skills."""
    t_lower = (title or "").lower()
    
    # Exclude irrelevant categories
    if any(w in t_lower for w in EXCLUDE_TITLE_WORDS):
        return False

    level_lower = level.lower()
    is_intern_level = any(w in level_lower for w in ["intern", "fresher", "student", "entry"])
    
    # For intern/fresher level: exclude Senior, Lead, Principal roles
    if is_intern_level:
        if any(w in t_lower for w in ["senior", "sr.", " sr ", "lead", "principal", "architect", "staff ", "principal"]):
            return False

    # Skills-based keyword match in title/description
    skill_keywords = [s.lower() for s in (skills or []) if len(s) > 2]
    title_words = t_lower.split()

    # General tech-role check
    tech_signals = ["engineer", "developer", "analyst", "scientist", "intern", "software", "python",
                    "ml", "ai", "data", "backend", "frontend", "fullstack", "full stack", "programming"]
    return any(s in t_lower for s in tech_signals) or any(s in t_lower for s in skill_keywords[:6])


def fetch_adzuna_india(skills: list, level: str) -> list:
    """Fetch Indian jobs from Adzuna API (free, no key needed for basic calls)."""
    jobs = []
    # Build search query from top skills
    query_terms = []
    if any(w in level.lower() for w in ["intern", "fresher"]):
        query_terms.append("internship")
    top_skills = [s for s in skills if len(s) > 2][:3]
    query_terms.extend(top_skills)
    query = " ".join(query_terms[:4])
    
    try:
        url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id=demo&app_key=demo&results_per_page=20&what={requests.utils.quote(query)}&content-type=application/json"
        resp = requests.get(url, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("results", []):
                title = item.get("title", "")
                job_url = item.get("redirect_url", "")
                company = item.get("company", {}).get("display_name", "Tech Company")
                location = item.get("location", {}).get("display_name", "India")
                description = item.get("description", "")
                
                if is_valid_url(job_url) and is_role_match_for_level(title, skills, level):
                    jobs.append({
                        "id": f"adzuna_{item.get('id')}",
                        "title": title,
                        "company": company,
                        "location": location + ", India",
                        "url": job_url,
                        "application_url": job_url,
                        "source": "Adzuna India",
                        "posted_date": item.get("created", "")[:10] or "Active",
                        "description": description[:2500],
                        "required_skills": []
                    })
    except Exception as e:
        print(f"Adzuna error: {e}")
    return jobs


def fetch_remotive_for_resume(skills: list, level: str) -> list:
    """Fetch remote jobs from Remotive that match resume skills."""
    jobs = []
    
    # Build targeted search queries from resume skills
    ai_ml_skills = ["machine learning", "ai", "deep learning", "llm", "generative ai", "nlp", "data science"]
    web_skills = ["react", "javascript", "frontend", "node.js"]
    python_skills = ["python", "django", "fastapi"]
    
    top_skills = [s.lower() for s in (skills or []) if len(s) > 2]
    
    if any(s in top_skills for s in ai_ml_skills):
        search_terms = ["python", "ai"]
    elif any(s in top_skills for s in web_skills):
        search_terms = ["react", "javascript"]
    elif any(s in top_skills for s in python_skills):
        search_terms = ["python"]
    else:
        # Generic developer internship
        search_terms = ["developer", "python"]

    for term in search_terms[:2]:
        try:
            url = f"https://remotive.com/api/remote-jobs?search={requests.utils.quote(term)}&limit=30"
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("jobs", []):
                    title = item.get("title", "")
                    desc = item.get("description", "")
                    job_url = item.get("url", "")
                    location = item.get("candidate_required_location", "Remote")
                    
                    soup = BeautifulSoup(desc, "html.parser")
                    clean_desc = soup.get_text(separator="\n").strip()
                    
                    # For Indian candidates, accept: Remote, Worldwide, Asia, India
                    loc_lower = location.lower()
                    location_ok = any(w in loc_lower for w in ["remote", "worldwide", "anywhere", "india", "asia", "global"])
                    
                    if is_valid_url(job_url) and location_ok and is_role_match_for_level(title, skills, level):
                        # Mark as India Remote friendly
                        display_location = "Remote (India Eligible)" if "india" not in loc_lower else location
                        jobs.append({
                            "id": f"remotive_{item.get('id')}",
                            "title": title,
                            "company": item.get("company_name", "Tech Company"),
                            "location": display_location,
                            "url": job_url,
                            "application_url": job_url,
                            "source": "Remotive (Remote)",
                            "posted_date": item.get("publication_date", "")[:10] or "Active",
                            "description": clean_desc[:2500],
                            "required_skills": item.get("tags", [])
                        })
        except Exception as e:
            print(f"Remotive error for {term}: {e}")
    return jobs


def fetch_jobicy_for_resume(skills: list, level: str) -> list:
    """Fetch jobs from Jobicy that match resume skills."""
    jobs = []
    top_skills = [s.lower() for s in (skills or []) if len(s) > 2]
    
    # Map skills to Jobicy-compatible tags
    if any(s in top_skills for s in ["machine learning", "ai", "deep learning", "python", "generative ai"]):
        tags = ["python", "data"]
    elif any(s in top_skills for s in ["react", "javascript", "frontend"]):
        tags = ["react", "javascript"]
    else:
        tags = ["python", "dev"]
    
    for tag in tags[:2]:
        try:
            url = f"https://jobicy.com/api/v2/remote-jobs?count=20&tag={requests.utils.quote(tag)}"
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("jobs", []):
                    title = item.get("jobTitle", "")
                    desc = item.get("jobDescription", "")
                    job_url = item.get("url", "")
                    geo = item.get("jobGeo", "Worldwide")
                    
                    soup = BeautifulSoup(desc, "html.parser")
                    clean_desc = soup.get_text(separator="\n").strip()
                    
                    # Accept worldwide/remote or India-specific
                    geo_lower = geo.lower()
                    location_ok = any(w in geo_lower for w in ["worldwide", "remote", "anywhere", "global", "india", ""])
                    
                    if is_valid_url(job_url) and is_role_match_for_level(title, skills, level):
                        jobs.append({
                            "id": f"jobicy_{item.get('id')}",
                            "title": title,
                            "company": item.get("companyName", "Tech Company"),
                            "location": "Remote (India Eligible)" if "india" not in geo_lower else geo,
                            "url": job_url,
                            "application_url": job_url,
                            "source": "Jobicy (Remote)",
                            "posted_date": item.get("pubDate", "")[:10] or "Active",
                            "description": clean_desc[:2500],
                            "required_skills": item.get("jobIndustry", []) if isinstance(item.get("jobIndustry"), list) else []
                        })
        except Exception as e:
            print(f"Jobicy error for {tag}: {e}")
    return jobs


def search_jobs_for_resume(parsed_resume: dict) -> list:
    """
    Auto-search real job opportunities based on the candidate's resume.
    Returns India-specific remote/onsite jobs matched to candidate's level and skills.
    """
    if not parsed_resume or not isinstance(parsed_resume, dict):
        return []
    
    skills = parsed_resume.get("technical_skills", [])
    level = parsed_resume.get("experience_level", "Internship / Fresher")
    suitable_roles = parsed_resume.get("suitable_roles", [])
    
    raw_jobs = []
    raw_jobs.extend(fetch_remotive_for_resume(skills, level))
    raw_jobs.extend(fetch_jobicy_for_resume(skills, level))
    
    # Deduplicate
    seen = set()
    unique_jobs = []
    for j in raw_jobs:
        key = (j["title"].lower(), j["company"].lower())
        if key not in seen and is_valid_url(j.get("application_url")):
            seen.add(key)
            unique_jobs.append(j)
    
    return unique_jobs


def scrape_job_from_url(url: str) -> dict:
    """Scrape job description from a URL with LinkedIn graceful fallback."""
    url_clean = (url or "").strip()
    if not url_clean:
        return {"status": "error", "message": "Please enter a valid URL."}
    
    if not (url_clean.lower().startswith("http://") or url_clean.lower().startswith("https://")):
        url_clean = "https://" + url_clean

    if not is_valid_url(url_clean):
        return {"status": "error", "message": f"Invalid URL. Please enter a valid http:// or https:// job posting link."}
    
    url_lower = url_clean.lower()
    
    if "linkedin.com" in url_lower:
        if "/in/" in url_lower:
            return {
                "status": "blocked",
                "message": "That's a LinkedIn User Profile link, not a job posting. Please paste a job posting URL like linkedin.com/jobs/view/... or paste the job description text below."
            }
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            resp = requests.get(url_clean, headers=headers, timeout=6)
            soup = BeautifulSoup(resp.content, "html.parser")
            title_tag = soup.find("h1") or soup.title
            title_str = title_tag.get_text().strip()[:80] if title_tag else "LinkedIn Job"
            if "sign in" in title_str.lower() or "authwall" in resp.url.lower():
                return {"status": "blocked", "message": "LinkedIn requires login to access this page. Please paste the job description text in the box below to analyze this job."}
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = "\n".join([l.strip() for l in soup.get_text().splitlines() if l.strip()])
            return {"status": "success", "id": "linkedin_job", "title": title_str, "company": "LinkedIn Listing", "location": "India", "url": url_clean, "application_url": url_clean, "source": "LinkedIn", "posted_date": "Recent", "description": text[:3500], "required_skills": []}
        except:
            return {"status": "blocked", "message": "LinkedIn restricts automated access. Please paste the job description text below to analyze this job."}
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url_clean, headers=headers, timeout=6)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            title = soup.title.string[:80] if soup.title else "Web Job Posting"
            text = "\n".join([l.strip() for l in soup.get_text().splitlines() if l.strip()])
            return {"status": "success", "id": "scraped_job", "title": title, "company": "Employer", "location": "India", "url": url_clean, "application_url": url_clean, "source": "Job Posting", "posted_date": "Recent", "description": text[:3500], "required_skills": []}
    except Exception as e:
        print(f"Scrape error: {e}")
    
    return {"status": "error", "message": "Could not extract content from this URL. Please paste the job description text directly below."}
