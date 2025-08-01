# Enhanced Intelligent Job Scraper 🤖

A modular, AI-powered web scraper for job listings from multiple companies using Google's Gemini AI and Playwright with enhanced data extraction capabilities.

## 🏗️ **Modular Architecture**

### **Project Structure**
```
├── scrapper.py              # 🎯 Main entry point
├── config.py               # ⚙️  Configuration and environment setup
├── utils.py                # 🛠️  Utility functions and helpers
├── data_storage.py         # 💾 Data saving and storage management
├── gemini_ai.py           # 🧠 Google Gemini AI integration
├── web_scraper.py         # 🌐 Browser automation and scraping
├── batch_operations.py    # 📦 Batch processing workflows
├── __init__.py            # 📋 Package initialization
├── companies.json         # 🏢 List of companies (115 companies)
├── configurations.json    # ⚙️  Central configuration storage
├── data/                  # 📄 Individual company JSON files
├── results/               # 📊 CSV output files
└── configs/               # 🗂️  Individual config files (legacy)
```

## 🚀 **Enhanced Features**

- **🧠 AI-Powered Analysis**: Uses Google Gemini to automatically analyze website structures
- **🔍 Enhanced Data Extraction**: Extracts job IDs, URLs, descriptions, requirements, salary info, and more
- **⚙️ Intelligent Configuration**: Auto-scouts companies that need configurations
- **📦 Batch Processing**: Process all 115 companies with a single command
- **💾 Dual Storage**: Saves data in both CSV and JSON formats with rich metadata
- **🔄 Incremental Learning**: Once scouted, companies never need re-scouting
- **📊 Rich Reporting**: Comprehensive progress and summary reports
- **🔗 Full Job Details**: Navigates to individual job pages for complete information

## 🛠️ **Enhanced Module Overview**

### **config.py**
- Environment variables and API setup
- File and directory constants
- Browser and timeout configurations

### **utils.py**
- Company data loading and management
- Configuration file operations
- Safe filename generation
- Directory management

### **data_storage.py**
- Enhanced CSV file generation with all fields
- Comprehensive JSON data structuring
- Dual-format saving with metadata
- Support for rich job data fields

### **gemini_ai.py**
- Google Gemini API integration
- HTML analysis and selector extraction
- Job detail page structure analysis
- Enhanced prompt engineering for comprehensive data extraction
- Error handling and response cleaning

### **web_scraper.py**
- Browser automation with Playwright
- HTML cleaning and parsing
- Multi-page scraping with pagination
- Enhanced job data extraction (IDs, URLs, descriptions)
- Automatic job detail page analysis and extraction
- Job data extraction with comprehensive field coverage

### **batch_operations.py**
- Intelligent workflow orchestration
- Enhanced batch scouting and scraping
- Progress tracking and reporting
- Error handling for multiple companies

## 📋 **Enhanced Usage**

### **Simple Command (Recommended)**
```bash
python scrapper.py
```
This runs the intelligent enhanced workflow:
1. ✅ Checks existing configurations
2. 🕵️‍♂️ Scouts companies that need it
3. ⚡ Scrapes jobs from all companies with enhanced data extraction

### **Enhanced vs Basic Extraction**
```bash
# Enhanced extraction (default) - includes job descriptions, IDs, requirements, etc.
python scrapper.py

# Basic extraction - only title and location
python scrapper.py batch-scrape --companies-file companies.json

# Enhanced single company scrape
python scrapper.py scrape --url https://careers.google.com/ --enhanced
```

### **Individual Commands**
```bash
# Scout a single website
python scrapper.py scout --url https://careers.google.com/

# Scrape a single website with enhanced data
python scrapper.py scrape --url https://careers.google.com/ --enhanced

# Scout all companies
python scrapper.py batch-scout

# Scrape all companies with enhanced extraction
python scrapper.py batch-scrape --enhanced
```

## 📦 **Installation**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

3. **Create `.env` file:**
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

## 📊 **Enhanced Output Structure**

### **JSON Data Files** (Primary)
```json
{
  "company_name": "Google",
  "career_url": "https://careers.google.com/",
  "total_jobs": 150,
  "scraped_at": "2025-07-28T14:30:22.123456",
  "enhanced_extraction": true,
  "jobs": [
    {
      "title": "Software Engineer",
      "location": "Mountain View, CA",
      "job_id": "12345",
      "job_url": "https://careers.google.com/jobs/results/12345",
      "preview_description": "Join our team to build...",
      "full_description": "We are looking for talented engineers...",
      "requirements": "Bachelor's degree in Computer Science...",
      "job_type": "Full-time",
      "experience_level": "Mid-level",
      "salary": "$120,000 - $180,000",
      "skills": "Python, JavaScript, React",
      "company": "Google",
      "scraped_date": "2025-07-28"
    }
  ]
}
```

### **CSV Files** (Enhanced Support)
- Timestamped CSV files in `results/` folder
- Enhanced format includes all extracted fields
- Standard format: `company_jobs_YYYYMMDD_HHMMSS.csv`
- Columns: title, location, job_id, job_url, preview_description, full_description, requirements, job_type, experience_level, salary, skills, etc.

## 🔧 **Enhanced Configuration Management**

- **Central Storage**: All configurations in `configurations.json`
- **Enhanced Selectors**: Includes job links, IDs, descriptions, and detail page elements
- **Automatic Scouting**: Missing configs trigger AI analysis for both listing and detail pages
- **Incremental Updates**: Only scout when needed
- **Error Recovery**: Failed scouts don't stop the process

## 📈 **Enhanced Data Fields**

The scraper now extracts comprehensive job information:

### **Listing Page Data**
- Job title
- Job location  
- Job ID/identifier
- Job URL/link
- Preview description
- Company name

### **Detail Page Data** (Enhanced Mode)
- Full job description
- Requirements/qualifications
- Job type (full-time, part-time, etc.)
- Experience level required
- Salary information
- Required skills/technologies
- Application deadline
- Company information

## 🏢 **Supported Companies**

The scraper includes 115+ companies across industries:
- **Tech Giants**: Google, Microsoft, Meta, Apple, Amazon
- **E-commerce**: Flipkart, Myntra, Nykaa, Meesho
- **Consulting**: McKinsey, BCG, Deloitte, PwC
- **Airlines**: Emirates, Qatar Airways, British Airways
- **And many more!**

## 🚀 **Quick Start**

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Install Playwright: `playwright install`
4. Set up your API key in `.env`
5. Run: `python scrapper.py`
6. Wait for enhanced magic to happen! ✨

The scraper will automatically handle everything - scouting, configuration, and enhanced data extraction for all 115 companies! 🎉

## 🔍 **Enhanced Benefits**

1. **🧹 Clean Code**: Each module has a single responsibility
2. **🔧 Easy Maintenance**: Update individual components without affecting others
3. **🧪 Testable**: Each module can be tested independently  
4. **📦 Reusable**: Import and use modules in other projects
5. **📖 Readable**: Clear separation of concerns
6. **⚡ Extensible**: Easy to add new features or data sources
7. **🔍 Comprehensive**: Extracts maximum job information available
8. **🤖 Intelligent**: AI-powered analysis for both listing and detail pages
