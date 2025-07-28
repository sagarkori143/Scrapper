"""
Web scraper module for the intelligent job scraper.
Handles browser automation, HTML parsing, and data extraction.
"""

import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup, Comment
from config import BROWSER_TIMEOUT, PAGE_LOAD_WAIT, SELECTOR_TIMEOUT, CONFIG_FILE
from gemini_ai import get_selectors_from_gemini, get_job_detail_selectors_from_gemini
from utils import save_configuration, get_company_configuration
import re


def extract_job_id(element, selector: str) -> str:
    """
    Extracts job ID from various sources (href, data attributes, text content).
    """
    try:
        # Try to get href attribute first
        href = element.get_attribute('href')
        if href:
            # Look for common ID patterns in URLs
            id_patterns = [
                r'/job[s]?/(\w+)',
                r'/position[s]?/(\w+)',
                r'/career[s]?/(\w+)',
                r'id=(\w+)',
                r'jobId=(\w+)',
                r'positionId=(\w+)',
                r'/(\d+)/?$'
            ]
            for pattern in id_patterns:
                match = re.search(pattern, href)
                if match:
                    return match.group(1)
        
        # Try data attributes
        for attr in ['data-id', 'data-job-id', 'data-position-id', 'id']:
            value = element.get_attribute(attr)
            if value:
                return value
        
        # Try text content as fallback
        text = element.inner_text().strip()
        if text and text.isdigit():
            return text
            
        return None
    except:
        return None


def extract_job_details(page, job_url: str, detail_selectors: dict) -> dict:
    """
    Navigates to a job detail page and extracts comprehensive job information.
    Enhanced version that intelligently extracts detailed job data.
    """
    try:
        print(f"  📄 Fetching comprehensive job details from: {job_url}")
        page.goto(job_url, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)
        page.wait_for_timeout(3000)  # Wait for dynamic content to load
        
        details = {}
        
        # Extract using AI-provided selectors
        if detail_selectors:
            for key, selector in detail_selectors.items():
                if selector:
                    try:
                        elements = page.locator(selector).all()
                        if elements:
                            # For multiple elements, combine the text
                            texts = []
                            for element in elements:
                                if element.is_visible():
                                    text = element.inner_text().strip()
                                    if text:
                                        texts.append(text)
                            
                            if texts:
                                # Join multiple texts with newlines for readability
                                details[key] = '\n'.join(texts) if len(texts) > 1 else texts[0]
                            else:
                                details[key] = None
                        else:
                            details[key] = None
                    except Exception as e:
                        print(f"    ⚠️ Error extracting {key}: {e}")
                        details[key] = None
                else:
                    details[key] = None
        
        # Fallback extraction using common patterns if AI selectors failed
        fallback_extracted = extract_job_details_fallback(page)
        
        # Merge fallback data with AI-extracted data (AI takes priority)
        for key, value in fallback_extracted.items():
            if key not in details or details[key] is None:
                details[key] = value
        
        # Additional metadata extraction
        details.update(extract_job_metadata(page, job_url))
        
        # Clean and validate extracted data
        details = clean_job_details(details)
        
        return details
        
    except Exception as e:
        print(f"  🔴 Error fetching job details from {job_url}: {e}")
        return {}


