#!/usr/bin/env python3
"""Test script to verify investment evaluation is included in emails."""

import json
from email_sender import EmailSender
from config import Config

def test_investment_evaluation_in_email():
    """Test that investment evaluation appears in email HTML."""
    
    # Create sample stock data with investment evaluation
    test_stock = {
        'symbol': 'TEST',
        'name': 'Test Company',
        'changesPercentage': 15.5,
        'mktCap': 1000000000,
        'description': 'A test company for testing purposes.',
        'growth_rate': '2025: 20%, 2026: 22%, 2027: 25%',
        'ps_ratio': 5.2,
        'competitive_score': 8,
        'competitive_reasoning': 'Strong competitive position',
        'market_growth_score': 7,
        'market_growth_reasoning': 'Growing market',
        'earnings_guidance': 'Q3 guidance raised by 10%',
        'analyst_price_targets': 'Average target: $150',
        'revenue_projection_2030': 'Expected to reach $5B by 2030',
        'investment_evaluation': 'This company shows strong growth potential with expanding market share and innovative product pipeline. Key investment thesis: 1) Leading position in growing market, 2) Strong financial metrics, 3) Experienced management team.',
        'gross_margin': 45.2,
        'rd_margin': 12.5,
        'ebitda_margin': 22.3,
        'net_income_margin': 15.8,
        'long_term_debt': 500000000,
        'cash_and_equivalents': 800000000,
        'pt_consensus_current': 150,
        'pt_consensus_7d': 148,
        'pt_consensus_30d': 145,
        'pt_consensus_180d': 140,
        'polygon_consensus': 152,
        'polygon_analyst_count': 12,
        'polygon_trend_7d': 'Stable',
        'polygon_trend_30d': 'Upward'
    }
    
    # Initialize email sender with dummy config
    email_sender = EmailSender(
        smtp_server='smtp.gmail.com',
        smtp_port=587,
        sender_email='test@example.com',
        sender_password='test'
    )
    
    # Generate email HTML
    html = email_sender.create_email_html([test_stock])
    
    # Check if investment evaluation section is present
    if 'Investment Evaluation' in html:
        print("✓ Investment Evaluation section found in email template")
    else:
        print("✗ Investment Evaluation section NOT found in email template")
        return False
    
    # Check if the actual content is included
    if 'strong growth potential' in html:
        print("✓ Investment evaluation content is displayed")
    else:
        print("✗ Investment evaluation content is NOT displayed")
        return False
    
    # Save HTML for inspection
    with open('test_email_with_investment_eval.html', 'w') as f:
        f.write(html)
    print("✓ Test email saved to test_email_with_investment_eval.html")
    
    return True

if __name__ == '__main__':
    print("Testing Investment Evaluation Integration")
    print("-" * 40)
    
    if test_investment_evaluation_in_email():
        print("\n✓ All tests passed! Investment evaluation is now included in emails.")
    else:
        print("\n✗ Test failed. Please check the implementation.")