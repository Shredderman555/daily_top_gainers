"""Financial Modeling Prep API client for fetching stock gainers."""

import logging
from typing import List, Dict, Any, Optional
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError


logger = logging.getLogger(__name__)


class FMPAPIClient:
    """Client for interacting with Financial Modeling Prep API."""
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    GAINERS_ENDPOINT = "/stock_market/gainers"
    
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
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close the session."""
        self.session.close()