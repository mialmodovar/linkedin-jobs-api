# LinkedIn Jobs API - Python Version

A Python module for scraping job listings from LinkedIn, translated from the original Node.js version. This module provides both synchronous and asynchronous interfaces for fetching job data.

## Features

- ⚡ Lightning Fast
- ✨ Minimal and lightweight
- 🔥 Advanced Filters
- 🤩 Async/Await Support
- 📦 Easy to integrate with FastAPI
- 🗄️ Built-in caching system
- 🛡️ Error handling and retry logic

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install aiohttp beautifulsoup4 lxml
```

## Quick Start

### Basic Usage

```python
from linkedin_jobs_api import query

# Basic job search
query_options = {
    "keyword": "software engineer",
    "location": "San Francisco",
    "limit": 10
}

jobs = query(query_options)
print(f"Found {len(jobs)} jobs")
```

### Async Usage (Recommended for FastAPI)

```python
from linkedin_jobs_api import query_async, get_job_details

async def search_jobs():
    query_options = {
        "keyword": "python developer",
        "location": "Remote",
        "remoteFilter": "remote",
        "limit": 5
    }
    
    jobs = await query_async(query_options)
    return jobs

async def get_detailed_job_info(job_url):
    """Get detailed information from a specific job URL"""
    job_details = await get_job_details(job_url)
    return job_details
```

### FastAPI Integration

```python
from fastapi import FastAPI
from linkedin_jobs_api import query_async

app = FastAPI()

@app.get("/jobs")
async def get_jobs(keyword: str = "", location: str = ""):
    query_options = {
        "keyword": keyword,
        "location": location,
        "limit": 20
    }
    
    jobs = await query_async(query_options)
    return {"jobs": jobs, "count": len(jobs)}
```

## API Parameters

| Parameter | Type | Description | Example Values |
|-----------|------|-------------|----------------|
| `keyword` | string | Job title or keywords to search | "software engineer", "data scientist" |
| `location` | string | Location to search in | "San Francisco", "Remote", "New York" |
| `dateSincePosted` | string | Time filter for job postings | "past month", "past week", "24hr" |
| `jobType` | string | Type of employment | "full time", "part time", "contract", "internship" |
| `remoteFilter` | string | Remote work preference | "on-site", "remote", "hybrid" |
| `salary` | string | Minimum salary expectation | "40000", "60000", "80000", "100000", "120000" |
| `experienceLevel` | string | Required experience level | "internship", "entry level", "associate", "senior", "director", "executive" |
| `limit` | int | Maximum number of jobs to return | 10, 50, 100 |
| `page` | int | Page number (0-based) | 0, 1, 2 |
| `sortBy` | string | Sort order | "recent", "relevant" |
| `has_verification` | bool | Only verified companies | true, false |
| `under_10_applicants` | bool | Jobs with fewer than 10 applicants | true, false |

## Response Format

Each job object contains the following fields:

```python
{
    "position": "Software Engineer",
    "company": "Tech Corp",
    "location": "San Francisco, CA",
    "date": "2023-11-20",
    "salary": "$80,000 - $120,000",
    "jobUrl": "https://linkedin.com/jobs/view/...",
    "companyLogo": "https://static.licdn.com/...",
    "agoTime": "2 days ago"
}
```

## Job Details Extraction

The module now includes a function to extract detailed information from individual job URLs:

```python
from linkedin_jobs_api import get_job_details

# Extract detailed job information
job_url = "https://www.linkedin.com/jobs/view/software-engineer-..."
job_details = await get_job_details(job_url)

