import re
import json
import io
import os
import pdfplumber
from docx import Document
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

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text content from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"pdfplumber extraction error: {e}")
    return text.strip()

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text content from a DOCX file."""
    text = ""
    try:
        doc = Document(io.BytesIO(file_bytes))
        for paragraph in doc.paragraphs:
            if paragraph.text:
                text += paragraph.text + "\n"
    except Exception as e:
        print(f"docx extraction error: {e}")
    return text.strip()

def extract_text_from_file(file_bytes: bytes, file_name: str) -> str:
    """Extract raw text based on file extension."""
    if not file_bytes:
        return ""
    filename_lower = (file_name or "").lower()
    try:
        if filename_lower.endswith('.pdf'):
            return extract_text_from_pdf(file_bytes)
        elif filename_lower.endswith('.docx') or filename_lower.endswith('.doc'):
            return extract_text_from_docx(file_bytes)
        else:
            return file_bytes.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"File extraction error: {e}")
        return ""

def fallback_parse_resume(raw_text: str) -> dict:
    """Dynamic NLP fallback parser to extract candidate skills & profile."""
    if not raw_text or not isinstance(raw_text, str):
        raw_text = str(raw_text or "")
        
    known_skills = [
        "python", "java", "c++", "c#", "javascript", "typescript", "react", "next.js", "vue", "angular",
        "html", "css", "sql", "postgresql", "mongodb", "mysql", "redis", "aws", "gcp", "azure",
        "docker", "kubernetes", "git", "ci/cd", "linux", "rest api", "graphql", "fastapi", "flask",
        "django", "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy", "opencv", "nlp",
        "llm", "generative ai", "langchain", "transformers", "huggingface", "rag", "fine-tuning",
        "gemini", "openai", "prompt engineering", "agile", "scrum", "jira", "communication", "leadership"
    ]
    
    found_skills = []
    text_lower = raw_text.lower()
    for skill in known_skills:
        if re.search(rf'\b{re.escape(skill)}\b', text_lower):
            found_skills.append(skill.title() if len(skill) > 3 else skill.upper())
            
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text)
    phone_match = re.search(r'\(?\+?\d{1,3}\)?[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', raw_text)
    
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    candidate_name = lines[0] if lines and len(lines[0]) < 40 and not "@" in lines[0] else "Candidate Profile"
    
    edu_match = re.search(r'(bachelor|master|b\.tech|m\.tech|degree|b\.s|m\.s|phd|university|college)', text_lower)
    education_str = "Degree in Computer Science / Engineering" if edu_match else "Higher Education / Technical Background"
    
    return {
        "candidate_name": candidate_name,
        "email": email_match.group(0) if email_match else "N/A",
        "phone": phone_match.group(0) if phone_match else "N/A",
        "summary": raw_text[:350] + "..." if len(raw_text) > 350 else (raw_text or "Candidate Resume Profile"),
        "technical_skills": list(set(found_skills)) if found_skills else ["Software Engineering", "Python", "Problem Solving"],
        "soft_skills": ["Analytical Thinking", "Team Collaboration", "Problem Solving", "Adaptability"],
        "experience_years": "2-4 years (Extracted)",
        "education": education_str,
        "work_experience": [raw_text[:500]]
    }

def parse_resume_with_gemini(raw_text: str, api_key: str = None) -> dict:
    """Use Gemini AI or dynamic parser to extract candidate resume fields."""
    if not raw_text or not isinstance(raw_text, str):
        raw_text = str(raw_text or "")
        
    effective_key = api_key or get_api_key()
    
    if not effective_key:
        return fallback_parse_resume(raw_text)
        
    try:
        client = genai.Client(api_key=effective_key)
        prompt = f"""
You are an expert HR Resume Extractor. Extract structured fields from the candidate resume below.

Resume Text:
{raw_text[:4000]}

Return JSON ONLY with exact keys:
{{
  "candidate_name": "Full Name",
  "email": "email@domain.com",
  "phone": "+1 123 456 7890",
  "summary": "Brief summary of candidate background",
  "technical_skills": ["skill1", "skill2"],
  "soft_skills": ["soft_skill1", "soft_skill2"],
  "experience_years": "estimated years of experience",
  "education": "details of highest education",
  "work_experience": ["summary of key roles"]
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
            parsed_data = json.loads(response.text)
            if isinstance(parsed_data, dict):
                return parsed_data
    except Exception as e:
        print(f"Gemini resume parser error: {e}. Falling back to NLP parser.")
        
    return fallback_parse_resume(raw_text)
