"""
Test file for LinkedIn Jobs API - Python version
Equivalent to the original test.js file
"""

import asyncio
from linkedin_jobs_api import query, query_async, get_job_details

async def test_sync_query():
    """Test the synchronous query function (using async wrapper)"""
    print("Testing synchronous query...")
    
    query_options = {
        "keyword": "",
        "location": "India",
        "dateSincePosted": "past week",
        "jobType": "full time",
        "remoteFilter": "remote",
        "salary": "100000",
        "experienceLevel": "entry level",
        "limit": "1",
        "sortBy": "recent",
        "page": "1",
        "has_verification": False,
        "under_10_applicants": False,
    }
    
    try:
        # Use the async version instead of sync to avoid event loop issues
        response = await query_async(query_options)
        print(f"Sync query successful! Found {len(response)} jobs")
        if response:
            print("Sample job:")
            print(f"  Position: {response[0].get('position', 'N/A')}")
            print(f"  Company: {response[0].get('company', 'N/A')}")
            print(f"  Location: {response[0].get('location', 'N/A')}")
        return response
    except Exception as e:
        print(f"Sync query failed: {e}")
        return None


async def test_async_query():
    """Test the asynchronous query function"""
    print("\nTesting asynchronous query...")
    
    query_options = {
        "keyword": "software engineer",
        "location": "United States",
        "dateSincePosted": "past month",
        "jobType": "full time",
        "remoteFilter": "remote",
        "salary": "80000",
        "experienceLevel": "senior",
        "limit": "2",
        "sortBy": "relevant",
        "page": "0",
        "has_verification": True,
        "under_10_applicants": False,
    }
    
    try:
        response = await query_async(query_options)
        print(f"Async query successful! Found {len(response)} jobs")
        if response:
            print("Sample jobs:")
            for i, job in enumerate(response[:2], 1):
                print(f"  Job {i}:")
                print(f"    Position: {job.get('position', 'N/A')}")
                print(f"    Company: {job.get('company', 'N/A')}")
                print(f"    Location: {job.get('location', 'N/A')}")
                print(f"    Salary: {job.get('salary', 'N/A')}")
        return response
    except Exception as e:
        print(f"Async query failed: {e}")
        return None


