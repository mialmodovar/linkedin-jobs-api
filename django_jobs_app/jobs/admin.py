from django.contrib import admin
from .models import JobQuery, JobDetail


@admin.register(JobQuery)
class JobQueryAdmin(admin.ModelAdmin):
    list_display = ['name', 'keyword', 'location', 'frequency', 'is_active', 'last_run', 'next_run']
    list_filter = ['frequency', 'is_active', 'created_at']
    search_fields = ['name', 'keyword', 'location']
    readonly_fields = ['created_at', 'updated_at', 'last_run', 'next_run']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'user', 'is_active')
        }),
        ('Search Parameters', {
            'fields': ('keyword', 'location', 'date_since_posted', 'job_type', 
                      'remote_filter', 'salary', 'experience_level', 'limit', 
                      'sort_by', 'has_verification', 'under_10_applicants')
        }),
        ('Scheduling', {
            'fields': ('frequency', 'custom_schedule')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_run', 'next_run'),
            'classes': ('collapse',)
        }),
    )


@admin.register(JobDetail)
class JobDetailAdmin(admin.ModelAdmin):
    list_display = ['position', 'company', 'location', 'details_scraped', 'scraped_at']
    list_filter = ['details_scraped', 'scraped_at', 'job_query']
    search_fields = ['position', 'company', 'location']
    readonly_fields = ['scraped_at', 'details_scraped_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('job_query', 'position', 'company', 'location', 'job_url')
        }),
        ('Job Details', {
            'fields': ('job_title', 'company_name', 'posted_date', 'applicant_count', 
                      'employment_type', 'seniority_level', 'job_function', 'industries')
        }),
        ('Additional Info', {
            'fields': ('salary', 'job_description', 'benefits', 'skills', 
                      'company_logo', 'company_size')
        }),
        ('Metadata', {
            'fields': ('scraped_at', 'details_scraped', 'details_scraped_at'),
            'classes': ('collapse',)
        }),
    )
