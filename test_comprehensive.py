"""
Standalone test for comprehensive LinkedIn Jobs API workflow with retry logic
This test searches for 20 jobs and extracts full details for each with retry logic
"""

import asyncio
import json
from datetime import datetime
from linkedin_jobs_api import query_async, get_job_details

async def test_comprehensive_workflow_with_retry():
    """Test comprehensive workflow: search for jobs and extract details for each with retry logic"""
    print("LinkedIn Jobs API - Comprehensive Workflow Test with Retry Logic")
    print("=" * 70)
    
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
        
        # Step 2: Extract detailed information for each job with retry logic
        print(f"\nStep 2: Extracting detailed information for {len(jobs)} jobs with retry logic...")
        detailed_jobs = []
        failed_jobs = []
        
        for i, job in enumerate(jobs, 1):
            print(f"\nProcessing job {i}/{len(jobs)}: {job.get('position', 'Unknown')} at {job.get('company', 'Unknown')}")
            
            if job.get('jobUrl'):
                try:
                    # Add a small delay between requests to be respectful
                    if i > 1:
                        await asyncio.sleep(2)
                    
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
                        failed_jobs.append(job)
                        
                except Exception as e:
                    print(f"  ❌ Error extracting details after retries: {e}")
                    failed_jobs.append(job)
            else:
                print(f"  ⚠️ No job URL available")
                failed_jobs.append(job)
        
        # Step 3: Display summary
        print(f"\n" + "=" * 70)
        print(f"Step 3: Summary of results")
        print(f"Total jobs processed: {len(jobs)}")
        print(f"Jobs with detailed information: {len(detailed_jobs)}")
        print(f"Jobs that failed: {len(failed_jobs)}")
        print(f"Success rate: {len(detailed_jobs)/len(jobs)*100:.1f}%")
        
        # Step 4: Show sample detailed results
        print(f"\nStep 4: Sample detailed results")
        for i, job in enumerate(detailed_jobs[:3], 1):  # Show first 3 detailed jobs
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
        if detailed_jobs:
            avg_description_length = sum(len(job['detailed_info']['full_description']) for job in detailed_jobs) / len(detailed_jobs)
            print(f"Average description length: {avg_description_length:.0f} characters")
            
            jobs_with_salary = [job for job in detailed_jobs if job['detailed_info']['salary_detailed']]
            print(f"Jobs with salary information: {len(jobs_with_salary)}")
            
            jobs_with_skills = [job for job in detailed_jobs if job['detailed_info']['skills']]
            print(f"Jobs with skills listed: {len(jobs_with_skills)}")
            
            # Show companies
            companies = list(set(job['company'] for job in detailed_jobs))
            print(f"Companies found: {', '.join(companies[:5])}{'...' if len(companies) > 5 else ''}")
        
        # Step 6: Failed jobs summary
        if failed_jobs:
            print(f"\nStep 6: Failed jobs summary")
            print(f"Failed jobs: {len(failed_jobs)}")
            for i, job in enumerate(failed_jobs[:3], 1):
                print(f"  {i}. {job.get('position', 'Unknown')} at {job.get('company', 'Unknown')}")
        
        # Step 7: Write results to JSON file
        print(f"\nStep 7: Writing results to JSON file...")
        
        # Prepare the complete results data
        results_data = {
            "test_info": {
                "test_name": "Comprehensive LinkedIn Jobs API Workflow Test",
                "timestamp": datetime.now().isoformat(),
                "search_params": search_params,
                "total_jobs_found": len(jobs),
                "jobs_with_details": len(detailed_jobs),
                "failed_jobs": len(failed_jobs),
                "success_rate": f"{len(detailed_jobs)/len(jobs)*100:.1f}%" if jobs else "0%"
            },
            "detailed_jobs": detailed_jobs,
            "failed_jobs": failed_jobs,
            "statistics": {
                "average_description_length": sum(len(job['detailed_info']['full_description']) for job in detailed_jobs) / len(detailed_jobs) if detailed_jobs else 0,
                "jobs_with_salary": len([job for job in detailed_jobs if job['detailed_info']['salary_detailed']]),
                "jobs_with_skills": len([job for job in detailed_jobs if job['detailed_info']['skills']]),
                "unique_companies": len(set(job['company'] for job in detailed_jobs))
            }
        }
        
        # Write to JSON file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_jobs_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to: {filename}")
        print(f"Total jobs processed: {len(jobs)}")
        print(f"Jobs with detailed information: {len(detailed_jobs)}")
        print(f"Jobs that failed: {len(failed_jobs)}")
        print(f"Success rate: {len(detailed_jobs)/len(jobs)*100:.1f}%")
        print(f"\n" + "=" * 70)
        print("Comprehensive workflow test completed!")
        
        return detailed_jobs
        
    except Exception as e:
        print(f"Comprehensive workflow test failed: {e}")
        return None


async def main():
    """Main test function"""
    result = await test_comprehensive_workflow_with_retry()
    
    if result:
        print(f"\n🎉 Test completed successfully! Extracted details for {len(result)} jobs.")
        print(f"📄 Results have been saved to a JSON file with timestamp.")
    else:
        print(f"\n❌ Test failed or no results obtained.")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())

