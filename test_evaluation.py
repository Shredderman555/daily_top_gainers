#!/usr/bin/env python3
"""Test script to check investment evaluation display."""

import os
from dotenv import load_dotenv
from api_client import FMPAPIClient
from email_sender import EmailSender
from config import Config

# Load environment variables
load_dotenv()

def test_investment_evaluation():
    """Test investment evaluation for a single stock."""
    config = Config()
    api_client = FMPAPIClient(config.fmp_api_key)
    email_sender = EmailSender(
        config.smtp_server,
        config.smtp_port,
        config.email_sender,
        config.email_password
    )
    
    # Create a test stock entry
    test_stock = {
        'symbol': 'RKLB',
        'name': 'Rocket Lab USA, Inc.',
        'changesPercentage': '15%',
        'mktCap': 5000000000,
        'ps_ratio': 25.0,
        'description': 'Rocket Lab is a space company that provides launch services and spacecraft components.'
    }
    
    print("Fetching investment evaluation for RKLB...")
    
    # Get investment evaluation
    from perplexity_client import PerplexityClient
    perplexity_client = PerplexityClient(config.perplexity_api_key)
    evaluation = perplexity_client.get_investment_evaluation('Rocket Lab')
    
    if evaluation:
        print(f"✓ Evaluation fetched ({len(evaluation)} chars)")
        test_stock['investment_evaluation'] = evaluation
        
        # Show first part of evaluation
        print("\nFirst 500 chars of evaluation:")
        print(evaluation[:500])
        
        # Parse the evaluation
        eval_data = email_sender.parse_investment_evaluation(evaluation)
        
        print(f"\n✓ Parsed evaluation:")
        print(f"  - Total Score: {eval_data.get('total_score', 'N/A')}/20")
        print(f"  - Category: {eval_data.get('category', 'N/A')}")
        print(f"  - Has full_text: {'Yes' if 'full_text' in eval_data else 'No'}")
        print(f"  - Keys in eval_data: {list(eval_data.keys())}")
        
        # Add full text to eval_data
        eval_data['full_text'] = evaluation
        
        # Generate HTML for the evaluation
        html = email_sender.format_investment_evaluation_html(eval_data)
        
        # Check if full text section is in HTML
        if '📊 Detailed Investment Analysis' in html:
            print("\n✓ Full evaluation section found in HTML")
        else:
            print("\n✗ Full evaluation section NOT found in HTML")
        
        # Save HTML to file for inspection
        with open('test_evaluation.html', 'w') as f:
            f.write(f"""
            <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 0; background-color: #ffffff;">
                <div style="max-width: 700px; margin: 0 auto; padding: 40px 20px;">
                    <h2>Investment Evaluation Test for RKLB</h2>
                    {html}
                </div>
            </body>
            </html>
            """)
        print("\n✓ HTML saved to test_evaluation.html")
        print("  Open this file in a browser to see the formatting")
        
    else:
        print("✗ No evaluation returned")

if __name__ == "__main__":
    test_investment_evaluation()