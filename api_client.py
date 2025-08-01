"""Financial Modeling Prep API client for fetching stock gainers."""

import logging
import time
from typing import List, Dict, Any, Optional, Callable
import re
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from perplexity_client import PerplexityClient


logger = logging.getLogger(__name__)


class FMPAPIClient:
    """Client for interacting with Financial Modeling Prep API."""
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    GAINERS_ENDPOINT = "/stock_market/gainers"
    PROFILE_ENDPOINT = "/profile"
    
    def _parse_company_analysis(self, full_response: str) -> Dict[str, Any]:
        """Parse the structured company analysis response.
        
        Args:
            full_response: Full response from Perplexity containing description,
                          competitive advantage, and market growth analysis
                          
        Returns:
            Dictionary with parsed components
        """
        result = {
            'short_description': None,
            'competitive_score': None,
            'competitive_reasoning': None,
            'growth_score': None,
            'growth_reasoning': None
        }
        
        if not full_response:
            return result
        
        # Try to parse sections
        lines = full_response.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for section markers or scores
            if 'One,' in line or line.startswith('1.') or (current_section is None and len(lines) > 0):
                # This is likely the description
                result['short_description'] = line.replace('One,', '').replace('1.', '').strip()
                current_section = 'description'
            elif 'Two,' in line or line.startswith('2.') or 'competitive advantage' in line.lower():
                current_section = 'competitive'
                # Try to extract score
                score_match = re.search(r'(\d+)\s*(?:out of\s*10|/\s*10)', line)
                if score_match:
                    result['competitive_score'] = int(score_match.group(1))
                # Rest is reasoning
                reasoning = re.sub(r'Two,|2\.|Score:\s*\d+/10|\d+\s*out of\s*10', '', line).strip()
                if reasoning:
                    result['competitive_reasoning'] = reasoning
            elif 'Three,' in line or line.startswith('3.') or 'market' in line.lower() and 'grow' in line.lower():
                current_section = 'growth'
                # Try to extract score
                score_match = re.search(r'(\d+)\s*(?:out of\s*10|/\s*10)', line)
                if score_match:
                    result['growth_score'] = int(score_match.group(1))
                # Rest is reasoning
                reasoning = re.sub(r'Three,|3\.|Score:\s*\d+/10|\d+\s*out of\s*10', '', line).strip()
                if reasoning:
                    result['growth_reasoning'] = reasoning
            else:
                # Continuation of previous section
                if current_section == 'competitive' and not result['competitive_reasoning']:
                    result['competitive_reasoning'] = line
                elif current_section == 'growth' and not result['growth_reasoning']:
                    result['growth_reasoning'] = line
        
        # If we couldn't parse it structured, just use first 20 words as description
        if not result['short_description'] and full_response:
            words = full_response.split()[:20]
            result['short_description'] = ' '.join(words)
        
        # Clean up reasoning to remove duplicate score text
        if result['competitive_reasoning']:
            # Remove patterns like "Competitive advantage score: 4/10." from the beginning
            result['competitive_reasoning'] = re.sub(
                r'^(Competitive\s+advantage\s+score:|Score:)\s*\d+/10\.?\s*', 
                '', 
                result['competitive_reasoning'], 
                flags=re.IGNORECASE
            ).strip()
        
        if result['growth_reasoning']:
            # Remove patterns like "Market growth score: 9/10." from the beginning
            result['growth_reasoning'] = re.sub(
                r'^(Market\s+growth\s+score:|Growth\s+score:|Score:)\s*\d+/10\.?\s*', 
                '', 
                result['growth_reasoning'], 
                flags=re.IGNORECASE
            ).strip()
        
        return result
    
    def __init__(self, api_key: str):
        """Initialize the API client with an API key.
        
        Args:
            api_key: Financial Modeling Prep API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'StockAlertsBot/1.0'
        })
    
    def get_daily_gainers(self) -> List[Dict[str, Any]]:
        """Fetch daily stock gainers from the API.
        
        Note: This endpoint returns only the top 50 gainers. Stocks with gains
        below the top 50 threshold will not be included, even if they gained 10%+.
        
        Returns:
            List of stock dictionaries containing gainer information
            
        Raises:
            RequestException: If the API request fails
        """
        url = f"{self.BASE_URL}{self.GAINERS_ENDPOINT}"
        params = {'apikey': self.api_key}
        
        try:
            logger.debug("Fetching daily gainers from FMP API")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, dict) and 'Error Message' in data:
                error_msg = data.get('Error Message', 'Unknown API error')
                logger.error(f"API error: {error_msg}")
                raise RequestException(f"API error: {error_msg}")
            
            logger.info(f"Successfully fetched {len(data)} gainers from FMP API (top 50 only)")
            return data
            
        except Timeout:
            logger.error("API request timed out")
            raise RequestException("API request timed out after 30 seconds")
            
        except ConnectionError:
            logger.error("Failed to connect to FMP API")
            raise RequestException("Failed to connect to Financial Modeling Prep API")
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            if e.response.status_code == 401:
                raise RequestException("Invalid API key or unauthorized access")
            elif e.response.status_code == 429:
                raise RequestException("API rate limit exceeded")
            else:
                raise RequestException(f"HTTP error: {e}")
                
        except Exception as e:
            logger.error(f"Unexpected error fetching gainers: {e}")
            raise RequestException(f"Unexpected error: {e}")
    
    def filter_by_gain_percentage(self, stocks: List[Dict[str, Any]], 
                                  min_gain: float = 10.0) -> List[Dict[str, Any]]:
        """Filter stocks by minimum gain percentage.
        
        Args:
            stocks: List of stock dictionaries
            min_gain: Minimum gain percentage threshold (default: 10.0)
            
        Returns:
            Filtered list of stocks meeting the gain criteria
        """
        filtered_stocks = []
        
        for stock in stocks:
            try:
                change_value = stock.get('changesPercentage', 0)
                # Handle both string and float formats
                if isinstance(change_value, str):
                    change_percent = float(change_value.replace('%', ''))
                else:
                    change_percent = float(change_value)
                
                if change_percent >= min_gain:
                    filtered_stocks.append(stock)
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing gain percentage for {stock.get('symbol', 'Unknown')}: {e}")
                continue
        
        logger.debug(f"Filtered {len(filtered_stocks)} stocks with gains >= {min_gain}%")
        return filtered_stocks
    
    def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch company profile data including market cap.
        
        Args:
            symbol: Stock symbol to fetch profile for
            
        Returns:
            Company profile dictionary or None if error
        """
        url = f"{self.BASE_URL}{self.PROFILE_ENDPOINT}/{symbol}"
        params = {'apikey': self.api_key}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                return data[0]
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching profile for {symbol}: {e}")
            return None
    
    def enrich_with_market_cap(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich stock data with market cap, industry, and sector information.
        
        Args:
            stocks: List of stock dictionaries
            
        Returns:
            List of stocks with added market cap, industry, and sector data
        """
        logger.debug(f"Fetching company profile data for {len(stocks)} stocks")
        
        for i, stock in enumerate(stocks):
            symbol = stock.get('symbol')
            if not symbol:
                continue
                
            # Add small delay to avoid rate limiting
            if i > 0:
                time.sleep(0.1)
            
            # Fetch company profile for market cap, industry, and sector
            profile = self.get_company_profile(symbol)
            if profile:
                # Add market cap
                if 'mktCap' in profile:
                    stock['mktCap'] = profile['mktCap']
                    logger.debug(f"Added market cap for {symbol}: ${profile['mktCap']:,.0f}")
                else:
                    stock['mktCap'] = None
                    logger.debug(f"No market cap data for {symbol}")
                
                # Add industry and sector
                stock['industry'] = profile.get('industry', '')
                stock['sector'] = profile.get('sector', '')
                logger.debug(f"Added industry/sector for {symbol}: {stock['sector']} / {stock['industry']}")
            else:
                stock['mktCap'] = None
                stock['industry'] = ''
                stock['sector'] = ''
                logger.debug(f"No profile data for {symbol}")
        
        return stocks
    
    def filter_by_market_cap(self, stocks: List[Dict[str, Any]], 
                             min_market_cap: float = 300_000_000) -> List[Dict[str, Any]]:
        """Filter stocks by minimum market cap.
        
        Args:
            stocks: List of stock dictionaries with market cap data
            min_market_cap: Minimum market cap in dollars (default: $300M)
            
        Returns:
            Filtered list of stocks meeting the market cap criteria
        """
        filtered_stocks = []
        excluded_count = 0
        
        for stock in stocks:
            market_cap = stock.get('mktCap')
            symbol = stock.get('symbol', 'Unknown')
            
            # Skip if no market cap data
            if market_cap is None:
                logger.debug(f"No market cap data for {symbol}, excluding")
                excluded_count += 1
                continue
            
            # Check if meets minimum market cap
            if market_cap >= min_market_cap:
                filtered_stocks.append(stock)
            else:
                logger.debug(f"Excluding {symbol} - Market cap ${market_cap:,.0f} < ${min_market_cap:,.0f}")
                excluded_count += 1
        
        logger.debug(f"Filtered {excluded_count} stocks with market cap < ${min_market_cap/1_000_000:.0f}M")
        logger.debug(f"Remaining stocks after market cap filter: {len(filtered_stocks)}")
        return filtered_stocks
    
    def filter_by_technical_nature(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter stocks to keep only technical/engineering-heavy companies.
        
        Args:
            stocks: List of stock dictionaries with is_technical data
            
        Returns:
            Filtered list of technical stocks
        """
        filtered_stocks = []
        excluded_count = 0
        
        for stock in stocks:
            symbol = stock.get('symbol', 'Unknown')
            is_technical = stock.get('is_technical', None)
            
            # Keep if technical or if we couldn't determine (give benefit of doubt)
            if is_technical is not False:
                filtered_stocks.append(stock)
            else:
                logger.debug(f"Excluding {symbol} - Not technical/engineering-heavy")
                excluded_count += 1
        
        logger.debug(f"Filtered {excluded_count} non-technical stocks")
        logger.debug(f"Remaining stocks after technical filter: {len(filtered_stocks)}")
        return filtered_stocks
    
    def filter_by_industry(self, stocks: List[Dict[str, Any]], 
                           exclude_biotech: bool = True) -> List[Dict[str, Any]]:
        """Filter stocks by industry, optionally excluding biotechnology.
        
        Args:
            stocks: List of stock dictionaries with industry data
            exclude_biotech: Whether to exclude biotechnology/pharmaceutical stocks (default: True)
            
        Returns:
            Filtered list of stocks
        """
        if not exclude_biotech:
            return stocks
            
        filtered_stocks = []
        excluded_count = 0
        excluded_industries = ['biotechnology', 'pharmaceutical']
        
        for stock in stocks:
            symbol = stock.get('symbol', 'Unknown')
            industry = stock.get('industry', '').lower()
            
            # Check if stock is in excluded industries
            is_excluded = any(term in industry for term in excluded_industries)
            
            if is_excluded:
                logger.debug(f"Excluding {symbol} - Industry: {stock.get('industry', 'N/A')}")
                excluded_count += 1
            else:
                filtered_stocks.append(stock)
        
        logger.debug(f"Filtered {excluded_count} biotechnology/pharmaceutical stocks")
        logger.debug(f"Remaining stocks after industry filter: {len(filtered_stocks)}")
        return filtered_stocks
    
    def check_technical_nature(self, stocks: List[Dict[str, Any]], 
                               perplexity_api_key: str,
                               progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Check if companies are technical/engineering-heavy.
        
        Args:
            stocks: List of stock dictionaries
            perplexity_api_key: Perplexity API key
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of stocks with added is_technical data
        """
        if not perplexity_api_key:
            logger.warning("No Perplexity API key provided, skipping technical checks")
            return stocks
        
        logger.info("Checking technical nature of companies")
        
        # Initialize Perplexity client
        with PerplexityClient(perplexity_api_key) as client:
            # Get company names with ticker symbols for better accuracy
            company_names = []
            for stock in stocks:
                name = stock.get('name', stock.get('symbol', 'Unknown'))
                symbol = stock.get('symbol', '')
                # Format as "Company Name (SYMBOL)" if we have both
                if name and symbol and name != symbol:
                    company_names.append(f"{name} ({symbol})")
                else:
                    company_names.append(name)
            
            # Check technical nature
            technical_checks, tech_successful = client.get_technical_companies_batch(
                company_names,
                progress_callback=progress_callback,
                delay=1.5
            )
            
            # Add technical nature to stock data
            for stock, company_name in zip(stocks, company_names):
                stock['is_technical'] = technical_checks.get(company_name, None)
            
            logger.info(f"Successfully checked technical nature for {tech_successful}/{len(stocks)} companies")
        
        return stocks
    
    def enrich_with_descriptions(self, stocks: List[Dict[str, Any]], 
                                 perplexity_api_key: str,
                                 progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Enrich stock data with company descriptions, growth rates, and P/S ratios from Perplexity.
        
        Args:
            stocks: List of stock dictionaries
            perplexity_api_key: Perplexity API key
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of stocks with added description, growth rate, and P/S ratio data
        """
        if not perplexity_api_key:
            logger.warning("No Perplexity API key provided, skipping descriptions")
            return stocks
        
        logger.info("Fetching company data from Perplexity API")
        
        # Initialize Perplexity client
        with PerplexityClient(perplexity_api_key) as client:
            # Get company names with ticker symbols for better accuracy
            company_names = []
            for stock in stocks:
                name = stock.get('name', stock.get('symbol', 'Unknown'))
                symbol = stock.get('symbol', '')
                # Format as "Company Name (SYMBOL)" if we have both
                if name and symbol and name != symbol:
                    company_names.append(f"{name} ({symbol})")
                else:
                    company_names.append(name)
            
            # Fetch descriptions
            descriptions, desc_successful = client.get_descriptions_batch(
                company_names, 
                progress_callback=progress_callback,
                delay=1.5
            )
            
            # Fetch growth rates
            growth_rates, growth_successful = client.get_growth_rates_batch(
                company_names, 
                progress_callback=progress_callback,
                delay=1.5
            )
            
            # Fetch P/S ratios
            ps_ratios, ps_successful = client.get_ps_ratios_batch(
                company_names, 
                progress_callback=progress_callback,
                delay=1.5
            )
            
            # Add descriptions, growth rates, and P/S ratios to stock data
            for stock, company_name in zip(stocks, company_names):
                # Parse the structured description response
                full_description = descriptions.get(company_name, None)
                if full_description:
                    parsed = self._parse_company_analysis(full_description)
                    stock['description'] = parsed['short_description']
                    stock['competitive_score'] = parsed['competitive_score']
                    stock['competitive_reasoning'] = parsed['competitive_reasoning']
                    stock['market_growth_score'] = parsed['growth_score']
                    stock['market_growth_reasoning'] = parsed['growth_reasoning']
                else:
                    stock['description'] = None
                    stock['competitive_score'] = None
                    stock['competitive_reasoning'] = None
                    stock['market_growth_score'] = None
                    stock['market_growth_reasoning'] = None
                
                stock['growth_rate'] = growth_rates.get(company_name, None)
                stock['ps_ratio'] = ps_ratios.get(company_name, None)
            
            logger.info(f"Successfully fetched descriptions for {desc_successful}/{len(stocks)} companies")
            logger.info(f"Successfully fetched growth rates for {growth_successful}/{len(stocks)} companies")
            logger.info(f"Successfully fetched P/S ratios for {ps_successful}/{len(stocks)} companies")
        
        return stocks
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close the session."""
        self.session.close()