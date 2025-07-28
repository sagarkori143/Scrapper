"""
Intelligent Job Scraper Package
A modular, AI-powered web scraper for job listings from multiple companies.

This package provides:
- AI-powered website analysis using Google Gemini
- Automated CSS selector generation
- Batch processing of multiple companies
- Intelligent configuration management
- Multiple output formats (CSV and JSON)

Modules:
    config: Configuration and environment setup
    utils: Utility functions and helpers  
    data_storage: Data saving and storage management
    gemini_ai: Google Gemini AI integration
    web_scraper: Browser automation and scraping
    batch_operations: Batch processing workflows

Usage:
    python scrapper.py  # Run intelligent workflow for all companies
    python scrapper.py scout --url <URL>  # Scout single website
    python scrapper.py scrape --url <URL>  # Scrape single website
    python scrapper.py batch-scout  # Scout all companies
    python scrapper.py batch-scrape  # Scrape all companies

Author: Your Name
Version: 2.0 (Modular)
"""

__version__ = "2.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import main functions for easy access
from web_scraper import scout_mode, scrape_mode
from batch_operations import batch_scout_mode, batch_scrape_mode, intelligent_scrape_all
from data_storage import save_job_data, save_company_data_json, save_job_data_csv
from utils import load_companies, get_company_configuration, ensure_directories

__all__ = [
    'scout_mode',
    'scrape_mode', 
    'batch_scout_mode',
    'batch_scrape_mode',
    'intelligent_scrape_all',
    'save_job_data',
    'save_company_data_json',
    'save_job_data_csv',
    'load_companies',
    'get_company_configuration',
    'ensure_directories'
]
