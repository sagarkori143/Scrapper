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
_model_rate_limit_flags = {}  # Track which models hit rate limits

# Model configuration with fallback hierarchy
MODEL_HIERARCHY = [
    {"name": GEMINI_MODEL_PRIMARY, "description": "Primary (Fast)"},
    {"name": GEMINI_MODEL_FALLBACK, "description": "Fallback (Reliable)"},
    {"name": GEMINI_MODEL_EMERGENCY, "description": "Emergency (Stable)"}
]


def mark_model_rate_limited(model_name: str):
    """
    Mark a model as having hit rate limits to avoid immediate retries.
    """
    global _model_rate_limit_flags
    _model_rate_limit_flags[model_name] = time.time()
    print(f"🚫 Model {model_name} marked as rate-limited at {time.strftime('%H:%M:%S')}")


def is_model_rate_limited(model_name: str, cooldown_minutes: int = 5) -> bool:
    """
    Check if a model was recently rate-limited and should be skipped.
    """
    global _model_rate_limit_flags
    if model_name not in _model_rate_limit_flags:
        return False
    
    time_since_limit = time.time() - _model_rate_limit_flags[model_name]
    if time_since_limit > (cooldown_minutes * 60):
        # Cooldown period over, remove the flag
        del _model_rate_limit_flags[model_name]
        return False
    
    return True


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
    Automatically switches models when rate limits are hit for faster recovery.
    """
    print(f"🤖 Starting {operation_name} with smart fallback and rate limit avoidance...")
    print(f"📊 HTML content size: {len(html_content):,} characters")
    
    for model_config in MODEL_HIERARCHY:
        model_name = model_config["name"]
        model_desc = model_config["description"]
        
        # Skip models that recently hit rate limits
        if is_model_rate_limited(model_name):
            print(f"⏭️ Skipping {model_name} (recently rate-limited, cooldown active)")
            continue
        
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
                
                # Log raw response for debugging
                raw_response = response.text.strip()
                print(f"   📝 Raw response length: {len(raw_response)} characters")
                print(f"   📄 Raw response preview: {raw_response[:200]}...")
                
                # Clean and parse response
                cleaned_response = raw_response.replace('```json', '').replace('```', '').strip()
                parsed_response = json.loads(cleaned_response)
                
                # Validate that we got actual selectors (not all null)
                non_null_selectors = {k: v for k, v in parsed_response.items() if v is not None}
                if len(non_null_selectors) == 0:
                    print(f"   ⚠️ Warning: All selectors are null - Gemini may not have found valid elements")
                    print(f"   🔍 Parsed response: {parsed_response}")
                else:
                    print(f"   ✅ Found {len(non_null_selectors)} non-null selectors")
                
                print(f"✅ {operation_name.capitalize()} successful with {model_name}!")
                return parsed_response
                
            except json.JSONDecodeError as e:
                print(f"   🔴 JSON parsing error with {model_name} (attempt {attempt + 1}): {e}")
                print(f"   📄 Failed to parse: {response.text[:500] if response and response.text else 'No response'}...")
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    print(f"   ⏳ Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(RETRY_DELAY_SECONDS)
                continue
                
            except Exception as e:
                error_msg = str(e).lower()
                # Check for rate limit/quota specific errors - immediately switch to next model
                if any(keyword in error_msg for keyword in ["quota", "rate", "limit", "resource_exhausted", "429", "exceeded"]):
                    print(f"   🚨 QUOTA/RATE LIMIT DETECTED for {model_name}!")
                    print(f"   🔄 IMMEDIATELY switching to next model (no waiting)...")
                    mark_model_rate_limited(model_name)  # Mark this model as rate-limited
                    break  # Break out of retry loop and try next model immediately
                
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
    global _model_rate_limit_flags
    
    rate_limited_models = []
    for model_name, timestamp in _model_rate_limit_flags.items():
        time_since = time.time() - timestamp
        rate_limited_models.append({
            "model": model_name,
            "rate_limited_at": time.strftime('%H:%M:%S', time.localtime(timestamp)),
            "minutes_ago": f"{time_since/60:.1f}m"
        })
    
    return {
        "model_hierarchy": MODEL_HIERARCHY,
        "max_retry_attempts": MAX_RETRY_ATTEMPTS,
        "retry_delay_seconds": RETRY_DELAY_SECONDS,
        "total_fallback_options": len(MODEL_HIERARCHY),
        "rate_limiting": {
            "requests_per_minute": GEMINI_REQUESTS_PER_MINUTE,
            "min_request_interval": f"{GEMINI_MIN_REQUEST_INTERVAL:.1f}s",
            "current_requests_this_minute": _request_count
        },
        "rate_limited_models": rate_limited_models,
        "available_models": [m["name"] for m in MODEL_HIERARCHY if not is_model_rate_limited(m["name"])]
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


def get_selectors_from_gemini(html_content: str, url: str = "") -> dict:
    """
    Analyzes HTML with Gemini to extract CSS selectors for scraping.
    Uses enhanced prompts and fallback system for improved reliability.
    """
    # Create site-specific enhanced prompt
    site_hints = ""
    url_lower = url.lower()
    
    if 'google' in url_lower:
        site_hints = """
        GOOGLE CAREERS SPECIFIC HINTS:
        - Jobs are often in elements with [data-job-id] attributes
        - Look for [role="listitem"] containers or .search-result elements
        - Titles are usually in h3 tags or elements with 'job-title' classes
        - Locations often have 'location' or 'job-location' classes
        - Links typically have href patterns like '/jobs/results/...'
        """
    elif 'microsoft' in url_lower:
        site_hints = """
        MICROSOFT CAREERS SPECIFIC HINTS:
        - Jobs may be in .ms-List-cell containers
        - Look for [data-automation-id] attributes especially "jobTitle"
        - Titles often have 'job-title' classes or are in anchor tags
        - Location info may have [data-automation-id="jobLocation"]
        """
    elif any(company in url_lower for company in ['meta', 'facebook']):
        site_hints = """
        META/FACEBOOK CAREERS SPECIFIC HINTS:
        - Jobs often in article or div containers with job-related data attributes
        - Look for semantic HTML like <article> or [role="listitem"]
        - Titles typically in h3 or strong tags within job containers
        """
    
    prompt = f"""
    You are an expert web scraping assistant analyzing a company's job listings page. 

    IMPORTANT: You must analyze the HTML structure carefully and provide SPECIFIC CSS selectors that actually exist in the HTML.

    {site_hints}

    Your task is to identify CSS selectors for these elements:

    1. **job_item**: Container for each individual job posting (div, article, li, section, etc.)
    2. **title**: Job title text within each job container  
    3. **location**: Job location text within each job container
    4. **job_link**: Clickable link/button that opens full job details (must be <a> tag)
    5. **job_id**: Unique identifier (in href URLs, data attributes, or visible text)
    6. **description**: Brief job summary/description text visible on listing page
    7. **pagination_next**: Next page button/link for pagination

    ANALYSIS STRATEGY:
    - First identify the repeating job listing pattern in the HTML
    - Look for semantic elements: <article>, <section>, [role="listitem"], or divs with job-related classes
    - Common patterns: classes/IDs containing "job", "position", "career", "listing", "search-result"
    - For data attributes, look for: data-job-id, data-automation-id, data-testid
    - For job_link: Find <a> tags within job containers that lead to detail pages
    - For job_id: Extract from href patterns like "/job/12345" or data-id attributes
    - If you cannot find a reliable selector that exists in the HTML, use null

    CRITICAL REQUIREMENTS:
    - Only return selectors that you can verify exist in the provided HTML
    - Be as specific as possible to avoid false matches
    - If you're unsure about a selector, use null rather than guessing
    - Focus on the most common/reliable pattern you can identify

    Return ONLY a raw JSON object with no explanations:
    {{
      "job_item": "css.selector.for.job.container",
      "title": "css.selector.for.title", 
      "location": "css.selector.for.location",
      "job_link": "css.selector.for.clickable.link",
      "job_id": "css.selector.for.identifier", 
      "description": "css.selector.for.description",
      "pagination_next": "css.selector.for.next.page"
    }}
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
