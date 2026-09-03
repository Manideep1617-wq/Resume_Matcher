import re
import json
import os
from google import genai
from google.genai import types
from modules.resume_parser import get_api_key

TECH_KEYWORDS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "ruby", "go", "golang", "rust", "php", "swift", "kotlin", "scala", "r", "matlab", "sql", "bash", "powershell",
    "react", "react native", "next.js", "vue", "angular", "node.js", "express", "django", "flask", "fastapi", "spring boot", "dotnet", "asp.net", "laravel", "bootstrap", "tailwind",
    "generative ai", "llm", "large language models", "rag", "retrieval augmented generation", "langchain", "llamaindex", "openai", "gemini", "anthropic", "claude", "transformers", "huggingface", "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy", "opencv", "nlp", "natural language processing", "computer vision", "spacy", "nltk", "fine-tuning", "prompt engineering", "vector database", "chromadb", "faiss", "pinecone", "qdrant", "weaviate",
    "aws", "amazon web services", "gcp", "google cloud", "azure", "docker", "kubernetes", "git", "github", "gitlab", "ci/cd", "terraform", "ansible", "jenkins", "linux", "unix", "rest api", "graphql", "microservices", "kafka", "rabbitmq", "redis", "elasticsearch", "mongodb", "postgresql", "mysql", "sqlite", "oracle", "snowflake", "databricks", "spark", "hadoop",
    "pytest", "unittest", "selenium", "cypress", "playwright", "agile", "scrum", "jira", "confluence", "tdd", "clean code", "system design", "object-oriented programming", "oop"
]

def extract_keywords_from_text(text: str) -> set:
    """Extract technical keywords dynamically from text."""
    if not text or not isinstance(text, str):
        return set()
    text_lower = text.lower()
    found = set()
    for kw in TECH_KEYWORDS:
        pattern = rf'(?:^|[\s,.\-\/()\'"])' + re.escape(kw) + rf'(?:$|[\s,.\-\/()\'"])'
        if re.search(pattern, text_lower):
            if kw in ["aws", "gcp", "sql", "rag", "llm", "nlp", "oop", "tdd", "api", "rest api", "ci/cd", "r", "c++", "c#"]:
                found.add(kw.upper())
            elif kw in ["node.js", "next.js", "react native"]:
                found.add(kw.title())
            else:
                found.add(kw.title())
    return found

def calculate_multi_factor_match(parsed_resume: dict, job: dict, search_query: str = "") -> dict:
    """
    Compute multi-factor match score combining:
    1. Role Relevance Score (0-30 pts)
    2. Resume Skill Match Score (0-40 pts)
    3. Experience / Level Match Score (0-20 pts)
    4. Domain Fit (0-10 pts)
    """
    if not parsed_resume or not isinstance(parsed_resume, dict):
        parsed_resume = {}
        
    job_title = str(job.get("title", "") or "")
    job_desc = str(job.get("description", "") or "")
    candidate_level = str(parsed_resume.get("experience_level", "Internship / Fresher"))
    
    # 1. Candidate's skills
    resume_skills_raw = set([s.strip().title() for s in parsed_resume.get("technical_skills", []) if isinstance(s, str) and s.strip()])
    resume_text = (str(parsed_resume.get("summary", "")) + " " + " ".join([str(x) for x in parsed_resume.get("work_experience", [])])).lower()
    resume_extracted = extract_keywords_from_text(resume_text)
    candidate_skills = resume_skills_raw.union(resume_extracted)
    candidate_skills_lower = {s.lower() for s in candidate_skills}

    # 2. Job's extracted requirements
    job_skills_extracted = extract_keywords_from_text(job_desc)
    if not job_skills_extracted:
        job_skills_extracted = extract_keywords_from_text(job_title)
        if not job_skills_extracted:
            job_skills_extracted = {"Python", "Git", "REST API", "SQL"}
            
    # 3. Dynamic Skill Intersect & Difference
    matching_skills = []
    missing_skills = []
    
    for j_skill in job_skills_extracted:
        j_lower = j_skill.lower()
        if any(j_lower == c_lower or j_lower in c_lower or c_lower in j_lower for c_lower in candidate_skills_lower):
            matching_skills.append(j_skill)
        else:
            missing_skills.append(j_skill)
            
    matching_skills = sorted(list(set(matching_skills)))
    missing_skills = sorted(list(set(missing_skills)))

    # --- SCORE COMPONENTS ---
    # Factor A: Skill Match Score (0 to 40 pts)
    total_reqs = len(job_skills_extracted)
    skill_match_ratio = (len(matching_skills) / total_reqs) if total_reqs > 0 else 0.7
    skill_pts = skill_match_ratio * 40.0

    # Factor B: Role Relevance (0 to 30 pts)
    q_lower = (search_query or job_title).lower()
    t_lower = job_title.lower()
    role_pts = 30.0 if any(word in t_lower for word in q_lower.split() if len(word) > 2) else 18.0

    # Factor C: Experience Level Compatibility (0 to 20 pts)
    level_pts = 20.0
    if "intern" in candidate_level.lower() or "fresher" in candidate_level.lower():
        if any(s in t_lower for s in ["senior", "sr.", "lead", "principal", "architect", "manager", "director"]):
            level_pts = 0.0  # Massive penalty for senior roles
        elif "intern" in t_lower or "junior" in t_lower or "entry" in t_lower or "trainee" in t_lower:
            level_pts = 20.0
        else:
            level_pts = 14.0  # General non-senior role

    # Factor D: Domain & Technology Fit (0 to 10 pts)
    tech_pts = 10.0 if len(matching_skills) >= 2 else 5.0

    # Final Combined Score Calculation
    total_score = int(min(max(skill_pts + role_pts + level_pts + tech_pts, 35), 98))

    # Candidate Name & Why it matches summary
    candidate_name = parsed_resume.get("candidate_name", "Candidate")
    
    if matching_skills:
        why_matches = f"Your resume demonstrates strong technical proficiency in {', '.join(matching_skills[:3])} required for this role."
    else:
        why_matches = f"Your background aligns with the core requirements of this position."

    strengths = [
        f"Demonstrated technical skills matching target posting: {', '.join(matching_skills[:4]) if matching_skills else 'General Software Engineering'}.",
        f"Experience level compatible with {candidate_level} requirements."
    ]

    improvements = [
        f"Consider adding key missing technologies: {', '.join(missing_skills[:3]) if missing_skills else 'Quantifiable metrics'}."
    ]

    bullets = [
        f"Engineered scalable solutions utilizing {matching_skills[0] if matching_skills else 'Python'} to optimize application workflows.",
        f"Collaborated cross-functionally following modern software engineering practices."
    ]

    cover_letter = f"""Dear Hiring Team,

I am writing to express my strong enthusiasm for the {job_title} position at {job.get('company', 'your organization')}. With a solid foundation in {', '.join(matching_skills[:3]) if matching_skills else 'software development'}, I am eager to contribute to your team.

My background aligns well with your role's focus. My experience with {', '.join(list(candidate_skills)[:4]) if candidate_skills else 'core programming stacks'} directly prepares me for these responsibilities.

Thank you for your time and consideration. I look forward to discussing how I can add value to your team.

Sincerely,
{candidate_name}"""

    return {
        "overall_score": total_score,
        "technical_score": int(min(max(total_score + 3, 30), 98)),
        "soft_skills_score": int(min(max(total_score - 2, 40), 92)),
        "experience_relevance_score": int(min(max(level_pts * 5, 30), 95)),
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "why_matches": why_matches,
        "key_strengths": strengths,
        "improvement_areas": improvements,
        "tailored_resume_bullets": bullets,
        "cover_letter": cover_letter
    }

