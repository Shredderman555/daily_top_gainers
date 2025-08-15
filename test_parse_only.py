#!/usr/bin/env python3
"""Test parsing of investment evaluation without API calls."""

from email_sender import EmailSender

# Sample evaluation text from new format
sample_evaluation = """Company Similarity Score: 80/100 (closest public comp mix: SpaceX for vertical integration/launch cadence, plus L3Harris/Maxar for defense space systems and payloads).

PART A: TECHNICAL EXCELLENCE (28/30) – 30%

1) Fundamental Technical Innovation: 6/8
- Rocket Lab has developed proprietary small-launch and space-systems tech

2) Technical Complexity & Barriers: 7/8
- Very difficult to replicate their full stack

3) Technical Risk & Systems Mastery: 7/7
- Pushing boundaries of small launch economics

4) Irreplaceable Technical Assets: 8/7
- World-class team and infrastructure

Subtotal Part A: 28/30

PART B: GROWTH & PROFITABILITY RUNWAY (24/30) – 30%
Strong growth potential with expanding markets

PART C: BUSINESS QUALITY (18/30) – 30%
Solid business fundamentals

PART D: VALUATION REALITY (0/10) – 10%
Currently expensive at 50x sales

TOTAL SCORE: 70/100
====================

SCORING GUIDE:
70-84: Strong buy - high conviction position

Quick Screening Questions:
- Technical Test: Could 10 engineers replicate in 6 months? No
- Business Test: Rule of 40+? Yes
- Growth Test: 10x in 10 years? Yes
- Moat Test: What would make irrelevant? Hard
- Price Test: Valuation < 2x growth? No"""

def test_parsing():
    """Test the parsing function."""
    email_sender = EmailSender("", 0, "", "")
    
    # Parse the evaluation
    eval_data = email_sender.parse_investment_evaluation(sample_evaluation)
    
    print("Parsed evaluation data:")
    print(f"  - Total Score: {eval_data.get('total_score', 'NOT FOUND')}/100")
    print(f"  - Category: {eval_data.get('category', 'NOT FOUND')}")
    print(f"  - Comparison: {eval_data.get('comparison', 'NOT FOUND')}")
    print(f"  - Keys found: {list(eval_data.keys())}")
    
    # Add full text for HTML generation
    eval_data['full_text'] = sample_evaluation
    
    # Generate HTML
    html = email_sender.format_investment_evaluation_html(eval_data)
    
    if html:
        print("\n✓ HTML generated successfully")
        print(f"  - HTML length: {len(html)} chars")
        
        # Check for key elements
        if '70/100' in html:
            print("  - Score display: ✓")
        else:
            print("  - Score display: ✗")
            
        if 'Strong Buy' in html:
            print("  - Category display: ✓")
        else:
            print("  - Category display: ✗")
            
        if 'Detailed Investment Analysis' in html:
            print("  - Detailed analysis section: ✓")
        else:
            print("  - Detailed analysis section: ✗")
        
        # Save to file
        with open('test_parse_output.html', 'w') as f:
            f.write(f"""<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
    <div style="max-width: 700px; margin: 0 auto; padding: 40px 20px;">
        {html}
    </div>
</body>
</html>""")
        print("\n✓ HTML saved to test_parse_output.html")
    else:
        print("\n✗ No HTML generated")

if __name__ == "__main__":
    test_parsing()