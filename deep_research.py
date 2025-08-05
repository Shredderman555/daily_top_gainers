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


def format_research_content(content: str) -> str:
    """Format research content from markdown-style to HTML.
    
    Args:
        content: Raw research content with markdown formatting
        
    Returns:
        HTML formatted content
    """
    import re
    
    # Remove citation brackets [1], [2], etc.
    content = re.sub(r'\[\d+\]', '', content)
    
    # Convert **text** to <strong>text</strong>
    content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', content)
    
    # Split into sections based on common headers
    sections = []
    current_section = []
    
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Check if this line is a section header
        is_section_header = any(header in line.lower() for header in [
            'competitive advantage', 'competitive landscape', 'market share', 
            'valuation', 'irr buildup', 'revenue change', 'ps ratio change',
            'factors influencing', 'what they do'
        ])
        
        if is_section_header and current_section:
            # Process the previous section
            sections.append(format_section(current_section))
            current_section = [line]
        else:
            current_section.append(line)
    
    # Don't forget the last section
    if current_section:
        sections.append(format_section(current_section))
    
    return '\n'.join(sections)


def format_section(lines: list) -> str:
    """Format a section of content."""
    if not lines:
        return ''
    
    formatted = []
    first_line = lines[0].strip()
    
    # Check if it's a header
    if any(header in first_line.lower() for header in [
        'competitive advantage', 'competitive landscape', 'market share', 
        'valuation', 'irr buildup', 'revenue change', 'ps ratio change'
    ]):
        # Make it a styled header
        formatted.append(f'<h3 style="color: #0066cc; margin: 30px 0 15px 0; font-size: 20px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px;">{first_line}</h3>')
        remaining_lines = lines[1:]
    else:
        remaining_lines = lines
    
    # Process remaining lines
    for line in remaining_lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if it's a metric line
        if ':' in line and any(metric in line.lower() for metric in [
            'market cap', 'rev gr', 'ps', 'gross margin', 'r&d', 'irr'
        ]):
            parts = line.split(':', 1)
            if len(parts) == 2:
                label, value = parts
                formatted.append(f'''
                    <div style="background-color: #f8f9fa; padding: 12px 16px; margin: 8px 0; border-radius: 8px; display: flex; justify-content: space-between;">
                        <strong style="color: #333;">{label.strip()}:</strong>
                        <span style="color: #0066cc; font-weight: 500;">{value.strip()}</span>
                    </div>
                ''')
            else:
                formatted.append(f'<p style="margin: 12px 0; line-height: 1.7; color: #444;">{line}</p>')
        # Check if it's an IRR or score line
        elif any(keyword in line.lower() for keyword in ['irr over', 'score:', '/10']):
            formatted.append(f'<div style="background-color: #e8f4f8; padding: 16px; margin: 16px 0; border-radius: 8px; border-left: 4px solid #0066cc;"><strong style="font-size: 18px; color: #0066cc;">{line}</strong></div>')
        else:
            formatted.append(f'<p style="margin: 12px 0; line-height: 1.7; color: #444;">{line}</p>')
    
    return ''.join(formatted)


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
    
    # Format the research content
    formatted_content = format_research_content(research_content)
    
    html = f"""
    <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f7fa;">
            <div style="max-width: 800px; margin: 0 auto; padding: 40px 20px;">
                <!-- Header -->
                <div style="background-color: white; border-radius: 16px; padding: 30px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h1 style="color: #1a1a1a; text-align: center; margin-bottom: 10px; font-weight: 600; font-size: 32px;">
                        Deep Research Report
                    </h1>
                    <h2 style="color: #0066cc; text-align: center; margin-bottom: 0; font-weight: 500; font-size: 24px;">
                        {company_name} ({symbol})
                    </h2>
                    {f'<p style="color: #666; text-align: center; margin-top: 10px; font-size: 16px;">{gain_info[3:]}</p>' if gain_info else ''}
                </div>
                
                <!-- Main Content -->
                <div style="background-color: white; border-radius: 16px; padding: 40px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    {formatted_content}
                </div>
                
                <!-- Footer -->
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
        email_sent = False
        try:
            with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                server.starttls()
                server.login(config.email_sender, config.email_password)
                server.send_message(msg)
                email_sent = True
                logger.info("Research report sent successfully!")
        except Exception as smtp_error:
            logger.error(f"Failed to send email: {smtp_error}")
            return 1
        
        # If email was sent successfully, return success even if there are cleanup errors
        if email_sent:
            logger.info(f"Deep research report for {symbol} completed and emailed successfully")
            return 0
        else:
            return 1
        
    except ConnectionResetError as e:
        # Connection reset errors during cleanup are not critical if email was sent
        logger.warning(f"Connection reset during cleanup (non-critical): {e}")
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