print(f"Job Title: {job_details['job_title']}")
print(f"Company: {job_details['company_name']}")
print(f"Description: {job_details['job_description'][:200]}...")
print(f"Salary: {job_details['salary']}")
print(f"Skills: {job_details['skills']}")
```

### Job Details Response Format

The `get_job_details()` function returns comprehensive job information:

```python
{
    "job_title": "Software Engineer",
    "company_name": "Tech Corp",
    "location": "San Francisco, CA",
    "posted_date": "2023-11-20",
    "applicant_count": "Over 200 applicants",
    "job_description": "Full job description text...",
    "salary": "$140k-$220k",
    "employment_type": "Full-time",
    "seniority_level": "Mid-Senior level",
    "job_function": "Engineering",
    "industries": "Technology",
    "company_logo": "https://static.licdn.com/...",
    "company_size": "11-50 employees",
    "benefits": "Health insurance, 401k...",
    "skills": ["Python", "JavaScript", "React"],
    "job_url": "https://www.linkedin.com/jobs/view/...",
    "scraped_at": 1703123456.789
}
```

## Advanced Examples

### Search for Remote Python Jobs

```python
query_options = {
    "keyword": "python developer",
    "remoteFilter": "remote",
    "experienceLevel": "senior",
    "salary": "100000",
    "limit": 20
}

jobs = query(query_options)
```

### Find Entry-Level Jobs in Specific Location

```python
query_options = {
    "keyword": "junior developer",
    "location": "Austin, Texas",
    "experienceLevel": "entry level",
    "jobType": "full time",
    "dateSincePosted": "past week",
    "limit": 15
}

jobs = query(query_options)
```

### Search with Multiple Filters

```python
query_options = {
    "keyword": "machine learning engineer",
    "location": "Seattle",
    "remoteFilter": "hybrid",
    "experienceLevel": "senior",
    "salary": "120000",
    "has_verification": True,
    "sortBy": "recent",
    "limit": 25
}

jobs = query(query_options)
```

### Extract Details from Job URLs

```python
# First, search for jobs
jobs = await query_async({
    "keyword": "machine learning engineer",
    "location": "Seattle",
    "limit": 5
})

# Then extract detailed information for each job
for job in jobs:
    if job['jobUrl']:
        details = await get_job_details(job['jobUrl'])
        print(f"Detailed info for {details['job_title']}:")
        print(f"  Description: {details['job_description'][:100]}...")
        print(f"  Skills: {details['skills']}")
```

## Caching

The module includes a built-in caching system to improve performance and reduce API calls:

```python
from linkedin_jobs_api import clear_cache, get_cache_size

# Check cache size
print(f"Cache size: {get_cache_size()}")

# Clear cache
clear_cache()
```

## Error Handling

The module includes robust error handling with automatic retries:

```python
try:
    jobs = query(query_options)
except Exception as e:
    print(f"Error fetching jobs: {e}")
```

## FastAPI Complete Example

See `fastapi_example.py` for a complete FastAPI application that demonstrates:

- RESTful API endpoints
- Request/response models with Pydantic
- Both GET and POST endpoints
- Cache management
- Error handling
- API documentation

To run the FastAPI example:

```bash
pip install fastapi uvicorn
python fastapi_example.py
```

Then visit `http://localhost:8000/docs` for interactive API documentation.

## Testing

Run the test suite to verify everything works:

```bash
python test_python.py
```

## Differences from Node.js Version

1. **Async Support**: Full async/await support for better performance in web applications
2. **Type Hints**: Complete type annotations for better IDE support
3. **Pydantic Models**: Ready-to-use models for FastAPI integration
4. **Better Error Handling**: More detailed error messages and logging
5. **Pythonic API**: Follows Python conventions and best practices

## Rate Limiting

The module includes built-in rate limiting and retry logic to avoid being blocked by LinkedIn. It automatically:

- Adds delays between requests
- Implements exponential backoff on errors
- Handles 429 (rate limit) responses
- Caches results to reduce API calls

## Legal Notice

This module is for educational and research purposes. Please respect LinkedIn's Terms of Service and robots.txt. Use responsibly and consider implementing appropriate delays between requests.

## Contributing

Feel free to contribute improvements, bug fixes, or additional features!

## License

MIT License - see LICENSE file for details.
