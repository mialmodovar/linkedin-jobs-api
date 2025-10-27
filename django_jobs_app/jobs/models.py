from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class JobQuery(models.Model):
    """Model to store user-defined job search queries"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=200, help_text="Name for this job search query")
    keyword = models.CharField(max_length=200, blank=True, help_text="Job keyword to search for")
    location = models.CharField(max_length=200, blank=True, help_text="Location to search in")
    date_since_posted = models.CharField(max_length=50, blank=True, help_text="Date filter: 'past month', 'past week', '24hr' (LinkedIn API only supports these 3 options)")
    job_type = models.CharField(max_length=50, blank=True, help_text="Job type: full time, part time, contract, etc.")
    remote_filter = models.CharField(max_length=50, blank=True, help_text="Remote filter: on-site, remote, hybrid")
    salary = models.CharField(max_length=50, blank=True, help_text="Minimum salary: 40000, 60000, 80000, 100000, 120000")
    experience_level = models.CharField(max_length=50, blank=True, help_text="Experience level: internship, entry level, associate, etc.")
    limit = models.IntegerField(default=25, help_text="Maximum number of jobs to return")
    sort_by = models.CharField(max_length=50, blank=True, help_text="Sort by: recent, relevant")
    has_verification = models.BooleanField(default=False, help_text="Only verified companies")
    under_10_applicants = models.BooleanField(default=False, help_text="Under 10 applicants")
    
    # Scheduling
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    custom_schedule = models.CharField(max_length=100, blank=True, help_text="Custom cron expression (if frequency is custom)")
    is_active = models.BooleanField(default=True, help_text="Whether this query is active")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Default user (since we're not implementing user system)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    
    class Meta:
        verbose_name = "Job Query"
        verbose_name_plural = "Job Queries"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.frequency})"
    
    def get_search_params(self):
        """Return search parameters as a dictionary for the API"""
        return {
            'keyword': self.keyword,
            'location': self.location,
            'date_since_posted': self.date_since_posted,  # Fixed: use snake_case for FastAPI
            'job_type': self.job_type,  # Fixed: use snake_case for FastAPI
            'remote_filter': self.remote_filter,  # Fixed: use snake_case for FastAPI
            'salary': self.salary,
            'experience_level': self.experience_level,  # Fixed: use snake_case for FastAPI
            'limit': self.limit,
            'page': 0,
            'sort_by': self.sort_by,  # Fixed: use snake_case for FastAPI
            'has_verification': self.has_verification,
            'under_10_applicants': self.under_10_applicants,
        }
    
    def update_next_run(self):
        """Update the next_run field based on frequency"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        
        if self.frequency == 'daily':
            self.next_run = now + timedelta(days=1)
        elif self.frequency == 'weekly':
            self.next_run = now + timedelta(weeks=1)
        elif self.frequency == 'monthly':
            self.next_run = now + timedelta(days=30)
        # For custom frequency, we'll handle it in the Celery task
        
        self.save()


class JobDetail(models.Model):
    """Model to store detailed job information"""
    
    # Basic job info from search results
    position = models.CharField(max_length=500)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    date_posted = models.CharField(max_length=100, blank=True)
    salary = models.CharField(max_length=200, blank=True)
    job_url = models.URLField()
    linkedin_job_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    company_logo = models.URLField(blank=True)
    ago_time = models.CharField(max_length=100, blank=True)
    
    # Detailed info from job details API
    job_title = models.CharField(max_length=500, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    posted_date = models.CharField(max_length=100, blank=True)
    applicant_count = models.CharField(max_length=100, blank=True)
    job_description = models.TextField(blank=True)
    employment_type = models.CharField(max_length=100, blank=True)
    seniority_level = models.CharField(max_length=100, blank=True)
    job_function = models.CharField(max_length=200, blank=True)
    industries = models.CharField(max_length=200, blank=True)
    company_size = models.CharField(max_length=100, blank=True)
    benefits = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    
    # Metadata
    scraped_at = models.DateTimeField(auto_now_add=True)
    details_scraped_at = models.DateTimeField(null=True, blank=True)
    details_scraped = models.BooleanField(default=False)
    
    # Related query
    job_query = models.ForeignKey(JobQuery, on_delete=models.CASCADE, related_name='jobs')
    
    class Meta:
        verbose_name = "Job Detail"
        verbose_name_plural = "Job Details"
        ordering = ['-scraped_at']
    
    def __str__(self):
        return f"{self.position} at {self.company}"
    
    def get_skills_display(self):
        """Return skills as a comma-separated string"""
        if isinstance(self.skills, list):
            return ', '.join(self.skills)
        return str(self.skills) if self.skills else ''
    
    def update_with_details(self, details_data):
        """Update job with detailed information from the API"""
        self.job_title = details_data.get('job_title', '')
        self.company_name = details_data.get('company_name', '')
        self.posted_date = details_data.get('posted_date', '')
        self.applicant_count = details_data.get('applicant_count', '')
        self.job_description = details_data.get('job_description', '')
        self.employment_type = details_data.get('employment_type', '')
        self.seniority_level = details_data.get('seniority_level', '')
        self.job_function = details_data.get('job_function', '')
        self.industries = details_data.get('industries', '')
        self.company_size = details_data.get('company_size', '')
        self.benefits = details_data.get('benefits', '')
        self.skills = details_data.get('skills', [])
        self.details_scraped = True
        self.details_scraped_at = timezone.now()
        self.save()
