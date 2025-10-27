"""
LinkedIn Jobs API - Python Module
A Python module for scraping job listings from LinkedIn
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import aiohttp
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobCache:
    """Cache implementation for job results"""
    
    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl  # Time to live in seconds (1 hour default)
    
    def set(self, key: str, value: List[Dict[str, str]]) -> None:
        """Set a value in the cache with timestamp"""
        self.cache[key] = {
            'data': value,
            'timestamp': time.time()
        }
    
    def get(self, key: str) -> Optional[List[Dict[str, str]]]:
        """Get a value from the cache if it's still valid"""
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        if time.time() - item['timestamp'] > self.ttl:
            del self.cache[key]
            return None
        
        return item['data']
    
    def clear(self) -> None:
        """Clear expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, value in self.cache.items()
            if current_time - value['timestamp'] > self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def size(self) -> int:
        """Get the current cache size"""
        return len(self.cache)


class LinkedInJobsQuery:
    """Main query class for LinkedIn job searches"""
    
    def __init__(self, query_obj: Dict[str, Any]):
        self.host = query_obj.get('host', 'www.linkedin.com')
        self.keyword = query_obj.get('keyword', '').strip().replace(' ', '+')
        self.location = query_obj.get('location', '').strip().replace(' ', '+')
        self.date_since_posted = query_obj.get('dateSincePosted', '')
        self.job_type = query_obj.get('jobType', '')
        self.remote_filter = query_obj.get('remoteFilter', '')
        self.salary = query_obj.get('salary', '')
        self.experience_level = query_obj.get('experienceLevel', '')
        self.sort_by = query_obj.get('sortBy', '')
        self.limit = int(query_obj.get('limit', 0))
        self.page = int(query_obj.get('page', 0))
        self.has_verification = query_obj.get('has_verification', False)
        self.under_10_applicants = query_obj.get('under_10_applicants', False)
    
    def get_date_since_posted(self) -> str:
        """Convert date range to LinkedIn parameter"""
        date_range = {
            'past month': 'r2592000',
            'past week': 'r604800',
            '24hr': 'r86400',
        }
        return date_range.get(self.date_since_posted.lower(), '')
    
    def get_experience_level(self) -> str:
        """Convert experience level to LinkedIn parameter"""
        experience_range = {
            'internship': '1',
            'entry level': '2',
            'associate': '3',
            'senior': '4',
            'director': '5',
            'executive': '6',
        }
        return experience_range.get(self.experience_level.lower(), '')
    
    def get_job_type(self) -> str:
        """Convert job type to LinkedIn parameter"""
        job_type_range = {
            'full time': 'F',
            'full-time': 'F',
            'part time': 'P',
            'part-time': 'P',
            'contract': 'C',
            'temporary': 'T',
            'volunteer': 'V',
            'internship': 'I',
        }
        return job_type_range.get(self.job_type.lower(), '')
    
    def get_remote_filter(self) -> str:
        """Convert remote filter to LinkedIn parameter"""
        remote_filter_range = {
            'on-site': '1',
            'on site': '1',
            'remote': '2',
            'hybrid': '3',
        }
        return remote_filter_range.get(self.remote_filter.lower(), '')
    
    def get_salary(self) -> str:
        """Convert salary to LinkedIn parameter"""
        salary_range = {
            40000: '1',
            60000: '2',
            80000: '3',
            100000: '4',
            120000: '5',
        }
        return salary_range.get(self.salary, '')
    
    def get_has_verification(self) -> str:
        """Convert verification flag to LinkedIn parameter"""
        return 'true' if self.has_verification else 'false'
    
    def get_under_10_applicants(self) -> str:
        """Convert under 10 applicants flag to LinkedIn parameter"""
        return 'true' if self.under_10_applicants else 'false'
    
    def get_page(self) -> int:
        """Calculate page offset"""
        return self.page * 25
    
    def get_cache_key(self) -> str:
        """Generate a unique cache key based on query parameters"""
        return f"{self.url(0)}_limit:{self.limit}"
    
    def url(self, start: int) -> str:
        """Build the LinkedIn jobs API URL"""
        base_url = f"https://{self.host}/jobs-guest/jobs/api/seeMoreJobPostings/search"
        
        params = {}
        
        # Core search parameters
        if self.keyword:
            params['keywords'] = self.keyword
        if self.location:
            params['location'] = self.location
        
        # Time-based filters
        if self.get_date_since_posted():
            params['f_TPR'] = self.get_date_since_posted()
        
        
        # Job filters
        if self.get_salary():
            params['f_SB2'] = self.get_salary()
        if self.get_experience_level():
            params['f_E'] = self.get_experience_level()
        if self.get_remote_filter():
            params['f_WT'] = self.get_remote_filter()
        if self.get_job_type():
            params['f_JT'] = self.get_job_type()
        
        # Additional filters (always include these with default values)
        params['f_VJ'] = self.get_has_verification()
        params['f_EA'] = self.get_under_10_applicants()
        
        # Pagination
        params['start'] = start + self.get_page()
        
        # Sorting
        if self.sort_by == 'recent':
            params['sortBy'] = 'DD'
        elif self.sort_by == 'relevant':
            params['sortBy'] = 'R'
        
        return f"{base_url}?{urlencode(params)}"
    
    async def fetch_job_batch(self, session: aiohttp.ClientSession, start: int) -> List[Dict[str, str]]:
        """Fetch a batch of jobs from LinkedIn"""
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.linkedin.com/jobs',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        try:
            request_url = self.url(start)
            print(f"\n🔍 LINKEDIN JOB SEARCH REQUEST:")
            print(f"   URL: {request_url}")
            print(f"   Headers: {headers}")
            print(f"   Start: {start}")
            
            async with session.get(
                request_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f"\n📥 LINKEDIN JOB SEARCH RESPONSE:")
                print(f"   Status: {response.status}")
                print(f"   Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    html_content = await response.text()
                    print(f"   Content Length: {len(html_content)} characters")
                    print(f"   Content Preview: {html_content[:200]}...")
                    
                    jobs = self._parse_job_list(html_content)
                    print(f"   Parsed Jobs: {len(jobs)} jobs found")
                    if jobs:
                        print(f"   Sample Job: {jobs[0].get('position', 'N/A')} at {jobs[0].get('company', 'N/A')}")
                    
                    return jobs
                elif response.status == 429:
                    print(f"   ❌ Rate limit reached")
                    raise Exception("Rate limit reached")
                else:
                    print(f"   ❌ HTTP Error: {response.status} - {response.reason}")
                    raise Exception(f"HTTP {response.status}: {response.reason}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            logger.error(f"Error fetching job batch: {e}")
            raise
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
        return random.choice(user_agents)
    
    def _parse_job_list(self, html_content: str) -> List[Dict[str, str]]:
        """Parse HTML content to extract job information"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            job_elements = soup.find_all('li')
            
            jobs = []
            for element in job_elements:
                try:
                    job_data = self._extract_job_data(element)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.warning(f"Error parsing job element: {e}")
                    continue
            
            return jobs
        except Exception as e:
            logger.error(f"Error parsing job list: {e}")
            return []
    
    def _extract_job_data(self, element) -> Optional[Dict[str, str]]:
        """Extract job data from a single job element"""
        try:
            # Extract position
            position_elem = element.find(class_='base-search-card__title')
            position = position_elem.get_text(strip=True) if position_elem else ''
            
            # Extract company
            company_elem = element.find(class_='base-search-card__subtitle')
            company = company_elem.get_text(strip=True) if company_elem else ''
            
            # Extract location
            location_elem = element.find(class_='job-search-card__location')
            location = location_elem.get_text(strip=True) if location_elem else ''
            
            # Extract date
            date_elem = element.find('time')
            date = date_elem.get('datetime', '') if date_elem else ''
            
            # Extract salary
            salary_elem = element.find(class_='job-search-card__salary-info')
            salary = salary_elem.get_text(strip=True).replace('\n', ' ').replace('\t', ' ') if salary_elem else 'Not specified'
            
            # Extract job URL
            job_url_elem = element.find(class_='base-card__full-link')
            job_url = job_url_elem.get('href', '') if job_url_elem else ''
            
            # Extract company logo
            logo_elem = element.find(class_='artdeco-entity-image')
            company_logo = logo_elem.get('data-delayed-url', '') if logo_elem else ''
            
            # Extract ago time
            ago_elem = element.find(class_='job-search-card__listdate')
            ago_time = ago_elem.get_text(strip=True) if ago_elem else ''
            
            # Only return job if we have at least position and company
            if not position or not company:
                return None
            
            return {
                'position': position,
                'company': company,
                'location': location,
                'date': date,
                'salary': salary,
                'jobUrl': job_url,
                'companyLogo': company_logo,
                'agoTime': ago_time,
            }
        except Exception as e:
            logger.warning(f"Error extracting job data: {e}")
            return None
    
    async def get_jobs(self) -> List[Dict[str, str]]:
        """Main method to fetch jobs with caching and error handling"""
        all_jobs = []
        start = 0
        batch_size = 25
        has_more = True
        
        print(f"\n🚀 LINKEDIN JOB SEARCH STARTED:")
        print(f"   Base URL: {self.url(0)}")
        print(f"   Cache Key: {self.get_cache_key()}")
        print(f"   Limit: {self.limit}")
        
        logger.info(f"Fetching jobs from: {self.url(0)}")
        logger.info(f"Cache key: {self.get_cache_key()}")
        
        try:
            # Check cache first
            cache_key = self.get_cache_key()
            cached_jobs = cache.get(cache_key)
            if cached_jobs:
                print(f"   ✅ Using cached results ({len(cached_jobs)} jobs)")
                logger.info("Returning cached results")
                return cached_jobs
            
            async with aiohttp.ClientSession() as session:
                while has_more:
                    jobs = await self.fetch_job_batch(session, start)
                    
                    if not jobs:
                        has_more = False
                        break
                    
                    all_jobs.extend(jobs)
                    logger.info(f"Fetched {len(jobs)} jobs. Total: {len(all_jobs)}")
                    
                    if self.limit and len(all_jobs) >= self.limit:
                        all_jobs = all_jobs[:self.limit]
                        break
                    
                    start += batch_size
                    
                    # Add reasonable delay between requests
                    await asyncio.sleep(2 + random.random())
            
            # Cache results if we got any
            if all_jobs:
                cache.set(cache_key, all_jobs)
                print(f"   💾 Cached {len(all_jobs)} jobs")
            
            print(f"\n✅ LINKEDIN JOB SEARCH COMPLETED:")
            print(f"   Total Jobs Found: {len(all_jobs)}")
            print(f"   Cached: {'Yes' if all_jobs else 'No'}")
            
            return all_jobs
            
        except Exception as error:
            print(f"\n❌ LINKEDIN JOB SEARCH FAILED:")
            print(f"   Error: {error}")
            logger.error(f"Fatal error in job fetching: {error}")
            raise


