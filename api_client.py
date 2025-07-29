"""Financial Modeling Prep API client for fetching stock gainers."""

import logging
import time
from typing import List, Dict, Any, Optional
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError


logger = logging.getLogger(__name__)


class FMPAPIClient:
    """Client for interacting with Financial Modeling Prep API."""
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    GAINERS_ENDPOINT = "/stock_market/gainers"
    PROFILE_ENDPOINT = "/profile"
    
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
        
        Returns:
            List of stock dictionaries containing gainer information
            
        Raises:
            RequestException: If the API request fails
        """
        url = f"{self.BASE_URL}{self.GAINERS_ENDPOINT}"
        params = {'apikey': self.api_key}
        
        try:
            logger.info("Fetching daily gainers from FMP API")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, dict) and 'Error Message' in data:
                error_msg = data.get('Error Message', 'Unknown API error')
                logger.error(f"API error: {error_msg}")
                raise RequestException(f"API error: {error_msg}")
            
            logger.info(f"Successfully fetched {len(data)} gainers")
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
        
        logger.info(f"Filtered {len(filtered_stocks)} stocks with gains >= {min_gain}%")
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
        """Enrich stock data with market cap information.
        
        Args:
            stocks: List of stock dictionaries
            
        Returns:
            List of stocks with added market cap data
        """
        logger.info(f"Fetching market cap data for {len(stocks)} stocks")
        
        for i, stock in enumerate(stocks):
            symbol = stock.get('symbol')
            if not symbol:
                continue
                
            # Add small delay to avoid rate limiting
            if i > 0:
                time.sleep(0.1)
            
            profile = self.get_company_profile(symbol)
            if profile and 'mktCap' in profile:
                stock['mktCap'] = profile['mktCap']
                logger.debug(f"Added market cap for {symbol}: ${profile['mktCap']:,.0f}")
            else:
                stock['mktCap'] = None
                logger.debug(f"No market cap data for {symbol}")
        
        return stocks
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close the session."""
        self.session.close()