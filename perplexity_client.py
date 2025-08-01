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
                    "model": "sonar-pro",
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
                # Remove citation markers like [1], [2], etc. and any trailing brackets
                import re
                description = re.sub(r'\[\d+\]|\[\d*$', '', description).strip()
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
        prompt = f"What is {company_name}'s expected revenue growth rate for 2025, 2026, and 2027? Return ONLY in this exact format: '2025: X%, 2026: Y%, 2027: Z%' where X, Y, Z are the growth percentages. No other text."
        
        try:
            logger.debug(f"Requesting growth rate for {company_name}")
            
            response = self.session.post(
                f"{self.BASE_URL}/chat/completions",
                json={
                    "model": "sonar-pro",
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
                # Remove citation markers like [1], [2], etc. and any trailing brackets
                import re
                growth_rate = re.sub(r'\[\d+\]|\[\d*$', '', growth_rate).strip()
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
                if description is not None:
                    successful += 1
                    if progress_callback:
                        progress_callback(company, True)
                else:
                    if progress_callback:
                        progress_callback(company, False, "No data returned")
                    
            except RequestException as e:
                results[company] = None
                error_msg = str(e)
                if progress_callback:
                    progress_callback(company, False, error_msg)
                logger.warning(f"Failed to get description for {company}: {error_msg}")
        
        logger.info(f"Successfully fetched descriptions for {successful}/{len(company_names)} companies")
        return results, successful
    
    def get_ps_ratio(self, company_name: str) -> Optional[float]:
        """Get price-to-sales ratio for the company.
        
        Args:
            company_name: Name of the company
            
        Returns:
            P/S ratio as float or None if error/unavailable
        """
        prompt = f"What is the price to sales ratio of {company_name}? Only return the value, nothing else"
        
        try:
            logger.debug(f"Requesting P/S ratio for {company_name}")
            
            response = self.session.post(
                f"{self.BASE_URL}/chat/completions",
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 20
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract P/S ratio from response
            if 'choices' in data and len(data['choices']) > 0:
                ps_text = data['choices'][0]['message']['content'].strip()
                # Remove citation markers like [1], [2], etc. and any trailing brackets
                import re
                ps_text = re.sub(r'\[\d+\]|\[\d*$', '', ps_text).strip()
                
                # Try to extract numeric value
                # Handle formats like "7.8", "7.8x", "7.8 times", etc.
                ps_match = re.search(r'(\d+\.?\d*)', ps_text)
                if ps_match:
                    ps_value = float(ps_match.group(1))
                    logger.debug(f"Got P/S ratio for {company_name}: {ps_value}")
                    return ps_value
                else:
                    logger.warning(f"Could not parse P/S ratio from '{ps_text}' for {company_name}")
                    return None
            else:
                logger.warning(f"No P/S ratio in response for {company_name}")
                return None
                
        except Timeout:
            logger.warning(f"Timeout getting P/S ratio for {company_name}")
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
            logger.error(f"Unexpected error getting P/S ratio for {company_name}: {e}")
            raise RequestException(str(e))
    
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
                if growth_rate is not None:
                    successful += 1
                    if progress_callback:
                        progress_callback(company, True, "growth")
                else:
                    if progress_callback:
                        progress_callback(company, False, "No data returned")
                    
            except RequestException as e:
                results[company] = None
                error_msg = str(e)
                if progress_callback:
                    progress_callback(company, False, error_msg)
                logger.warning(f"Failed to get growth rate for {company}: {error_msg}")
        
        logger.info(f"Successfully fetched growth rates for {successful}/{len(company_names)} companies")
        return results, successful
    
    def get_ps_ratios_batch(self, company_names: list, 
                            progress_callback: Optional[Callable] = None,
                            delay: float = 0.5) -> dict:
        """Get P/S ratios for multiple companies with rate limiting.
        
        Args:
            company_names: List of company names
            progress_callback: Optional callback for progress updates
            delay: Delay between requests in seconds
            
        Returns:
            Dictionary mapping company names to P/S ratios
        """
        results = {}
        successful = 0
        
        for i, company in enumerate(company_names):
            if i > 0:
                time.sleep(delay)  # Rate limiting
            
            try:
                ps_ratio = self.get_ps_ratio(company)
                results[company] = ps_ratio
                if ps_ratio is not None:
                    successful += 1
                if progress_callback:
                    progress_callback(company, ps_ratio is not None, "ps_ratio")
                    
            except RequestException as e:
                results[company] = None
                error_msg = str(e)
                if progress_callback:
                    progress_callback(company, False, error_msg)
                logger.warning(f"Failed to get P/S ratio for {company}: {error_msg}")
        
        logger.info(f"Successfully fetched P/S ratios for {successful}/{len(company_names)} companies")
        return results, successful
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close the session."""
        self.session.close()