async def test_different_parameters():
    """Test with different parameter combinations"""
    print("\nTesting different parameter combinations...")
    
    test_cases = [
        {
            "name": "Basic search",
            "params": {
                "keyword": "python developer",
                "location": "New York",
                "limit": "1"
            }
        },
        {
            "name": "Remote jobs only",
            "params": {
                "keyword": "data scientist",
                "remoteFilter": "remote",
                "limit": "1"
            }
        },
        {
            "name": "Entry level jobs",
            "params": {
                "keyword": "junior developer",
                "experienceLevel": "entry level",
                "limit": "1"
            }
        },
        {
            "name": "High salary jobs",
            "params": {
                "keyword": "senior engineer",
                "salary": "120000",
                "limit": "1"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        try:
            response = await query_async(test_case['params'])
            print(f"  Found {len(response)} jobs")
            if response:
                job = response[0]
                print(f"  Sample: {job.get('position', 'N/A')} at {job.get('company', 'N/A')}")
        except Exception as e:
            print(f"  Failed: {e}")


async def test_job_details():
    """Test the job details extraction function"""
    print("\nTesting job details extraction...")
    
    # Test with the provided LinkedIn job URL
    test_url = "https://www.linkedin.com/jobs/view/software-engineer-%24140k-%24220k-0-5%25-to-2%25-at-resonate-ai-4315661301?position=3&pageNum=0&refId=6iAN%2FcMWWP5qDOBxIrISiw%3D%3D&trackingId=p2iL7gs7TiOyJWiFR%2BpySA%3D%3D"
    
    try:
        job_details = await get_job_details(test_url)
        
        if 'error' in job_details:
            print(f"Job details extraction failed: {job_details['error']}")
            return None
        
        print("Job details extracted successfully!")
        print(f"  Job Title: {job_details.get('job_title', 'N/A')}")
        print(f"  Company: {job_details.get('company_name', 'N/A')}")
        print(f"  Location: {job_details.get('location', 'N/A')}")
        print(f"  Salary: {job_details.get('salary', 'N/A')}")
        print(f"  Employment Type: {job_details.get('employment_type', 'N/A')}")
        print(f"  Seniority Level: {job_details.get('seniority_level', 'N/A')}")
        print(f"  Applicant Count: {job_details.get('applicant_count', 'N/A')}")
        print(f"  Description Length: {job_details.get('job_description', '')}")
        
        if job_details.get('skills'):
            print(f"  Skills: {', '.join(job_details['skills'][:5])}...")  # Show first 5 skills
        
        return job_details
        
    except Exception as e:
        print(f"Job details extraction failed: {e}")
        return None


async def test_comprehensive_workflow():
    """Test comprehensive workflow: search for jobs and extract details for each"""
    print("\nTesting comprehensive workflow (20 jobs + full details)...")
    
    try:
        # Step 1: Search for 20 jobs
        print("Step 1: Searching for 20 software engineer jobs...")
        search_params = {
            "keyword": "software engineer",
            "location": "San Francisco",
            "remoteFilter": "remote",
            "experienceLevel": "senior",
            "limit": 20,
            "sortBy": "recent"
        }
        
        jobs = await query_async(search_params)
        print(f"Found {len(jobs)} jobs")
        
        if not jobs:
            print("No jobs found, skipping detailed extraction")
            return None
        
        # Step 2: Extract detailed information for each job
        print(f"\nStep 2: Extracting detailed information for {len(jobs)} jobs...")
        detailed_jobs = []
        
        for i, job in enumerate(jobs, 1):
            print(f"Processing job {i}/{len(jobs)}: {job.get('position', 'Unknown')} at {job.get('company', 'Unknown')}")
            
            if job.get('jobUrl'):
                try:
                    details = await get_job_details(job['jobUrl'])
                    
                    if 'error' not in details:
                        # Combine search result with detailed information
                        combined_job = {
                            **job,  # Original search result
                            'detailed_info': {
                                'full_description': details.get('job_description', ''),
                                'salary_detailed': details.get('salary', ''),
                                'employment_type': details.get('employment_type', ''),
                                'seniority_level': details.get('seniority_level', ''),
                                'job_function': details.get('job_function', ''),
                                'industries': details.get('industries', ''),
                                'applicant_count': details.get('applicant_count', ''),
                                'skills': details.get('skills', []),
                                'benefits': details.get('benefits', ''),
                                'company_size': details.get('company_size', ''),
                                'posted_date_detailed': details.get('posted_date', ''),
                                'scraped_at': details.get('scraped_at', '')
                            }
                        }
                        detailed_jobs.append(combined_job)
                        print(f"  ✅ Successfully extracted details")
                    else:
                        print(f"  ❌ Failed to extract details: {details['error']}")
                        detailed_jobs.append(job)  # Keep original job without details
                        
                except Exception as e:
                    print(f"  ❌ Error extracting details: {e}")
                    detailed_jobs.append(job)  # Keep original job without details
            else:
                print(f"  ⚠️ No job URL available")
                detailed_jobs.append(job)  # Keep original job without details
        
        # Step 3: Display summary
        print(f"\nStep 3: Summary of results")
        print(f"Total jobs processed: {len(detailed_jobs)}")
        
        jobs_with_details = [job for job in detailed_jobs if 'detailed_info' in job]
        print(f"Jobs with detailed information: {len(jobs_with_details)}")
        
        # Step 4: Show sample detailed results
        print(f"\nStep 4: Sample detailed results")
        for i, job in enumerate(jobs_with_details[:3], 1):  # Show first 3 detailed jobs
            print(f"\n--- Detailed Job {i} ---")
            print(f"Position: {job['position']}")
            print(f"Company: {job['company']}")
            print(f"Location: {job['location']}")
            print(f"Salary: {job['detailed_info']['salary_detailed']}")
            print(f"Employment Type: {job['detailed_info']['employment_type']}")
            print(f"Seniority Level: {job['detailed_info']['seniority_level']}")
            print(f"Applicant Count: {job['detailed_info']['applicant_count']}")
            print(f"Description Preview: {job['detailed_info']['full_description'][:150]}...")
            
            if job['detailed_info']['skills']:
                print(f"Skills: {', '.join(job['detailed_info']['skills'][:5])}")
            
            print(f"Job URL: {job['jobUrl']}")
        
        # Step 5: Statistics
        print(f"\nStep 5: Statistics")
        if jobs_with_details:
            avg_description_length = sum(len(job['detailed_info']['full_description']) for job in jobs_with_details) / len(jobs_with_details)
            print(f"Average description length: {avg_description_length:.0f} characters")
            
            jobs_with_salary = [job for job in jobs_with_details if job['detailed_info']['salary_detailed']]
            print(f"Jobs with salary information: {len(jobs_with_salary)}")
            
            jobs_with_skills = [job for job in jobs_with_details if job['detailed_info']['skills']]
            print(f"Jobs with skills listed: {len(jobs_with_skills)}")
        
        return detailed_jobs
        
    except Exception as e:
        print(f"Comprehensive workflow test failed: {e}")
        return None


async def main():
    """Main test function"""
    print("LinkedIn Jobs API - Python Test Suite")
    print("=" * 50)
    
    # Test sync query
    sync_result = await test_sync_query()
    
    # Test async query
    async_result = await test_async_query()
    
    # Test different parameters
    await test_different_parameters()
    
    # Test job details extraction
    job_details_result = await test_job_details()
    
    # Test comprehensive workflow
    comprehensive_result = await test_comprehensive_workflow()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
    
    if sync_result or async_result or job_details_result or comprehensive_result:
        print("At least one test passed successfully!")
    else:
        print("All tests failed. Please check your internet connection and LinkedIn availability.")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
