#!/usr/bin/env python3
"""Generate deep research reports for stocks using Perplexity's sonar-deep-research model."""

import argparse
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional

from config import Config
from api_client import FMPAPIClient
from email_sender import EmailSender
from perplexity_client import PerplexityClient


logger = logging.getLogger(__name__)


def format_deep_research_prompt(company_name: str, symbol: str) -> str:
    """Format the deep research prompt for a company.
    
    Args:
        company_name: Full company name
        symbol: Stock symbol
        
    Returns:
        Formatted prompt for deep research
    """
    prompt = f"""Write a research report per the below for {company_name} ({symbol})

[Company name, [IRR over time horizon]]
What they do in 100 words or less

Market cap:
Rev gr cur yr:
PS current:
Gross margin:
Rev gr nxt yr: 
PS nxt yr:
R&D % of rev:
Rev gr nxt + 1: 
PS nxt +1 t:

Competitive advantage [x/10]

Competitive landscape
[100 words] Describe the market the company operates in, the key competitors, market share split, and competitors' strengths/weaknesses. 

Competitive advantage
[200 words] Describe the strength of the company's competitive advantage and why it exists. Do this in a simple way so readers unfamiliar to the industry can understand. Will this competitive advantage naturally grow/compound over time? How hard would it be to replicate what this company has done if you had unlimited funding? 

Market share change
[100 words] How do you see the market evolving over the next 5, 10 years? How fast will the market grow, and why will this company take market share, if it will? 

Valuation [expected IRR over xx years]

IRR buildup
[100 words] Provide your IRR building, stating the revenue and PS ratio now and the exit revenue and PS ratio at the end of your investment period. 

Revenue change
[100 words] What is revenue right now, why is it what it is today, and why do you think revenue will change the way it will over your investment horizon? 

PS ratio change
[200 words] What is the PS ratio right now, why is it what it is today, and why do you think the PS ratio will change the way it will over your investment horizon? 

Factors influencing exit PS
Growth runway
Competitive advantage strength
Margin potential 
Industry growth"""
    
    return prompt


def create_research_email_html(company_name: str, symbol: str, research_content: str, 
                              stock_data: Optional[Dict[str, Any]] = None) -> str:
    """Create HTML email for the deep research report.
    
    Args:
        company_name: Company name
        symbol: Stock symbol
        research_content: The research report content
        stock_data: Optional stock data for context
        
    Returns:
        HTML string for email body
    """
    # Get current gain info if available
    gain_info = ""
    if stock_data:
        change_percent = stock_data.get('changesPercentage', 'N/A')
        if isinstance(change_percent, str):
            change_percent = change_percent.replace('%', '')
        gain_info = f" | Today's Gain: {change_percent}%"
    
    html = f"""
    <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 0; background-color: #ffffff;">
            <div style="max-width: 800px; margin: 0 auto; padding: 40px 20px;">
                <h1 style="color: #000; text-align: center; margin-bottom: 10px; font-weight: 600;">
                    Deep Research Report
                </h1>
                <h2 style="color: #666; text-align: center; margin-bottom: 40px; font-weight: 500;">
                    {company_name} ({symbol}){gain_info}
                </h2>
                
                <div style="background-color: #f5f5f5; border-radius: 16px; padding: 30px; margin-bottom: 20px;">
                    <div style="white-space: pre-wrap; color: #333; font-size: 15px; line-height: 1.6;">
{research_content}
                    </div>
                </div>
                
                <p style="color: #999; font-size: 14px; text-align: center; margin-top: 40px;">
                    Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
                </p>
            </div>
        </body>
    </html>
    """
    
    return html


def generate_deep_research(symbol: str, company_name: Optional[str] = None) -> int:
    """Generate and send a deep research report for a stock.
    
    Args:
        symbol: Stock symbol
        company_name: Optional company name (will fetch if not provided)
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Generating deep research report for {symbol}")
    
    try:
        # Load configuration
        config = Config()
        
        # Get company data if name not provided
        stock_data = None
        if not company_name:
            logger.info("Fetching company profile...")
            with FMPAPIClient(config.fmp_api_key) as api:
                profile = api.get_company_profile(symbol)
                if profile and 'companyName' in profile:
                    company_name = profile['companyName']
                    stock_data = {'symbol': symbol, 'name': company_name}
                    logger.info(f"Found company: {company_name}")
                else:
                    logger.error(f"Could not find company profile for {symbol}")
                    return 1
        
        # Generate deep research using Perplexity
        logger.info("Generating deep research report...")
        with PerplexityClient(config.perplexity_api_key) as client:
            prompt = format_deep_research_prompt(company_name, symbol)
            
            # Call the deep research API
            research_content = client.get_deep_research(prompt)
            
            if not research_content:
                logger.error("Failed to generate research report")
                return 1
            
            logger.info("Research report generated successfully")
        
        # Create and send email
        logger.info(f"Sending research report to {config.email_recipient}")
        email_html = create_research_email_html(company_name, symbol, research_content, stock_data)
        
        email_sender = EmailSender(
            smtp_server=config.smtp_server,
            smtp_port=config.smtp_port,
            sender_email=config.email_sender,
            sender_password=config.email_password
        )
        
        # Create email with custom subject
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart('alternative')
        msg['From'] = config.email_sender
        msg['To'] = config.email_recipient
        msg['Subject'] = f"Deep Research: {company_name} ({symbol})"
        
        html_part = MIMEText(email_html, 'html')
        msg.attach(html_part)
        
        # Send using SMTP
        import smtplib
        with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
            server.starttls()
            server.login(config.email_sender, config.email_password)
            server.send_message(msg)
        
        logger.info("Research report sent successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Error generating research report: {e}")
        return 1


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Generate deep research report for a stock')
    parser.add_argument('symbol', help='Stock symbol (e.g., AAPL, MSFT)')
    parser.add_argument('--name', help='Company name (optional, will fetch if not provided)')
    
    args = parser.parse_args()
    
    exit_code = generate_deep_research(args.symbol, args.name)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()