def extract_job_details_fallback(page) -> dict:
    """
    Fallback extraction using common job page patterns.
    Used when AI selectors are incomplete or missing.
    """
    fallback_details = {}
    
    try:
        # Common selectors for job descriptions
        description_selectors = [
            '[data-testid="job-description"]',
            '.job-description',
            '.job-details',
            '.description',
            '[class*="description"]',
            '[class*="job-content"]',
            'div[role="main"]',
            'main',
            '.content'
        ]
        
        for selector in description_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    text = element.inner_text().strip()
                    if text and len(text) > 100:  # Ensure it's substantial content
                        fallback_details['full_description'] = text
                        break
            except:
                continue
        
        # Common selectors for requirements
        requirements_selectors = [
            '[data-testid="requirements"]',
            '.requirements',
            '.qualifications',
            '[class*="requirement"]',
            '[class*="qualification"]',
            'ul li',  # List items often contain requirements
            '.skills'
        ]
        
        for selector in requirements_selectors:
            try:
                elements = page.locator(selector).all()
                if elements:
                    texts = []
                    for element in elements:
                        text = element.inner_text().strip()
                        if text and any(keyword in text.lower() for keyword in ['year', 'experience', 'degree', 'skill', 'required', 'bachelor', 'master']):
                            texts.append(text)
                    if texts:
                        fallback_details['requirements'] = '\n'.join(texts[:10])  # Limit to first 10 items
                        break
            except:
                continue
        
        # Extract salary information
        salary_patterns = [
            r'\$[\d,]+(?:\.\d{2})?\s*-?\s*\$?[\d,]+(?:\.\d{2})?',
            r'[\d,]+\s*-\s*[\d,]+\s*(?:USD|usd|\$)',
            r'Salary[:\s]*\$?[\d,]+',
            r'Compensation[:\s]*\$?[\d,]+'
        ]
        
        page_text = page.inner_text()
        for pattern in salary_patterns:
            import re
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                fallback_details['salary'] = matches[0]
                break
        
    except Exception as e:
        print(f"    ⚠️ Fallback extraction error: {e}")
    
    return fallback_details


def extract_job_metadata(page, job_url: str) -> dict:
    """
    Extract additional metadata about the job posting.
    """
    metadata = {}
    
    try:
        # Extract page title
        title = page.title()
        if title:
            metadata['page_title'] = title
        
        # Extract posting date if available
        date_selectors = [
            '[data-testid="posting-date"]',
            '.posting-date',
            '.date-posted',
            '[class*="date"]'
        ]
        
        for selector in date_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    date_text = element.inner_text().strip()
                    if any(keyword in date_text.lower() for keyword in ['posted', 'date', 'ago', 'day', 'week', 'month']):
                        metadata['posting_date'] = date_text
                        break
            except:
                continue
        
        # Extract department/team information
        dept_selectors = [
            '[data-testid="department"]',
            '.department',
            '.team',
            '[class*="department"]',
            '[class*="team"]'
        ]
        
        for selector in dept_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    dept_text = element.inner_text().strip()
                    if dept_text:
                        metadata['department'] = dept_text
                        break
            except:
                continue
        
        # Extract job level/seniority
        level_keywords = ['senior', 'junior', 'lead', 'principal', 'staff', 'entry', 'mid', 'director', 'manager']
        page_text = page.inner_text().lower()
        for keyword in level_keywords:
            if keyword in page_text:
                metadata['level_detected'] = keyword
                break
        
    except Exception as e:
        print(f"    ⚠️ Metadata extraction error: {e}")
    
    return metadata


def clean_job_details(details: dict) -> dict:
    """
    Clean and normalize extracted job details.
    """
    cleaned = {}
    
    for key, value in details.items():
        if value is not None:
            # Clean whitespace and normalize
            if isinstance(value, str):
                value = ' '.join(value.split())  # Normalize whitespace
                value = value.strip()
                
                # Remove empty values
                if value and value not in ['N/A', 'n/a', 'None', 'null', '-']:
                    cleaned[key] = value
            else:
                cleaned[key] = value
    
    return cleaned


