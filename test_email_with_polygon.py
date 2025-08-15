#!/usr/bin/env python3
"""Test script to preview email with Polygon data."""

from email_sender import EmailSender
from config import Config

def test_email_with_polygon():
    """Test email generation with Polygon data."""
    
    # Mock stock data with Polygon fields
    test_stock = {
        'symbol': 'CRWD',
        'name': 'CrowdStrike Holdings Inc.',
        'changesPercentage': 12.5,
        'mktCap': 85000000000,
        'description': 'CrowdStrike provides cloud-delivered endpoint protection.',
        'growth_rate': '2025: 25%, 2026: 23%, 2027: 21%',
        'ps_ratio': '15.2x',
        'earnings_guidance': 'Q3: Beat by 8%, Full year raised',
        'analyst_price_targets': '5 upgrades in last 30 days',
        'revenue_projection_2030': '15-20% annual growth',
        'competitive_score': 8,
        'market_growth_score': 9,
        'gross_margin': 75.3,
        'rd_margin': 18.2,
        'ebitda_margin': 22.5,
        'net_income_margin': 15.1,
        'long_term_debt': 750000000,
        'cash_and_equivalents': 3200000000,
        'pt_consensus_current': 380,
        'pt_consensus_7d': 375,
        'pt_consensus_30d': 365,
        'pt_consensus_180d': 350,
        # Polygon data
        'polygon_consensus': 385.5,
        'polygon_consensus_7d': 382.0,
        'polygon_consensus_30d': 370.0,
        'polygon_trend_7d': '↑ 0.9%',
        'polygon_trend_30d': '↑ 4.2%',
        'polygon_analyst_count': 28,
        'polygon_recent_actions': [
            {
                'date': 'Aug 14',
                'firm': 'Morgan Stanley',
                'action': 'Upgrades',
                'rating': 'Overweight',
                'target': 400,
                'target_prior': 375
            },
            {
                'date': 'Aug 12',
                'firm': 'Goldman Sachs',
                'action': 'Maintains',
                'rating': 'Buy',
                'target': 390,
                'target_prior': 390
            },
            {
                'date': 'Aug 10',
                'firm': 'Jefferies',
                'action': 'Initiates',
                'rating': 'Buy',
                'target': 385,
                'target_prior': None
            }
        ]
    }
    
    # Create email sender
    config = Config()
    email_sender = EmailSender(
        config.smtp_server,
        config.smtp_port,
        config.email_sender,
        config.email_password
    )
    
    # Generate HTML
    html = email_sender.create_email_html([test_stock], put_call_ratio="0.85")
    
    # Save to file for preview
    with open('test_email_polygon_preview.html', 'w') as f:
        f.write(html)
    
    print("✓ Email preview generated: test_email_polygon_preview.html")
    print("\nPolygon data included:")
    print(f"  - Consensus Target: ${test_stock['polygon_consensus']:.1f}")
    print(f"  - Analyst Count: {test_stock['polygon_analyst_count']}")
    print(f"  - 7-Day Trend: {test_stock['polygon_trend_7d']}")
    print(f"  - 30-Day Trend: {test_stock['polygon_trend_30d']}")
    print(f"  - Recent Actions: {len(test_stock['polygon_recent_actions'])} displayed")

if __name__ == "__main__":
    test_email_with_polygon()