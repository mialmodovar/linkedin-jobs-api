from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import JobQuery, JobDetail
from .tasks import run_job_query, fetch_job_details


def index(request):
    """Home page showing overview of queries and recent jobs"""
    # Get default user (since we're not implementing user system)
    default_user = User.objects.first()
    if not default_user:
        default_user = User.objects.create_user('default', 'default@example.com', 'password')
    
    # Get recent queries
    recent_queries = JobQuery.objects.filter(user=default_user).order_by('-created_at')[:5]
    
    # Get recent jobs
    recent_jobs = JobDetail.objects.filter(job_query__user=default_user).order_by('-scraped_at')[:10]
    
    # Get statistics
    total_queries = JobQuery.objects.filter(user=default_user).count()
    active_queries = JobQuery.objects.filter(user=default_user, is_active=True).count()
    total_jobs = JobDetail.objects.filter(job_query__user=default_user).count()
    jobs_with_details = JobDetail.objects.filter(job_query__user=default_user, details_scraped=True).count()
    
    context = {
        'recent_queries': recent_queries,
        'recent_jobs': recent_jobs,
        'total_queries': total_queries,
        'active_queries': active_queries,
        'total_jobs': total_jobs,
        'jobs_with_details': jobs_with_details,
    }
    
    return render(request, 'jobs/index.html', context)


def query_list(request):
    """List all job queries"""
    # Get default user
    default_user = User.objects.first()
    if not default_user:
        default_user = User.objects.create_user('default', 'default@example.com', 'password')
    
    queries = JobQuery.objects.filter(user=default_user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(queries, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'queries': page_obj,
    }
    
    return render(request, 'jobs/query_list.html', context)


def query_detail(request, pk):
    """Show details of a specific query and its jobs"""
    query = get_object_or_404(JobQuery, pk=pk)
    
    # Get jobs for this query
    jobs = query.jobs.all().order_by('-scraped_at')
    
    # Get statistics
    total_jobs = jobs.count()
    jobs_with_details = jobs.filter(details_scraped=True).count()
    
    # Pagination
    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'jobs': page_obj,
        'total_jobs': total_jobs,
        'jobs_with_details': jobs_with_details,
    }
    
    return render(request, 'jobs/query_detail.html', context)


def query_create(request):
    """Create a new job query"""
    if request.method == 'POST':
        # Get default user
        default_user = User.objects.first()
        if not default_user:
            default_user = User.objects.create_user('default', 'default@example.com', 'password')
        
        # Create query from form data
        query = JobQuery.objects.create(
            user=default_user,
            name=request.POST.get('name'),
            keyword=request.POST.get('keyword', ''),
            location=request.POST.get('location', ''),
            date_since_posted=request.POST.get('date_since_posted', ''),
            job_type=request.POST.get('job_type', ''),
            remote_filter=request.POST.get('remote_filter', ''),
            salary=request.POST.get('salary', ''),
            experience_level=request.POST.get('experience_level', ''),
            limit=int(request.POST.get('limit', 25)),
            sort_by=request.POST.get('sort_by', ''),
            has_verification=request.POST.get('has_verification') == 'on',
            under_10_applicants=request.POST.get('under_10_applicants') == 'on',
            frequency=request.POST.get('frequency', 'daily'),
            custom_schedule=request.POST.get('custom_schedule', ''),
            is_active=request.POST.get('is_active') == 'on',
        )
        
        # Update next run time
        query.update_next_run()
        
        messages.success(request, f'Query "{query.name}" created successfully!')
        return redirect('jobs:query_detail', pk=query.pk)
    
    context = {
        'frequency_choices': JobQuery.FREQUENCY_CHOICES,
    }
    
    return render(request, 'jobs/query_form.html', context)


def query_edit(request, pk):
    """Edit an existing job query"""
    query = get_object_or_404(JobQuery, pk=pk)
    
    if request.method == 'POST':
        # Update query from form data
        query.name = request.POST.get('name')
        query.keyword = request.POST.get('keyword', '')
        query.location = request.POST.get('location', '')
        query.date_since_posted = request.POST.get('date_since_posted', '')
        query.job_type = request.POST.get('job_type', '')
        query.remote_filter = request.POST.get('remote_filter', '')
        query.salary = request.POST.get('salary', '')
        query.experience_level = request.POST.get('experience_level', '')
        query.limit = int(request.POST.get('limit', 25))
        query.sort_by = request.POST.get('sort_by', '')
        query.has_verification = request.POST.get('has_verification') == 'on'
        query.under_10_applicants = request.POST.get('under_10_applicants') == 'on'
        query.frequency = request.POST.get('frequency', 'daily')
        query.custom_schedule = request.POST.get('custom_schedule', '')
        query.is_active = request.POST.get('is_active') == 'on'
        
        query.save()
        
        # Update next run time
        query.update_next_run()
        
        messages.success(request, f'Query "{query.name}" updated successfully!')
        return redirect('jobs:query_detail', pk=query.pk)
    
    context = {
        'query': query,
        'frequency_choices': JobQuery.FREQUENCY_CHOICES,
    }
    
    return render(request, 'jobs/query_form.html', context)


