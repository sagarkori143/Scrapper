"""
Batch operations module for the intelligent job scraper.
Handles batch processing of multiple companies for scouting and scraping.
"""

from config import COMPANIES_FILE, CONFIGURATIONS_FILE, RESULTS_DIR, DATA_DIR
from utils import load_companies, ensure_directories, get_company_configuration
from web_scraper import scout_mode, scrape_mode
from data_storage import save_job_data


def batch_scout_mode(companies_file: str = COMPANIES_FILE):
    """
    Scout mode for all companies in the companies file.
    """
    print("🚀 Running Batch Scout Mode for all companies...")
    companies = load_companies(companies_file)
    
    if not companies:
        return
    
    successful_scouts = 0
    failed_scouts = 0
    
    for company in companies:
        company_name = company.get('name', 'Unknown')
        career_url = company.get('career_url', '')
        
        if not career_url:
            print(f"🔴 No career URL found for {company_name}. Skipping...")
            failed_scouts += 1
            continue
        
        print(f"\n{'='*60}")
        print(f"🏢 Processing: {company_name}")
        print(f"🔗 URL: {career_url}")
        print(f"{'='*60}")
        
        selectors = scout_mode(career_url, company_name)
        if selectors:
            successful_scouts += 1
        else:
            failed_scouts += 1
    
    print(f"\n📊 Batch Scout Summary:")
    print(f"✅ Successful: {successful_scouts}")
    print(f"🔴 Failed: {failed_scouts}")
    print(f"📁 Configurations saved in: {CONFIGURATIONS_FILE}")


def batch_scrape_mode(companies_file: str = COMPANIES_FILE):
    """
    Enhanced scrape mode for all companies in the companies file.
    Always uses enhanced extraction with comprehensive job data.
    """
    print("🚀 Running Enhanced Batch Scrape Mode for all companies...")
    print("� Enhanced extraction: Job IDs, URLs, descriptions, requirements, salary, etc.")
    companies = load_companies(companies_file)
    
    if not companies:
        return
    
    ensure_directories()
    successful_scrapes = 0
    failed_scrapes = 0
    total_jobs = 0
    
    for company in companies:
        company_name = company.get('name', 'Unknown')
        career_url = company.get('career_url', '')
        
        if not career_url:
            print(f"🔴 No career URL found for {company_name}. Skipping...")
            failed_scrapes += 1
            continue
        
        print(f"\n{'='*60}")
        print(f"🏢 Processing: {company_name}")
        print(f"🔗 URL: {career_url}")
        print(f"� Enhanced Extraction: Job IDs, URLs, descriptions, requirements, etc.")
        print(f"{'='*60}")
        
        # Get configuration
        selectors = get_company_configuration(company_name)
        if not selectors:
            print(f"🔴 No configuration found for {company_name}. Skipping...")
            failed_scrapes += 1
            continue
        
        jobs = scrape_mode(career_url, company_name, selectors, extract_full_details=True)
        if jobs:
            # Save both CSV and JSON formats
            save_job_data(company_name, jobs, career_url)
            successful_scrapes += 1
            total_jobs += len(jobs)
            print(f"✅ Found {len(jobs)} jobs for {company_name}")
        else:
            failed_scrapes += 1
            print(f"🔴 No jobs found for {company_name}")
    
    print(f"\n📊 Enhanced Batch Scrape Summary:")
    print(f"✅ Successful companies: {successful_scrapes}")
    print(f"🔴 Failed companies: {failed_scrapes}")
    print(f"💼 Total jobs found: {total_jobs}")
    print(f"🔍 Enhanced data: Job IDs, URLs, descriptions, requirements, salary, etc.")
    print(f"📁 CSV Results saved in: {RESULTS_DIR}")
    print(f"📄 JSON Data saved in: {DATA_DIR}")


