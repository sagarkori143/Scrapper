"""
Data storage module for the intelligent job scraper.
Handles saving job data in various formats (CSV and JSON).
"""

import os
import json
import csv
from datetime import datetime
from config import RESULTS_DIR, DATA_DIR
from utils import get_safe_company_name


def save_job_data_csv(company_name: str, jobs: list):
    """Save scraped job data to CSV file with enhanced fields."""
    if not jobs:
        print(f"No jobs to save for {company_name}")
        return
    
    safe_name = get_safe_company_name(company_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(RESULTS_DIR, f"{safe_name}_jobs_{timestamp}.csv")
    
    # Determine all available fields from the job data
    all_fields = set()
    for job in jobs:
        all_fields.update(job.keys())
    
    # Define field order (common fields first, then additional ones)
    ordered_fields = ['title', 'location', 'company', 'job_id', 'job_url', 'preview_description', 
                     'full_description', 'requirements', 'job_type', 'experience_level', 
                     'salary', 'skills', 'deadline', 'company_info', 'scraped_date']
    
    # Add any additional fields that might exist
    fieldnames = [field for field in ordered_fields if field in all_fields]
    fieldnames.extend([field for field in all_fields if field not in ordered_fields])
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for job in jobs:
            # Ensure company and scraped_date are included
            job_data = job.copy()
            job_data['company'] = company_name
            job_data['scraped_date'] = datetime.now().strftime("%Y-%m-%d")
            writer.writerow(job_data)
    
    print(f"✅ Saved {len(jobs)} jobs to CSV: {filename}")
    return filename


def save_company_data_json(company_name: str, jobs: list, company_url: str = ""):
    """Save scraped job data as JSON file in the data folder with enhanced fields."""
    if not jobs:
        print(f"No jobs to save for {company_name}")
        return
    
    safe_name = get_safe_company_name(company_name)
    filename = os.path.join(DATA_DIR, f"{safe_name}.json")
    
    # Prepare the data structure
    company_data = {
        "company_name": company_name,
        "career_url": company_url,
        "total_jobs": len(jobs),
        "scraped_at": datetime.now().isoformat(),
        "enhanced_extraction": True,  # Flag to indicate enhanced data
        "jobs": []
    }
    
    # Add job data with enhanced structure
    for job in jobs:
        job_entry = job.copy()
        
        # Ensure basic fields are present
        job_entry["company"] = company_name
        job_entry["scraped_date"] = datetime.now().strftime("%Y-%m-%d")
        
        # Clean up any None values for better JSON readability
        job_entry = {k: v for k, v in job_entry.items() if v is not None}
        
        company_data["jobs"].append(job_entry)
    
    # Save to JSON file
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(company_data, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(jobs)} jobs to JSON: {filename}")
    return filename


def save_job_data(company_name: str, jobs: list, company_url: str = ""):
    """Save job data in both CSV and JSON formats."""
    if not jobs:
        print(f"No jobs to save for {company_name}")
        return
    
    # Save in both formats
    csv_file = save_job_data_csv(company_name, jobs)
    json_file = save_company_data_json(company_name, jobs, company_url)
    
    return csv_file, json_file
