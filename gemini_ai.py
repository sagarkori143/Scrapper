"""
Gemini AI module for the intelligent job scraper.
Handles all interactions with Google's Gemini AI for website analysis.
Includes robust fallback system for enhanced reliability.
"""

import json
import time
import google.generativeai as genai
from config import (
    GEMINI_MODEL_PRIMARY, 
    GEMINI_MODEL_FALLBACK, 
    GEMINI_MODEL_EMERGENCY,
    MAX_RETRY_ATTEMPTS,
    RETRY_DELAY_SECONDS
)

# Model configuration with fallback hierarchy
MODEL_HIERARCHY = [
    {"name": GEMINI_MODEL_PRIMARY, "description": "Primary (Fast)"},
    {"name": GEMINI_MODEL_FALLBACK, "description": "Fallback (Reliable)"},
    {"name": GEMINI_MODEL_EMERGENCY, "description": "Emergency (Stable)"}
]


def get_model_with_fallback(model_name: str):
    """
    Initialize a Gemini model with error handling.
    """
    try:
        return genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"⚠️ Failed to initialize model {model_name}: {e}")
        return None


def call_gemini_with_fallback(prompt: str, html_content: str, operation_name: str = "analysis") -> dict:
    """
    Calls Gemini API with comprehensive fallback mechanism.
    Tries multiple models and implements retry logic for enhanced reliability.
    """
    print(f"🤖 Starting {operation_name} with fallback support...")
    
    for model_config in MODEL_HIERARCHY:
        model_name = model_config["name"]
        model_desc = model_config["description"]
        
        print(f"🔄 Trying {model_name} ({model_desc})...")
        
        # Initialize model
        model = get_model_with_fallback(model_name)
        if not model:
            print(f"❌ Failed to initialize {model_name}, trying next model...")
            continue
        
        # Attempt API call with retries
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                print(f"   📡 Attempt {attempt + 1}/{MAX_RETRY_ATTEMPTS} with {model_name}...")
                
                response = model.generate_content([prompt, html_content])
                
                if not response or not response.text:
                    raise ValueError("Empty response from Gemini API")
                
                # Clean and parse response
                cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
                parsed_response = json.loads(cleaned_response)
                
                print(f"✅ {operation_name.capitalize()} successful with {model_name}!")
                return parsed_response
                
            except json.JSONDecodeError as e:
                print(f"   🔴 JSON parsing error with {model_name} (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    print(f"   ⏳ Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(RETRY_DELAY_SECONDS)
                continue
                
            except Exception as e:
                print(f"   🔴 API error with {model_name} (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    print(f"   ⏳ Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(RETRY_DELAY_SECONDS)
                continue
        
        print(f"❌ All attempts failed for {model_name}, trying next model...")
    
    print("🚨 All fallback models exhausted! Returning None.")
    return None


def get_fallback_status() -> dict:
    """
    Returns the current fallback configuration status.
    Useful for debugging and monitoring.
    """
    return {
        "model_hierarchy": MODEL_HIERARCHY,
        "max_retry_attempts": MAX_RETRY_ATTEMPTS,
        "retry_delay_seconds": RETRY_DELAY_SECONDS,
        "total_fallback_options": len(MODEL_HIERARCHY)
    }


def get_selectors_from_gemini(html_content: str) -> dict:
    """
    Analyzes HTML with Gemini to extract CSS selectors for scraping.
    Uses fallback system for enhanced reliability.
    """
    prompt = """
    You are an expert web scraping assistant. Analyze the provided HTML of a company's job listings page.
    Your task is to identify the CSS selectors for the following elements:

    1. A container for each individual job posting (key: "job_item").
    2. The job title within that job container (key: "title").
    3. The job location within that job container (key: "location").
    4. A clickable link/button within each job item that leads to the full job details page (key: "job_link").
    5. The job ID or unique identifier, often found in href attributes, data attributes, or as text (key: "job_id").
    6. A brief job description or summary text, if visible on the listing page (key: "description").
    7. The link or button to click to go to the NEXT page of results (key: "pagination_next").

    IMPORTANT NOTES:
    - For "job_link": This should be a selector for a clickable element (usually <a> tag) that opens the full job details.
    - For "job_id": Look for unique identifiers in href URLs (like /job/12345), data-id attributes, or ID text.
    - For "description": Look for preview text, summary, or snippet content visible on the listing page.
    - If any element is not found or doesn't exist, set its value to null.

    You MUST return your response as a single, raw JSON object, and nothing else.
    Do not include markdown formatting like ```json or any explanations.
    Your response should look EXACTLY like this example:
    {
      "job_item": "div.job-card",
      "title": "h2.job-title",
      "location": "span.location",
      "job_link": "a.job-link",
      "job_id": "a.job-link",
      "description": "div.job-summary",
      "pagination_next": "a.next-page"
    }
    """
    
    return call_gemini_with_fallback(prompt, html_content, "job listing analysis")


def get_job_detail_selectors_from_gemini(html_content: str) -> dict:
    """
    Analyzes HTML of a job detail page with Gemini to extract selectors for job description and additional details.
    Uses fallback system for enhanced reliability.
    """
    prompt = """
    You are an expert web scraping assistant. Analyze the provided HTML of a company's individual job detail page.
    Your task is to identify the CSS selectors for the following elements on the job detail page:

    1. The full job description content (key: "full_description").
    2. Job requirements or qualifications section (key: "requirements").
    3. Company information or about section (key: "company_info").
    4. Job type (full-time, part-time, contract, etc.) (key: "job_type").
    5. Experience level required (entry, mid, senior, etc.) (key: "experience_level").
    6. Salary information, if available (key: "salary").
    7. Application deadline, if available (key: "deadline").
    8. Skills or technologies mentioned (key: "skills").

    IMPORTANT NOTES:
    - Focus on finding the main content areas that contain job information.
    - If any element is not found or doesn't exist, set its value to null.
    - Prioritize the most comprehensive selectors that capture the full content.

    You MUST return your response as a single, raw JSON object, and nothing else.
    Do not include markdown formatting like ```json or any explanations.
    Your response should look EXACTLY like this example:
    {
      "full_description": "div.job-description",
      "requirements": "div.requirements",
      "company_info": "div.company-info",
      "job_type": "span.job-type",
      "experience_level": "span.experience",
      "salary": "div.salary-info",
      "deadline": "span.deadline",
      "skills": "div.skills"
    }
    """
    
    return call_gemini_with_fallback(prompt, html_content, "job detail analysis")
