from django.core.management.base import BaseCommand
from jobs.tasks import fetch_pending_job_details, fetch_specific_job_details


class Command(BaseCommand):
    help = 'List pending job details or fetch specific job details'

    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run the task asynchronously using Celery',
        )
        parser.add_argument(
            '--fetch',
            type=str,
            help='Fetch details for specific job IDs (comma-separated)',
        )

    def handle(self, *args, **options):
        if options['fetch']:
            # Fetch specific job details
            job_ids = [int(id.strip()) for id in options['fetch'].split(',')]
            
            if options['async']:
                result = fetch_specific_job_details.delay(job_ids)
                self.stdout.write(
                    self.style.SUCCESS(f'Fetch task started asynchronously with ID: {result.id}')
                )
            else:
                result = fetch_specific_job_details(job_ids)
                self.stdout.write(
                    self.style.SUCCESS(f'Fetch task completed: {result}')
                )
        else:
            # List pending jobs (default behavior)
            if options['async']:
                result = fetch_pending_job_details.delay()
                self.stdout.write(
                    self.style.SUCCESS(f'Listing task started asynchronously with ID: {result.id}')
                )
            else:
                result = fetch_pending_job_details()
                self.stdout.write(
                    self.style.SUCCESS(f'Listing task completed: {result}')
                )
