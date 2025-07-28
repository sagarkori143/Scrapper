"""
Intelligent Job Scraper - Main Entry Point
A modular, AI-powered web scraper for job listings from multiple companies.

This scraper uses Google's Gemini AI to automatically analyze website structures
and extract job information. It supports batch processing of multiple companies
with intelligent configuration management and robust fallback support.

Author: Your Name
Version: 2.0 (Enhanced with Fallback Support)
"""

import argparse
from config import COMPANIES_FILE
from web_scraper import scout_mode, scrape_mode
from batch_operations import batch_scout_mode, batch_scrape_mode, intelligent_scrape_all
from data_storage import save_job_data
from gemini_ai import get_fallback_status


def display_startup_info():
    """Display startup information including fallback configuration."""
    print("🚀 Enhanced Job Scraper Starting...")
    print("=" * 50)
    
    # Display fallback status
    fallback_info = get_fallback_status()
    print("🛡️ AI Fallback Configuration:")
    for i, model in enumerate(fallback_info["model_hierarchy"], 1):
        print(f"   {i}. {model['name']} ({model['description']})")
    print(f"   📊 Max retry attempts: {fallback_info['max_retry_attempts']}")
    print(f"   ⏱️ Retry delay: {fallback_info['retry_delay_seconds']}s")
    print(f"   🔄 Total fallback options: {fallback_info['total_fallback_options']}")
    print("=" * 50)


def main():
    """Main entry point for the intelligent job scraper."""
    # Display startup information and fallback configuration
    display_startup_info()
    
    parser = argparse.ArgumentParser(
        description="An intelligent scraper using Gemini AI and Playwright.",
        epilog="Example: python scrapper.py (runs intelligent workflow for all companies)"
    )
    subparsers = parser.add_subparsers(dest="mode", required=False, help="Operating mode")

    # Scout mode parser
    parser_scout = subparsers.add_parser(
        "scout", 
        help="Analyze a website with Gemini and create a config file."
    )
    parser_scout.add_argument(
        "--url", 
        required=True, 
        help="The URL of the job listings page to scout."
    )

    # Scrape mode parser
    parser_scrape = subparsers.add_parser(
        "scrape", 
        help="Scrape a website with enhanced extraction (job descriptions, IDs, etc.)"
    )
    parser_scrape.add_argument(
        "--url", 
        required=True, 
        help="The URL of the job listings page to scrape."
    )

    # Batch scout mode parser
    parser_batch_scout = subparsers.add_parser(
        "batch-scout", 
        help="Scout all companies from companies.json file."
    )
    parser_batch_scout.add_argument(
        "--companies-file", 
        default=COMPANIES_FILE, 
        help="Path to the companies JSON file."
    )

    # Batch scrape mode parser
    parser_batch_scrape = subparsers.add_parser(
        "batch-scrape", 
        help="Scrape all companies with enhanced extraction (job descriptions, IDs, etc.)"
    )
    parser_batch_scrape.add_argument(
        "--companies-file", 
        default=COMPANIES_FILE, 
        help="Path to the companies JSON file."
    )

    args = parser.parse_args()

    # Route to appropriate function based on mode
    if args.mode is None:
        # Default: Run intelligent workflow with enhanced extraction
        print("🤖 Running Enhanced Intelligent Scraping Workflow...")
        print("   🔍 Enhanced mode: Job IDs, URLs, descriptions, requirements, salary, etc.")
        print("   (Use 'python scrapper.py --help' to see other options)")
        intelligent_scrape_all()
        
    elif args.mode == "scout":
        # Scout single website
        scout_mode(args.url)
        
    elif args.mode == "scrape":
        # Scrape single website with enhanced extraction
        jobs = scrape_mode(args.url, extract_full_details=True)
        if jobs:
            save_job_data("SingleScrape", jobs, args.url)
            
    elif args.mode == "batch-scout":
        # Scout all companies
        batch_scout_mode(args.companies_file)
        
    elif args.mode == "batch-scrape":
        # Scrape all companies with enhanced extraction
        batch_scrape_mode(args.companies_file)


if __name__ == "__main__":
    main()