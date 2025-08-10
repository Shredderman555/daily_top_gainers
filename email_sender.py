"""Email functionality for sending stock alerts."""

import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional


logger = logging.getLogger(__name__)


class EmailSender:
    """Handles sending stock alert emails via SMTP."""
    
    def __init__(self, smtp_server: str, smtp_port: int, 
                 sender_email: str, sender_password: str):
        """Initialize email sender with SMTP configuration.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            sender_email: Sender email address
            sender_password: Sender email password/app password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def format_market_cap(self, market_cap: Optional[float]) -> str:
        """Format market cap value for display.
        
        Args:
            market_cap: Market cap value in dollars
            
        Returns:
            Formatted string (e.g., $1.2T, $450M, $25.7B)
        """
        if market_cap is None:
            return "N/A"
        
        if market_cap >= 1_000_000_000_000:  # Trillion
            return f"${market_cap / 1_000_000_000_000:.1f}T"
        elif market_cap >= 1_000_000_000:  # Billion
            return f"${market_cap / 1_000_000_000:.1f}B"
        elif market_cap >= 1_000_000:  # Million
            return f"${market_cap / 1_000_000:.1f}M"
        else:
            return f"${market_cap:,.0f}"
    
    def create_email_html(self, stocks: List[Dict[str, Any]]) -> str:
        """Create HTML content for the email.
        
        Args:
            stocks: List of stock dictionaries with gainer information
            
        Returns:
            HTML string for email body
        """
        if not stocks:
            return """
            <html>
                <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 0; background-color: #ffffff;">
                    <div style="max-width: 700px; margin: 0 auto; padding: 40px 20px;">
                        <h1 style="color: #000; text-align: center; font-weight: 600;">Stock Alert: No 10%+ Gainers Today</h1>
                        <p style="color: #666; text-align: center; font-size: 16px; margin-top: 20px;">No stocks gained 10% or more today.</p>
                        <p style="color: #999; font-size: 14px; text-align: center; margin-top: 40px;">
                            Generated on {date}
                        </p>
                    </div>
                </body>
            </html>
            """.format(date=datetime.now().strftime("%B %d, %Y at %I:%M %p"))
        
        stock_cards = []
        for i, stock in enumerate(stocks):
            symbol = stock.get('symbol', 'N/A')
            name = stock.get('name', 'N/A')
            change_percent = stock.get('changesPercentage', 'N/A')
            market_cap = stock.get('mktCap')
            ps_ratio = stock.get('ps_ratio')
            description = stock.get('description', '')
            growth_rate = stock.get('growth_rate', '')
            
            # Clean up percentage display
            if isinstance(change_percent, str):
                change_percent = change_percent.replace('%', '')
            
            try:
                change_float = float(change_percent)
                change_display = f"{change_float:.0f}%"
            except:
                change_display = change_percent
            
            # Format market cap
            market_cap_display = self.format_market_cap(market_cap)
            
            # Format P/S ratio
            if ps_ratio is not None:
                try:
                    ps_ratio_display = f"{ps_ratio:.0f}x"
                except (ValueError, TypeError):
                    ps_ratio_display = "N/A"
            else:
                ps_ratio_display = "N/A"
            
            # Handle missing description
            description_display = description if description else "Description unavailable"
            
            # Parse growth rates by year for individual variables
            growth_25 = "N/A"
            growth_26 = "N/A"
            growth_27 = "N/A"
            
            if growth_rate:
                # Try to parse format like "2025: 20%, 2026: 21%, 2027: 22%"
                import re
                year_pattern = r'(\d{4}):\s*([\d.]+(?:-[\d.]+)?)%'
                matches = re.findall(year_pattern, growth_rate)
                if matches:
                    growth_dict = {year: rate for year, rate in matches}
                    growth_25 = f"{growth_dict.get('2025', 'N/A')}%" if growth_dict.get('2025') else "N/A"
                    growth_26 = f"{growth_dict.get('2026', 'N/A')}%" if growth_dict.get('2026') else "N/A"
                    growth_27 = f"{growth_dict.get('2027', 'N/A')}%" if growth_dict.get('2027') else "N/A"
            
            # Get competitive and growth analysis data
            competitive_score = stock.get('competitive_score', None)
            competitive_reasoning = stock.get('competitive_reasoning', '')
            market_growth_score = stock.get('market_growth_score', None)
            market_growth_reasoning = stock.get('market_growth_reasoning', '')
            
            # Get earnings guidance
            earnings_guidance = stock.get('earnings_guidance', None)
            
            # Get analyst price targets
            analyst_price_targets = stock.get('analyst_price_targets', None)
            
            # Get revenue projection for 2030
            revenue_projection_2030 = stock.get('revenue_projection_2030', None)
            
            # Get financial metrics
            gross_margin = stock.get('gross_margin', None)
            rd_margin = stock.get('rd_margin', None)
            ebitda_margin = stock.get('ebitda_margin', None)
            net_income_margin = stock.get('net_income_margin', None)
            long_term_debt = stock.get('long_term_debt', None)
            cash_and_equivalents = stock.get('cash_and_equivalents', None)
            
            # Format financial values
            def format_margin(margin):
                if margin is not None:
                    if margin < 0:
                        return f'<span style="color: #cc0000;">{margin:.1f}%</span>'
                    return f"{margin:.1f}%"
                return "N/A"
            
            def format_billions(value):
                if value is not None:
                    if value >= 1_000_000_000:
                        return f"${value / 1_000_000_000:.1f}B"
                    elif value >= 1_000_000:
                        return f"${value / 1_000_000:.1f}M"
                    else:
                        return f"${value:,.0f}"
                return "N/A"
            
            # Format scores
            competitive_display = f"{competitive_score}/10" if competitive_score is not None else "N/A"
            growth_score_display = f"{market_growth_score}/10" if market_growth_score is not None else "N/A"
            
            stock_cards.append(f"""
                <div style="background-color: #f5f5f5; border-radius: 16px; padding: 24px; margin-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
                    <!-- Header with company name and symbol -->
                    <div style="margin-bottom: 16px;">
                        <h2 style="margin: 0; font-size: 24px; font-weight: 600; color: #000;">
                            {name} &nbsp;&nbsp;<span style="font-weight: 700;">{symbol}</span>
                        </h2>
                    </div>
                    
                    <!-- Description -->
                    <p style="margin: 0 0 20px 0; color: #333; font-size: 16px; line-height: 1.5;">
                        {description_display}
                    </p>
                    
                    <!-- Combined Key Metrics Section -->
                    <div style="background-color: #fff; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                        <p style="margin: 0 0 12px 0; color: #333; font-size: 16px; font-weight: 600;">
                            Key Metrics
                        </p>
                        <table style="width: 100%; border-collapse: collapse;">
                            <!-- First row: Growth rates and valuation -->
                            <tr>
                                <td style="padding: 6px 0; color: #666; font-size: 14px; width: 20%;">Rev gr 25:</td>
                                <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500; width: 13%;">{growth_25}</td>
                                <td style="padding: 6px 0; color: #666; font-size: 14px; width: 20%;">PS ratio:</td>
                                <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500; width: 13%;">{ps_ratio_display}</td>
                                <td style="padding: 6px 0; color: #666; font-size: 14px; width: 20%;">Gross Margin:</td>
                                <td style="padding: 6px 0; color: #333; font-size: 14px; font-weight: 500; width: 14%;">{format_margin(gross_margin)}</td>
                            </tr>
                            <!-- Second row -->
                            <tr>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">Rev gr 26:</td>
                                <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500;">{growth_26}</td>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">Mkt cap:</td>
                                <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500;">{market_cap_display}</td>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">R&D Margin:</td>
                                <td style="padding: 6px 0; color: #333; font-size: 14px; font-weight: 500;">{format_margin(rd_margin)}</td>
                            </tr>
                            <!-- Third row -->
                            <tr>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">Rev gr 27:</td>
                                <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500;">{growth_27}</td>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">Today's gain:</td>
                                <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500;">{change_display}</td>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">EBITDA Margin:</td>
                                <td style="padding: 6px 0; color: #333; font-size: 14px; font-weight: 500;">{format_margin(ebitda_margin)}</td>
                            </tr>
                            <!-- Fourth row -->
                            <tr>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">Debt:</td>
                                <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500;">{format_billions(long_term_debt)}</td>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">Cash:</td>
                                <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500;">{format_billions(cash_and_equivalents)}</td>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">Net Margin:</td>
                                <td style="padding: 6px 0; color: #333; font-size: 14px; font-weight: 500;">{format_margin(net_income_margin)}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <!-- Competitive Advantage -->
                    <p style="margin: 0 0 8px 0; color: #333; font-size: 16px; font-weight: 600;">
                        Competitive Advantage: {competitive_display}
                    </p>
                    <p style="margin: 0 0 16px 0; color: #333; font-size: 16px; line-height: 1.5;">
                        {competitive_reasoning if competitive_reasoning else "Analysis not available"}
                    </p>
                    
                    <!-- Market Growth -->
                    <p style="margin: 0 0 8px 0; color: #333; font-size: 16px; font-weight: 600;">
                        Market Growth: {growth_score_display}
                    </p>
                    <p style="margin: 0 0 16px 0; color: #333; font-size: 16px; line-height: 1.5;">
                        {market_growth_reasoning if market_growth_reasoning else "Analysis not available"}
                    </p>
                    
                    <!-- Earnings Guidance -->
                    <p style="margin: 0 0 8px 0; color: #333; font-size: 16px; font-weight: 600;">
                        Earnings Guidance Update
                    </p>
                    <p style="margin: 0 0 16px 0; color: #333; font-size: 16px; line-height: 1.5;">
                        {earnings_guidance if earnings_guidance else "No recent earnings guidance updates available"}
                    </p>
                    
                    <!-- Analyst Price Targets -->
                    <p style="margin: 0 0 8px 0; color: #333; font-size: 16px; font-weight: 600;">
                        Analyst Price Target Changes
                    </p>
                    <p style="margin: 0 0 16px 0; color: #333; font-size: 16px; line-height: 1.5;">
                        {analyst_price_targets if analyst_price_targets else "No recent analyst price target changes available"}
                    </p>
                    
                    <!-- Revenue Growth Projection for 2030 -->
                    <p style="margin: 0 0 8px 0; color: #333; font-size: 16px; font-weight: 600;">
                        Revenue Growth Projection for 2030
                    </p>
                    <p style="margin: 0 0 20px 0; color: #333; font-size: 16px; line-height: 1.5;">
                        {revenue_projection_2030 if revenue_projection_2030 else "Revenue growth projection analysis not available"}
                    </p>
                    
                    <!-- Deep Research Button -->
                    <div style="text-align: center; margin-top: 24px;">
                        <a href="https://shredderman555.github.io/daily_top_gainers/trigger.html?symbol={symbol}&name={name.replace(' ', '%20')}&token=research2024" 
                           style="display: inline-block; background-color: #0066cc; color: white; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-size: 16px; font-weight: 500;"
                           target="_blank">
                            Generate Deep Research Report
                        </a>
                        <p style="margin: 8px 0 0 0; color: #999; font-size: 12px;">
                            Click for in-depth analysis (delivered via email in 2-5 minutes)
                        </p>
                    </div>
                </div>
            """)
        
        html = f"""
        <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 0; background-color: #ffffff;">
                <div style="max-width: 700px; margin: 0 auto; padding: 40px 20px;">
                    <h1 style="color: #000; text-align: center; margin-bottom: 40px; font-weight: 600;">Stock Alert: {len(stocks)} Stocks Gained 10%+ Today</h1>
                    
                    <!-- Stock cards -->
                    {''.join(stock_cards)}
                    
                    <p style="color: #999; font-size: 14px; text-align: center; margin-top: 40px;">
                        Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
                    </p>
                </div>
            </body>
        </html>
        """
        
        return html
    
    def send_email(self, recipient: str, stocks: List[Dict[str, Any]], 
                   dry_run: bool = False) -> bool:
        """Send stock alert email.
        
        Args:
            recipient: Recipient email address
            stocks: List of stock dictionaries
            dry_run: If True, preview email without sending
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = recipient
            
            # Set subject based on number of gainers
            if stocks:
                msg['Subject'] = f"Stock Alert: {len(stocks)} stocks gained 10%+ today"
            else:
                msg['Subject'] = "Stock Alert: No 10%+ gainers today"
            
            # Create HTML content
            html_content = self.create_email_html(stocks)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            if dry_run:
                logger.info("DRY RUN MODE - Email preview:")
                logger.info(f"To: {recipient}")
                logger.info(f"Subject: {msg['Subject']}")
                logger.info(f"Found {len(stocks)} stocks with 10%+ gains")
                if stocks:
                    for stock in stocks[:5]:  # Show first 5 stocks
                        symbol = stock.get('symbol', 'N/A')
                        change = stock.get('changesPercentage', 'N/A')
                        logger.info(f"  - {symbol}: {change}")
                    if len(stocks) > 5:
                        logger.info(f"  ... and {len(stocks) - 5} more")
                return True
            
            # Send email
            logger.debug(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.debug(f"Email sent successfully to {recipient}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check email and password.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False