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
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #333;">Stock Alert: No 10%+ Gainers Today</h2>
                    <p style="color: #666;">No stocks gained 10% or more today.</p>
                    <hr style="border: 1px solid #eee;">
                    <p style="color: #999; font-size: 12px;">
                        Generated on {date}
                    </p>
                </body>
            </html>
            """.format(date=datetime.now().strftime("%B %d, %Y at %I:%M %p"))
        
        table_rows = []
        for stock in stocks:
            symbol = stock.get('symbol', 'N/A')
            name = stock.get('name', 'N/A')
            change_percent = stock.get('changesPercentage', 'N/A')
            price = stock.get('price', 0)
            market_cap = stock.get('mktCap')
            description = stock.get('description', '')
            
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
            
            # Handle missing description
            description_display = description if description else "Description unavailable"
            
            table_rows.append(f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{symbol}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{name}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; font-size: 12px; color: #666;">{description_display}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; color: #0a0; font-weight: bold;">{change_display}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">${price:.2f}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{market_cap_display}</td>
                </tr>
            """)
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #333;">📈 Stock Alert: {len(stocks)} Stocks Gained 10%+ Today</h2>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <thead>
                        <tr style="background-color: #f5f5f5;">
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Symbol</th>
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Company Name</th>
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Description</th>
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">% Gain</th>
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Current Price</th>
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Market Cap</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
                
                <hr style="border: 1px solid #eee; margin-top: 30px;">
                <p style="color: #999; font-size: 12px;">
                    Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
                </p>
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