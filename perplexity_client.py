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
                timeout=20
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
                timeout=20
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
                timeout=20
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
                timeout=20
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
                timeout=20
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
                timeout=20
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
                timeout=20
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
    
    def get_investment_evaluation(self, company_name: str) -> Optional[str]:
        """Get comprehensive investment evaluation using the 20-point framework.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Investment evaluation with scores and analysis or None if error
        """
        prompt = f"""Complete Investment Evaluation Framework for {company_name}

Evaluate {company_name} on these criteria:

PART A: TECHNICAL EXCELLENCE (0-20 points) - 20%
================================================

1. Fundamental Technical Innovation (0-5 points)
- Are they inventing new algorithms, materials, or methods vs. integrating existing ones?
- Would world-class engineers with unlimited funding still need 3+ years to replicate?
- Have they solved problems previously thought intractable?
- Do they have breakthrough IP that's defendable?

Score 0-5: (0-1=using existing tech, 2-3=incremental innovation, 4-5=breakthrough innovation)

2. Technical Complexity & Barriers (0-5 points)
- Does replication require rare expertise, massive datasets, or specialized infrastructure?
- Are there compounding technical advantages that grow over time?
- Would a competitor need to solve multiple hard problems in sequence?
- Is the technical challenge in the implementation details that take years to perfect?

Score 0-5: (0-1=straightforward, 2-3=complex but doable, 4-5=extremely difficult to replicate)

3. Technical Risk & Systems Mastery (0-5 points)
- Are they attempting something with genuine technical risk?
- Do they excel at making complex systems work at unprecedented scale?
- Do they require mastery across multiple technical domains?
- Are they 5-10 years ahead of competitors technically?

Score 0-5: (0-1=proven approach, 2-3=moderate innovation, 4-5=pushing limits of possible)

4. Irreplaceable Technical Assets (0-5 points)
- Do they have technical assets (team, data, infrastructure) that money alone can't buy?
- Have they accumulated technical advantages that compound?
- Do the world's best engineers specifically want to work there?
- Would losing their key technical resources be company-ending?

Score 0-5: (0-1=replaceable, 2-3=strong assets, 4-5=irreplaceable advantages)

PART B: FUTURE GROWTH & MULTIPLE SUSTAINABILITY (0-50 points) - 50% 🔴🔴🔴
===========================================================================

Evaluate the company's ability to maintain/expand valuation multiples over the next decade:

FIRST: Check for Narrative Violations (Bonus opportunity)
----------------------------------------------------------
Before scoring, ask: Is the market fundamentally wrong about this company?

NARRATIVE VIOLATION INDICATORS (if 3+ apply, add 10-15 bonus points):
□ Market calls it "just a [commodity business]" but it's really a platform
□ "TAM too small" but behavior shift could expand it 100x
□ "Incumbents will win" but they have non-obvious advantages
□ "Too capital intensive" but that creates the moat
□ "Services company" but building software/platform
□ Trading at depressed multiple due to misunderstanding
□ Founder investing heavily in "unnecessary" capabilities
□ Building for a world that doesn't exist yet

Examples of narrative violations that worked:
- Amazon 2010: "Low margin retailer" → Everything store + AWS
- Netflix 2005: "DVD by mail" → Streaming transformation  
- Tesla 2015: "Luxury cars" → Energy & transportation revolution
- Nvidia 2019: "Gaming company" → AI infrastructure
- Palantir 2022: "Services company" → AI operating system

SECOND: Check for Early Stage Frontier Opportunity
---------------------------------------------------
For companies with <$500M revenue, evaluate differently:

EARLY STAGE FRONTIER BONUS (add 15-20 points if 5+ are true):
□ Founder has unique domain expertise (ex-SEAL, ex-SpaceX, PhD in field)
□ Building for market that WILL exist but doesn't yet
□ Solving problem that MUST be solved (national security, climate, health)
□ Technical approach is revolutionary not evolutionary
□ Top-tier VCs investing (Founders Fund, a16z, Sequoia)
□ Government or Fortune 500 already piloting
□ Recruiting world-class team from day 1
□ 10+ years ahead but catalyst approaching

Examples:
- Anduril 2019: Defense autonomy before Ukraine made it obvious
- SpaceX 2008: Reusable rockets when everyone said impossible
- Palantir 2010: Data integration before big data explosion
- OpenAI 2019: AGI research before ChatGPT breakthrough

THIRD: Identify Upcoming Catalysts (add 10-15 points)
------------------------------------------------------
Is there a catalyst that will make this obvious?

□ Geopolitical (Ukraine → defense tech)
□ Regulatory (AI regulation → need for governance)
□ Technology breakthrough (GPT → AI explosion)
□ Cost curve (batteries → EVs viable)
□ Behavior shift (COVID → remote work)
□ Government spending (CHIPS Act → semiconductors)
□ Infrastructure buildout (5G → edge computing)
□ Demographic shift (aging → healthcare tech)

THEN: Score Base Future Potential
----------------------------------

45-50 points (before bonuses): Generational inflection point company
- Positioned for massive behavior shift others don't see
- Building capabilities that seem excessive today but critical tomorrow
- At intersection of multiple exploding trends
- Market will re-rate from "commodity" to "platform" multiple
- Could sustain 50x+ sales multiple for years as market realizes
- The "obvious in retrospect" investment

35-44 points: Frontier industry leader with expanding multiples
- At the forefront of consensus frontier industries (AI, space, biotech)
- Market understands direction but not magnitude
- 40%+ growth sustainable for 5-7 years
- Multiple expansion as TAM becomes clear
- Rule of 80+ with improving trajectory

25-34 points: Strong growth with sustained premium multiples
- Leading a major technological shift that's <20% penetrated
- 25-35% growth for 5+ years
- Rule of 60+ sustainable
- Can maintain current multiple for 5+ years

15-24 points: Solid growth but multiple compression likely
- Good growth (15-25%) but market maturing
- Competition increasing
- Multiple likely to compress 30-50% over 5 years

5-14 points: Limited growth, significant multiple compression ahead
- Single-digit to low-teens growth
- Market saturating or being disrupted
- Multiple likely to compress 50-70%

0-4 points: Declining relevance
- Business model being disrupted
- Losing market share

KEY QUESTIONS FOR MAXIMUM SCORE:
- What does the founder see that the market doesn't?
- What are they building that seems unnecessary today?
- What behavior change makes this inevitable?
- What capabilities took them 10 years to build that suddenly matter?
- Why is the current multiple wrong (too low OR too high)?
- What narrative shift unlocks 10x multiple expansion?
- What catalyst will make this obvious to everyone?

FOUNDER-MARKET FIT BONUS (0-5 additional points):
- Founder has unique insight from experience (2 points)
- Building solution to problem they personally faced (1 point)
- 10+ years preparing for this exact opportunity (1 point)
- Obsessed with problem not solution (1 point)

PART C: BUSINESS QUALITY (0-20 points) - 20%
=============================================

Note: For pre-revenue or <$100M revenue companies, score generously based on potential

5. Revenue Quality & Durability (0-7 points)
- Does the product become mission-critical and embedded?
- Do they have 120%+ net revenue retention (land-and-expand)?
- Are contracts multi-year with 90%+ gross renewal rates?
- Are switching costs measured in years and millions of dollars?

Score 0-7: (0-2=high churn, 3-4=solid retention, 5-7=deeply embedded/expanding)
*For early stage: Score based on product stickiness potential*

6. Market Position & Competitive Dynamics (0-7 points)
- Are they the default choice or heading there?
- Do they have winner-take-most dynamics?
- Is their competitive lead widening?
- Would customers panic if they disappeared tomorrow?

Score 0-7: (0-2=weak position, 3-4=solid competitor, 5-7=dominant/irreplaceable)
*For early stage: Score based on early customer feedback and competitive advantages*

7. Capital Efficiency & Cash Generation (0-6 points)
- Can they self-fund growth or need constant capital raises?
- Do they have or have clear path to 20%+ FCF margins?
- Does each dollar invested yield >$3 in enterprise value?
- Can they grow revenue faster than OpEx?

Score 0-6: (0-2=perpetual capital needs, 3-4=path to self-funding, 5-6=cash generation machine)
*For early stage: Score based on business model potential, not current burn*

PART D: CURRENT VALUATION (0-10 points) - 10%
==============================================

With possible -10 penalty for egregious overvaluation:

Note: If company has narrative violation or early stage frontier bonus, expensive valuation matters less

9-10 points: Exceptional value (<10x sales for 20%+ growth, <20x for 40%+ growth)
7-8 points: Fair value (10-20x for 20-30% growth, 20-40x for 40-60% growth)
5-6 points: Full valuation (30-50x for 50%+ growth)
3-4 points: Expensive (50-75x for hypergrowth)
0-2 points: Very expensive (75-100x sales)
-5 to -10 points: Uninvestable (>100x sales or >3x growth rate multiple)

For early stage (<$100M revenue): Use EV/Revenue Run Rate or compare to similar stage companies

TOTAL SCORE: ___/100
====================

SCORING GUIDE:
85-100: Generational investment - will dominate the next decade
70-84: Strong buy - positioned for sustained outperformance
60-69: Buy - solid multi-year compounder
50-59: Starter position or wait for better price
40-49: Watch list only
<40: Avoid

QUICK SCREENING QUESTIONS:
1. Narrative Test: Is the market wrong about what this company really is?
2. Catalyst Test: What catalyst will make this obvious in 2-3 years?
3. Founder Test: Does the founder have unique insight others lack?
4. Frontier Test: Are they building for a world that doesn't exist yet?
5. Smart Money Test: Are top VCs/insiders buying aggressively?

SCORING EXAMPLES:
================

EARLY STAGE EXAMPLES (With Bonuses Applied):
Anduril 2019 @ $1B valuation (78/100):
- Technical: 18/20 (Lattice OS, autonomous systems)
- Future Growth: 30 + 20 (early stage) + 10 (catalyst) = 60/50
- Business: 5/20 (early revenue but strong potential)
- Valuation: 5/10 (fair for potential)
- WOULD HAVE CAUGHT IT!

SpaceX 2008 @ $500M valuation (82/100):
- Technical: 20/20 (reusable rockets)
- Future Growth: 35 + 20 (early stage) + 15 (narrative) = 70/50
- Business: 2/20 (no revenue yet)
- Valuation: 10/10 (cheap in retrospect!)
- WOULD HAVE CAUGHT IT!

INFLECTION POINT EXAMPLES:
Netflix 2007 @ $1.2B market cap (76/100):
- Technical: 8/20 (streaming tech)
- Future Growth: 35 + 15 (narrative) + 10 (catalyst) = 60/50
- Business: 10/20 (growing subs)
- Valuation: 8/10 (very cheap)

Nvidia 2021 @ $350B market cap (90/100):
- Technical: 18/20 (CUDA ecosystem)
- Future Growth: 42 + 10 (AI catalyst) = 52/50
- Business: 16/20 (strong fundamentals)
- Valuation: 4/10 (expensive but justified)

Palantir 2022 @ $15B market cap (86/100):
- Technical: 18/20 (Foundry platform)
- Future Growth: 30 + 15 (narrative) + 10 (AI catalyst) = 55/50
- Business: 14/20 (improving margins)
- Valuation: 9/10 (8x sales was gift!)

CURRENT MARKET EXAMPLES:
Nvidia @ 30x sales today (87/100):
- Technical: 18/20
- Future Growth: 48/50 (AI dominance)
- Business: 18/20
- Valuation: 3/10

Google @ 5x sales (58/100):
- Technical: 17/20
- Future Growth: 18/50 (size limits growth)
- Business: 18/20
- Valuation: 10/10

KEY INSIGHTS:
============
The framework now catches:
1. Early stage frontier companies (Anduril, SpaceX)
2. Narrative violations before they're obvious (Netflix, Amazon)
3. Catalyst-driven re-ratings (Nvidia pre-AI, Palantir pre-AI boom)
4. Founder-market fit advantages
5. Pre-consensus opportunities

The biggest returns come from:
- Being 2-3 years early on consensus
- Identifying catalysts before they happen
- Backing exceptional founders in frontier markets
- Buying when narrative is wrong
- Holding through the re-rating

RED FLAGS THAT CAP SCORES:
- Customer concentration >50%: Cap at 65/100
- Founder departed (without clear succession): Cap at 60/100
- Declining growth rate: -10 points on Future Growth
- Losing market share: -5 points on Market Position
- Regulatory risk that could kill business: -10 points overall
- No path to profitability after 10 years: Cap at 50/100
"""
        
        try:
            logger.debug(f"Requesting investment evaluation for {company_name}")
            
            response = self.session.post(
                f"{self.BASE_URL}/chat/completions",
                json={
                    "model": "sonar-reasoning-pro",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 20000
                },
                timeout=300
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract evaluation from response
            if 'choices' in data and len(data['choices']) > 0:
                evaluation = data['choices'][0]['message']['content'].strip()
                # Remove think tags and their content
                import re
                evaluation = re.sub(r'<think>.*?</think>', '', evaluation, flags=re.DOTALL).strip()
                # Remove citation markers
                evaluation = re.sub(r'\[\d+\]|\[\d*$', '', evaluation).strip()
                # Clean markdown formatting
                evaluation = clean_markdown(evaluation)
                logger.debug(f"Got investment evaluation for {company_name}")
                return evaluation
            else:
                logger.warning(f"No investment evaluation in response for {company_name}")
                return None
                
        except Timeout:
            logger.warning(f"Timeout getting investment evaluation for {company_name}")
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
            logger.error(f"Unexpected error getting investment evaluation for {company_name}: {e}")
            raise RequestException(str(e))
    
    def get_investment_evaluation_batch(self, company_names: list, 
                                        progress_callback: Optional[Callable] = None,
                                        delay: float = 0.5) -> dict:
        """Get investment evaluations for multiple companies with rate limiting.
        
        Args:
            company_names: List of company names
            progress_callback: Optional callback for progress updates
            delay: Delay between requests in seconds
            
        Returns:
            Dictionary mapping company names to investment evaluations
        """
        results = {}
        successful = 0
        
        for i, company in enumerate(company_names):
            if i > 0:
                time.sleep(delay)  # Rate limiting
            
            try:
                evaluation = self.get_investment_evaluation(company)
                results[company] = evaluation
                if evaluation is not None:
                    successful += 1
                    if progress_callback:
                        progress_callback(company, True, "investment_evaluation")
                else:
                    if progress_callback:
                        progress_callback(company, False, "No data returned")
                    
            except RequestException as e:
                results[company] = None
                error_msg = str(e)
                if progress_callback:
                    progress_callback(company, False, error_msg)
                logger.warning(f"Failed to get investment evaluation for {company}: {error_msg}")
        
        logger.info(f"Successfully fetched investment evaluations for {successful}/{len(company_names)} companies")
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
    
    def get_put_call_ratio(self) -> Optional[str]:
        """Get the latest total put/call ratio from CBOE.
        
        Returns:
            Put/call ratio as a string or None if error
        """
        prompt = "What is the latest TOTAL put/call ratio from the SUMMARY section at the top of https://www.cboe.com/us/options/market_statistics/daily/? Only give the final daily summary TOTAL put/call ratio as a numerical value. No other text"
        
        try:
            logger.debug("Requesting put/call ratio from CBOE")
            
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
                timeout=20
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract ratio from response
            if 'choices' in data and len(data['choices']) > 0:
                ratio_text = data['choices'][0]['message']['content'].strip()
                # Remove any citation markers
                import re
                ratio_text = re.sub(r'\[\d+\]|\[\d*$', '', ratio_text).strip()
                
                # Try to extract numeric value
                ratio_match = re.search(r'(\d+\.?\d*)', ratio_text)
                if ratio_match:
                    ratio_value = ratio_match.group(1)
                    logger.debug(f"Got put/call ratio: {ratio_value}")
                    return ratio_value
                else:
                    logger.warning(f"Could not parse put/call ratio from '{ratio_text}'")
                    return None
            else:
                logger.warning("No put/call ratio in response")
                return None
                
        except Timeout:
            logger.warning("Timeout getting put/call ratio")
            return None
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limit hit for put/call ratio")
            else:
                logger.error(f"HTTP error getting put/call ratio: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error getting put/call ratio: {e}")
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