import os
import random
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL = "openai/gpt-oss-120b"

# Local/Admin only key
API_KEYS = [
    ("Main_AI_Key", os.getenv("AI_Key")),
]

SYSTEM_PROMPT = """You are a Senior Career Consultant, Technical Recruiter, and Data Extractor.
The user will provide a raw Job Description text. Your task is to extract job metadata AND rewrite the description into a high-value 'Career Guide' to make it unique and valuable for SEO.

You MUST return a valid JSON object with the following keys and values:
- "title": The extracted Job title.
- "company": The EXACT company name. IF NO COMPANY IS MENTIONED, you MUST USE the exact phrase "Not Disclosed". DO NOT use "Confidential". DO NOT guess or hallucinate.
- "location": The extracted Job location.
- "job_type": MUST strictly be an employment type: e.g., "Full-time", "Part-time", "Internship", or "Contract". DO NOT use location modifiers like "Remote" or "Hybrid" here.
- "experience": Brief summary of required experience/skills (MAX 100 characters. e.g., "5+ years, Java").
- "salary": The extracted salary. IF NO salary is mentioned in the text: If it is a "Contract" role, intelligently guess a highly realistic approximate hourly rate based on the role and experience (e.g., "$50 - $60/hr"). If it is a "Full-time" role, guess an approximate annual salary (e.g., "$110k - $130k/yr"). DO NOT use words like "Competitive" or "Not Specified" anymore; always provide a numerical estimate if missing.
- "duration": The project/contract duration (e.g. "6 Months", "Long-term"). Extracted from text.
- "apply_url": The primary URL or email address found in the text for applying. Look specifically for links following keywords like "Apply Here:", "Link:", "LinkedIn:", or "Application:". NEVER omit an application URL if one is present. If multiple are found, pick the most direct one. If none found, leave as empty string "".
- "description": The rewritten, unique Career Guide in Markdown format.

The "description" string MUST follow this EXACT sequence and Markdown structure. ALWAYS use `#` for H1 headings where specified below:

(Begin description string immediately with a 3-sentence, conversational introduction explaining why this niche is currently important and why this job is a great opportunity. Do NOT include a title for this intro. Just write the text directly.)

# Job Summary
(Summarize the role in a clean, professional way.)

# Top 3 Critical Skills Table
(Create a Markdown table exactly with columns: 'Skill', 'Why it's critical', and 'Mastery Level' (Junior/Mid/Senior). Do not forget to format it properly as a markdown table using | and - characters.)

# Interview Preparation
(Provide 5 deep-dive technical questions based on the JD, followed by 'What the interviewer is looking for' for each.)

# Resume Optimization
(List 10 specific keywords from the JD that will pass an Applicant Tracking System (ATS). Output them cleanly as a bulleted list.)

# Application Strategy
(Write a guide to the candidate on how to email the recruiter. Do NOT write the exact email draft for them. Instead, tell them to send an email saying "Hello", attaching their resume, and guide them to explicitly mention their top skills, relevant projects, and highlight the exact skills they have that map to this JD. E.g. "Make sure to mention related skills you possess, such as [insert 2-3 specific skills from JD here].")

# Career Roadmap
(Create a Markdown table showing how to grow from this role to a higher position (e.g., Junior -> Senior -> Director). Use columns: 'Current Role', 'Typical Experience', 'Core Focus', and 'Next Position'.)

Constraint: Return ONLY valid JSON. The "description" value MUST contain the full markdown with exact H1 (#) headings, bold text, and perfectly formatted markdown tables."""

def call_with_rotation(jd_text):
    """Try each API key in a random order until one works."""
    keys_to_try = list(API_KEYS)
    random.shuffle(keys_to_try)
    
    for i, (key_name, key) in enumerate(keys_to_try):
        if not key:
            continue
        try:
            print(f"  → Trying [{key_name}] ({i+1}/{len(API_KEYS)})...", end=" ", flush=True)
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Here is the Job Description to process:\n\n{jd_text}"}
                ],
                max_tokens=4096,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            print("✅ Success!")
            print(f"  🔑 Used Key: {key_name}")
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Failed: {str(e)[:60]}")
            continue

    return None


def main():
    print("=" * 60)
    print("   ALLATA1 - Career Guide Generator (Admin Tool)")
    print("=" * 60)
    print(f"   Model : {MODEL}")
    print(f"    Keys  : {len([k for k in API_KEYS if k[1]])} available")
    print("=" * 60)
    print()
    print("Paste the Job Description below.")
    print("When done, type END on a new line and press Enter:")
    print("-" * 60)

    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)

    jd_text = "\n".join(lines).strip()

    if not jd_text:
        print("❌ No Job Description provided. Exiting.")
        return

    print()
    print(f"📝 JD received ({len(jd_text)} characters). Generating Career Guide...")
    print("-" * 60)

    result = call_with_rotation(jd_text)

    if result:
        print()
        print("=" * 60)
        print("              ✅ CAREER GUIDE OUTPUT")
        print("=" * 60)
        print(result)
        print("=" * 60)

        # Optionally save to file
        save = input("\n💾 Save output to file? (y/n): ").strip().lower()
        if save == "y":
            filename = f"career_guide_output.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"✅ Saved to {filename}")
    else:
        print("❌ All API keys failed. Please check your keys or try again later.")


if __name__ == "__main__":
    main()
