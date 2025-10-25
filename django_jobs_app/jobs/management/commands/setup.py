from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from jobs.models import JobQuery
from jobs.api_client import api_client


class Command(BaseCommand):
    help = 'Set up the LinkedIn Jobs Tracker application'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Setting up LinkedIn Jobs Tracker...'))
        
        # Create default user if it doesn't exist
        default_user, created = User.objects.get_or_create(
            username='default',
            defaults={
                'email': 'default@example.com',
                'first_name': 'Default',
                'last_name': 'User',
            }
        )
        
        if created:
            default_user.set_password('password')
            default_user.save()
            self.stdout.write(self.style.SUCCESS('✅ Created default user'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Default user already exists'))
        
        # Test API connection
        self.stdout.write('🔍 Testing LinkedIn Jobs API connection...')
        health = api_client.health_check()
        
        if health.get('status') == 'healthy':
            self.stdout.write(self.style.SUCCESS('✅ LinkedIn Jobs API is healthy'))
        else:
            self.stdout.write(self.style.ERROR('❌ LinkedIn Jobs API is not responding'))
            self.stdout.write(f'   Error: {health.get("error", "Unknown error")}')
        
        # Create sample query if none exist
        if not JobQuery.objects.exists():
            sample_query = JobQuery.objects.create(
                user=default_user,
                name='Python Developer Jobs',
                keyword='Python Developer',
                location='San Francisco, CA',
                job_type='full time',
                experience_level='senior',
                limit=25,
                frequency='daily',
                is_active=True
            )
            sample_query.update_next_run()
            self.stdout.write(self.style.SUCCESS('✅ Created sample query: "Python Developer Jobs"'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 Setup complete!'))
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Start Redis: redis-server')
        self.stdout.write('2. Start LinkedIn Jobs API: python ../fastapi_example.py')
        self.stdout.write('3. Run migrations: python manage.py migrate')
        self.stdout.write('4. Start the application: python manage.py runserver')
        self.stdout.write('5. Start Celery worker: celery -A django_jobs_app worker --loglevel=info')
        self.stdout.write('6. Start Celery beat: celery -A django_jobs_app beat --loglevel=info')
        self.stdout.write('')
        self.stdout.write('Or use the startup script: ./start.sh (Linux/Mac) or start.bat (Windows)')