# Global cache instance
cache = JobCache()


def query(query_object: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Main function to query LinkedIn jobs (synchronous)
    
    Args:
        query_object: Dictionary containing search parameters
        
    Returns:
        List of job dictionaries
    """
    query_instance = LinkedInJobsQuery(query_object)
    
    # Check if we're already in an event loop
    try:
        loop = asyncio.get_running_loop()
        # If we're in an event loop, we need to use a different approach
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, query_instance.get_jobs())
            return future.result()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        return asyncio.run(query_instance.get_jobs())


async def query_async(query_object: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Async version of the query function for use in async contexts
    
    Args:
        query_object: Dictionary containing search parameters
        
    Returns:
        List of job dictionaries
    """
    query_instance = LinkedInJobsQuery(query_object)
    return await query_instance.get_jobs()


def clear_cache() -> None:
    """Clear expired entries from the cache"""
    cache.clear()


def get_cache_size() -> int:
    """Get the current cache size"""
    return cache.size()


def get_job_details_sync(job_url: str) -> Dict[str, Any]:
    """
    Synchronous version of get_job_details
    
    Args:
        job_url: The LinkedIn job URL to scrape
        
    Returns:
        Dictionary containing detailed job information
    """
    # Check if we're already in an event loop
    try:
        loop = asyncio.get_running_loop()
        # If we're in an event loop, we need to use a different approach
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, _get_job_details_async(job_url))
            return future.result()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        return asyncio.run(_get_job_details_async(job_url))


