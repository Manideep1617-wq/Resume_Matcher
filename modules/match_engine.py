import re
import json
import math
from google import genai
from google.genai import types

def calculate_rule_based_match(parsed_resume: dict, job_description: str, job_skills: list = None) -> dict:
    """
    Fallback NLP semantic keyword overlap score generator.
    """
    resume_skills = [s.lower() for s in parsed_resume.get("technical_skills", []) + parsed_resume.get("soft_skills", [])]
    job_desc_lower = job_description.lower()
    
    # Common tech skills dictionary for detection in job desc
    common_tech_terms = [
        "python", "java", "c++", "javascript", "typescript", "react", "node.js", "vue", "angular",
        "html", "css", "sql", "postgresql", "mongodb", "mysql", "redis", "aws", "gcp", "azure",
        "docker", "kubernetes", "git", "ci/cd", "linux", "rest api", "graphql", "fastapi", "flask",
        "django", "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy", "opencv", "nlp",
        "llm", "generative ai", "langchain", "transformers", "huggingface", "rag", "fine-tuning",
        "gemini", "openai", "prompt engineering", "agile", "scrum", "jira", "vector db", "faiss", "chromadb"
    ]
    
    # Find all tech terms present in job description
    extracted_job_skills = set(job_skills if job_skills else [])
    for term in common_tech_terms:
        if re.search(rf'\b{re.escape(term)}\b', job_desc_lower):
            extracted_job_skills.add(term)
            
    if not extracted_job_skills:
        extracted_job_skills = set(["python", "communication", "git", "problem solving", "rest api"])
        
    extracted_job_skills = list(extracted_job_skills)
    
    # Compare overlap
    matching_skills = []
    missing_skills = []
    
    for skill in extracted_job_skills:
        skill_clean = skill.lower()
        if any(skill_clean in r_skill or r_skill in skill_clean for r_skill in resume_skills):
            matching_skills.append(skill.title() if len(skill) > 3 else skill.upper())
        else:
            missing_skills.append(skill.title() if len(skill) > 3 else skill.upper())
            
    total_reqs = len(extracted_job_skills)
    match_count = len(matching_skills)
    
    if total_reqs > 0:
        base_score = int((match_count / total_reqs) * 100)
    else:
        base_score = 75
        
    # Clamp score between 40 and 95
    overall_score = min(max(base_score, 45), 95)
    tech_score = min(max(overall_score + 5, 50), 98)
    soft_score = min(max(overall_score - 5, 55), 92)
    exp_score = min(max(overall_score - 2, 50), 90)
    
    return {
        "overall_score": overall_score,
        "technical_score": tech_score,
        "soft_skills_score": soft_score,
        "experience_relevance_score": exp_score,
        "matching_skills": matching_skills if matching_skills else ["Python", "Git", "Problem Solving"],
        "missing_skills": missing_skills if missing_skills else ["Docker", "Kubernetes"],
        "key_strengths": [
            "Strong foundation in core programming languages.",
            "Relevant experience matching project requirements.",
            "Clear technical skill stack."
        ],
        "improvement_areas": [
            f"Add explicit bullet points demonstrating hands-on experience with: {', '.join(missing_skills[:3])}.",
            "Quantify project outcomes with concrete metrics (e.g. % performance increase, users served).",
            "Align resume summary section with keywords from the target job post."
        ],
        "tailored_resume_bullets": [
            f"Architected scalable solution utilizing {matching_skills[0] if matching_skills else 'Python'} to optimize data workflows.",
            f"Integrated RESTful APIs and modern backend frameworks to enhance application responsiveness.",
            f"Collaborated in an Agile environment using Git version control and modern testing practices."
        ],
        "cover_letter": f"""Dear Hiring Team,

I am writing to express my strong interest in the target role at your company. With a solid foundation in {', '.join(matching_skills[:3] if matching_skills else ['Python', 'Software Development'])}, I am confident in my ability to contribute effectively to your engineering team.

My background aligns well with your team's objectives. I have hands-on experience developing clean software solutions and working with modern tools. I am eager to bring my problem-solving skills and enthusiasm for innovation to this position.

Thank you for your time and consideration. I look forward to discussing how my experience can add value to your team.

Sincerely,
Candidate"""
    }

def analyze_resume_job_match(parsed_resume: dict, job_title: str, job_description: str, api_key: str = None) -> dict:
    """
    Perform deep LLM semantic matching between Parsed Resume and Job Description using Gemini API.
    """
    if not api_key:
        return calculate_rule_based_match(parsed_resume, job_description)
        
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
You are an expert HR Recruiter & Generative AI Career Advisor.
Evaluate the candidate's parsed resume profile against the job description.

Candidate Profile:
{json.dumps(parsed_resume, indent=2)}

Job Title: {job_title}
Job Description:
{job_description[:3500]}

Analyze the match and return JSON ONLY with exact structure:
{{
  "overall_score": 85, (integer 0 to 100)
  "technical_score": 88, (integer 0 to 100)
  "soft_skills_score": 80, (integer 0 to 100)
  "experience_relevance_score": 82, (integer 0 to 100)
  "matching_skills": ["Skill1", "Skill2", "Skill3"],
  "missing_skills": ["MissingSkill1", "MissingSkill2"],
  "key_strengths": ["Strength 1", "Strength 2", "Strength 3"],
  "improvement_areas": ["Area 1", "Area 2", "Area 3"],
  "tailored_resume_bullets": ["Action verb bullet 1 incorporating job keywords", "Action verb bullet 2"],
  "cover_letter": "A compelling, professional 3-paragraph cover letter customized for this job"
}}
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"Error in Gemini match analysis: {e}. Using rule-based calculation fallback.")
        return calculate_rule_based_match(parsed_resume, job_description)
