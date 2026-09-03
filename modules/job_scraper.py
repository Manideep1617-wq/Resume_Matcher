import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse, quote

INVALID_DOMAINS = ["example.com", "placeholder.com", "test.com", "localhost", "127.0.0.1"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── URL Helpers ────────────────────────────────────────────────────────────────

def is_valid_url(url: str) -> bool:
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
    "recruiter", "accountant", "copywriter", "office assistant",
    "customer support", "help desk", "network engineer",
    "security engineer", "site reliability", "technical support"
]

def is_role_match_for_level(title: str, skills: list, level: str) -> bool:
    """Keep only tech roles appropriate to the candidate's level and skills."""
    t_lower = (title or "").lower()

    if any(w in t_lower for w in EXCLUDE_TITLE_WORDS):
        return False

    level_lower = level.lower()
    is_intern_level = any(w in level_lower for w in ["intern", "fresher", "student", "entry", "junior"])

    if is_intern_level:
        senior_words = ["senior", "sr.", " sr ", "lead ", "principal", "architect", "staff ", "manager", "director"]
        if any(w in t_lower for w in senior_words):
            return False

    skill_keywords = [s.lower() for s in (skills or []) if len(s) > 2]
    tech_signals = [
        "engineer", "developer", "analyst", "scientist", "intern", "internship",
        "software", "python", "ml", "ai", "data", "backend", "frontend",
        "fullstack", "full stack", "programming", "researcher", "trainee"
    ]
    return (
        any(s in t_lower for s in tech_signals)
        or any(s in t_lower for s in skill_keywords[:8])
    )


def _build_skill_query(skills: list, level: str, include_internship: bool = True) -> str:
    """Build a search query string from resume skills."""
    top = [s for s in skills if len(s) > 2][:3]
    parts = []
    if include_internship and any(w in level.lower() for w in ["intern", "fresher", "student", "entry"]):
        parts.append("intern")
    parts.extend(top)
    return " ".join(parts[:4]).strip() or "developer intern"


def _internshala_slug(skills: list) -> str:
    """Map resume skills to an Internshala URL keyword slug."""
    mapping = {
        "machine learning": "machine-learning",
        "deep learning": "deep-learning",
        "generative ai": "artificial-intelligence",
        "llm": "artificial-intelligence",
        "nlp": "natural-language-processing",
        "data science": "data-science",
        "python": "python",
        "django": "django",
        "fastapi": "python",
        "react": "reactjs",
        "javascript": "javascript",
        "node": "nodejs",
        "java": "java",
        "android": "android",
        "flutter": "flutter",
        "sql": "sql",
        "data analysis": "data-analytics",
    }
    top = [s.lower() for s in skills if len(s) > 2]
    for skill in top:
        for key, slug in mapping.items():
            if key in skill or skill in key:
                return slug
    return "computer-science"


# ── Source 1: Internshala ──────────────────────────────────────────────────────