def query_delete(request, pk):
    """Delete a job query"""
    query = get_object_or_404(JobQuery, pk=pk)
    
    if request.method == 'POST':
        query_name = query.name
        query.delete()
        messages.success(request, f'Query "{query_name}" deleted successfully!')
        return redirect('jobs:query_list')
    
    context = {
        'query': query,
    }
    
    return render(request, 'jobs/query_confirm_delete.html', context)


def query_toggle(request, pk):
    """Toggle active status of a query"""
    query = get_object_or_404(JobQuery, pk=pk)
    query.is_active = not query.is_active
    query.save()
    
    status = "activated" if query.is_active else "deactivated"
    messages.success(request, f'Query "{query.name}" {status}!')
    
    return redirect('jobs:query_detail', pk=query.pk)


def job_list(request):
    """List all jobs"""
    # Get default user
    default_user = User.objects.first()
    if not default_user:
        default_user = User.objects.create_user('default', 'default@example.com', 'password')
    
    jobs = JobDetail.objects.filter(job_query__user=default_user).order_by('-scraped_at')
    
    # Filter by query if specified
    query_id = request.GET.get('query')
    if query_id:
        jobs = jobs.filter(job_query_id=query_id)
    
    # Filter by details scraped status
    details_scraped = request.GET.get('details_scraped')
    if details_scraped == 'true':
        jobs = jobs.filter(details_scraped=True)
    elif details_scraped == 'false':
        jobs = jobs.filter(details_scraped=False)
    
    # Filter by posted date
    posted_date = request.GET.get('posted_date')
    if posted_date:
        if posted_date == 'today':
            from datetime import date
            today = date.today()
            jobs = jobs.filter(posted_date__icontains=str(today))
        elif posted_date == 'week':
            from datetime import date, timedelta
            week_ago = date.today() - timedelta(days=7)
            jobs = jobs.filter(posted_date__gte=str(week_ago))
        elif posted_date == 'month':
            from datetime import date, timedelta
            month_ago = date.today() - timedelta(days=30)
            jobs = jobs.filter(posted_date__gte=str(month_ago))
        elif posted_date == 'custom':
            # Handle custom date range
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            if start_date:
                jobs = jobs.filter(posted_date__gte=start_date)
            if end_date:
                jobs = jobs.filter(posted_date__lte=end_date)
    
    # Pagination
    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all queries for filter dropdown
    queries = JobQuery.objects.filter(user=default_user).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'jobs': page_obj,
        'queries': queries,
        'selected_query': query_id,
        'selected_details_scraped': details_scraped,
        'selected_posted_date': posted_date,
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
    }
    
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, pk):
    """Show details of a specific job"""
    job = get_object_or_404(JobDetail, pk=pk)
    
    # If job details haven't been fetched yet, start fetching them
    if not job.details_scraped:
        from .tasks import fetch_job_details
        task = fetch_job_details.delay(job.id)
        # Store the task ID in the session so we can check status
        request.session[f'fetch_task_{job.id}'] = task.id
    
    context = {
        'job': job,
        'fetch_task_id': request.session.get(f'fetch_task_{job.id}', None) if not job.details_scraped else None,
    }
    
    return render(request, 'jobs/job_detail.html', context)


@require_http_methods(["GET"])
def check_fetch_status(request, pk):
    """Check the status of job detail fetching"""
    job = get_object_or_404(JobDetail, pk=pk)
    
    # Check if we have a task ID in session
    task_id = request.session.get(f'fetch_task_{job.id}')
    if not task_id:
        return JsonResponse({
            'success': False,
            'message': 'No fetch task found',
            'details_scraped': job.details_scraped
        })
    
    # Check task status using Celery
    from celery.result import AsyncResult
    from django_jobs_app import celery_app
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.ready():
        if task_result.successful():
            # Task completed successfully, refresh job data
            job.refresh_from_db()
            # Clear the task ID from session
            if f'fetch_task_{job.id}' in request.session:
                del request.session[f'fetch_task_{job.id}']
            
            return JsonResponse({
                'success': True,
                'message': 'Job details fetched successfully',
                'details_scraped': job.details_scraped,
                'completed': True
            })
        else:
            # Task failed
            return JsonResponse({
                'success': False,
                'message': f'Failed to fetch job details: {task_result.result}',
                'details_scraped': job.details_scraped,
                'completed': True
            })
    else:
        # Task still running
        return JsonResponse({
            'success': True,
            'message': 'Fetching job details...',
            'details_scraped': job.details_scraped,
            'completed': False
        })


@require_http_methods(["POST"])
def run_query_now(request, pk):
    """Run a query immediately"""
    query = get_object_or_404(JobQuery, pk=pk)
    
    # Start the task
    task = run_job_query.delay(query.id)
    
    return JsonResponse({
        'success': True,
        'message': f'Query "{query.name}" started successfully!',
        'task_id': task.id
    })


@require_http_methods(["POST"])
def fetch_job_details_now(request, pk):
    """Fetch details for a job immediately"""
    job = get_object_or_404(JobDetail, pk=pk)
    
    if job.details_scraped:
        return JsonResponse({
            'success': False,
            'message': 'Job details already fetched!'
        })
    
    # Start the task
    task = fetch_job_details.delay(job.id)
    
    return JsonResponse({
        'success': True,
        'message': f'Detail fetch for "{job.position}" started successfully!',
        'task_id': task.id
    })
