"""
Gemini AI module for the intelligent job scraper.
Handles all interactions with Google's Gemini AI for website analysis.
Includes robust fallback system and intelligent rate limiting for enhanced reliability.
"""

import json
import time
import threading
import google.generativeai as genai
from config import (
    GEMINI_MODEL_PRIMARY, 
    GEMINI_MODEL_FALLBACK, 
    GEMINI_MODEL_EMERGENCY,
    MAX_RETRY_ATTEMPTS,
    RETRY_DELAY_SECONDS,
    GEMINI_REQUESTS_PER_MINUTE,
    GEMINI_MIN_REQUEST_INTERVAL
)

# Global rate limiting variables
_last_request_time = 0
_request_lock = threading.Lock()
_request_count = 0
_minute_start_time = time.time()

# Model configuration with fallback hierarchy
MODEL_HIERARCHY = [
    {"name": GEMINI_MODEL_PRIMARY, "description": "Primary (Fast)"},
    {"name": GEMINI_MODEL_FALLBACK, "description": "Fallback (Reliable)"},
    {"name": GEMINI_MODEL_EMERGENCY, "description": "Emergency (Stable)"}
]


def wait_for_rate_limit():
    """
    Implements intelligent rate limiting to respect Gemini API limits.
    Ensures we don't exceed the requests per minute quota.
    """
    global _last_request_time, _request_count, _minute_start_time
    
    with _request_lock:
        current_time = time.time()
        
        # Reset counter if a new minute has started
        if current_time - _minute_start_time >= 60:
            _request_count = 0
            _minute_start_time = current_time
        
        # Check if we've hit the per-minute limit
        if _request_count >= GEMINI_REQUESTS_PER_MINUTE:
            wait_time = 60 - (current_time - _minute_start_time)
            if wait_time > 0:
                print(f"⏳ Rate limit reached ({GEMINI_REQUESTS_PER_MINUTE} requests/min). Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                # Reset after waiting
                _request_count = 0
                _minute_start_time = time.time()
        
        # Ensure minimum interval between requests
        time_since_last_request = current_time - _last_request_time
        if time_since_last_request < GEMINI_MIN_REQUEST_INTERVAL:
            wait_time = GEMINI_MIN_REQUEST_INTERVAL - time_since_last_request
            print(f"⏱️ Rate limiting: waiting {wait_time:.1f}s before next request...")
            time.sleep(wait_time)
        
        # Update tracking variables
        _last_request_time = time.time()
        _request_count += 1
        print(f"📊 API Request #{_request_count} this minute")


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
    Calls Gemini API with comprehensive fallback mechanism and intelligent rate limiting.
    Tries multiple models and implements retry logic for enhanced reliability.
    """
    print(f"🤖 Starting {operation_name} with fallback support and rate limiting...")
    
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
                
                # Apply rate limiting before each API call
                wait_for_rate_limit()
                
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
                error_msg = str(e).lower()
                # Check for rate limit specific errors
                if "quota" in error_msg or "rate" in error_msg or "limit" in error_msg:
                    print(f"   🚨 Rate limit detected! Waiting longer before retry...")
                    time.sleep(60)  # Wait a full minute for rate limit errors
                
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
    Returns the current fallback configuration status including rate limiting.
    Useful for debugging and monitoring.
    """
    return {
        "model_hierarchy": MODEL_HIERARCHY,
        "max_retry_attempts": MAX_RETRY_ATTEMPTS,
        "retry_delay_seconds": RETRY_DELAY_SECONDS,
        "total_fallback_options": len(MODEL_HIERARCHY),
        "rate_limiting": {
            "requests_per_minute": GEMINI_REQUESTS_PER_MINUTE,
            "min_request_interval": f"{GEMINI_MIN_REQUEST_INTERVAL:.1f}s",
            "current_requests_this_minute": _request_count
        }
    }


def get_rate_limit_status() -> dict:
    """
    Returns current rate limiting status for monitoring.
    """
    global _request_count, _minute_start_time
    current_time = time.time()
    time_in_current_minute = current_time - _minute_start_time
    
    return {
        "requests_this_minute": _request_count,
        "requests_remaining": max(0, GEMINI_REQUESTS_PER_MINUTE - _request_count),
        "time_in_current_minute": f"{time_in_current_minute:.1f}s",
        "time_until_reset": f"{max(0, 60 - time_in_current_minute):.1f}s",
        "last_request": f"{time.time() - _last_request_time:.1f}s ago"
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
