"""
FastAPI example showing how to use the LinkedIn Jobs API module
"""

from fastapi import FastAPI, HTTPException, Query as FastAPIQuery
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import asyncio
from linkedin_jobs_api import query_async, get_job_details, clear_cache, get_cache_size

app = FastAPI(
    title="LinkedIn Jobs API",
    description="A FastAPI wrapper for the LinkedIn Jobs scraper",
    version="1.0.0"
)


class JobSearchRequest(BaseModel):
    """Request model for job search"""
    keyword: Optional[str] = ""
    location: Optional[str] = ""
    date_since_posted: Optional[str] = ""  # "past month", "past week", "24hr"
    job_type: Optional[str] = ""  # "full time", "part time", "contract", etc.
    remote_filter: Optional[str] = ""  # "on-site", "remote", "hybrid"
    salary: Optional[str] = ""  # "40000", "60000", "80000", "100000", "120000"
    experience_level: Optional[str] = ""  # "internship", "entry level", "associate", etc.
    limit: Optional[int] = 0
    page: Optional[int] = 0
    sort_by: Optional[str] = ""  # "recent", "relevant"
    has_verification: Optional[bool] = False
    under_10_applicants: Optional[bool] = False


class JobResponse(BaseModel):
    """Response model for individual job"""
    position: str
    company: str
    location: str
    date: str
    salary: str
    job_url: str
    company_logo: str
    ago_time: str


class JobSearchResponse(BaseModel):
    """Response model for job search results"""
    jobs: List[JobResponse]
    total_count: int
    cache_size: int


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "LinkedIn Jobs API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "cache_size": get_cache_size()}


