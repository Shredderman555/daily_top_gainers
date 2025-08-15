#!/usr/bin/env python3
"""Test script to verify price target changes are shown correctly."""

from config import Config
from polygon_client import PolygonClient
from email_sender import EmailSender

def test_price_changes():
    config = Config()
    
    # Test with Polygon data
    with PolygonClient(config.polygon_api_key) as client:
        # Get data for a stock
        data = client.get_price_targets_for_stock('CRWD')
        
        print("Polygon Data for CRWD:")
        print(f"  Current Consensus: ${data.get('current_consensus', 0):.0f}")
        print(f"  Analyst Count: {data.get('analyst_count', 0)}")
        print(f"\nRecent Actions (first 5):")
        
        for i, action in enumerate(data.get('recent_actions', [])[:5], 1):
            target = action.get('target')
            target_prior = action.get('target_prior')
            
            print(f"\n  {i}. {action.get('date')} - {action.get('firm')}")
            print(f"     Rating: {action.get('rating')}")
            print(f"     Current Target: ${target:.0f}" if target else "     Current Target: N/A")
            print(f"     Previous Target: ${target_prior:.0f}" if target_prior else "     Previous Target: None")
            
            if target and target_prior and target != target_prior:
                if target > target_prior:
                    print(f"     Change: ↑ Raised from ${target_prior:.0f} to ${target:.0f}")
                else:
                    print(f"     Change: ↓ Lowered from ${target_prior:.0f} to ${target:.0f}")
    
    # Test email formatting
    print("\n" + "="*50)
    print("Testing Email Format:")
    
    test_stock = {
        'symbol': 'CRWD',
        'name': 'CrowdStrike Holdings',
        'changesPercentage': 5.2,
        'polygon_recent_actions': data.get('recent_actions', [])[:15]
    }
    
    sender = EmailSender('', 0, '', '')
    table_html = sender._create_price_target_table(test_stock['polygon_recent_actions'])
    
    if table_html:
        print("✓ Price target table generated successfully")
        print("  Table will show previous prices in format: $XXX (from $YYY)")
    else:
        print("✗ No table generated")

if __name__ == "__main__":
    test_price_changes()