def fetch_from_internshala(skills: list, level: str) -> list:
    """
    Fetch live internship listings from Internshala using their open REST API.
    Internshala is India's #1 internship platform.
    Note: Internshala's main site is a React SPA (requires JS), so we use their
    open API endpoint that returns JSON without authentication.
    """
    jobs = []
    slug = _internshala_slug(skills)

    # Internshala open/public API endpoints
    api_urls = [
        f"https://internshala.com/internships/matching-preferences/",
    ]

    # Try their open search API with query params
    query_terms = [s for s in skills[:3] if len(s) > 2]
    query_str = " ".join(query_terms[:2])

    headers_api = {
        **HEADERS,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    # Attempt their AJAX endpoint used by their search page
    try:
        search_url = (
            f"https://internshala.com/internships/{slug}-internship/"
        )
        resp = requests.get(search_url, headers=headers_api, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")

            # 2024 layout selectors
            cards = (
                soup.select(".individual_internship")
                or soup.select(".internship_meta")
                or soup.select("[id^='internship_id_']")
                or soup.select(".internship-listing-card")
            )

            for card in cards[:20]:
                try:
                    title_tag = (
                        card.select_one(".profile a")
                        or card.select_one("h3 a")
                        or card.select_one("a[href*='/internship/detail']")
                        or card.select_one(".title a")
                    )
                    title = title_tag.get_text(strip=True) if title_tag else ""

                    co_tag = (
                        card.select_one(".company_name a")
                        or card.select_one(".company-name")
                        or card.select_one("[class*='company']")
                    )
                    company = co_tag.get_text(strip=True) if co_tag else "Company"

                    loc_tag = (
                        card.select_one(".locations span")
                        or card.select_one(".location_name")
                        or card.select_one("[class*='location']")
                    )
                    location = loc_tag.get_text(strip=True) if loc_tag else "India"
                    if not location.strip():
                        location = "Remote / India"

                    link_tag = title_tag if (title_tag and title_tag.name == "a") else card.select_one("a")
                    href = link_tag.get("href", "") if link_tag else ""
                    if href and not href.startswith("http"):
                        href = "https://internshala.com" + href

                    stip_tag = card.select_one(".stipend") or card.select_one("[class*='stipend']")
                    stipend = stip_tag.get_text(strip=True) if stip_tag else ""
                    description = f"Internship at {company}. Location: {location}. {stipend}".strip()

                    if not title or not href:
                        continue

                    if is_role_match_for_level(title, skills, level):
                        jobs.append({
                            "id": f"internshala_{hash(href)}",
                            "title": title + (" Intern" if "intern" not in title.lower() else ""),
                            "company": company,
                            "location": location + (", India" if "india" not in location.lower() else ""),
                            "url": href,
                            "application_url": href,
                            "source": "Internshala 🎓",
                            "posted_date": "Active",
                            "description": description,
                            "required_skills": []
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Internshala error: {e}")

    # If scraping failed (JS-rendered), generate deep-link search page as fallback
    if not jobs:
        search_page = f"https://internshala.com/internships/{slug}-internship/"
        jobs.append({
            "id": f"internshala_search_{slug}",
            "title": f"{slug.replace('-', ' ').title()} Internships",
            "company": "Multiple Companies on Internshala",
            "location": "India (Remote + On-site)",
            "url": search_page,
            "application_url": search_page,
            "source": "Internshala 🎓",
            "posted_date": "Live Listings",
            "description": (
                f"Browse active {slug.replace('-', ' ')} internship opportunities "
                f"across India on Internshala — India's #1 internship platform. "
                f"Click 'Apply on Internshala →' to see all matching internships."
            ),
            "required_skills": []
        })

    return jobs





# ── Source 2: LinkedIn Guest API ───────────────────────────────────────────────

def fetch_from_linkedin_india(skills: list, level: str) -> list:
    """
    Fetch jobs from LinkedIn using the public guest jobs API endpoint.
    Works without login for public job listings in India.
    """
    jobs = []
    query = _build_skill_query(skills, level, include_internship=True)

    # LinkedIn India GeoID = 102713980
    guest_urls = [
        (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={quote(query)}&location=India&geoId=102713980&start=0&count=15"
        ),
        (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={quote(query)}&location=India&geoId=102713980&f_JT=I&start=0&count=15"
            # f_JT=I → Internship job type filter
        ),
    ]

    for url in guest_urls:
        try:
            li_headers = {**HEADERS, "Referer": "https://www.linkedin.com/jobs/search/"}
            resp = requests.get(url, headers=li_headers, timeout=8)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("li")

            for card in cards[:20]:
                try:
                    title_tag = card.select_one(".base-search-card__title") or card.select_one("h3")
                    co_tag    = card.select_one(".base-search-card__subtitle") or card.select_one("h4")
                    loc_tag   = card.select_one(".job-search-card__location") or card.select_one(".base-search-card__metadata")
                    link_tag  = card.select_one("a.base-card__full-link") or card.select_one("a")

                    title   = title_tag.get_text(strip=True) if title_tag else ""
                    company = co_tag.get_text(strip=True)   if co_tag    else "Company"
                    location= loc_tag.get_text(strip=True)  if loc_tag   else "India"
                    href    = link_tag.get("href", "")       if link_tag  else ""

                    # Keep only the clean job URL (strip tracking params)
                    if href and "?" in href:
                        href = href.split("?")[0]

                    if not title or not is_valid_url(href):
                        continue

                    if is_role_match_for_level(title, skills, level):
                        jobs.append({
                            "id": f"linkedin_{hash(href)}",
                            "title": title,
                            "company": company,
                            "location": location if location else "India",
                            "url": href,
                            "application_url": href,
                            "source": "LinkedIn India 💼",
                            "posted_date": "Active",
                            "description": f"{title} at {company}. Location: {location}. Apply directly on LinkedIn.",
                            "required_skills": []
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"LinkedIn guest API error: {e}")

    return jobs


# ── Source 3: Indeed India ──────────────────────────────────────────────────────

def fetch_from_indeed_india(skills: list, level: str) -> list:
    """
    Scrape job listings from Indeed India.
    """
    jobs = []
    query = _build_skill_query(skills, level, include_internship=True)

    try:
        url = f"https://in.indeed.com/jobs?q={quote(query)}&l=India&sort=date&fromage=14"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")

            # Indeed 2024 card structure
            cards = (soup.select(".job_seen_beacon")
                     or soup.select(".jobsearch-SerpJobCard")
                     or soup.select("[data-jk]"))

            for card in cards[:20]:
                try:
                    title_tag = (card.select_one(".jobTitle a span")
                                 or card.select_one(".jobTitle")
                                 or card.select_one("h2 a"))
                    co_tag    = (card.select_one(".companyName")
                                 or card.select_one("[data-testid='company-name']"))
                    loc_tag   = (card.select_one(".companyLocation")
                                 or card.select_one("[data-testid='text-location']"))
                    link_tag  = card.select_one("a[href]")

                    title   = title_tag.get_text(strip=True) if title_tag else ""
                    company = co_tag.get_text(strip=True)    if co_tag    else "Company"
                    location= loc_tag.get_text(strip=True)   if loc_tag   else "India"

                    jk = card.get("data-jk", "")
                    if jk:
                        href = f"https://in.indeed.com/viewjob?jk={jk}"
                    elif link_tag:
                        href = link_tag.get("href", "")
                        if href and not href.startswith("http"):
                            href = "https://in.indeed.com" + href
                    else:
                        href = ""

                    if not title or not is_valid_url(href):
                        continue

                    if is_role_match_for_level(title, skills, level):
                        jobs.append({
                            "id": f"indeed_{jk or hash(href)}",
                            "title": title,
                            "company": company,
                            "location": location if location else "India",
                            "url": href,
                            "application_url": href,
                            "source": "Indeed India 🔍",
                            "posted_date": "Active",
                            "description": f"{title} at {company}. Location: {location}.",
                            "required_skills": []
                        })
                except Exception:
                    continue

    except Exception as e:
        print(f"Indeed India error: {e}")

    return jobs


# ── Source 4: Unstop (student internships & competitions) ─────────────────────

def fetch_from_unstop(skills: list, level: str) -> list:
    """
    Fetch internship listings from Unstop (formerly Dare2Compete) — India's #1 student opportunity platform.
    """
    jobs = []
    top_skills = [s.lower() for s in skills if len(s) > 2][:3]

    # Map to Unstop search terms
    if any(k in top_skills for k in ["machine learning", "ai", "python", "data science", "generative ai"]):
        keyword = "machine learning python"
    elif any(k in top_skills for k in ["react", "javascript", "frontend", "web"]):
        keyword = "web development react"
    else:
        keyword = " ".join(top_skills[:2]) or "software developer"

    try:
        url = f"https://unstop.com/api/public/opportunity/search-result?opportunity=jobs&page=1&per_page=10&query={quote(keyword)}&filters[0][filter]=opportunity_type&filters[0][value]=internship"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("data", {}).get("data", []) or []
            for item in items[:15]:
                title   = item.get("title", "")
                company = (item.get("organisation", {}) or {}).get("name", "Company")
                loc     = item.get("city", {}) or {}
                location= loc.get("name", "India") if isinstance(loc, dict) else "India"
                slug    = item.get("slug", "")
                href    = f"https://unstop.com/jobs/{slug}" if slug else ""

                if not title or not is_valid_url(href):
                    continue

                if is_role_match_for_level(title, skills, level):
                    jobs.append({
                        "id": f"unstop_{item.get('id', hash(href))}",
                        "title": title,
                        "company": company,
                        "location": location + (", India" if "india" not in location.lower() else ""),
                        "url": href,
                        "application_url": href,
                        "source": "Unstop 🚀",
                        "posted_date": item.get("deadlineDate", "")[:10] or "Active",
                        "description": item.get("description", f"{title} internship opportunity at {company} on Unstop."),
                        "required_skills": []
                    })
    except Exception as e:
        print(f"Unstop API error: {e}")

    return jobs


# ── Source 5: Remotive (Remote fallback) ───────────────────────────────────────

def fetch_from_remotive(skills: list, level: str) -> list:
    """Fetch remote-friendly jobs from Remotive (worldwide / India-eligible remote)."""
    jobs = []
    top = [s.lower() for s in skills if len(s) > 2]

    if any(k in top for k in ["machine learning", "ai", "generative ai", "deep learning", "llm", "data science"]):
        terms = ["python", "ai"]
    elif any(k in top for k in ["react", "javascript", "frontend"]):
        terms = ["react"]
    else:
        terms = ["python"]

    for term in terms[:2]:
        try:
            url = f"https://remotive.com/api/remote-jobs?search={quote(term)}&limit=20"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                for item in resp.json().get("jobs", []):
                    title    = item.get("title", "")
                    job_url  = item.get("url", "")
                    company  = item.get("company_name", "Company")
                    loc      = item.get("candidate_required_location", "Remote")
                    loc_low  = loc.lower()

                    if not is_valid_url(job_url):
                        continue

                    location_ok = any(w in loc_low for w in ["remote", "worldwide", "anywhere", "india", "asia", "global"])
                    if not location_ok:
                        continue

                    soup = BeautifulSoup(item.get("description", ""), "html.parser")
                    desc = soup.get_text(separator="\n").strip()

                    if is_role_match_for_level(title, skills, level):
                        jobs.append({
                            "id": f"remotive_{item.get('id')}",
                            "title": title,
                            "company": company,
                            "location": "Remote (India Eligible)" if "india" not in loc_low else loc,
                            "url": job_url,
                            "application_url": job_url,
                            "source": "Remotive 🌐",
                            "posted_date": item.get("publication_date", "")[:10] or "Active",
                            "description": desc[:2000],
                            "required_skills": item.get("tags", [])
                        })
        except Exception as e:
            print(f"Remotive error: {e}")
    return jobs


# ── Search entrypoint ───────────────────────────────────────────────────────────

def search_jobs_for_resume(parsed_resume: dict) -> list:
    """
    Auto-search live Indian job/internship listings based on candidate's resume.
    Sources: Internshala, LinkedIn India, Indeed India, Unstop, Remotive.
    """
    if not parsed_resume or not isinstance(parsed_resume, dict):
        return []

    skills  = parsed_resume.get("technical_skills", [])
    level   = parsed_resume.get("experience_level", "Internship / Fresher")

    raw = []

    # Priority order: most relevant for India candidates first
    print("[1/5] Fetching from Internshala...")
    raw.extend(fetch_from_internshala(skills, level))

    print("[2/5] Fetching from LinkedIn India...")
    raw.extend(fetch_from_linkedin_india(skills, level))

    print("[3/5] Fetching from Indeed India...")
    raw.extend(fetch_from_indeed_india(skills, level))

    print("[4/5] Fetching from Unstop...")
    raw.extend(fetch_from_unstop(skills, level))

    print("[5/5] Fetching from Remotive (remote fallback)...")
    raw.extend(fetch_from_remotive(skills, level))

    # Deduplicate by (title, company)
    seen, unique = set(), []
    for j in raw:
        key = (j["title"].lower()[:50], j["company"].lower()[:40])
        if key not in seen and is_valid_url(j.get("application_url")):
            seen.add(key)
            unique.append(j)

    print(f"[Done] Total unique jobs found: {len(unique)}")
    return unique


# ── URL / paste scraper ────────────────────────────────────────────────────────

def scrape_job_from_url(url: str) -> dict:
    """Scrape a single job posting from any URL; gracefully handles LinkedIn."""
    url_clean = (url or "").strip()
    if not url_clean:
        return {"status": "error", "message": "Please enter a valid URL."}

    if not url_clean.lower().startswith(("http://", "https://")):
        url_clean = "https://" + url_clean

    if not is_valid_url(url_clean):
        return {"status": "error", "message": "Invalid URL. Please enter a valid http:// or https:// job posting link."}

    url_lower = url_clean.lower()

    # LinkedIn handling
    if "linkedin.com" in url_lower:
        if "/in/" in url_lower:
            return {
                "status": "blocked",
                "message": "That's a LinkedIn User Profile, not a job posting. Use a linkedin.com/jobs/view/... URL or paste the JD text below."
            }
        try:
            resp = requests.get(url_clean, headers=HEADERS, timeout=8)
            soup = BeautifulSoup(resp.content, "html.parser")
            h1 = soup.find("h1")
            title = h1.get_text(strip=True)[:80] if h1 else "LinkedIn Job"
            if "sign in" in title.lower() or "authwall" in resp.url.lower():
                return {"status": "blocked", "message": "LinkedIn requires sign-in for this page. Paste the JD text below to run analysis."}
            for t in soup(["script", "style", "nav", "footer"]):
                t.decompose()
            text = "\n".join(l.strip() for l in soup.get_text().splitlines() if l.strip())
            return {"status": "success", "id": "linkedin_job", "title": title, "company": "LinkedIn Listing",
                    "location": "India", "url": url_clean, "application_url": url_clean,
                    "source": "LinkedIn", "posted_date": "Recent", "description": text[:3500], "required_skills": []}
        except:
            return {"status": "blocked", "message": "LinkedIn restricts automated access. Paste the JD text below to analyze this job."}

    # Internshala / Indeed / other pages
    try:
        resp = requests.get(url_clean, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            for t in soup(["script", "style", "nav", "footer", "header"]):
                t.decompose()
            title = soup.title.string[:80] if soup.title else "Job Posting"
            text = "\n".join(l.strip() for l in soup.get_text().splitlines() if l.strip())
            return {"status": "success", "id": "scraped_job", "title": title, "company": "Employer",
                    "location": "India", "url": url_clean, "application_url": url_clean,
                    "source": "Job Posting", "posted_date": "Recent", "description": text[:3500], "required_skills": []}
    except Exception as e:
        print(f"Scrape error: {e}")

    return {"status": "error", "message": "Could not load this URL automatically. Paste the job description text below to analyse it."}
