import os
import re
import json
import requests
import time
import random
from dotenv import load_dotenv

load_dotenv()

URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"

# --- MODERATION LOGIC ---
prompt_text = (
    "You are a professional HR Job Board Moderator. Analyze the following job posting. "
    "If it uses profanity, looks like a prank, is clearly fake, or doesn't look like a real "
    "job description, your decision is 'REJECT'. If it looks like a genuine, "
    "professional job posting, your decision is 'APPROVE'. "
    "You MUST respond with a JSON object containing exactly one key named 'decision'. "
    "Do not use markdown formatting, backticks, or conversational filler. Output raw, machine-readable JSON only.\n\n"
    "Example Output:\n"
    "{\n"
    "  \"decision\": \"APPROVE\"\n"
    "}\n\n"
    "Job Posting:\n"
)

def extract_json(response_string):
    """
    Finds the first '{' and the last '}' to extract the raw JSON.
    Strips away markdown wrappers or conversational fluff.
    """
    match = re.search(r'\{.*\}', response_string, re.DOTALL)
    if match:
        return match.group(0)
    return ""

def get_recruiter_keys():
    """Returns the set of keys dedicated to the UI/Recruiter public submissions."""
    ai_keys = {
        "Vardhan": os.environ.get("Vardhan_API_Key"),
        "Charan": os.environ.get("Charan_API_Key"),
        "Vishnu": os.environ.get("Vishnu_API_Key"),
        "Vidyadhar": os.environ.get("Vidyadhar_API_Key"),
        "Santhosh": os.environ.get("Santhosh_API_Key")
    }
    return [k for k in ai_keys.values() if k]

def moderate_job_post(title, company, location, description):
    """
    Sends the job details to the Groq AI Moderator API to check for spam/profanity.
    Uses Recruiter keys.
    """
    valid_keys = get_recruiter_keys()
    if not valid_keys:
        print("[AI Moderator] Error: No valid API keys found. Defaulting to APPROVE.")
        return True
        
    active_key = random.choice(valid_keys)
    job_text = f"Title: {title}\nCompany: {company}\nLocation: {location}\nDescription: {description}"
    
    HEADERS = {
        "Authorization": f"Bearer {active_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt_text + job_text}
        ],
        "temperature": 0.0
    }
    
    try:
        response = requests.post(URL, headers=HEADERS, json=payload, timeout=8)
        if response.status_code == 200:
            raw_output = response.json()['choices'][0]['message']['content'].strip()
            sanitized_json = extract_json(raw_output)
            parsed_data = json.loads(sanitized_json)
            decision = parsed_data.get('decision', 'REJECT').upper()
            print(f"[AI Moderator] Decision: {decision}")
            return decision == 'APPROVE'
        return True
    except Exception as e:
        print(f"[AI Moderator] Error: {e}")
        return True

# --- ENHANCEMENT LOGIC ---
ENHANCEMENT_PROMPT = """You are a Senior Career Consultant, Technical Recruiter, and Data Extractor.
The user will provide a raw Job Description text. Your task is to extract job metadata AND rewrite the description into a high-value 'Career Guide' to make it unique and valuable for SEO.

You MUST return a valid JSON object with the following keys and values:
- "title": The extracted Job title.
- "company": The EXACT company name. IF NO COMPANY IS MENTIONED, you MUST USE the exact phrase "Not Disclosed". DO NOT use "Confidential".
- "location": The extracted Job location.
- "job_type": e.g., "Full-time", "Contract", "Remote", etc.
- "experience": Brief summary of required experience/skills (MAX 100 characters. e.g., "5+ years, Java").
- "salary": The extracted salary or "Competitive".
- "apply_url": The primary URL or email address found in the text for applying.
- "description": The rewritten, unique Career Guide in Markdown format.

Structure for "description":
(Begin with a 3-sentence intro about the niche's importance.)

# Job Summary
(Professional summary.)

# Top 3 Critical Skills Table
(Markdown table: Skill | Why it's critical | Mastery Level)

# Interview Preparation
(5 technical questions + what interviewer looks for.)

# Resume Optimization
(10 ATS bullet points.)

# Application Strategy
(Guide on how to email the recruiter.)

# Career Roadmap
(Markdown table: Current Role | Typical Experience | Core Focus | Next Position)

Constraint: Return ONLY valid JSON. The "description" value MUST contain the full markdown with H1 (#) headings and tables."""

def enhance_job_post(jd_text):
    """
    Uses Recruiter keys to transform a raw JD into an enhanced Career Guide.
    Matches the logic of adminpost.py but uses UI-dedicated keys.
    """
    valid_keys = get_recruiter_keys()
    if not valid_keys:
        return None
        
    random.shuffle(valid_keys) # Try different keys if one fails
    
    for key in valid_keys:
        HEADERS = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": ENHANCEMENT_PROMPT},
                {"role": "user", "content": f"Here is the Job Description to process:\n\n{jd_text}"}
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=25)
            if response.status_code == 200:
                raw_output = response.json()['choices'][0]['message']['content'].strip()
                return raw_output
        except Exception:
            continue
            
    return None
