#!/usr/bin/env python3
"""Test the enhanced investment evaluation formatting with markdown content."""

from email_sender import EmailSender

# Sample evaluation with markdown formatting (like what you showed in the screenshot)
sample_evaluation = """Total Score: 11/20

--

### Quick Screening Questions

- Technical Test: 10 world-class engineers could not fully replicate Rubrik in 6 months due to enterprise integration and scale, but could build a basic version. Pass, but not a deep tech moat.
- Business Test: Rubrik is likely achieving Rule of 40+ (41% growth + positive FCF margin). Pass.
- 10x Test: 10x in 10 years is possible but would require sustained high growth and margin expansion. Possible, but not certain.
- Moat Test: Becoming irrelevant would require a major shift in enterprise data security paradigms or a catastrophic breach. Moat is solid but not unassailable.
- Price Test: Valuation is ~16.7x sales for 41% growth (~0.4x growth rate multiple). Fair, not cheap.

--

### Red Flags

- Net losses remain high (~$524M TTM).
- No evidence of founder departure or customer concentration in available data.
- Competitive market with large incumbents (e.g., Veeam, Cohesity, Commvault).

### Green Flags

- Founder-led, high insider ownership (Bipul Sinha, CEO and co-founder).
- Leader in Gartner Magic Quadrant for six years.
- Positive free cash flow milestone.
- Expanding TAM with AI/data security focus.

--

### Reference Company Comparison

- Most similar to: Palantir and Databricks (mission-critical enterprise software, strong but not unassailable technical moat, high growth, fair-to-expensive valuation).

--

Summary:

Rubrik scores 11/20—placing it in the "Watch list" category. It is a high-quality, mission-critical enterprise software company with strong growth, improving cash flow, and a solid market position, but lacks deep technical breakthroughs and trades at a fair (not bargain) valuation."""

# Create email sender instance
email_sender = EmailSender("", 0, "", "")

# Format the evaluation
formatted_html = email_sender.format_investment_evaluation(sample_evaluation)

# Create a test HTML file to view the formatting
html_output = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Markdown Investment Evaluation Formatting Test</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            max-width: 700px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #f5f5f5;
        }}
        .original {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 13px;
            margin-bottom: 30px;
        }}
    </style>
</head>
<body>
    <h2>Original Text (with markdown):</h2>
    <div class="original">{sample_evaluation}</div>
    
    <h2>Formatted Output:</h2>
    {formatted_html}
</body>
</html>
"""

with open("test_markdown_formatting.html", "w") as f:
    f.write(html_output)

print("Test HTML file created: test_markdown_formatting.html")
print("Open this file in a browser to see the formatted output.")