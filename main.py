from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import os
import json
import re

# Configure Gemini API (set your API key in environment variables)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize FastAPI app
app = FastAPI()


# Request schema
class JobRequest(BaseModel):
    role: str
    experience: int


@app.post("/generate-jd")
def generate_jd(request: JobRequest):
    # Prompt for Gemini
    prompt = f"""
    You are an AI that generates structured job descriptions. 
    For the role "{request.role}" with {request.experience} years of experience,
    return ONLY valid JSON (no extra text, no markdown, no backticks).
    The JSON must have these keys:
    - skills_required (list of strings)
    - responsibilities (list of strings)
    - educational_qualification (string)
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    raw_text = response.text.strip()

    # Clean markdown code fences (```json ... ```)
    clean_text = re.sub(r"^```(json)?", "", raw_text, flags=re.IGNORECASE).strip()
    clean_text = re.sub(r"```$", "", clean_text).strip()

    # Try to parse into JSON
    try:
        jd_output = json.loads(clean_text)
    except Exception:
        return {"error": "Invalid JSON from model", "raw_output": raw_text}

    # ✅ Ensure all required keys exist
    required_keys = {
        "skills_required": [],
        "responsibilities": [],
        "educational_qualification": "",
    }

    for key, default_value in required_keys.items():
        if key not in jd_output:
            jd_output[key] = default_value

    return jd_output


# Optional root route
@app.get("/")
def root():
    return {"message": "Job Description API is running! Use POST /generate-jd"}
