from django.core.management.base import BaseCommand
from jobs.models import JobDetail
import re


class Command(BaseCommand):
    help = 'Extract and populate LinkedIn job IDs for existing jobs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def extract_linkedin_job_id(self, job_url):
        """
        Extract the LinkedIn job ID from a job URL.
        
        Example URL: https://www.linkedin.com/jobs/view/backend-software-engineer-at-login-works-4319344438
        Returns: 4319344438
        
        The job ID is the numeric sequence at the end of the URL path.
        """
        if not job_url:
            return None
        
        # Regex pattern to match the job ID at the end of the job title
        # Matches: -{digits} followed by ? or / or end of string
        pattern = r'-(\d+)(?:\?|/|$)'
        match = re.search(pattern, job_url)
        
        if match:
            return match.group(1)
        
        return None

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all jobs without linkedin_job_id
        jobs = JobDetail.objects.filter(linkedin_job_id__isnull=True)
        total = jobs.count()
        
        self.stdout.write(f"Found {total} jobs without LinkedIn job ID")
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('All jobs already have LinkedIn job IDs'))
            return
        
        updated_count = 0
        error_count = 0
        
        for job in jobs:
            linkedin_job_id = self.extract_linkedin_job_id(job.job_url)
            
            if linkedin_job_id:
                if dry_run:
                    self.stdout.write(
                        f"Would update job {job.id}: {job.position[:50]}... with ID: {linkedin_job_id}"
                    )
                else:
                    try:
                        # Check if this ID already exists for another job
                        existing_job = JobDetail.objects.filter(linkedin_job_id=linkedin_job_id).first()
                        if existing_job and existing_job.id != job.id:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"⚠ Skipping job {job.id} - ID {linkedin_job_id} already assigned to job {existing_job.id}"
                                )
                            )
                            error_count += 1
                        else:
                            job.linkedin_job_id = linkedin_job_id
                            job.save()
                            self.stdout.write(
                                f"✓ Updated job {job.id} ({job.position[:50]}...): {linkedin_job_id}"
                            )
                            updated_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"✗ Error updating job {job.id}: {e}")
                        )
                        error_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠ Could not extract ID from URL for job {job.id}: {job.job_url[:80]}...")
                )
                error_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nDRY RUN: Would update {updated_count} jobs, {error_count} errors'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Successfully updated {updated_count} jobs'
                )
            )
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(f'✗ {error_count} errors encountered')
                )
