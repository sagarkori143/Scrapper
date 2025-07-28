"""
Gemini AI module for the intelligent job scraper.
Handles all interactions with Google's Gemini AI for website analysis.
"""

import json
import google.generativeai as genai
from config import GEMINI_MODEL

# Initialize Gemini model
model = genai.GenerativeModel(GEMINI_MODEL)


def get_selectors_from_gemini(html_content: str) -> dict:
    """
    Analyzes HTML with Gemini to extract CSS selectors for scraping.
    """
    print("🤖 Contacting Gemini to analyze website structure...")
    
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
    
    try:
        response = model.generate_content([prompt, html_content])
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
        print("✅ Gemini analysis complete.")
        return json.loads(cleaned_response)
    except Exception as e:
        # The original error 'e' from the API is more informative.
        print(f"🔴 Error during Gemini API call or JSON parsing: {e}")
        return None


def get_job_detail_selectors_from_gemini(html_content: str) -> dict:
    """
    Analyzes HTML of a job detail page with Gemini to extract selectors for job description and additional details.
    """
    print("🤖 Analyzing job detail page structure with Gemini...")
    
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
    
    try:
        response = model.generate_content([prompt, html_content])
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
        print("✅ Job detail analysis complete.")
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"🔴 Error during job detail analysis: {e}")
        return None