def analyze_resume_job_match(parsed_resume: dict, job_title: str, job_description: str, api_key: str = None) -> dict:
    """Analyze single job vs resume for detailed Tab 3 dashboard."""
    dummy_job = {"title": job_title, "description": job_description, "company": "Target Company"}
    effective_key = api_key or get_api_key()
    
    if not effective_key:
        return calculate_multi_factor_match(parsed_resume, dummy_job, job_title)
        
    try:
        client = genai.Client(api_key=effective_key)
        prompt = f"""
You are an expert HR AI Evaluator. Analyze the candidate resume profile against the job description below.

Candidate Profile:
{json.dumps(parsed_resume, indent=2)}

Job Title: {job_title}
Job Description:
{str(job_description)[:3500]}

Return JSON ONLY with exact keys:
{{
  "overall_score": 85,
  "technical_score": 88,
  "soft_skills_score": 80,
  "experience_relevance_score": 82,
  "matching_skills": ["Skill1", "Skill2"],
  "missing_skills": ["MissingSkill1", "MissingSkill2"],
  "why_matches": "One concise sentence explaining why candidate fits this job",
  "key_strengths": ["Strength 1", "Strength 2"],
  "improvement_areas": ["Improvement 1", "Improvement 2"],
  "tailored_resume_bullets": ["Action verb bullet 1", "Action verb bullet 2"],
  "cover_letter": "A custom 3-paragraph cover letter"
}}
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        if response and hasattr(response, "text") and response.text:
            res = json.loads(response.text)
            if isinstance(res, dict):
                return res
    except Exception as e:
        print(f"Gemini match error: {e}. Falling back to multi-factor match.")
        
    return calculate_multi_factor_match(parsed_resume, dummy_job, job_title)

def rank_jobs_for_candidate(parsed_resume: dict, jobs: list, search_query: str = "") -> list:
    """
    Rank job listings by multi-factor combined score (Final Score descending).
    Injects match_score, matching_skills, missing_skills, and why_matches directly into each job object.
    """
    if not jobs:
        return []
        
    ranked = []
    for job in jobs:
        analysis = calculate_multi_factor_match(parsed_resume, job, search_query)
        job_copy = dict(job)
        job_copy["match_score"] = analysis["overall_score"]
        job_copy["matching_skills"] = analysis["matching_skills"]
        job_copy["missing_skills"] = analysis["missing_skills"]
        job_copy["why_matches"] = analysis["why_matches"]
        job_copy["match_analysis"] = analysis
        ranked.append(job_copy)
        
    # Sort descending by match_score
    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked
