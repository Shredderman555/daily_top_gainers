#!/usr/bin/env python3
"""Test the improved investment analysis formatting."""

from email_sender import EmailSender

# Sample evaluation text
sample_evaluation = """Rocket Lab scores 12/20 (Buy – good opportunity). It resembles Anduril in defense-driven systems.

Part A: Technical Excellence (0-8)

1) Fundamental Technical Innovation: 1/2
- Rocket Lab's core innovations are in reliable, high-cadence small launch (Electron)
- The firm demonstrates incremental but meaningful innovation

2) Technical Complexity & Barriers: 2/2
- Orbital launch, booster recovery/reuse across multiple domains
- Compounding advantages from vertical integration

3) Technical Risk & Systems Mastery: 1/2
- The Neutron medium-lift program adds genuine technical risk
- Demonstrated systems integration but not yet at SpaceX scale

4) Irreplaceable Technical Assets: 2/2
- Two launch sites (New Zealand and Virginia)
- Vertically integrated manufacturing capabilities

Subtotal Part A: 6/8

Part B: Business Power (0-12)

5) Revenue Quality & Durability: 1/2
- Space Systems now the larger revenue driver
- Multi-year defense contracts provide visibility

6) Market Position & Competitive Dynamics: 1/2
- Leading position in small-launch market
- Growing space systems business

7) Growth & Profitability Runway: 2/4
- 36% YoY revenue growth with margin expansion
- Path to profitability visible but not yet achieved

8) Capital Efficiency & Cash Generation: 1/2
- Still cash consumptive but improving metrics
- Heavy capex for Neutron development

9) Valuation Reality: 1/2
- Trading at reasonable multiples for growth
- Not in bubble territory

Subtotal Part B: 6/12

Total Score: 12/20

Quick Screening

- Technical Test: Could 10 engineers replicate in 6 months? No
- Business Test: Will they achieve Rule of 40? Not yet
- Growth Test: 30%+ growth for 5 years? Maybe
- Moat Test: Strong competitive position? Yes
- Price Test: Valuation < 2x growth? Yes

Red Flags (not scored)
- Continued losses through 2026
- Neutron schedule and execution risk
- Competitive pressure from SpaceX

Green Flags (not scored)
- Founder-led by Peter Beck
- Strong defense tailwinds
- Record quarterly revenue growth

Closest Resemblance
Most similar to Anduril with elements of SpaceX manufacturing ambition

Score Breakdown
Technical: 6/8, Business: 6/12, Total: 12/20

What would change the score upward
Neutron first flight success and customer uptake would add 2-3 points"""

def test_formatting():
    """Test the formatted display."""
    # Create email sender
    sender = EmailSender('smtp.gmail.com', 587, 'test@test.com', 'password')
    
    # Parse the evaluation
    eval_data = sender.parse_investment_evaluation(sample_evaluation)
    eval_data['full_text'] = sample_evaluation
    
    print(f"Parsed data:")
    print(f"  Score: {eval_data.get('total_score', 'N/A')}/20")
    print(f"  Category: {eval_data.get('category', 'N/A')}")
    
    # Format the HTML
    html = sender.format_investment_evaluation_html(eval_data)
    
    # Create full HTML page
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Investment Analysis Formatting Test</title>
        <meta charset="utf-8">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 0; background-color: #ffffff;">
        <div style="max-width: 700px; margin: 0 auto; padding: 40px 20px;">
            <h1 style="color: #333; margin-bottom: 30px;">Investment Analysis Formatting Test</h1>
            {html}
        </div>
    </body>
    </html>
    """
    
    # Save to file
    with open('test_formatted.html', 'w') as f:
        f.write(full_html)
    
    print("\nHTML saved to test_formatted.html")
    print("Opening in browser...")
    
    import subprocess
    subprocess.run(['open', 'test_formatted.html'])

if __name__ == "__main__":
    test_formatting()