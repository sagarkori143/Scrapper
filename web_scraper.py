"""
Web scraper module for the intelligent job scraper.
Handles browser automation, HTML parsing, and data extraction.
"""

import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
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
    """
    try:
        print(f"  📄 Fetching job details from: {job_url}")
        page.goto(job_url, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)
        page.wait_for_timeout(2000)  # Wait for dynamic content
        
        details = {}
        
        for key, selector in detail_selectors.items():
            if selector:
                try:
                    element = page.locator(selector).first
                    if element.is_visible():
                        text = element.inner_text().strip()
                        details[key] = text if text else None
                    else:
                        details[key] = None
                except:
                    details[key] = None
            else:
                details[key] = None
        
        return details
    except Exception as e:
        print(f"  🔴 Error fetching job details: {e}")
        return {}


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

            # Clean the HTML before sending to Gemini
            print("🧹 Cleaning HTML to reduce token count...")
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup(['script', 'style', 'svg']):  # Remove script, style, and svg tags
                tag.decompose()
            cleaned_html = str(soup.body)  # Only send the body content
            
            # Pass the smaller, cleaned HTML to the LLM
            selectors = get_selectors_from_gemini(cleaned_html)
            
            if selectors:
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
                            # Analyze job detail page structure (only once)
                            if not job_detail_analyzed and i == 0:
                                print("  🔍 Analyzing job detail page structure...")
                                try:
                                    # Navigate to first job to analyze structure
                                    page.goto(job_link, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)
                                    page.wait_for_timeout(2000)
                                    
                                    # Get HTML and analyze with Gemini
                                    html = page.content()
                                    soup = BeautifulSoup(html, 'html.parser')
                                    for tag in soup(['script', 'style', 'svg']):
                                        tag.decompose()
                                    cleaned_html = str(soup.body)
                                    
                                    detail_selectors = get_job_detail_selectors_from_gemini(cleaned_html)
                                    job_detail_analyzed = True
                                    
                                    # Go back to listings page
                                    page.go_back()
                                    page.wait_for_selector(selectors['job_item'], timeout=SELECTOR_TIMEOUT)
                                except Exception as e:
                                    print(f"  🔴 Error analyzing job detail structure: {e}")
                                    extract_full_details = False
                            
                            # Extract detailed information
                            if detail_selectors:
                                job_details = extract_job_details(page, job_link, detail_selectors)
                                job_data.update(job_details)
                                
                                # Go back to listings page
                                page.go_back()
                                page.wait_for_selector(selectors['job_item'], timeout=SELECTOR_TIMEOUT)
                        
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
