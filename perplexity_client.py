"""Perplexity API client for generating company descriptions."""

import logging
import time
from typing import Optional, Callable
import requests
from requests.exceptions import RequestException, Timeout


logger = logging.getLogger(__name__)


class PerplexityClient:
    """Client for interacting with Perplexity API."""
    
    BASE_URL = "https://api.perplexity.ai"
    
    def __init__(self, api_key: str):
        """Initialize the Perplexity client with an API key.
        
        Args:
            api_key: Perplexity API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def get_company_description(self, company_name: str) -> Optional[str]:
        """Get a 15-word description of what the company does.
        
        Args:
            company_name: Name of the company
            
        Returns:
            15-word description or None if error
        """
        prompt = f"Give me a 15-word description of what {company_name} does. Only return that fifteen-word description, nothing else."
        
        try:
            logger.debug(f"Requesting description for {company_name}")
            
            response = self.session.post(
                f"{self.BASE_URL}/chat/completions",
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 30
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract description from response
            if 'choices' in data and len(data['choices']) > 0:
                description = data['choices'][0]['message']['content'].strip()
                # Ensure it's roughly 15 words
                words = description.split()
                if len(words) > 20:
                    description = ' '.join(words[:15]) + '...'
                logger.debug(f"Got description for {company_name}: {len(words)} words")
                return description
            else:
                logger.warning(f"No description in response for {company_name}")
                return None
                
        except Timeout:
            logger.warning(f"Timeout getting description for {company_name}")
            raise RequestException("timeout")
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"Rate limit hit for {company_name}")
                raise RequestException("rate limit")
            else:
                logger.error(f"HTTP error for {company_name}: {e}")
                if e.response.text:
                    logger.error(f"Response body: {e.response.text}")
                raise RequestException(f"HTTP {e.response.status_code}")
                
        except Exception as e:
            logger.error(f"Unexpected error getting description for {company_name}: {e}")
            raise RequestException(str(e))
    
    def get_company_growth_rate(self, company_name: str) -> Optional[str]:
        """Get expected revenue growth rate for the company over next 2-3 years.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Growth rate percentage or None if error
        """
        prompt = f"Give me a 15 word description on how {company_name} is expected to grow revenue over the next two to three years."
        
        try:
            logger.debug(f"Requesting growth rate for {company_name}")
            
            response = self.session.post(
                f"{self.BASE_URL}/chat/completions",
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 50
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract growth rate from response
            if 'choices' in data and len(data['choices']) > 0:
                growth_rate = data['choices'][0]['message']['content'].strip()
                logger.debug(f"Got growth rate for {company_name}: {growth_rate}")
                return growth_rate
            else:
                logger.warning(f"No growth rate in response for {company_name}")
                return None
                
        except Timeout:
            logger.warning(f"Timeout getting growth rate for {company_name}")
            raise RequestException("timeout")
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"Rate limit hit for {company_name}")
                raise RequestException("rate limit")
            else:
                logger.error(f"HTTP error for {company_name}: {e}")
                if e.response.text:
                    logger.error(f"Response body: {e.response.text}")
                raise RequestException(f"HTTP {e.response.status_code}")
                
        except Exception as e:
            logger.error(f"Unexpected error getting growth rate for {company_name}: {e}")
            raise RequestException(str(e))
    
    def get_descriptions_batch(self, company_names: list, 
                             progress_callback: Optional[Callable] = None,
                             delay: float = 0.5) -> dict:
        """Get descriptions for multiple companies with rate limiting.
        
        Args:
            company_names: List of company names
            progress_callback: Optional callback for progress updates
            delay: Delay between requests in seconds
            
        Returns:
            Dictionary mapping company names to descriptions
        """
        results = {}
        successful = 0
        
        for i, company in enumerate(company_names):
            if i > 0:
                time.sleep(delay)  # Rate limiting
            
            try:
                description = self.get_company_description(company)
                results[company] = description
                successful += 1
                if progress_callback:
                    progress_callback(company, True)
                    
            except RequestException as e:
                results[company] = None
                error_msg = str(e)
                if progress_callback:
                    progress_callback(company, False, error_msg)
                logger.warning(f"Failed to get description for {company}: {error_msg}")
        
        logger.info(f"Successfully fetched descriptions for {successful}/{len(company_names)} companies")
        return results, successful
    
    def get_growth_rates_batch(self, company_names: list, 
                               progress_callback: Optional[Callable] = None,
                               delay: float = 0.5) -> dict:
        """Get growth rates for multiple companies with rate limiting.
        
        Args:
            company_names: List of company names
            progress_callback: Optional callback for progress updates
            delay: Delay between requests in seconds
            
        Returns:
            Dictionary mapping company names to growth rates
        """
        results = {}
        successful = 0
        
        for i, company in enumerate(company_names):
            if i > 0:
                time.sleep(delay)  # Rate limiting
            
            try:
                growth_rate = self.get_company_growth_rate(company)
                results[company] = growth_rate
                successful += 1
                if progress_callback:
                    progress_callback(company, True, "growth")
                    
            except RequestException as e:
                results[company] = None
                error_msg = str(e)
                if progress_callback:
                    progress_callback(company, False, error_msg)
                logger.warning(f"Failed to get growth rate for {company}: {error_msg}")
        
        logger.info(f"Successfully fetched growth rates for {successful}/{len(company_names)} companies")
        return results, successful
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close the session."""
        self.session.close()