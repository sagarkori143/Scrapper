"""
Enhanced selector detection for popular career sites
"""

CAREER_SITE_PATTERNS = {
    'google': {
        'likely_selectors': {
            'job_item': ['[data-job-id]', '.job-tile', '.search-result', '[role="listitem"]'],
            'title': ['h3', '.job-title', '[data-automation-id="jobTitle"]'],
            'location': ['.location', '.job-location', '[data-automation-id="jobLocation"]']
        }
    },
    'microsoft': {
        'likely_selectors': {
            'job_item': ['.ms-List-cell', '[data-automation-id="jobTitle"]', '.job-item'],
            'title': ['h3', '.job-title', 'a[data-automation-id="jobTitle"]'],
            'location': ['.location', '.job-location']
        }
    },
    'generic': {
        'common_patterns': [
            'job', 'position', 'career', 'listing', 'opening', 'vacancy', 
            'opportunity', 'role', 'posting', 'search-result'
        ]
    }
}

def get_enhanced_prompt_for_site(url: str) -> str:
    """
    Generate enhanced prompts based on the target website
    """
    site_hints = ""
    
    if 'google' in url.lower():
        site_hints = """
        GOOGLE CAREERS SPECIFIC HINTS:
        - Jobs are often in elements with data-job-id attributes
        - Look for role="listitem" containers
        - Titles are usually in h3 tags or elements with job-title classes
        - Locations often have location or job-location classes
        """
    elif 'microsoft' in url.lower():
        site_hints = """
        MICROSOFT CAREERS SPECIFIC HINTS:
        - Jobs may be in .ms-List-cell containers
        - Look for data-automation-id attributes
        - Titles often have job-title classes or are in anchor tags
        """
    
    base_prompt = """
    You are an expert web scraping assistant analyzing a company's job listings page. 

    IMPORTANT: You must analyze the HTML structure carefully and provide SPECIFIC CSS selectors.
    
    {}
    
    Your task is to identify CSS selectors for these elements:

    1. **job_item**: Container for each individual job posting (div, article, li, etc.)
    2. **title**: Job title text within each job container
    3. **location**: Job location text within each job container  
    4. **job_link**: Clickable link/button that opens full job details (must be <a> tag or clickable element)
    5. **job_id**: Unique identifier (in href URLs, data attributes, or visible text)
    6. **description**: Brief job summary/description text visible on listing page
    7. **pagination_next**: Next page button/link for pagination

    ANALYSIS STRATEGY:
    - Look for repeating patterns in the HTML structure
    - Focus on semantic HTML elements (article, section, div with job-related classes)
    - Common job listing patterns: class names containing "job", "position", "career", "listing"
    - Look for data attributes like data-job-id, data-automation-id
    - For job_link: Look for <a> tags with href containing job URLs
    - For job_id: Check href patterns like "/job/12345" or data-id attributes
    - If an element doesn't exist, set its value to null

    CRITICAL REQUIREMENTS:
    - Return ONLY valid CSS selectors that exist in the provided HTML
    - Test selectors mentally against the HTML structure
    - Prefer more specific selectors over generic ones
    - If you cannot find a reliable selector, use null

    You MUST return ONLY a raw JSON object with no explanations or markdown:
    {{
      "job_item": "specific.css.selector.for.job.container",
      "title": "specific.css.selector.for.title",
      "location": "specific.css.selector.for.location", 
      "job_link": "specific.css.selector.for.clickable.link",
      "job_id": "specific.css.selector.for.identifier",
      "description": "specific.css.selector.for.description",
      "pagination_next": "specific.css.selector.for.next.page"
    }}
    """.format(site_hints)
    
    return base_prompt
