"""
Utility functions for the intelligent job scraper.
Contains helper functions for file operations, directory management, and data processing.
"""

import os
import json
from datetime import datetime
from config import CONFIGS_DIR, RESULTS_DIR, DATA_DIR, COMPANIES_FILE, CONFIGURATIONS_FILE


def ensure_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(CONFIGS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)


def get_safe_company_name(company_name: str) -> str:
    """Convert company name to a safe key for storage."""
    safe_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return safe_name.replace(' ', '_').lower()


def get_company_config_file(company_name: str) -> str:
    """Get the config file path for a specific company."""
    safe_name = get_safe_company_name(company_name)
    return os.path.join(CONFIGS_DIR, f"{safe_name}_config.json")


def load_companies(companies_file: str = COMPANIES_FILE) -> list:
    """Load companies from JSON file."""
    if not os.path.exists(companies_file):
        print(f"🔴 Companies file '{companies_file}' not found.")
        return []
    
    with open(companies_file, 'r') as f:
        companies = json.load(f)
    print(f"✅ Loaded {len(companies)} companies from {companies_file}")
    return companies


def load_configurations() -> dict:
    """Load configurations from the configurations file."""
    if not os.path.exists(CONFIGURATIONS_FILE):
        return {}
    
    try:
        with open(CONFIGURATIONS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        print("🔴 Error loading configurations file. Starting with empty configurations.")
        return {}


def save_configuration(company_name: str, selectors: dict):
    """Save company configuration to the configurations file."""
    configurations = load_configurations()
    safe_name = get_safe_company_name(company_name)
    configurations[safe_name] = {
        'company_name': company_name,
        'selectors': selectors,
        'last_updated': datetime.now().isoformat()
    }
    
    with open(CONFIGURATIONS_FILE, 'w') as f:
        json.dump(configurations, f, indent=2)
    
    print(f"✅ Configuration saved for {company_name}")


def get_company_configuration(company_name: str) -> dict:
    """Get configuration for a specific company."""
    configurations = load_configurations()
    safe_name = get_safe_company_name(company_name)
    
    if safe_name in configurations:
        return configurations[safe_name].get('selectors', {})
    return None