@app.post("/jobs/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    """
    Search for jobs on LinkedIn
    
    This endpoint accepts a JobSearchRequest and returns matching job listings.
    """
    try:
        # Log incoming request parameters
      
        
        # Convert Pydantic model to dictionary for the LinkedIn API (snake_case to camelCase)
        query_params = {
            "keyword": request.keyword,
            "location": request.location,
            "dateSincePosted": request.date_since_posted,  # Convert snake_case to camelCase
            "jobType": request.job_type,  # Convert snake_case to camelCase
            "remoteFilter": request.remote_filter,  # Convert snake_case to camelCase
            "salary": request.salary,
            "experienceLevel": request.experience_level,  # Convert snake_case to camelCase
            "limit": request.limit,
            "page": request.page,
            "sortBy": request.sort_by,  # Convert snake_case to camelCase
            "has_verification": request.has_verification,
            "under_10_applicants": request.under_10_applicants,
        }
        
       
        # Call the LinkedIn Jobs API
        jobs_data = await query_async(query_params)
        
        # Convert to response format
        job_responses = []
        for job in jobs_data:
            job_responses.append(JobResponse(
                position=job.get("position", ""),
                company=job.get("company", ""),
                location=job.get("location", ""),
                date=job.get("date", ""),
                salary=job.get("salary", ""),
                job_url=job.get("jobUrl", ""),
                company_logo=job.get("companyLogo", ""),
                ago_time=job.get("agoTime", "")
            ))
        
        return JobSearchResponse(
            jobs=job_responses,
            total_count=len(job_responses),
            cache_size=get_cache_size()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")


@app.get("/jobs/search", response_model=JobSearchResponse)
async def search_jobs_get(
    keyword: Optional[str] = FastAPIQuery("", description="Job keyword to search for"),
    location: Optional[str] = FastAPIQuery("", description="Location to search in"),
    date_since_posted: Optional[str] = FastAPIQuery("", description="Date filter: past month, past week, 24hr"),
    job_type: Optional[str] = FastAPIQuery("", description="Job type: full time, part time, contract, etc."),
    remote_filter: Optional[str] = FastAPIQuery("", description="Remote filter: on-site, remote, hybrid"),
    salary: Optional[str] = FastAPIQuery("", description="Minimum salary: 40000, 60000, 80000, 100000, 120000"),
    experience_level: Optional[str] = FastAPIQuery("", description="Experience level: internship, entry level, associate, etc."),
    limit: Optional[int] = FastAPIQuery(0, description="Maximum number of jobs to return"),
    page: Optional[int] = FastAPIQuery(0, description="Page number (0-based)"),
    sort_by: Optional[str] = FastAPIQuery("", description="Sort by: recent, relevant"),
    has_verification: Optional[bool] = FastAPIQuery(False, description="Only verified companies"),
    under_10_applicants: Optional[bool] = FastAPIQuery(False, description="Under 10 applicants")
):
    """
    Search for jobs on LinkedIn (GET version)
    
    This endpoint allows you to search for jobs using query parameters.
    """
    try:
        # Convert query parameters to dictionary for the LinkedIn API
        query_params = {
            "keyword": keyword,
            "location": location,
            "dateSincePosted": date_since_posted,
            "jobType": job_type,
            "remoteFilter": remote_filter,
            "salary": salary,
            "experienceLevel": experience_level,
            "limit": limit,
            "page": page,
            "sortBy": sort_by,
            "has_verification": has_verification,
            "under_10_applicants": under_10_applicants,
        }
        
        # Call the LinkedIn Jobs API
        jobs_data = await query_async(query_params)
        
        # Convert to response format
        job_responses = []
        for job in jobs_data:
            job_responses.append(JobResponse(
                position=job.get("position", ""),
                company=job.get("company", ""),
                location=job.get("location", ""),
                date=job.get("date", ""),
                salary=job.get("salary", ""),
                job_url=job.get("jobUrl", ""),
                company_logo=job.get("companyLogo", ""),
                ago_time=job.get("agoTime", "")
            ))
        
        return JobSearchResponse(
            jobs=job_responses,
            total_count=len(job_responses),
            cache_size=get_cache_size()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")


@app.delete("/cache")
async def clear_job_cache():
    """Clear the job search cache"""
    try:
        clear_cache()
        return {"message": "Cache cleared successfully", "cache_size": get_cache_size()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@app.get("/cache/info")
async def get_cache_info():
    """Get information about the current cache"""
    return {
        "cache_size": get_cache_size(),
        "message": "Cache information retrieved successfully"
    }


@app.get("/jobs/details")
async def get_job_details_endpoint(job_url: str = FastAPIQuery(..., description="LinkedIn job URL to extract details from")):
    """
    Extract detailed job information from a LinkedIn job URL
    
    This endpoint scrapes the full job page to get detailed information including:
    - Full job description
    - Salary information
    - Employment type and seniority level
    - Company information
    - Skills and requirements
    - Benefits and perks
    """
    try:
        if not (job_url.startswith('https://www.linkedin.com/jobs/view/') or 
                job_url.startswith('https://pt.linkedin.com/jobs/view/') or
                job_url.startswith('https://') and '/linkedin.com/jobs/view/' in job_url):
            raise HTTPException(status_code=400, detail="Invalid LinkedIn job URL format")
        
        job_details = await get_job_details(job_url)
        
        if 'error' in job_details:
            raise HTTPException(status_code=500, detail=job_details['error'])
        
        return {
            "job_details": job_details,
            "message": "Job details extracted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting job details: {str(e)}")


@app.post("/jobs/details")
async def get_job_details_post(request: Dict[str, str]):
    """
    Extract detailed job information from a LinkedIn job URL (POST version)
    
    Request body should contain:
    {
        "job_url": "https://www.linkedin.com/jobs/view/..."
    }
    """
    try:
        job_url = request.get('job_url', '')
        
        if not job_url:
            raise HTTPException(status_code=400, detail="job_url is required")
        
        if not (job_url.startswith('https://www.linkedin.com/jobs/view/') or 
                job_url.startswith('https://pt.linkedin.com/jobs/view/') or
                job_url.startswith('https://') and '/linkedin.com/jobs/view/' in job_url):
            raise HTTPException(status_code=400, detail="Invalid LinkedIn job URL format")
        
        job_details = await get_job_details(job_url)
        
        if 'error' in job_details:
            raise HTTPException(status_code=500, detail=job_details['error'])
        
        return {
            "job_details": job_details,
            "message": "Job details extracted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting job details: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
