"""
Intelligent Job Scraper - Main Entry Point
A modular, AI-powered web scraper for job listings from multiple companies.

This scraper uses Google's Gemini AI to automatically analyze website structures
and extract job information. It supports batch processing of multiple companies
with intelligent configuration management.

Author: Your Name
Version: 2.0 (Modular)
"""

import argparse
from config import COMPANIES_FILE
from web_scraper import scout_mode, scrape_mode
from batch_operations import batch_scout_mode, batch_scrape_mode, intelligent_scrape_all
from data_storage import save_job_data


def main():
    """Main entry point for the intelligent job scraper."""
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
        help="Scrape a website using an existing config file."
    )
    parser_scrape.add_argument(
        "--url", 
        required=True, 
        help="The URL of the job listings page to scrape."
    )
    parser_scrape.add_argument(
        "--enhanced", 
        action="store_true", 
        help="Enable enhanced extraction (job descriptions, IDs, etc.)"
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
        help="Scrape all companies from companies.json file."
    )
    parser_batch_scrape.add_argument(
        "--companies-file", 
        default=COMPANIES_FILE, 
        help="Path to the companies JSON file."
    )
    parser_batch_scrape.add_argument(
        "--enhanced", 
        action="store_true", 
        help="Enable enhanced extraction for all companies (job descriptions, IDs, etc.)"
    )

    args = parser.parse_args()

    # Route to appropriate function based on mode
    if args.mode is None:
        # Default: Run intelligent workflow with enhanced extraction
        print("🤖 Running Enhanced Intelligent Scraping Workflow...")
        print("   (Use 'python scrapper.py --help' to see other options)")
        intelligent_scrape_all(enhanced=True)
        
    elif args.mode == "scout":
        # Scout single website
        scout_mode(args.url)
        
    elif args.mode == "scrape":
        # Scrape single website
        enhanced = getattr(args, 'enhanced', False)
        jobs = scrape_mode(args.url, extract_full_details=enhanced)
        if jobs:
            save_job_data("SingleScrape", jobs, args.url)
            
    elif args.mode == "batch-scout":
        # Scout all companies
        batch_scout_mode(args.companies_file)
        
    elif args.mode == "batch-scrape":
        # Scrape all companies
        enhanced = getattr(args, 'enhanced', False)
        batch_scrape_mode(args.companies_file, enhanced=enhanced)


if __name__ == "__main__":
    main()