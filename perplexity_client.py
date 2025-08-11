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

Part A: Technical Excellence (0-8 points)
1. Fundamental Technical Innovation (0-2 points)

Are they inventing new algorithms, materials, or methods vs. integrating existing ones?
Would world-class engineers with unlimited funding still need 3+ years to replicate?
Have they solved problems previously thought intractable?
Do they have breakthrough IP that's defendable?

Score 0-2: (0=using existing tech, 1=incremental innovation, 2=breakthrough innovation)
2. Technical Complexity & Barriers (0-2 points)

Does replication require rare expertise, massive datasets, or specialized infrastructure?
Are there compounding technical advantages that grow over time?
Would a competitor need to solve multiple hard problems in sequence?
Is the technical challenge in the implementation details that take years to perfect?

Score 0-2: (0=straightforward, 1=complex but doable, 2=extremely difficult to replicate)
3. Technical Risk & Systems Mastery (0-2 points)

Are they attempting something with genuine technical risk?
Do they excel at making complex systems work at unprecedented scale?
Do they require mastery across multiple technical domains?
Are they 5-10 years ahead of competitors technically?

Score 0-2: (0=proven approach, 1=moderate innovation, 2=pushing limits of possible)
4. Irreplaceable Technical Assets (0-2 points)

Do they have technical assets (team, data, infrastructure) that money alone can't buy?
Have they accumulated technical advantages that compound?
Do the world's best engineers specifically want to work there?
Would losing their key technical resources be company-ending?

Score 0-2: (0=replaceable, 1=strong assets, 2=irreplaceable advantages)
Part B: Business Power (0-12 points)
5. Revenue Quality & Durability (0-2 points)

Does the product become mission-critical and embedded?
Do they have 120%+ net revenue retention (land-and-expand)?
Are contracts multi-year with 90%+ gross renewal rates?
Are switching costs measured in years and millions of dollars?

Score 0-2: (0=high churn, 1=solid retention, 2=deeply embedded/expanding)
6. Market Position & Competitive Dynamics (0-2 points)

Are they the default choice or heading there?
Do they have winner-take-most dynamics?
Is their competitive lead widening?
Would customers panic if they disappeared tomorrow?

Score 0-2: (0=weak position, 1=solid competitor, 2=dominant/irreplaceable)
7. Growth & Profitability Runway (0-4 points) 🔴 DOUBLE WEIGHT
Evaluate total value creation potential (revenue growth × margin expansion × duration):

4 points: 20x+ potential over next decade

Rule of 80+ (Growth % + FCF Margin %), OR
50%+ growth sustainable for 7+ years with path to profitability, OR
Creating entirely new markets with massive TAM expansion
Examples: Nvidia (Rule of 155), early Tesla, SpaceX


3 points: 10-20x potential

Rule of 60+ sustained for multiple years, OR
30-40% growth for 7+ years with margin expansion
Multiple untapped growth vectors
Examples: Palantir, Databricks


2 points: 5-10x potential

Rule of 40-60, OR
25-30% growth for 5 years with stable margins
Clear path but eventually saturates


1 point: 3-5x potential

Rule of 30-40
15-25% growth OR profitable but slow growth


0 points: <3x potential

Rule of <30
Low growth AND low margins



8. Capital Efficiency & Cash Generation (0-2 points)

Can they self-fund growth or need constant capital raises?
Do they have or have clear path to 20%+ FCF margins?
Does each dollar invested yield >$3 in enterprise value?
Can they grow revenue faster than OpEx?

Score 0-2: (0=perpetual capital needs, 1=path to self-funding, 2=cash generation machine)
9. Valuation Reality (0-2 points with possible -2 penalty)

2 points: Exceptional value (e.g., <10x sales for 20%+ growth, <20x for 40%+ growth)
1 point: Fair value (e.g., 10-20x for 20-30% growth, 20-40x for 40-60% growth)
0 points: Expensive but justifiable (e.g., 40-60x for 60%+ growth with profitability)
-1 point: Overvalued (e.g., 60-100x sales, or >2x growth rate multiple)
-2 points: Uninvestable price (e.g., >100x sales or >3x growth rate multiple)


Total Score: X/20
Scoring Guide:

18-20: Generational investment - exceptional company at great price - Back up the truck
15-17: Strong buy - quality and value aligned - Build full position
12-14: Buy - good opportunity - Start accumulating
10-11: Watch list - interesting but wait for better entry - Wait for pullback
8-9: Pass - either weak fundamentals or too expensive - Look elsewhere
<8: Avoid - poor investment regardless of story - Hard pass


Quick Screening Questions (for rapid evaluation):

Technical Test: Could 10 world-class engineers replicate this in 6 months with unlimited funding? (If yes → likely not a fit)
Business Test: Will this company achieve Rule of 40+ while growing? (If no → be cautious)
10x Test: Can this company be 10x larger in 10 years? (If no → limited upside)
Moat Test: What would have to happen for this company to become irrelevant? (If easy → weak moat)
Price Test: Is valuation less than 2x the growth rate? (If no → very expensive)


Critical Elements to Also Consider (Not Scored):
🚩 Red Flags:

Customer concentration >30%
Founder/CEO departed recently
Declining win rates or elongating sales cycles
Key competitors gaining ground rapidly
Regulatory risks that could destroy the business
Technological disruption risk (their tech becoming obsolete)

✅ Green Flags:

Founder-led with high insider ownership
Accelerating organic growth
Expanding TAM faster than revenue growth
Network effects getting stronger
Government/regulatory tailwinds


Provide brief reasoning for each score and identify which of the reference companies (Rocket Lab, Nvidia, Anduril, Palantir, Databricks, Glean) they most resemble.
Remember: The best investments combine:

Hard technical problems that take years to solve
Products that become mission-critical infrastructure
Massive growth runways with expanding profitability
Reasonable valuations relative to opportunity

Companies scoring 15+ are rare - they represent the intersection of innovation, execution, market timing, and valuation that create multi-baggers."""
        
        try:
            logger.debug(f"Requesting investment evaluation for {company_name}")
            
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
                    "max_tokens": 2000
                },
                timeout=200
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract evaluation from response
            if 'choices' in data and len(data['choices']) > 0:
                evaluation = data['choices'][0]['message']['content'].strip()
                # Remove citation markers
                import re
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