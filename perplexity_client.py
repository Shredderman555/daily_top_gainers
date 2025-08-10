"""Perplexity API client for generating company descriptions."""

import logging
import time
from typing import Optional, Callable
import requests
from requests.exceptions import RequestException, Timeout


logger = logging.getLogger(__name__)


def clean_markdown(text: str) -> str:
    """Remove markdown formatting from text.
    
    Args:
        text: Text potentially containing markdown
        
    Returns:
        Cleaned text without markdown formatting
    """
    if not text:
        return text
    
    import re
    # Remove bold markdown (**text**)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # Remove bold markdown (__text__)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    # Remove italic markdown (*text*) - single asterisks
    text = re.sub(r'(?<=[^*])\*([^*]+)\*(?=[^*])', r'\1', text)
    # Handle italic at start of string
    text = re.sub(r'^\*([^*]+)\*', r'\1', text)
    # Remove italic markdown (_text_) - single underscores
    text = re.sub(r'(?<=[^_])_([^_]+)_(?=[^_])', r'\1', text)
    # Handle italic at start of string
    text = re.sub(r'^_([^_]+)_', r'\1', text)
    
    return text.strip()


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
        """Get company description with competitive advantage and market growth analysis.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Structured response with description, competitive advantage score/reasoning,
            and market growth score/reasoning, or None if error
        """
        prompt = f"Do three things. One, Give me a description of what {company_name} does in 50 words or less. Two, give a score out of 10 as to how strong this companies competitive advantage is based on how effectively it's competitors can compete with this company and explain your reasoning in 50 words or less. Near monopolies should receive the highest score. Three, give me a score out of 10 based on how fast this company's market is going to grow over the next 5 years and explain your thinking. 50 words or less. Only provide these three things and nothing else."
        
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
                    "max_tokens": 200
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
                # Clean markdown formatting
                description = clean_markdown(description)
                logger.debug(f"Got full response for {company_name}")
                # Return the full structured response
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
        prompt = f"What is the price to sales ratio of {company_name}? Critical: Your response format should be the value, no other words"
        
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
    
    def is_technical_company(self, company_name: str) -> Optional[bool]:
        """Determine if a company requires significant technical/engineering expertise.
        
        Args:
            company_name: Name of the company
            
        Returns:
            True if technical/engineering-heavy, False if not, None if error
        """
        prompt = f"Does {company_name} require significant technical or engineering expertise in its core operations (including software, hardware, aerospace, manufacturing, industrial, scientific, or R&D)? Answer only 'yes' or 'no'."
        
        try:
            logger.debug(f"Checking if {company_name} is technical/engineering-heavy")
            
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
                    "max_tokens": 10
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract yes/no from response
            if 'choices' in data and len(data['choices']) > 0:
                answer = data['choices'][0]['message']['content'].strip().lower()
                # Remove citation markers
                import re
                answer = re.sub(r'\[\d+\]|\[\d*$', '', answer).strip()
                
                if 'yes' in answer:
                    logger.debug(f"{company_name} is technical/engineering-heavy")
                    return True
                elif 'no' in answer:
                    logger.debug(f"{company_name} is not technical/engineering-heavy")
                    return False
                else:
                    logger.warning(f"Unclear answer for {company_name}: {answer}")
                    return None
            else:
                logger.warning(f"No answer in response for {company_name}")
                return None
                
        except Timeout:
            logger.warning(f"Timeout checking technical nature for {company_name}")
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
            logger.error(f"Unexpected error checking technical nature for {company_name}: {e}")
            raise RequestException(str(e))
    
    def get_technical_companies_batch(self, company_names: list, 
                                      progress_callback: Optional[Callable] = None,
                                      delay: float = 0.5) -> dict:
        """Check if multiple companies are technical/engineering-heavy.
        
        Args:
            company_names: List of company names
            progress_callback: Optional callback for progress updates
            delay: Delay between requests in seconds
            
        Returns:
            Dictionary mapping company names to boolean values
        """
        results = {}
        successful = 0
        
        for i, company in enumerate(company_names):
            if i > 0:
                time.sleep(delay)  # Rate limiting
            
            try:
                is_technical = self.is_technical_company(company)
                results[company] = is_technical
                if is_technical is not None:
                    successful += 1
                    if progress_callback:
                        progress_callback(company, True, "technical_check")
                else:
                    if progress_callback:
                        progress_callback(company, False, "Unclear response")
                    
            except RequestException as e:
                results[company] = None
                error_msg = str(e)
                if progress_callback:
                    progress_callback(company, False, error_msg)
                logger.warning(f"Failed to check technical nature for {company}: {error_msg}")
        
        logger.info(f"Successfully checked technical nature for {successful}/{len(company_names)} companies")
        return results, successful
    
    def get_earnings_guidance(self, company_name: str) -> Optional[str]:
        """Get earnings guidance update for the company.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Summary of guidance changes or None if error
        """
        prompt = f"Critical, answer exactly in this format: {company_name} last reported earnings on [date] and [commentary on how top and bottom line guidance changed]"
        
        try:
            logger.debug(f"Requesting earnings guidance for {company_name}")
            
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
                    "max_tokens": 300
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract guidance info from response
            if 'choices' in data and len(data['choices']) > 0:
                guidance = data['choices'][0]['message']['content'].strip()
                # Remove citation markers like [1], [2], etc. and any trailing brackets
                import re
                guidance = re.sub(r'\[\d+\]|\[\d*$', '', guidance).strip()
                # Clean markdown formatting
                guidance = clean_markdown(guidance)
                logger.debug(f"Got earnings guidance for {company_name}")
                return guidance
            else:
                logger.warning(f"No earnings guidance in response for {company_name}")
                return None
                
        except Timeout:
            logger.warning(f"Timeout getting earnings guidance for {company_name}")
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
            logger.error(f"Unexpected error getting earnings guidance for {company_name}: {e}")
            raise RequestException(str(e))
    
    def get_earnings_guidance_batch(self, company_names: list, 
                                    progress_callback: Optional[Callable] = None,
                                    delay: float = 0.5) -> dict:
        """Get earnings guidance for multiple companies with rate limiting.
        
        Args:
            company_names: List of company names
            progress_callback: Optional callback for progress updates
            delay: Delay between requests in seconds
            
        Returns:
            Dictionary mapping company names to earnings guidance
        """
        results = {}
        successful = 0
        
        for i, company in enumerate(company_names):
            if i > 0:
                time.sleep(delay)  # Rate limiting
            
            try:
                guidance = self.get_earnings_guidance(company)
                results[company] = guidance
                if guidance is not None:
                    successful += 1
                    if progress_callback:
                        progress_callback(company, True, "earnings_guidance")
                else:
                    if progress_callback:
                        progress_callback(company, False, "No data returned")
                    
            except RequestException as e:
                results[company] = None
                error_msg = str(e)
                if progress_callback:
                    progress_callback(company, False, error_msg)
                logger.warning(f"Failed to get earnings guidance for {company}: {error_msg}")
        
        logger.info(f"Successfully fetched earnings guidance for {successful}/{len(company_names)} companies")
        return results, successful
    
    def get_analyst_price_targets(self, company_name: str) -> Optional[str]:
        """Get analyst price target changes for the company.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Summary of analyst price target changes or None if error
        """
        prompt = f"Tell me about {company_name} analyst price target changes over the last week and the last 6 months. 50 words or less."
        
        try:
            logger.debug(f"Requesting analyst price targets for {company_name}")
            
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
                    "max_tokens": 300
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract price target info from response
            if 'choices' in data and len(data['choices']) > 0:
                price_targets = data['choices'][0]['message']['content'].strip()
                # Remove citation markers like [1], [2], etc. and any trailing brackets
                import re
                price_targets = re.sub(r'\[\d+\]|\[\d*$', '', price_targets).strip()
                # Clean markdown formatting
                price_targets = clean_markdown(price_targets)
                logger.debug(f"Got analyst price targets for {company_name}")
                return price_targets
            else:
                logger.warning(f"No analyst price targets in response for {company_name}")
                return None
                
        except Timeout:
            logger.warning(f"Timeout getting analyst price targets for {company_name}")
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
            logger.error(f"Unexpected error getting analyst price targets for {company_name}: {e}")
            raise RequestException(str(e))
    
    def get_analyst_price_targets_batch(self, company_names: list, 
                                        progress_callback: Optional[Callable] = None,
                                        delay: float = 0.5) -> dict:
        """Get analyst price targets for multiple companies with rate limiting.
        
        Args:
            company_names: List of company names
            progress_callback: Optional callback for progress updates
            delay: Delay between requests in seconds
            
        Returns:
            Dictionary mapping company names to analyst price targets
        """
        results = {}
        successful = 0
        
        for i, company in enumerate(company_names):
            if i > 0:
                time.sleep(delay)  # Rate limiting
            
            try:
                price_targets = self.get_analyst_price_targets(company)
                results[company] = price_targets
                if price_targets is not None:
                    successful += 1
                    if progress_callback:
                        progress_callback(company, True, "analyst_price_targets")
                else:
                    if progress_callback:
                        progress_callback(company, False, "No data returned")
                    
            except RequestException as e:
                results[company] = None
                error_msg = str(e)
                if progress_callback:
                    progress_callback(company, False, error_msg)
                logger.warning(f"Failed to get analyst price targets for {company}: {error_msg}")
        
        logger.info(f"Successfully fetched analyst price targets for {successful}/{len(company_names)} companies")
        return results, successful
    
    def get_revenue_projection_2030(self, company_name: str) -> Optional[str]:
        """Get revenue growth projection for 2030.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Revenue projection analysis or None if error
        """
        prompt = f"Think really hard and tell me how fast you think {company_name} will still be growing revenue in 2030? Take into account competitive advantages, how fast the industry in growing, the potential for new product/service lines, stickiness of existing customers, etc. Structure your response as follows: [percentage revenue growth rate] [reasoning]. Critical: keep your response to 100 words or less."
        
        try:
            logger.debug(f"Requesting revenue projection 2030 for {company_name}")
            
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
                    "max_tokens": 200
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract projection from response
            if 'choices' in data and len(data['choices']) > 0:
                projection = data['choices'][0]['message']['content'].strip()
                # Remove citation markers like [1], [2], etc. and any trailing brackets
                import re
                projection = re.sub(r'\[\d+\]|\[\d*$', '', projection).strip()
                # Clean markdown formatting
                projection = clean_markdown(projection)
                logger.debug(f"Got revenue projection 2030 for {company_name}")
                return projection
            else:
                logger.warning(f"No revenue projection 2030 in response for {company_name}")
                return None
                
        except Timeout:
            logger.warning(f"Timeout getting revenue projection 2030 for {company_name}")
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
            logger.error(f"Unexpected error getting revenue projection 2030 for {company_name}: {e}")
            raise RequestException(str(e))
    
    def get_revenue_projection_2030_batch(self, company_names: list, 
                                          progress_callback: Optional[Callable] = None,
                                          delay: float = 0.5) -> dict:
        """Get revenue projections for 2030 for multiple companies with rate limiting.
        
        Args:
            company_names: List of company names
            progress_callback: Optional callback for progress updates
            delay: Delay between requests in seconds
            
        Returns:
            Dictionary mapping company names to revenue projections
        """
        results = {}
        successful = 0
        
        for i, company in enumerate(company_names):
            if i > 0:
                time.sleep(delay)  # Rate limiting
            
            try:
                projection = self.get_revenue_projection_2030(company)
                results[company] = projection
                if projection is not None:
                    successful += 1
                    if progress_callback:
                        progress_callback(company, True, "revenue_projection_2030")
                else:
                    if progress_callback:
                        progress_callback(company, False, "No data returned")
                    
            except RequestException as e:
                results[company] = None
                error_msg = str(e)
                if progress_callback:
                    progress_callback(company, False, error_msg)
                logger.warning(f"Failed to get revenue projection 2030 for {company}: {error_msg}")
        
        logger.info(f"Successfully fetched revenue projections 2030 for {successful}/{len(company_names)} companies")
        return results, successful
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def get_deep_research(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Generate deep research using sonar-deep-research model.
        
        Args:
            prompt: Research prompt
            max_retries: Maximum number of retry attempts
            
        Returns:
            Deep research report or None if error
        """
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    retry_delay = 30 * (attempt + 1)  # 60, 90, 120 seconds
                    logger.info(f"Retrying deep research after {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                
                logger.debug(f"Requesting deep research (attempt {attempt + 1}/{max_retries})")
                
                response = self.session.post(
                    f"{self.BASE_URL}/chat/completions",
                    json={
                        "model": "sonar-deep-research",
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 4000  # Deep research needs more tokens
                    },
                    timeout=600  # Deep research can take up to 10 minutes
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract research from response
                if 'choices' in data and len(data['choices']) > 0:
                    research = data['choices'][0]['message']['content'].strip()
                    logger.debug(f"Got deep research response ({len(research)} chars)")
                    return research
                else:
                    logger.warning("No research in response")
                    return None
                    
            except Timeout:
                logger.warning(f"Timeout getting deep research (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return None
                continue
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limit hit for deep research (attempt {attempt + 1}/{max_retries})")
                    if attempt == max_retries - 1:
                        return None
                    continue
                elif e.response.status_code >= 500:
                    # Server errors are retryable
                    logger.warning(f"Server error {e.response.status_code} for deep research (attempt {attempt + 1}/{max_retries})")
                    if attempt == max_retries - 1:
                        return None
                    continue
                else:
                    # Client errors are not retryable
                    logger.error(f"HTTP error for deep research: {e}")
                    if e.response.text:
                        logger.error(f"Response body: {e.response.text}")
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error getting deep research: {e}")
                return None
        
        return None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close the session."""
        try:
            self.session.close()
        except Exception as e:
            # Ignore errors during cleanup
            logger.debug(f"Session cleanup error (non-critical): {e}")