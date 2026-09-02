import re
import json
import io
import pdfplumber
from docx import Document
from google import genai
from google.genai import types

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
    filename_lower = file_name.lower()
    if filename_lower.endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif filename_lower.endswith('.docx') or filename_lower.endswith('.doc'):
        return extract_text_from_docx(file_bytes)
    elif filename_lower.endswith('.txt'):
        return file_bytes.decode('utf-8', errors='ignore')
    else:
        return file_bytes.decode('utf-8', errors='ignore')

def fallback_parse_resume(raw_text: str) -> dict:
    """Rule-based fallback parser when LLM is unavailable."""
    # Basic skill keyword extraction list
    known_skills = [
        "python", "java", "c++", "javascript", "typescript", "react", "node.js", "vue", "angular",
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
            
    # Extract email & phone
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text)
    phone_match = re.search(r'\(?\+?\d{1,3}\)?[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', raw_text)
    
    return {
        "candidate_name": "Candidate",
        "email": email_match.group(0) if email_match else "N/A",
        "phone": phone_match.group(0) if phone_match else "N/A",
        "summary": raw_text[:300] + "..." if len(raw_text) > 300 else raw_text,
        "technical_skills": found_skills if found_skills else ["General Technical Skills"],
        "soft_skills": ["Problem Solving", "Team Collaboration", "Communication"],
        "experience_years": "2-4 years (Estimated)",
        "education": "Degree in Computer Science or related field",
        "work_experience": [raw_text[:400]]
    }

def parse_resume_with_gemini(raw_text: str, api_key: str) -> dict:
    """Use Gemini API to extract structured fields from resume text."""
    if not api_key:
        return fallback_parse_resume(raw_text)
        
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
You are an expert HR AI Assistant. Analyze the following resume text and return a JSON object with structured details.

Resume Text:
{raw_text[:4000]}

Return JSON ONLY with exact keys:
{{
  "candidate_name": "string",
  "email": "string",
  "phone": "string",
  "summary": "string brief summary of candidate background",
  "technical_skills": ["skill1", "skill2", ...],
  "soft_skills": ["soft_skill1", "soft_skill2", ...],
  "experience_years": "estimated total years of experience e.g. 3 years",
  "education": "string details of highest education",
  "work_experience": ["brief summary of role 1", "brief summary of role 2"]
}}
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        parsed_data = json.loads(response.text)
        return parsed_data
    except Exception as e:
        print(f"Gemini resume parsing error: {e}. Falling back to rule-based parser.")
        return fallback_parse_resume(raw_text)
