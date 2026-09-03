import re
import json
import os
from google import genai
from google.genai import types

def get_api_key() -> str:
    """Safely retrieve Gemini API Key from environment or Streamlit Secrets."""
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
    return str(key or "").strip()

TECH_KEYWORDS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "ruby", "go", "golang", "rust", "php", "swift", "kotlin", "scala", "r", "matlab", "sql", "bash", "powershell",
    "react", "react native", "next.js", "vue", "angular", "node.js", "express", "django", "flask", "fastapi", "spring boot", "dotnet", "asp.net", "laravel", "bootstrap", "tailwind",
    "generative ai", "llm", "large language models", "rag", "retrieval augmented generation", "langchain", "llamaindex", "openai", "gemini", "anthropic", "claude", "transformers", "huggingface", "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy", "opencv", "nlp", "natural language processing", "computer vision", "spacy", "nltk", "fine-tuning", "prompt engineering", "vector database", "chromadb", "faiss", "pinecone", "qdrant", "weaviate",
    "aws", "amazon web services", "gcp", "google cloud", "azure", "docker", "kubernetes", "git", "github", "gitlab", "ci/cd", "terraform", "ansible", "jenkins", "linux", "unix", "rest api", "graphql", "microservices", "kafka", "rabbitmq", "redis", "elasticsearch", "mongodb", "postgresql", "mysql", "sqlite", "oracle", "snowflake", "databricks", "spark", "hadoop",
    "pytest", "unittest", "selenium", "cypress", "playwright", "agile", "scrum", "jira", "confluence", "tdd", "clean code", "system design", "object-oriented programming", "oop"
]

def extract_keywords_from_text(text: str) -> set:
    """Extract recognized technical terms dynamically from any text block."""
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

def calculate_dynamic_rule_based_match(parsed_resume: dict, job_description: str, job_title: str) -> dict:
    """Dynamic NLP semantic comparison between candidate resume and target job."""
    if not parsed_resume or not isinstance(parsed_resume, dict):
        parsed_resume = {}
    job_description = str(job_description or "")
    job_title = str(job_title or "Target Role")
    
    resume_skills_raw = set([s.strip().title() for s in parsed_resume.get("technical_skills", []) if isinstance(s, str) and s.strip()])
    resume_text = (str(parsed_resume.get("summary", "")) + " " + " ".join([str(x) for x in parsed_resume.get("work_experience", [])])).lower()
    resume_extracted = extract_keywords_from_text(resume_text)
    candidate_all_skills = resume_skills_raw.union(resume_extracted)
    
    job_skills_extracted = extract_keywords_from_text(job_description)
    if not job_skills_extracted:
        job_skills_extracted = extract_keywords_from_text(job_title)
        if not job_skills_extracted:
            job_skills_extracted = {"Python", "Git", "REST API", "SQL", "Problem Solving"}
            
    matching_skills = []
    missing_skills = []
    
    candidate_skills_lower = {s.lower() for s in candidate_all_skills}
    
    for j_skill in job_skills_extracted:
        j_lower = j_skill.lower()
        if any(j_lower == c_lower or j_lower in c_lower or c_lower in j_lower for c_lower in candidate_skills_lower):
            matching_skills.append(j_skill)
        else:
            missing_skills.append(j_skill)
            
    matching_skills = sorted(list(set(matching_skills)))
    missing_skills = sorted(list(set(missing_skills)))
    
    total_reqs = len(job_skills_extracted)
    match_count = len(matching_skills)
    
    raw_pct = (match_count / total_reqs) * 100 if total_reqs > 0 else 70.0
    overall_score = int(min(max(raw_pct, 35), 96))
    tech_score = int(min(max(overall_score + (5 if match_count > 2 else -5), 30), 98))
    soft_score = int(min(max(overall_score + 2, 45), 92))
    exp_score = int(min(max(overall_score - 3, 40), 95))
    
    candidate_name = parsed_resume.get("candidate_name", "Candidate")
    
    strengths = []
    if matching_skills:
        strengths.append(f"Strong overlap in core target technologies: {', '.join(matching_skills[:4])}.")
    else:
        strengths.append("General technical experience outlined in profile.")
    if candidate_all_skills:
        strengths.append(f"Demonstrated technical toolkit including {', '.join(list(candidate_all_skills)[:4])}.")
    strengths.append(f"Relevant background applicable to {job_title} duties.")
    
    improvements = []
    if missing_skills:
        improvements.append(f"Missing explicit key skills required for this role: {', '.join(missing_skills[:4])}.")
        improvements.append(f"Highlight projects demonstrating hands-on experience with {missing_skills[0]} to boost ATS match.")
    else:
        improvements.append("Resume covers all core technical requirements. Consider adding quantified performance metrics.")
    improvements.append(f"Tailor professional summary to directly reflect keywords from the '{job_title}' job post.")
    
    bullets = []
    if matching_skills:
        bullets.append(f"Engineered production-grade applications using {matching_skills[0]} and modern software architecture principles.")
    else:
        bullets.append(f"Architected scalable backend and frontend modules to optimize data workflows.")
    if missing_skills:
        bullets.append(f"Expanded technical domain knowledge by integrating {missing_skills[0]} and cloud infrastructure tools.")
    bullets.append(f"Collaborated cross-functionally to deliver feature releases on schedule following Agile methodologies.")
    
    cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong enthusiasm for the {job_title} position. With my background in {', '.join(matching_skills[:3]) if matching_skills else 'software development'}, I am confident in my ability to deliver immediate value to your engineering team.

