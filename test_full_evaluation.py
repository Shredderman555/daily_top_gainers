#!/usr/bin/env python3
"""Test full investment evaluation display."""

from perplexity_client import PerplexityClient
from email_sender import EmailSender
from config import Config

def test_full_evaluation():
    """Test that full evaluation is properly formatted."""
    config = Config()
    client = PerplexityClient(config.perplexity_api_key)
    email_sender = EmailSender("", 0, "", "")
    
    print("Fetching evaluation for Meta...")
    evaluation = client.get_investment_evaluation('Meta')
    
    if evaluation:
        print(f"✓ Got evaluation ({len(evaluation)} chars)")
        
        # Parse the evaluation
        eval_data = email_sender.parse_investment_evaluation(evaluation)
        eval_data['full_text'] = evaluation
        
        print(f"✓ Parsed score: {eval_data.get('total_score', 'N/A')}/100")
        
        # Generate HTML
        html = email_sender.format_investment_evaluation_html(eval_data)
        
        # Check for key sections
        checks = {
            'Score display': '/100' in html,
            'Detailed Analysis header': 'Detailed Investment Analysis' in html,
            'PART A section': 'PART A' in html.upper(),
            'PART B section': 'PART B' in html.upper(),
            'PART C section': 'PART C' in html.upper(),
            'PART D section': 'PART D' in html.upper(),
            'Numbered items': '1)' in html or '1.' in html,
            'Score breakdowns': '/8' in html or '/10' in html or '/30' in html,
        }
        
        print("\nSection checks:")
        for check, result in checks.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check}")
        
        # Save full HTML
        with open('test_meta_evaluation.html', 'w') as f:
            f.write(f"""<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
    </style>
</head>
<body>
    <h1>Meta Investment Evaluation Test</h1>
    {html}
</body>
</html>""")
        
        print(f"\n✓ Full HTML saved to test_meta_evaluation.html")
        print(f"  Total HTML size: {len(html)} chars")
        
        # Check if detailed analysis is actually being formatted
        if len(html) > 5000:
            print("  ✓ HTML contains substantial content")
        else:
            print("  ✗ HTML seems too short - detailed analysis may be missing")
            
    else:
        print("✗ No evaluation returned")

if __name__ == "__main__":
    test_full_evaluation()