#!/usr/bin/env python3
"""Test script to verify point-in-time consensus calculations."""

from config import Config
from polygon_client import PolygonClient
import json

def test_point_in_time():
    config = Config()
    
    with PolygonClient(config.polygon_api_key) as client:
        # Test with AAPL to see the difference
        data = client.get_price_targets_for_stock('AAPL')
        
        print("Point-in-Time Consensus for AAPL:")
        print("="*50)
        print(f"Current Consensus: ${data.get('current_consensus', 0):.0f}")
        print(f"Consensus 7 days ago: ${data.get('consensus_7d', 0):.0f}" if data.get('consensus_7d') else "Consensus 7 days ago: N/A")
        print(f"Consensus 30 days ago: ${data.get('consensus_30d', 0):.0f}" if data.get('consensus_30d') else "Consensus 30 days ago: N/A")
        print(f"Consensus 90 days ago: ${data.get('consensus_90d', 0):.0f}" if data.get('consensus_90d') else "Consensus 90 days ago: N/A")
        
        print("\nChanges:")
        if data.get('consensus_7d'):
            change_7d = data.get('current_consensus', 0) - data.get('consensus_7d', 0)
            print(f"  Last 7 days: {'↑' if change_7d > 0 else '↓'} ${abs(change_7d):.0f}")
        
        if data.get('consensus_30d'):
            change_30d = data.get('current_consensus', 0) - data.get('consensus_30d', 0)
            print(f"  Last 30 days: {'↑' if change_30d > 0 else '↓'} ${abs(change_30d):.0f}")
        
        if data.get('consensus_90d'):
            change_90d = data.get('current_consensus', 0) - data.get('consensus_90d', 0)
            print(f"  Last 90 days: {'↑' if change_90d > 0 else '↓'} ${abs(change_90d):.0f}")
        
        print(f"\nNumber of analysts: {data.get('analyst_count', 0)}")
        
        # Show some recent actions to verify
        print("\nRecent Actions (first 3):")
        for action in data.get('recent_actions', [])[:3]:
            print(f"  {action['date']} - {action['firm']}: ${action['target']:.0f}", end="")
            if action.get('target_prior'):
                print(f" (from ${action['target_prior']:.0f})")
            else:
                print()

if __name__ == "__main__":
    test_point_in_time()