In reviewing the requirements for the {job_title} role, I noted your team's focus on building scalable systems. My experience with {', '.join(list(candidate_all_skills)[:4]) if candidate_all_skills else 'modern tech stacks'} directly aligns with your technical roadmap. Additionally, I am actively expanding my expertise in {', '.join(missing_skills[:2]) if missing_skills else 'advanced system architecture'} to drive innovation across projects.

I would welcome the opportunity to discuss how my skill set and problem-solving approach fit your team's objectives. Thank you for your time and consideration.

Sincerely,
{candidate_name}"""

    return {
        "overall_score": overall_score,
        "technical_score": tech_score,
        "soft_skills_score": soft_score,
        "experience_relevance_score": exp_score,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "key_strengths": strengths,
        "improvement_areas": improvements,
        "tailored_resume_bullets": bullets,
        "cover_letter": cover_letter
    }

def analyze_resume_job_match(parsed_resume: dict, job_title: str, job_description: str, api_key: str = None) -> dict:
    """Perform candidate-specific semantic match analysis using Gemini AI or dynamic NLP matching."""
    effective_key = api_key or get_api_key()
    
    if not effective_key:
        return calculate_dynamic_rule_based_match(parsed_resume, job_description, job_title)
        
    try:
        client = genai.Client(api_key=effective_key)
        prompt = f"""
You are an expert HR AI Evaluator. Analyze the SPECIFIC candidate resume profile against the SPECIFIC job description provided below. Compute dynamic, accurate candidate-specific results.

Candidate Profile:
{json.dumps(parsed_resume, indent=2)}

Job Title: {job_title}
Job Description:
{str(job_description)[:3500]}

Return JSON ONLY with exact keys:
{{
  "overall_score": 82,
  "technical_score": 85,
  "soft_skills_score": 80,
  "experience_relevance_score": 78,
  "matching_skills": ["Skill1_Found_In_Both", "Skill2_Found_In_Both"],
  "missing_skills": ["CriticalSkillInJobMissingFromResume1", "MissingSkill2"],
  "key_strengths": ["Specific strength relative to this exact job 1", "Specific strength 2"],
  "improvement_areas": ["Specific missing keyword gap 1", "Specific improvement 2"],
  "tailored_resume_bullets": ["Action verb bullet incorporating job keywords 1", "Action verb bullet 2"],
  "cover_letter": "A custom 3-paragraph cover letter tailored specifically for candidate and job"
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
            result = json.loads(response.text)
            if isinstance(result, dict):
                return result
    except Exception as e:
        print(f"Gemini API matching error: {e}. Falling back to dynamic NLP match.")
        
    return calculate_dynamic_rule_based_match(parsed_resume, job_description, job_title)
