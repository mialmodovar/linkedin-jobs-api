import requests
import logging
from typing import Dict, List, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class LinkedInJobsAPIClient:
    """Client to interact with the LinkedIn Jobs API service"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.LINKEDIN_JOBS_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def search_jobs(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for jobs using the LinkedIn Jobs API
        
        Args:
            search_params: Dictionary containing search parameters
            
        Returns:
            Dictionary containing job search results
        """
        try:
            url = f"{self.base_url}/jobs/search"
            
            # Log original parameters
            print(f"\n🔍 DJANGO API CLIENT REQUEST:")
            print(f"   Original search_params: {search_params}")
            print(f"   date_since_posted: '{search_params.get('date_since_posted')}'")
            
            # Remove None values and empty strings
            clean_params = {k: v for k, v in search_params.items() 
                          if v is not None and v != ''}
            
            print(f"   Cleaned params: {clean_params}")
            print(f"   date_since_posted after cleaning: '{clean_params.get('date_since_posted')}'")
            
            response = self.session.post(url, json=clean_params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching jobs: {e}")
            return {
                'error': f"Failed to search jobs: {str(e)}",
                'jobs': [],
                'total_count': 0
            }
        except Exception as e:
            logger.error(f"Unexpected error searching jobs: {e}")
            return {
                'error': f"Unexpected error: {str(e)}",
                'jobs': [],
                'total_count': 0
            }
    
    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific job
        
        Args:
            job_url: LinkedIn job URL
            
        Returns:
            Dictionary containing detailed job information
        """
        try:
            url = f"{self.base_url}/jobs/details"
            
            payload = {'job_url': job_url}
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting job details for {job_url}: {e}")
            return {
                'error': f"Failed to get job details: {str(e)}",
                'job_details': {}
            }
        except Exception as e:
            logger.error(f"Unexpected error getting job details for {job_url}: {e}")
            return {
                'error': f"Unexpected error: {str(e)}",
                'job_details': {}
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the LinkedIn Jobs API service is healthy
        
        Returns:
            Dictionary containing health status
        """
        try:
            url = f"{self.base_url}/health"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error in health check: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def clear_cache(self) -> Dict[str, Any]:
        """
        Clear the job search cache
        
        Returns:
            Dictionary containing cache clear result
        """
        try:
            url = f"{self.base_url}/cache"
            response = self.session.delete(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error clearing cache: {e}")
            return {
                'error': f"Failed to clear cache: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error clearing cache: {e}")
            return {
                'error': f"Unexpected error: {str(e)}"
            }


# Global client instance
api_client = LinkedInJobsAPIClient()
