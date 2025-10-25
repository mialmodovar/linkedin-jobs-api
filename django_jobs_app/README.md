# LinkedIn Jobs Tracker - Django App

A Django application with Celery integration that consumes the LinkedIn Jobs API service to automatically search for jobs and fetch detailed information.

## Features

- **Scheduled Job Searches**: Create queries with custom search parameters and set them to run automatically (daily, weekly, monthly, or custom schedule)
- **Automatic Detail Fetching**: For each job found, the system automatically fetches detailed information using the LinkedIn Jobs API
- **Web Interface**: User-friendly web interface to manage queries and view job results
- **Celery Integration**: Background task processing for job searches and detail fetching
- **Database Storage**: All jobs and queries are stored in the database for easy management

## Prerequisites

1. **LinkedIn Jobs API Service**: Make sure your FastAPI service is running on `http://localhost:8001`
2. **Redis**: Required for Celery message broker
3. **Python 3.8+**

## Installation

1. **Clone or navigate to the django_jobs_app directory**:
   ```bash
   cd django_jobs_app
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**:
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional, for admin access)**:
   ```bash
   python manage.py createsuperuser
   ```

## Configuration

1. **Update settings** (if needed):
   - Edit `django_jobs_app/settings.py`
   - Update `LINKEDIN_JOBS_API_URL` if your FastAPI service runs on a different URL (default: http://localhost:8001)
   - Update `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` if Redis runs on different settings

2. **Start Redis** (if not already running):
   ```bash
   redis-server
   ```

## Running the Application

### 1. Start the Django Development Server
```bash
python manage.py runserver
```

### 2. Start Celery Worker (in a new terminal)
```bash
celery -A django_jobs_app worker --loglevel=info
```

### 3. Start Celery Beat (in another terminal)
```bash
celery -A django_jobs_app beat --loglevel=info
```

### 4. Start Celery Flower (optional, for monitoring)
```bash
celery -A django_jobs_app flower
```

## Usage

1. **Access the application**: Open `http://localhost:8000` in your browser

2. **Create a job query**:
   - Click "Create New Query"
   - Fill in search parameters (keyword, location, job type, etc.)
   - Set the frequency (daily, weekly, monthly, or custom)
   - Save the query

3. **Monitor jobs**:
   - View all queries on the "Queries" page
   - See job results on the "Jobs" page
   - Click on individual jobs to see detailed information

4. **Manual operations**:
   - Run queries immediately using the "Run Query Now" button
   - Fetch job details manually using the "Fetch Details" button

## API Endpoints

The application provides the following endpoints:

- `/` - Home dashboard
- `/queries/` - List all queries
- `/queries/create/` - Create new query
- `/queries/<id>/` - View query details
- `/queries/<id>/edit/` - Edit query
- `/queries/<id>/delete/` - Delete query
- `/queries/<id>/toggle/` - Toggle query active status
- `/queries/<id>/run/` - Run query immediately
- `/jobs/` - List all jobs
- `/jobs/<id>/` - View job details
- `/jobs/<id>/fetch-details/` - Fetch job details immediately

## Celery Tasks

The application uses several Celery tasks:

- `run_job_query(query_id)` - Runs a specific job query
- `fetch_job_details(job_id)` - Fetches detailed information for a job
- `run_scheduled_queries()` - Runs all queries that are due (every 15 minutes)
- `fetch_pending_job_details()` - Fetches details for jobs without details (every 5 minutes)
- `cleanup_old_jobs()` - Cleans up old job records (daily at 2 AM)

## Database Models

- **JobQuery**: Stores user-defined search queries with scheduling information
- **JobDetail**: Stores individual job information from search results and detailed scraping

## Default User

The application uses a default user (no authentication system implemented). The first user created will be used for all queries.

## Troubleshooting

1. **Celery tasks not running**: Make sure Redis is running and Celery worker is started
2. **API connection errors**: Verify that the LinkedIn Jobs API service is running on the correct URL
3. **Database errors**: Run `python manage.py migrate` to ensure database is up to date

## Production Deployment

For production deployment:

1. Set `DEBUG = False` in settings
2. Configure proper database (PostgreSQL recommended)
3. Use a production WSGI server (Gunicorn)
4. Set up proper Redis configuration
5. Configure Celery with proper logging and monitoring
6. Set up proper security settings

## License

This project is part of the LinkedIn Jobs API project.
