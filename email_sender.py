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
                <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px;">
                        <h2 style="color: #333; text-align: center;">📈 Stock Alert: No 10%+ Gainers Today</h2>
                        <p style="color: #666; text-align: center;">No stocks gained 10% or more today.</p>
                        <hr style="border: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #999; font-size: 12px; text-align: center;">
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
            price = stock.get('price', 0)
            market_cap = stock.get('mktCap')
            ps_ratio = stock.get('ps_ratio')
            description = stock.get('description', '')
            growth_rate = stock.get('growth_rate', '')
            
            # Clean up percentage display
            if isinstance(change_percent, str):
                change_percent = change_percent.replace('%', '')
            
            try:
                change_float = float(change_percent)
                change_display = f"+{change_float:.2f}%"
            except:
                change_display = change_percent
            
            # Format market cap
            market_cap_display = self.format_market_cap(market_cap)
            
            # Format P/S ratio
            if ps_ratio is not None:
                try:
                    ps_ratio_display = f"{ps_ratio:.1f}x"
                except (ValueError, TypeError):
                    ps_ratio_display = "N/A"
            else:
                ps_ratio_display = "N/A"
            
            # Handle missing description
            description_display = description if description else "Description unavailable"
            
            # Handle missing growth rate
            growth_rate_display = growth_rate if growth_rate else "Growth data unavailable"
            
            # Alternate background colors
            bg_color = "#ffffff" if i % 2 == 0 else "#f8f9fa"
            growth_bg = "#f8f9fa" if i % 2 == 0 else "#ffffff"
            
            stock_cards.append(f"""
                <div style="background-color: {bg_color}; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header with symbol and gain -->
                    <div style="display: table; width: 100%; margin-bottom: 15px;">
                        <div style="display: table-cell; vertical-align: middle;">
                            <span style="font-size: 24px; font-weight: bold; color: #1a1a1a;">{symbol}</span>
                        </div>
                        <div style="display: table-cell; vertical-align: middle; text-align: right;">
                            <span style="font-size: 20px; font-weight: bold; color: #00aa00;">{change_display}</span>
                        </div>
                    </div>
                    
                    <!-- Company name -->
                    <h3 style="margin: 0 0 10px 0; font-size: 18px; color: #333; font-weight: 600;">{name}</h3>
                    
                    <!-- Description -->
                    <p style="margin: 0 0 15px 0; color: #666; font-size: 14px; line-height: 1.5;">
                        {description_display}
                    </p>
                    
                    <!-- Growth rate box -->
                    <div style="background-color: {growth_bg}; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
                        <p style="margin: 0; color: #444; font-size: 14px;">
                            📊 <strong>Expected Growth:</strong> {growth_rate_display}
                        </p>
                    </div>
                    
                    <!-- Footer with price, P/S ratio, and market cap -->
                    <div style="display: table; width: 100%; padding-top: 15px; border-top: 1px solid #eee;">
                        <div style="display: table-cell; vertical-align: middle;">
                            <span style="font-size: 16px; color: #333;">💵 ${price:.2f}</span>
                        </div>
                        <div style="display: table-cell; vertical-align: middle; text-align: center;">
                            <span style="font-size: 16px; color: #555;">📊 P/S: {ps_ratio_display}</span>
                        </div>
                        <div style="display: table-cell; vertical-align: middle; text-align: right;">
                            <span style="font-size: 16px; color: #666;">🏢 Market Cap: {market_cap_display}</span>
                        </div>
                    </div>
                </div>
            """)
        
        html = f"""
        <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px;">
                    <h2 style="color: #333; text-align: center; margin-bottom: 30px;">📈 Stock Alert: {len(stocks)} Stocks Gained 10%+ Today</h2>
                    
                    <!-- Stock cards -->
                    {''.join(stock_cards)}
                    
                    <hr style="border: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #999; font-size: 12px; text-align: center;">
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
                msg['Subject'] = f"📈 Stock Alert: {len(stocks)} stocks gained 10%+ today"
            else:
                msg['Subject'] = "📈 Stock Alert: No 10%+ gainers today"
            
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