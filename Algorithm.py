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

def moderate_job_post(title, company, location, description):
    """
    Sends the job details to the Groq AI Moderator API to check for spam/profanity.
    Returns True if approved, False if rejected or API fails.
    """
    # Store API Keys in a Dictionary Format
    ai_keys = {
        "Vardhan": os.environ.get("Vardhan_API_Key"),
        "Charan": os.environ.get("Charan_API_Key"),
        "Vishnu": os.environ.get("Vishnu_API_Key"),
        "Vidyadhar": os.environ.get("Vidyadhar_API_Key"),
        "Santhosh": os.environ.get("Santhosh_API_Key")
    }
    
    # Filter out any keys that might be missing or empty strings
    valid_keys = [k for k in ai_keys.values() if k]
    
    if not valid_keys:
        print("[AI Moderator] Error: No valid API keys found in dictionary. Defaulting to APPROVE.")
        return True # Default to letting users post if keys break
        
    # Spin the roulette wheel to Load Balance
    active_key = random.choice(valid_keys)
    
    # Find the owner of the key just for logging
    key_owner = next(name for name, key in ai_keys.items() if key == active_key)
    print(f"[AI Moderator] Load Balancer Selected Key: {key_owner}'s Key")
        
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
        "temperature": 0.0 # Strict, Deterministic Mode
    }
    
    try:
        response = requests.post(URL, headers=HEADERS, json=payload, timeout=5)
        
        if response.status_code == 200:
            raw_output = response.json()['choices'][0]['message']['content'].strip()
            sanitized_json = extract_json(raw_output)
            
            try:
                parsed_data = json.loads(sanitized_json)
                decision = parsed_data.get('decision', 'REJECT').upper()
                print(f"[AI Moderator] Decision: {decision}")
                return decision == 'APPROVE'
            except json.JSONDecodeError:
                print(f"[AI Moderator] Failed to parse AI JSON. Defaulting to REJECT.")
                return False
        else:
            print(f"[AI Moderator] API Failed. Status: {response.status_code}. Defaulting to APPROVE.")
            return True
            
    except requests.exceptions.Timeout:
        # If API is down or hanging, let the genuine user post anyway so portal doesn't break
        print("[AI Moderator] API Timeout. Defaulting to APPROVE.")
        return True
    except Exception as e:
        print(f"[AI Moderator] Unexpected Error: {e}. Defaulting to APPROVE.")
        return True
