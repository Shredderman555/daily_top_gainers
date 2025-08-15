#!/usr/bin/env python3
"""Test the investment evaluation formatting."""

from email_sender import EmailSender

# Sample investment evaluation text similar to what the AI generates
sample_evaluation = """Technical Complexity & Barriers (Score: 2/4):
- Reddit's technical moat is moderate compared to technical infrastructure companies
- The platform's scale and community engagement are assets that money alone cannot buy
- Natural language processing for content moderation is advanced but not irreplaceable

Revenue Quality & Durability (Score: 1/3):
- Reddit's advertising business lacks the precision targeting of Meta/Google
- User-generated content provides scale but monetization per user lags peers
- Revenue concentration in advertising makes it vulnerable to economic cycles

Market Saturation & Expansion (Score: 3/4):
- Reddit has significant untapped international growth potential
- The platform can expand into new verticals and use cases
- Community-driven content creation scales naturally with user growth

This stock shows mixed signals with strong community engagement but monetization challenges."""

# Create email sender instance
email_sender = EmailSender("", 0, "", "")

# Format the evaluation
formatted_html = email_sender.format_investment_evaluation(sample_evaluation)

# Create a test HTML file to view the formatting
html_output = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Investment Evaluation Formatting Test</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            max-width: 700px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #f5f5f5;
        }}
    </style>
</head>
<body>
    <h2>Original Text:</h2>
    <pre style="background: white; padding: 15px; border-radius: 8px; white-space: pre-wrap;">{sample_evaluation}</pre>
    
    <h2 style="margin-top: 40px;">Formatted Output:</h2>
    {formatted_html}
</body>
</html>
"""

with open("test_formatting_output.html", "w") as f:
    f.write(html_output)

print("Test HTML file created: test_formatting_output.html")
print("Open this file in a browser to see the formatted output.")