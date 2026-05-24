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
    """Returns the main active local Groq API Key."""
    key = os.environ.get("AI_Key")
    return [key] if key else []

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
        
        # If status code is not 200 (e.g., 401 Unauthorized, 429 Too Many Requests)
        print(f"[AI Moderator] API Error: {response.status_code} - {response.text}")
        return None 
        
    except Exception as e:
        print(f"[AI Moderator] System Error: {e}")
        return None

# --- ENHANCEMENT LOGIC ---
ENHANCEMENT_PROMPT = """You are a Senior Career Consultant, Technical Recruiter, and Data Extractor.
The user will provide a raw Job Description text. Your task is to extract job metadata AND rewrite the description into a high-value 'Career Guide' to make it unique and valuable for SEO.

You MUST return a valid JSON object with the following keys and values:
- "title": The extracted Job title.
- "company": The EXACT company name. IF NO COMPANY IS MENTIONED, you MUST USE the exact phrase "Not Disclosed". DO NOT use "Confidential".
- "location": The extracted Job location. Format it as: "City, State - WorkMode - Country". Rules: (1) Always append the country at the end (USA, India, Australia, UK, Canada, etc.) inferred from the city/state in the JD. (2) Include work mode (Onsite, Remote, Hybrid) if mentioned, BUT only if the location has a real city — do NOT repeat 'Remote' twice. (3) If the job is fully remote with NO specific city mentioned, just write: "Remote - Country" (e.g. "Remote - USA"). (4) If there IS a city, include work mode: "San Jose, CA - Onsite - USA". (5) More examples: "Sydney - Remote - Australia", "Hyderabad - Hybrid - India", "New York, NY - USA", "London - UK", "Remote - USA".
- "job_type": MUST strictly be an employment type: e.g., "Full-time", "Part-time", "Internship", or "Contract". DO NOT use location modifiers like "Remote" or "Hybrid" here.
- "experience": Brief summary of required experience/skills (MAX 100 characters. e.g., "5+ years, Java").
- "salary": The extracted salary. IF NO salary is mentioned in the text: If it is a "Contract" role, intelligently guess a highly realistic approximate hourly rate based on the role and experience (e.g., "$50 - $60/hr"). If it is a "Full-time" role, guess an approximate annual salary (e.g., "$110k - $130k/yr"). DO NOT use words like "Competitive" or "Not Specified" anymore; always provide a numerical estimate if missing.
- "duration": The project/contract duration (e.g. "6 Months", "Long-term"). Extracted from text.
- "apply_url": The primary URL or email address found in the text for applying. Look specifically for links following keywords like "Apply Here:", "Link:", "LinkedIn:", or "Application:". NEVER omit an application URL if one is present. If multiple are found, pick the most direct one. If none found, leave as empty string "".
- "description": The rewritten, humanized Job Review in Markdown format.

The "description" string MUST read like an honest, peer-to-peer technical breakdown from a Senior Engineer. DO NOT use robotic structures, generic marketing fluff, or AI cliches like "In today's fast-paced world", "Master the art of", or "Elevate your career". 

Write the description using the following narrative flow, using standard Markdown for formatting (use `###` for headings, `**` for bold):

(Begin directly with a 2-3 sentence honest take on the job. Skip the fluff. Tell the developer exactly what this job is and why it matters in the real world.)

### What You'll Actually Be Doing
(Write a conversational paragraph breaking down what the day-to-day actually looks like. Be specific and grounded. Talk about the real challenges they will face.)

### The Core Tech Stack
(Do not give a generic bulleted list. Write a paragraph highlighting the absolute most critical skills the candidate MUST know, and explain *why* the company needs them based on the JD. Sound like a senior dev explaining it over coffee.)

### Interview Expectations
(Provide 2 highly specific, difficult technical questions the candidate will likely face. Explain what the hiring manager is secretly looking for in the answer. Use conversational language, not lists.)

### Application Advice
(Give the candidate realistic advice on how to tweak their resume for this specific role. Tell them exactly which keywords from the JD they need to include to bypass the ATS, but weave it into a human paragraph instead of a robotic bulleted list.)

Constraint: Return ONLY valid JSON. The "description" value MUST contain the full markdown string, completely free of AI-isms, with conversational paragraphs."""

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
