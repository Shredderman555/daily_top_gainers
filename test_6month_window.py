#!/usr/bin/env python3
"""Test to verify 6-month window logic for consensus calculations."""

from config import Config
from polygon_client import PolygonClient
from datetime import datetime, timedelta

def test_6month_window():
    config = Config()
    
    with PolygonClient(config.polygon_api_key) as client:
        # Get raw ratings to analyze
        ratings = client.fetch_analyst_ratings('AAPL', limit=100)
        
        print("Testing 6-Month Window Logic for AAPL")
        print("="*60)
        
        # Manually count analysts by timeframe
        today = datetime.now()
        analysts_current = {}  # Within 180 days
        analysts_7d = {}       # Between 7-187 days ago
        analysts_30d = {}      # Between 30-210 days ago
        analysts_90d = {}      # Between 90-270 days ago
        
        for rating in ratings:
            pt = getattr(rating, 'price_target', None)
            if not pt or pt <= 0:
                continue
            
            # Get date
            if hasattr(rating, 'date'):
                try:
                    if isinstance(rating.date, str):
                        rating_date = datetime.strptime(rating.date[:10], "%Y-%m-%d")
                    else:
                        rating_date = rating.date
                except:
                    continue
            else:
                continue
            
            days_ago = (today - rating_date).days
            firm = getattr(rating, 'firm', 'Unknown')
            
            # Current consensus (0-180 days)
            if days_ago <= 180:
                if firm not in analysts_current or days_ago < analysts_current[firm]['days_ago']:
                    analysts_current[firm] = {'target': pt, 'days_ago': days_ago}
            
            # 7d ago consensus (7-187 days)
            if 7 <= days_ago <= 187:
                if firm not in analysts_7d or days_ago < analysts_7d[firm]['days_ago']:
                    analysts_7d[firm] = {'target': pt, 'days_ago': days_ago}
            
            # 30d ago consensus (30-210 days)
            if 30 <= days_ago <= 210:
                if firm not in analysts_30d or days_ago < analysts_30d[firm]['days_ago']:
                    analysts_30d[firm] = {'target': pt, 'days_ago': days_ago}
            
            # 90d ago consensus (90-270 days)
            if 90 <= days_ago <= 270:
                if firm not in analysts_90d or days_ago < analysts_90d[firm]['days_ago']:
                    analysts_90d[firm] = {'target': pt, 'days_ago': days_ago}
        
        # Calculate consensus for each period
        def calc_consensus(analyst_dict):
            if analyst_dict:
                targets = [data['target'] for data in analyst_dict.values()]
                return sum(targets) / len(targets), len(targets)
            return None, 0
        
        consensus_now, count_now = calc_consensus(analysts_current)
        consensus_7d, count_7d = calc_consensus(analysts_7d)
        consensus_30d, count_30d = calc_consensus(analysts_30d)
        consensus_90d, count_90d = calc_consensus(analysts_90d)
        
        print(f"PT Now (0-180 days):")
        print(f"  Consensus: ${consensus_now:.0f}" if consensus_now else "  Consensus: N/A")
        print(f"  Analyst Count: {count_now}")
        
        print(f"\nPT 7d ago (7-187 days):")
        print(f"  Consensus: ${consensus_7d:.0f}" if consensus_7d else "  Consensus: N/A")
        print(f"  Analyst Count: {count_7d}")
        
        print(f"\nPT 30d ago (30-210 days):")
        print(f"  Consensus: ${consensus_30d:.0f}" if consensus_30d else "  Consensus: N/A")
        print(f"  Analyst Count: {count_30d}")
        
        print(f"\nPT 90d ago (90-270 days):")
        print(f"  Consensus: ${consensus_90d:.0f}" if consensus_90d else "  Consensus: N/A")
        print(f"  Analyst Count: {count_90d}")
        
        # Get data from our function to compare
        data = client.get_price_targets_for_stock('AAPL')
        
        print("\n" + "="*60)
        print("Comparison with PolygonClient results:")
        print(f"PT Now: ${data.get('current_consensus', 0):.0f}" if data.get('current_consensus') else "PT Now: N/A")
        print(f"PT 7d: ${data.get('consensus_7d', 0):.0f}" if data.get('consensus_7d') else "PT 7d: N/A")
        print(f"PT 30d: ${data.get('consensus_30d', 0):.0f}" if data.get('consensus_30d') else "PT 30d: N/A")
        print(f"PT 90d: ${data.get('consensus_90d', 0):.0f}" if data.get('consensus_90d') else "PT 90d: N/A")

if __name__ == "__main__":
    test_6month_window()