#!/usr/bin/env python3
"""Test script to verify Polygon integration with the main pipeline."""

from config import Config
from api_client import FMPAPIClient
from polygon_client import PolygonClient

def test_polygon_integration():
    """Test the Polygon integration with a sample stock."""
    # Load configuration
    config = Config()
    
    print("Testing Polygon Integration")
    print("="*50)
    
    # Test with a sample stock
    test_stock = {
        'symbol': 'AAPL',
        'name': 'Apple Inc.',
        'changesPercentage': 15.5
    }
    
    # Initialize API client
    api_client = FMPAPIClient(config.fmp_api_key)
    
    # Test enrichment with Polygon data
    print(f"\nTesting Polygon data fetch for {test_stock['symbol']}...")
    
    stocks = [test_stock]
    enriched_stocks = api_client.enrich_with_polygon_data(
        stocks,
        config.polygon_api_key
    )
    
    # Display results
    stock = enriched_stocks[0]
    print(f"\nResults for {stock['symbol']}:")
    print(f"  Polygon Consensus: ${stock.get('polygon_consensus', 0):.0f}" if stock.get('polygon_consensus') else "  Polygon Consensus: N/A")
    print(f"  Analyst Count: {stock.get('polygon_analyst_count', 0)}")
    print(f"  7-Day Trend: {stock.get('polygon_trend_7d', 'N/A')}")
    print(f"  30-Day Trend: {stock.get('polygon_trend_30d', 'N/A')}")
    
    recent_actions = stock.get('polygon_recent_actions', [])
    if recent_actions:
        print(f"\n  Recent Actions:")
        for action in recent_actions[:3]:
            print(f"    {action.get('date')} - {action.get('firm')} - {action.get('rating')} - ${action.get('target', 0):.0f}")
    
    print("\n✓ Integration test complete!")

if __name__ == "__main__":
    test_polygon_integration()