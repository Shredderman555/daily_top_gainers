"""Polygon API client for fetching analyst ratings and price targets."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from polygon import RESTClient
from polygon.exceptions import BadResponse, AuthError

logger = logging.getLogger(__name__)


class PolygonClient:
    """Client for interacting with Polygon API for analyst data."""
    
    def __init__(self, api_key: str):
        """Initialize the Polygon API client.
        
        Args:
            api_key: Polygon API key
        """
        self.api_key = api_key
        self.client = RESTClient(api_key)
    
    def fetch_analyst_ratings(self, ticker: str, limit: int = 50) -> List[Any]:
        """Fetch analyst ratings and price targets for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of results to fetch
        
        Returns:
            List of analyst ratings
        """
        logger.debug(f"Fetching analyst ratings for {ticker} from Polygon")
        
        ratings = []
        try:
            for rating in self.client.list_benzinga_ratings(
                ticker=ticker,
                limit=limit,
                sort="date.desc"
            ):
                ratings.append(rating)
        except (BadResponse, AuthError) as e:
            logger.error(f"Error fetching Polygon ratings for {ticker}: {e}")
            return []
        except Exception as e:
            logger.warning(f"Unexpected error fetching ratings for {ticker}: {e}")
            return []
        
        logger.debug(f"Found {len(ratings)} analyst updates for {ticker}")
        return ratings
    
    def calculate_price_target_consensus(self, ratings: List[Any]) -> Dict[str, Any]:
        """Calculate consensus price targets and trends from analyst ratings.
        
        Args:
            ratings: List of analyst ratings from Polygon API
        
        Returns:
            Dictionary with consensus data and trends
        """
        if not ratings:
            return {
                'current_consensus': None,
                'consensus_7d': None,
                'consensus_30d': None,
                'consensus_90d': None,
                'trend_7d': None,
                'trend_30d': None,
                'analyst_count': 0,
                'recent_actions': [],
                'price_target_history': []
            }
        
        # Group ratings by timeframe
        today = datetime.now()
        targets_current = []
        targets_7d = []
        targets_30d = []
        targets_90d = []
        recent_actions = []
        price_target_history = []
        
        # Track unique analysts for current consensus
        analyst_targets = {}
        
        for rating in ratings:
            # Get price target
            pt = getattr(rating, 'price_target', None)
            if not pt or pt <= 0:
                continue
            
            # Get date
            rating_date = None
            if hasattr(rating, 'date'):
                try:
                    if isinstance(rating.date, str):
                        rating_date = datetime.strptime(rating.date[:10], "%Y-%m-%d")
                    else:
                        rating_date = rating.date
                except:
                    continue
            
            if not rating_date:
                continue
            
            days_ago = (today - rating_date).days
            
            # Get analyst firm
            firm = getattr(rating, 'firm', None) or getattr(rating, 'analyst_firm', 'Unknown')
            
            # Track most recent target per analyst for current consensus
            if firm not in analyst_targets or days_ago < analyst_targets[firm]['days_ago']:
                analyst_targets[firm] = {'target': pt, 'days_ago': days_ago}
            
            # Collect all actions for history (up to 15 most recent)
            if len(recent_actions) < 15:
                action = getattr(rating, 'rating_action', None) or getattr(rating, 'action', 'Updates')
                rating_value = getattr(rating, 'rating', None) or getattr(rating, 'rating_current', '')
                pt_prior = getattr(rating, 'previous_price_target', None)
                
                action_info = {
                    'date': rating_date.strftime("%b %d, %Y"),
                    'date_short': rating_date.strftime("%b %d"),
                    'firm': firm[:25] + "..." if len(firm) > 25 else firm,
                    'action': action.capitalize() if action else 'Updates',
                    'rating': rating_value,
                    'target': pt,
                    'target_prior': pt_prior,
                    'days_ago': days_ago
                }
                recent_actions.append(action_info)
            
            # Collect data for price target history chart (last 180 days)
            if days_ago <= 180:
                price_target_history.append({
                    'date': rating_date.isoformat(),
                    'target': pt,
                    'firm': firm,
                    'days_ago': days_ago
                })
            
            # Categorize by timeframe
            if days_ago <= 7:
                targets_7d.append(pt)
            elif days_ago <= 30:
                targets_30d.append(pt)
            elif days_ago <= 90:
                targets_90d.append(pt)
        
        # Calculate current consensus from unique analysts
        targets_current = [data['target'] for data in analyst_targets.values()]
        
        # Calculate consensus values
        current_consensus = sum(targets_current) / len(targets_current) if targets_current else None
        consensus_7d = sum(targets_7d) / len(targets_7d) if targets_7d else None
        consensus_30d = sum(targets_30d) / len(targets_30d) if targets_30d else None
        consensus_90d = sum(targets_90d) / len(targets_90d) if targets_90d else None
        
        # Calculate trends
        trend_7d = None
        trend_30d = None
        
        if current_consensus:
            # 7-day trend
            if consensus_7d:
                if consensus_7d > current_consensus:
                    trend_7d = f"↑ {((consensus_7d/current_consensus - 1) * 100):.1f}%"
                elif consensus_7d < current_consensus:
                    trend_7d = f"↓ {((1 - consensus_7d/current_consensus) * 100):.1f}%"
                else:
                    trend_7d = "→ Unchanged"
            
            # 30-day trend (compare 30d average to current)
            if consensus_30d:
                if consensus_30d > current_consensus:
                    trend_30d = f"↑ {((consensus_30d/current_consensus - 1) * 100):.1f}%"
                elif consensus_30d < current_consensus:
                    trend_30d = f"↓ {((1 - consensus_30d/current_consensus) * 100):.1f}%"
                else:
                    trend_30d = "→ Unchanged"
        
        return {
            'current_consensus': current_consensus,
            'consensus_7d': consensus_7d,
            'consensus_30d': consensus_30d,
            'consensus_90d': consensus_90d,
            'trend_7d': trend_7d,
            'trend_30d': trend_30d,
            'analyst_count': len(analyst_targets),
            'recent_actions': recent_actions,
            'price_target_history': price_target_history
        }
    
    def get_price_targets_for_stock(self, ticker: str) -> Dict[str, Any]:
        """Get comprehensive price target data for a stock.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with all price target data
        """
        # Fetch ratings
        ratings = self.fetch_analyst_ratings(ticker, limit=50)
        
        # Calculate consensus and trends
        consensus_data = self.calculate_price_target_consensus(ratings)
        
        # Add ticker to the result
        consensus_data['ticker'] = ticker
        consensus_data['last_updated'] = datetime.now().isoformat()
        
        return consensus_data
    
    def get_price_targets_batch(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get price targets for multiple stocks.
        
        Args:
            tickers: List of stock ticker symbols
        
        Returns:
            Dictionary mapping tickers to their price target data
        """
        results = {}
        
        for ticker in tickers:
            logger.debug(f"Processing Polygon data for {ticker}")
            try:
                results[ticker] = self.get_price_targets_for_stock(ticker)
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                results[ticker] = {
                    'ticker': ticker,
                    'current_consensus': None,
                    'error': str(e)
                }
        
        return results
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Polygon client doesn't need explicit cleanup
        pass