async def _get_job_details_async(job_url: str) -> Dict[str, Any]:
    """
    Extract detailed job information from a LinkedIn job URL
    
    Args:
        job_url: The LinkedIn job URL to scrape
        
    Returns:
        Dictionary containing detailed job information
    """
    # Convert pt.linkedin.com URLs to www.linkedin.com for consistent English responses
    if 'pt.linkedin.com' in job_url:
        job_url = job_url.replace('pt.linkedin.com', 'www.linkedin.com')
        print(f"   🔄 Converted pt.linkedin.com URL to: {job_url}")
    
    headers = {
        'User-Agent': LinkedInJobsQuery({})._get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    
    try:
      
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                job_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
               
                
                if response.status == 200:
                    html_content = await response.text()
                   
                    
                    details = _parse_job_details(html_content, job_url)
                   
                    
                    return details
                elif response.status == 429:
                    
                    logger.error(f"Rate limit reached for {job_url}")
                    raise Exception("Rate limit reached")
                else:
    
                    logger.error(f"HTTP {response.status}: {response.reason} for {job_url}")
                    raise Exception(f"HTTP {response.status}: {response.reason}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        logger.error(f"Error fetching job details from {job_url}: {e}")
        raise


def _parse_job_metadata(soup) -> tuple[str, bool, str]:
    """
    Parse job metadata including posted date, reposted status, and applicant count
    from the new LinkedIn HTML structure
    
    Returns:
        tuple: (posted_date, applicant_count)
    """
    from datetime import datetime, timedelta
    import re
    
    posted_date = ''
    applicant_count = ''
    
    try:
        # Look for posted time using the correct selector
        posted_time_elem = soup.find('span', class_='posted-time-ago__text')
        if posted_time_elem:
            posted_time_text = posted_time_elem.get_text(strip=True)
            print(f"   🕒 FOUND POSTED TIME: '{posted_time_text}'")
            
        else:
            print(f"   ❌ POSTED TIME ELEMENT NOT FOUND")
        
        
        # Parse relative time patterns if we found posted time
        if posted_time_elem and posted_time_text:
            time_patterns = [
                (r'(\d+)\s+(hours?)\s+ago', 'hour'),
                (r'(\d+)\s+(days?)\s+ago', 'day'), 
                (r'(\d+)\s+(weeks?)\s+ago', 'week'),
                (r'(\d+)\s+(months?)\s+ago', 'month'),
                (r'(\d+)\s+(years?)\s+ago', 'year')
            ]
            
            for pattern, unit_type in time_patterns:
                match = re.search(pattern, posted_time_text.lower())
                if match:
                    value = int(match.group(1))
                    
                    print(f"   🕒 TIME PARSING:")
                    print(f"      Text: '{posted_time_text}'")
                    print(f"      Pattern: {pattern}")
                    print(f"      Match: {match.group(0)}")
                    print(f"      Value: {value}")
                    print(f"      Unit Type: '{unit_type}'")
                    
                    # Convert to actual date
                    now = datetime.now()
                    if unit_type == 'hour':
                        posted_date = (now - timedelta(hours=value)).strftime('%Y-%m-%d')
                    elif unit_type == 'day':
                        posted_date = (now - timedelta(days=value)).strftime('%Y-%m-%d')
                    elif unit_type == 'week':
                        posted_date = (now - timedelta(weeks=value)).strftime('%Y-%m-%d')
                    elif unit_type == 'month':
                        posted_date = (now - timedelta(days=value*30)).strftime('%Y-%m-%d')
                    elif unit_type == 'year':
                        posted_date = (now - timedelta(days=value*365)).strftime('%Y-%m-%d')
                    
                    print(f"      Calculated Date: {posted_date}")
                    break
        
        # Look for applicant count using the correct selector
        applicant_elem = soup.find('figcaption', class_='num-applicants__caption')
        if applicant_elem:
            applicant_text = applicant_elem.get_text(strip=True)
            print(f"   👥 FOUND APPLICANT COUNT: '{applicant_text}'")
            
            # Parse applicant count patterns
            applicant_patterns = [
                (r'(\d+)\s+people?\s+clicked?\s+apply', 'people_clicked'),
                (r'(\d+)\s+applicants?', 'applicants'),
                (r'be\s+among\s+the\s+first\s+(\d+)', 'first_applicants'),
                (r'(\d+)\+?\s+applicants?', 'applicants_plus')
            ]
            
            for pattern, pattern_type in applicant_patterns:
                match = re.search(pattern, applicant_text.lower())
                if match:
                    count = match.group(1)
                    
                    print(f"   👥 APPLICANT COUNT PARSING:")
                    print(f"      Text: '{applicant_text}'")
                    print(f"      Pattern: {pattern}")
                    print(f"      Pattern Type: {pattern_type}")
                    print(f"      Match: {match.group(0)}")
                    print(f"      Count: '{count}'")
                    
                    if count.isdigit():
                        applicant_count = f"{count} applicants"
                    else:
                        applicant_count = applicant_text
                    
                    print(f"      Final Applicant Count: '{applicant_count}'")
                    break
            
            # Handle "100+ applicants" case
            if '100+' in applicant_text.lower() or 'over 100' in applicant_text.lower():
                print(f"   👥 APPLICANT COUNT PARSING (100+):")
                print(f"      Text: '{applicant_text}'")
                print(f"      Found '100+' or 'over 100' - setting to 100+ applicants")
                applicant_count = "100+ applicants"
        
        # If we didn't find the specific elements, use fallback methods
        if not posted_date or not applicant_count:
            print(f"   📋 Using fallback methods for missing data")
        
        # Fallback: try to find time element
        if not posted_date:
            date_elem = soup.find('time')
            if date_elem:
                posted_date = date_elem.get('datetime', '')
                print(f"   📅 Found posted date via <time> element: '{posted_date}'")
        
        # Fallback: try to find applicant count in other elements
        if not applicant_count:
            applicants_elem = soup.find('figcaption', class_='num-applicants__caption')
            if applicants_elem:
                applicant_count = applicants_elem.get_text(strip=True)
                print(f"   👥 Found applicant count via <figcaption>: '{applicant_count}'")
            
            # Try other selectors for applicant count
            if not applicant_count:
                # Look for any text containing "applicant" or "apply"
                all_text = soup.get_text()
                import re
                applicant_matches = re.findall(r'(\d+)\s*(?:people?\s*clicked?\s*apply|applicants?|be\s+among\s+the\s+first\s+\d+)', all_text.lower())
                if applicant_matches:
                    applicant_count = f"{applicant_matches[0]} applicants"
                   
        
        
        
    except Exception as e:
        logger.warning(f"Error parsing job metadata: {e}")
    
    return posted_date, applicant_count


def _parse_job_details(html_content: str, job_url: str) -> Dict[str, Any]:
    """Parse HTML content to extract detailed job information"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract job title
        title_elem = soup.find('h1', class_='top-card-layout__title')
        job_title = title_elem.get_text(strip=True) if title_elem else ''
        
        # Extract company name
        company_elem = soup.find('a', class_='topcard__org-name-link')
        if not company_elem:
            company_elem = soup.find('span', class_='topcard__flavor--black-link')
        company_name = company_elem.get_text(strip=True) if company_elem else ''
        
        # Extract location
        location_elem = soup.find('span', class_='topcard__flavor--bullet')
        location = location_elem.get_text(strip=True) if location_elem else ''
        
        # Extract posted date and applicant count from new structure
        posted_date, applicant_count = _parse_job_metadata(soup)
        print(posted_date)
        # Extract job description
        description_elem = soup.find('div', class_='show-more-less-html__markup')
        if not description_elem:
            description_elem = soup.find('div', class_='description__text')
        job_description = description_elem.get_text(strip=True) if description_elem else ''
        
        # Extract salary information
        salary_elem = soup.find('span', class_='salary')
        if not salary_elem:
            # Try alternative selectors for salary
            salary_elem = soup.find('div', string=lambda text: text and '$' in text)
        salary = salary_elem.get_text(strip=True) if salary_elem else ''
        
        # Extract employment type
        employment_type_elem = soup.find('span', class_='description__job-criteria-text')
        employment_type = employment_type_elem.get_text(strip=True) if employment_type_elem else ''
        
        # Extract seniority level
        seniority_elem = soup.find_all('span', class_='description__job-criteria-text')
        seniority_level = ''
        if len(seniority_elem) > 1:
            seniority_level = seniority_elem[1].get_text(strip=True)
        
        # Extract job function
        job_function = ''
        if len(seniority_elem) > 2:
            job_function = seniority_elem[2].get_text(strip=True)
        
        # Extract industries
        industries = ''
        if len(seniority_elem) > 3:
            industries = seniority_elem[3].get_text(strip=True)
        
        # Extract company logo
        logo_elem = soup.find('img', class_='topcard__org-logo')
        company_logo = logo_elem.get('src', '') if logo_elem else ''
        
        # Extract company size (if available)
        company_size_elem = soup.find('dd', class_='topcard__flavor--metadata')
        company_size = company_size_elem.get_text(strip=True) if company_size_elem else ''
        
        # Extract benefits and perks (if available)
        benefits_elem = soup.find('div', class_='benefits')
        benefits = benefits_elem.get_text(strip=True) if benefits_elem else ''
        
        # Extract skills (if available)
        skills_elements = soup.find_all('span', class_='job-details-skill-pill__text')
        skills = [skill.get_text(strip=True) for skill in skills_elements] if skills_elements else []
        
        return {
            'job_title': job_title,
            'company_name': company_name,
            'location': location,
            'posted_date': posted_date,
            'applicant_count': applicant_count,
            'job_description': job_description,
            'salary': salary,
            'employment_type': employment_type,
            'seniority_level': seniority_level,
            'job_function': job_function,
            'industries': industries,
            'company_logo': company_logo,
            'company_size': company_size,
            'benefits': benefits,
            'skills': skills,
            'job_url': job_url,
            'scraped_at': time.time()
        }
        
    except Exception as e:
        logger.error(f"Error parsing job details: {e}")
        return {
            'error': f"Failed to parse job details: {str(e)}",
            'job_url': job_url,
            'scraped_at': time.time()
        }


# Convenience async wrapper
async def get_job_details(job_url: str) -> Dict[str, Any]:
    """Async wrapper for get_job_details"""
    return await _get_job_details_async(job_url)


# Export classes and functions
__all__ = [
    'query',
    'query_async', 
    'get_job_details',
    'get_job_details_sync',
    'LinkedInJobsQuery',
    'JobCache',
    'clear_cache',
    'get_cache_size'
]