def intelligent_scrape_all():
    """
    Main intelligent workflow: Scout companies without configs, then scrape all with enhanced extraction.
    Always uses enhanced mode for comprehensive job data extraction.
    """
    print(f"🚀 Starting Intelligent Enhanced Job Scraping Workflow")
    print("🔍 Enhanced extraction: Job IDs, URLs, descriptions, requirements, salary, etc.")
    print("=" * 60)
    
    # Load companies
    companies = load_companies()
    if not companies:
        print("🔴 No companies found. Please check your companies.json file.")
        return
    
    ensure_directories()
    
    # Statistics
    total_companies = len(companies)
    companies_needing_scout = 0
    companies_with_config = 0
    successful_scrapes = 0
    failed_scrapes = 0
    total_jobs = 0
    
    print(f"📊 Found {total_companies} companies to process")
    
    # Phase 1: Check which companies need scouting
    print("\n🔍 Phase 1: Checking existing configurations...")
    for company in companies:
        company_name = company.get('name', 'Unknown')
        existing_config = get_company_configuration(company_name)
        
        if existing_config:
            companies_with_config += 1
            print(f"✅ {company_name}: Configuration exists")
        else:
            companies_needing_scout += 1
            print(f"🔍 {company_name}: Needs scouting")
    
    print(f"\n📈 Configuration Status:")
    print(f"   ✅ Companies with configs: {companies_with_config}")
    print(f"   🔍 Companies needing scout: {companies_needing_scout}")
    
    # Phase 2: Scout companies that need it
    if companies_needing_scout > 0:
        print(f"\n🕵️‍♂️ Phase 2: Scouting {companies_needing_scout} companies...")
        scout_success = 0
        scout_failed = 0
        
        for company in companies:
            company_name = company.get('name', 'Unknown')
            career_url = company.get('career_url', '')
            
            # Skip if already has configuration
            if get_company_configuration(company_name):
                continue
                
            if not career_url:
                print(f"🔴 No career URL found for {company_name}. Skipping...")
                scout_failed += 1
                continue
            
            print(f"\n{'='*50}")
            print(f"🕵️‍♂️ Scouting: {company_name}")
            print(f"🔗 URL: {career_url}")
            print(f"{'='*50}")
            
            selectors = scout_mode(career_url, company_name)
            if selectors:
                scout_success += 1
                print(f"✅ Successfully scouted {company_name}")
            else:
                scout_failed += 1
                print(f"🔴 Failed to scout {company_name}")
        
        print(f"\n📊 Scouting Summary:")
        print(f"   ✅ Successful: {scout_success}")
        print(f"   🔴 Failed: {scout_failed}")
    
    # Phase 3: Scrape all companies with enhanced extraction
    print(f"\n⚡ Phase 3: Scraping jobs from all companies (Enhanced mode)...")
    
    for company in companies:
        company_name = company.get('name', 'Unknown')
        career_url = company.get('career_url', '')
        
        if not career_url:
            print(f"🔴 No career URL found for {company_name}. Skipping...")
            failed_scrapes += 1
            continue
        
        # Get configuration
        selectors = get_company_configuration(company_name)
        if not selectors:
            print(f"🔴 No configuration available for {company_name}. Skipping...")
            failed_scrapes += 1
            continue
        
        print(f"\n{'='*50}")
        print(f"⚡ Scraping: {company_name}")
        print(f"🔗 URL: {career_url}")
        print(f"� Enhanced Extraction: Job IDs, URLs, descriptions, requirements, etc.")
        print(f"{'='*50}")
        
        jobs = scrape_mode(career_url, company_name, selectors, extract_full_details=True)
        if jobs:
            # Save both CSV and JSON formats
            save_job_data(company_name, jobs, career_url)
            successful_scrapes += 1
            total_jobs += len(jobs)
            print(f"✅ Found {len(jobs)} jobs for {company_name}")
        else:
            failed_scrapes += 1
            print(f"🔴 No jobs found for {company_name}")
    
    # Final Summary
    print(f"\n{'='*60}")
    print(f"🎉 FINAL ENHANCED EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"📊 Total companies processed: {total_companies}")
    print(f"✅ Successful scrapes: {successful_scrapes}")
    print(f"🔴 Failed scrapes: {failed_scrapes}")
    print(f"💼 Total jobs found: {total_jobs}")
    print(f"📁 CSV Results saved in: {RESULTS_DIR}")
    print(f"📄 JSON Data saved in: {DATA_DIR}")
    print(f"⚙️  Configurations saved in: {CONFIGURATIONS_FILE}")
    print(f"🔍 Enhanced data includes: Job IDs, URLs, Descriptions, Requirements, Salary, Skills, etc.")
    print(f"{'='*60}")
