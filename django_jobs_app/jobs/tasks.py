from celery import shared_task
from celery.schedules import crontab
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
import logging

from .models import JobQuery, JobDetail
from .api_client import api_client

logger = logging.getLogger(__name__)


@shared_task
def run_job_query(query_id):
    """
    Run a specific job query and save results to database
    
    Args:
        query_id: ID of the JobQuery to run
    """
    try:
        query = JobQuery.objects.get(id=query_id, is_active=True)
        logger.info(f"Running job query: {query.name}")
        
        # Get search parameters
        search_params = query.get_search_params()
        
        # Log search parameters
        print(f"\n🔍 DJANGO CELERY TASK:")
        print(f"   Query name: {query.name}")
        print(f"   Search params: {search_params}")
        print(f"   date_since_posted: '{search_params.get('date_since_posted')}'")
        
        # Search for jobs using the API
        search_result = api_client.search_jobs(search_params)
        
        if 'error' in search_result:
            logger.error(f"Error in job search for query {query.name}: {search_result['error']}")
            return f"Error: {search_result['error']}"
        
        jobs_data = search_result.get('jobs', [])
        logger.info(f"Found {len(jobs_data)} jobs for query: {query.name}")
        
        # Debug: Log first job data structure
        if jobs_data:
            logger.info(f"Sample job data structure: {jobs_data[0]}")
        
        # Save jobs to database
        saved_count = 0
        for job_data in jobs_data:
            # The FastAPI returns job_url (snake_case) not jobUrl (camelCase)
            job_url = job_data.get('job_url', '')
            if not job_url:
                logger.warning(f"Job data missing job_url: {job_data}")
                continue
            
            # Check if job already exists
            job_detail, created = JobDetail.objects.get_or_create(
                job_url=job_url,
                defaults={
                    'position': job_data.get('position', ''),
                    'company': job_data.get('company', ''),
                    'location': job_data.get('location', ''),
                    'date_posted': job_data.get('date', ''),
                    'salary': job_data.get('salary', ''),
                    'company_logo': job_data.get('company_logo', ''),
                    'ago_time': job_data.get('ago_time', ''),
                    'job_query': query,
                }
            )
            
            if created:
                saved_count += 1
                logger.info(f"Saved new job: {job_detail.position} at {job_detail.company}")
                
                # Automatically fetch detailed information for new jobs
               # fetch_job_details.delay(job_detail.id)
        
        # Update query metadata
        query.last_run = timezone.now()
        query.update_next_run()
        query.save()
        
        logger.info(f"Query {query.name} completed. Saved {saved_count} new jobs.")
        return f"Successfully saved {saved_count} new jobs for query: {query.name}"
        
    except JobQuery.DoesNotExist:
        logger.error(f"JobQuery with id {query_id} not found or inactive")
        return f"JobQuery with id {query_id} not found or inactive"
    except Exception as e:
        logger.error(f"Error running job query {query_id}: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def fetch_job_details(job_id):
    """
    Fetch detailed information for a specific job
    
    Args:
        job_id: ID of the JobDetail to fetch details for
    """
    try:
        job = JobDetail.objects.get(id=job_id)
        logger.info(f"Fetching details for job: {job.position} at {job.company}")
        
        # Get job details from API
        details_result = api_client.get_job_details(job.job_url)
        
        if 'error' in details_result:
            logger.error(f"Error fetching job details for {job.job_url}: {details_result['error']}")
            return f"Error: {details_result['error']}"
        
        job_details = details_result.get('job_details', {})
        
        # Debug: Log the job details structure
        logger.info(f"Job details structure: {job_details}")
        
        # Update job with detailed information
        job.update_with_details(job_details)
        
        logger.info(f"Successfully updated job details for: {job.position} at {job.company}")
        return f"Successfully updated job details for: {job.position} at {job.company}"
        
    except JobDetail.DoesNotExist:
        logger.error(f"JobDetail with id {job_id} not found or already scraped")
        return f"JobDetail with id {job_id} not found or already scraped"
    except Exception as e:
        logger.error(f"Error fetching job details for job {job_id}: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def run_scheduled_queries():
    """
    Run all queries that are due to be executed
    """
    try:
        now = timezone.now()
        
        # Find queries that are due to run
        due_queries = JobQuery.objects.filter(
            is_active=True,
            next_run__lte=now
        )
        
        logger.info(f"Found {due_queries.count()} queries due to run")
        
        results = []
        for query in due_queries:
            # Run the query asynchronously
            result = run_job_query.delay(query.id)
            results.append(f"Started query {query.name} (task: {result.id})")
            logger.info(f"Started query {query.name} (task: {result.id})")
        
        return f"Started {len(results)} queries: {', '.join(results)}"
        
    except Exception as e:
        logger.error(f"Error running scheduled queries: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def fetch_pending_job_details():
    """
    List jobs that need details fetched without actually fetching them
    Runs every 10 minutes to identify pending job details
    """
    try:
        # Get jobs that need details fetched
        pending_jobs = JobDetail.objects.filter(
            details_scraped=False
        ).order_by('scraped_at')[:50]  # Increased limit for listing
        
        total_pending = JobDetail.objects.filter(details_scraped=False).count()
        logger.info(f"Found {pending_jobs.count()} jobs to list (total pending: {total_pending})")
        
        if not pending_jobs.exists():
            logger.info("No pending jobs found for detail fetching")
            return "No pending jobs found"
        
        # Just list the jobs without fetching details
        job_list = []
        for job in pending_jobs:
            job_info = f"{job.position} at {job.company} (ID: {job.id})"
            job_list.append(job_info)
            logger.info(f"Pending job: {job_info}")
        
        return f"Listed {len(job_list)} pending jobs. Total pending: {total_pending}. Jobs: {', '.join(job_list[:5])}{'...' if len(job_list) > 5 else ''}"
        
    except Exception as e:
        logger.error(f"Error in fetch_pending_job_details task: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def fetch_specific_job_details(job_ids):
    """
    Fetch details for specific job IDs
    Can be called manually when needed
    """
    try:
        if isinstance(job_ids, int):
            job_ids = [job_ids]
        
        results = []
        for job_id in job_ids:
            try:
                job = JobDetail.objects.get(id=job_id)
                if job.details_scraped:
                    results.append(f"Job {job_id} ({job.position} at {job.company}) already has details")
                    continue
                
                # Fetch details asynchronously
                result = fetch_job_details.delay(job_id)
                results.append(f"Started detail fetch for {job.position} at {job.company} (task: {result.id})")
                logger.info(f"Started detail fetch for {job.position} at {job.company} (task: {result.id})")
            except JobDetail.DoesNotExist:
                results.append(f"Job {job_id} not found")
            except Exception as e:
                logger.error(f"Error starting detail fetch for job {job_id}: {str(e)}")
                results.append(f"Error starting fetch for job {job_id}: {str(e)}")
        
        return f"Started {len(results)} detail fetches: {', '.join(results)}"
        
    except Exception as e:
        logger.error(f"Error in fetch_specific_job_details task: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def cleanup_old_jobs():
    """
    Clean up old job records (optional maintenance task)
    """
    try:
        # Delete jobs older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        old_jobs = JobDetail.objects.filter(scraped_at__lt=cutoff_date)
        
        count = old_jobs.count()
        old_jobs.delete()
        
        logger.info(f"Cleaned up {count} old job records")
        return f"Cleaned up {count} old job records"
        
    except Exception as e:
        logger.error(f"Error cleaning up old jobs: {str(e)}")
        return f"Error: {str(e)}"


# # Celery Beat schedule configuration
# CELERY_BEAT_SCHEDULE = {
#     'run-scheduled-queries': {
#         'task': 'jobs.tasks.run_scheduled_queries',
#         'schedule': crontab(minute='*/15'),  # Every 15 minutes
#     },
#     'fetch-pending-job-details': {
#         'task': 'jobs.tasks.fetch_pending_job_details',
#         'schedule': crontab(minute='*/10'),  # Every 10 minutes
#     },
#     'cleanup-old-jobs': {
#         'task': 'jobs.tasks.cleanup_old_jobs',
#         'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
#     },
# }