def scout_mode(url: str, company_name: str = None):
    """
    Launches browser, gets and CLEANS HTML, asks Gemini for selectors, and saves them.
    """
    print(f"🕵️‍♂️ Running in Scout Mode for: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)
            page.wait_for_timeout(PAGE_LOAD_WAIT)
            html = page.content()

            # Intelligent HTML cleaning to reduce token count while preserving structure
            print("🧹 Intelligently cleaning HTML for optimal AI analysis...")
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unnecessary elements but keep structure
            for tag in soup(['script', 'style', 'noscript', 'svg', 'img']):
                tag.decompose()
            
            # Remove HTML comments
            for comment in soup(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            # Remove attributes that aren't useful for scraping (reduce noise)
            for tag in soup.find_all():
                # Keep only essential attributes that might be useful for selectors
                if tag.name:
                    attrs_to_keep = ['class', 'id', 'data-id', 'data-job-id', 'href', 'role', 'data-testid']
                    new_attrs = {k: v for k, v in tag.attrs.items() if k in attrs_to_keep}
                    tag.attrs = new_attrs
            
            # Focus on the main content area if we can identify it
            main_content = soup.find('main') or soup.find(class_=lambda x: x and 'job' in x.lower()) or soup.body
            cleaned_html = str(main_content) if main_content else str(soup.body)
            
            print(f"📊 HTML size reduced from {len(html):,} to {len(cleaned_html):,} characters")
            
            # Pass the optimized HTML and URL to Gemini for enhanced analysis
            selectors = get_selectors_from_gemini(cleaned_html, url)
            
            if selectors:
                # Validate selectors before saving
                non_null_count = sum(1 for v in selectors.values() if v is not None)
                print(f"🔍 Validation: {non_null_count}/{len(selectors)} selectors found")
                
                # Save to central configurations file
                if company_name:
                    save_configuration(company_name, selectors)
                else:
                    # Fallback to old behavior for single-company mode
                    with open(CONFIG_FILE, 'w') as f:
                        json.dump(selectors, f, indent=2)
                    print(f"✅ Configuration saved successfully to {CONFIG_FILE}")
                return selectors
            else:
                print("🔴 Scout mode failed. Could not generate selectors.")
                return None
        
        except Exception as e:
            print(f"🔴 An error occurred in Scout Mode: {e}")
            return None
        finally:
            browser.close()


def scrape_mode(url: str, company_name: str = None, selectors: dict = None, extract_full_details: bool = True) -> list:
    """
    Enhanced scraping with comprehensive job data extraction.
    Always extracts job IDs, URLs, descriptions, requirements, salary info, and more.
    """
    print(f"⚡ Running Enhanced Scrape Mode for: {url}")
    print("🔍 Enhanced extraction: Job IDs, URLs, descriptions, requirements, salary, etc.")
    
    # Use provided selectors or load from configuration
    if selectors:
        print("✅ Using provided selectors")
    elif company_name:
        selectors = get_company_configuration(company_name)
        if not selectors:
            print(f"🔴 No configuration found for {company_name}")
            return []
        print(f"✅ Loaded selectors for {company_name}")
    else:
        # Fallback to old behavior for single-company mode
        import os
        if not os.path.exists(CONFIG_FILE):
            print(f"🔴 Config file '{CONFIG_FILE}' not found. Please run Scout Mode first.")
            return []
        with open(CONFIG_FILE, 'r') as f:
            selectors = json.load(f)
        print(f"✅ Loaded selectors from {CONFIG_FILE}")

    print(f"🔧 Using selectors: {selectors}")
    
    all_jobs = []
    detail_selectors = None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)
            page_count = 1
            job_detail_analyzed = False
            
            while True:
                print(f"\n--- Scraping Page {page_count} ---")
                page.wait_for_selector(selectors['job_item'], timeout=SELECTOR_TIMEOUT)
                job_cards = page.locator(selectors['job_item']).all()
                
                if not job_cards:
                    print("No job cards found on this page. Exiting.")
                    break

                for i, card in enumerate(job_cards):
                    try:
                        # Extract basic information
                        title = card.locator(selectors['title']).inner_text().strip() if selectors.get('title') else None
                        location = card.locator(selectors['location']).first.inner_text().strip() if selectors.get('location') else None
                        
                        # Extract job link and ID
                        job_link = None
                        job_id = None
                        description = None
                        
                        if selectors.get('job_link'):
                            try:
                                link_element = card.locator(selectors['job_link']).first
                                job_link = link_element.get_attribute('href')
                                if job_link and not job_link.startswith('http'):
                                    # Handle relative URLs
                                    base_url = f"{page.url.split('/')[0]}//{page.url.split('/')[2]}"
                                    job_link = base_url + job_link
                                
                                # Extract job ID
                                if selectors.get('job_id'):
                                    job_id = extract_job_id(link_element, selectors['job_id'])
                            except Exception as e:
                                print(f"  🔴 Error extracting job link/ID: {e}")
                        
                        # Extract preview description from listing page
                        if selectors.get('description'):
                            try:
                                description = card.locator(selectors['description']).first.inner_text().strip()
                            except:
                                description = None
                        
                        # Create base job data
                        job_data = {
                            'title': title,
                            'location': location,
                            'job_id': job_id,
                            'job_url': job_link,
                            'preview_description': description,
                            'company': company_name
                        }
                        
                        # Extract full job details if requested and job link is available
                        if extract_full_details and job_link:
                            # Analyze job detail page structure (only once per session)
                            if not job_detail_analyzed and i == 0:
                                print("  🔍 Analyzing job detail page structure...")
                                try:
                                    # Navigate to first job to analyze structure
                                    temp_page = browser.new_page()
                                    temp_page.goto(job_link, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)
                                    temp_page.wait_for_timeout(3000)
                                    
                                    # Get HTML and analyze with Gemini
                                    html = temp_page.content()
                                    soup = BeautifulSoup(html, 'html.parser')
                                    
                                    # Enhanced cleaning for job detail pages
                                    for tag in soup(['script', 'style', 'noscript', 'svg', 'img']):
                                        tag.decompose()
                                    
                                    # Focus on main content area
                                    main_content = soup.find('main') or soup.find('article') or soup.find(class_=lambda x: x and any(keyword in x.lower() for keyword in ['job', 'content', 'detail'])) or soup.body
                                    cleaned_html = str(main_content) if main_content else str(soup.body)
                                    
                                    print(f"    📊 Job detail HTML size: {len(cleaned_html):,} characters")
                                    detail_selectors = get_job_detail_selectors_from_gemini(cleaned_html)
                                    job_detail_analyzed = True
                                    
                                    temp_page.close()
                                    
                                    if detail_selectors:
                                        non_null_count = sum(1 for v in detail_selectors.values() if v is not None)
                                        print(f"    ✅ Found {non_null_count}/8 job detail selectors")
                                    else:
                                        print("    ⚠️ No job detail selectors found, using fallback extraction")
                                        
                                except Exception as e:
                                    print(f"  🔴 Error analyzing job detail structure: {e}")
                                    print("    ⚠️ Will use fallback extraction methods")
                                    detail_selectors = {}
                            
                            # Extract detailed information for this job
                            print(f"    🔍 Extracting details for: {title}")
                            job_details = extract_job_details(page, job_link, detail_selectors or {})
                            
                            if job_details:
                                job_data.update(job_details)
                                print(f"    ✅ Extracted {len(job_details)} additional fields")
                                
                                # Show preview of extracted details
                                if job_details.get('full_description'):
                                    desc_preview = job_details['full_description'][:150] + "..." if len(job_details['full_description']) > 150 else job_details['full_description']
                                    print(f"    📝 Description: {desc_preview}")
                                
                                if job_details.get('salary'):
                                    print(f"    💰 Salary: {job_details['salary']}")
                                    
                                if job_details.get('requirements'):
                                    req_preview = job_details['requirements'][:100] + "..." if len(job_details['requirements']) > 100 else job_details['requirements']
                                    print(f"    📋 Requirements: {req_preview}")
                            else:
                                print(f"    ⚠️ No additional details extracted")
                        
                        all_jobs.append(job_data)
                        print(f"  - Title: {title}")
                        print(f"    Location: {location}")
                        print(f"    Job ID: {job_id}")
                        if description:
                            print(f"    Preview: {description[:100]}...")
                        
                    except Exception as e:
                        print(f"  🔴 Error extracting job data: {e}")
                        continue
                
                # Pagination logic
                if 'pagination_next' in selectors and selectors['pagination_next']:
                    next_button = page.locator(selectors['pagination_next'])
                    if next_button.is_visible() and not next_button.is_disabled():
                        next_button.click()
                        print("\nNavigating to next page...")
                        page.wait_for_load_state("networkidle", timeout=BROWSER_TIMEOUT)
                        page_count += 1
                        continue
                
                print("\n✅ Reached the last page or no pagination available.")
                break

        except Exception as e:
            print(f"🔴 An error occurred during scraping: {e}")
        finally:
            browser.close()
    
    return all_jobs
