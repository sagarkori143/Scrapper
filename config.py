"""
Configuration module for the intelligent job scraper.
Contains all configuration constants and environment setup.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# API Configuration
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("🔴 GOOGLE_API_KEY not found in .env file. Please create it before running.")

# Configure Gemini API
genai.configure(api_key=API_KEY)

# File and Directory Constants
CONFIG_FILE = 'config.json'
COMPANIES_FILE = 'companies.json'
CONFIGURATIONS_FILE = 'configurations.json'
CONFIGS_DIR = 'configs'
RESULTS_DIR = 'results'
DATA_DIR = 'data'

# Gemini Model Configuration with Fallback Support
# Primary model (fastest and most cost-effective)
GEMINI_MODEL_PRIMARY = 'gemini-1.5-flash'
# Fallback model (more reliable for complex tasks)
GEMINI_MODEL_FALLBACK = 'gemini-1.5-pro'
# Emergency fallback model (most stable)
GEMINI_MODEL_EMERGENCY = 'gemini-1.0-pro'

# Model retry configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2

# Gemini API Rate Limiting Configuration
# You can adjust these based on your Gemini API tier:
# Free tier: 15 requests per minute
# Pay-as-you-go: 1000 requests per minute  
# Paid plans: Higher limits (check your quota)

# Set your tier here: 'free', 'paid', or 'custom'
GEMINI_API_TIER = 'free'

# Rate limiting configurations by tier
RATE_LIMITS = {
    'free': {'requests_per_minute': 15, 'buffer_seconds': 5},
    'paid': {'requests_per_minute': 300, 'buffer_seconds': 2},  # Conservative for paid
    'custom': {'requests_per_minute': 15, 'buffer_seconds': 5}  # Modify as needed
}

# Apply rate limits based on tier
current_limits = RATE_LIMITS[GEMINI_API_TIER]
GEMINI_REQUESTS_PER_MINUTE = current_limits['requests_per_minute']
GEMINI_RATE_LIMIT_BUFFER = current_limits['buffer_seconds']
GEMINI_MIN_REQUEST_INTERVAL = 60 / GEMINI_REQUESTS_PER_MINUTE + GEMINI_RATE_LIMIT_BUFFER

# Browser Configuration
BROWSER_TIMEOUT = 60000
PAGE_LOAD_WAIT = 5000
SELECTOR_TIMEOUT = 30000
