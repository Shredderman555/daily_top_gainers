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
    
    def _create_price_target_chart(self, recent_actions: List[Dict[str, Any]], symbol: str) -> str:
        """Create a simple HTML chart showing price target changes over time.
        
        Args:
            recent_actions: List of recent analyst actions with price targets
            symbol: Stock symbol
            
        Returns:
            HTML string for the chart
        """
        if not recent_actions:
            return ""
        
        # Get min and max targets for scaling
        targets = [a['target'] for a in recent_actions if a.get('target')]
        if not targets:
            return ""
        
        min_target = min(targets) * 0.95  # Add 5% padding
        max_target = max(targets) * 1.05
        target_range = max_target - min_target
        
        # Create bars for the chart
        bars = []
        max_bars = min(10, len(recent_actions))  # Show max 10 bars
        bar_width = 100 / max_bars
        
        for i, action in enumerate(recent_actions[:max_bars]):
            if not action.get('target'):
                continue
            
            target = action['target']
            height_pct = ((target - min_target) / target_range) * 100 if target_range > 0 else 50
            left_pct = i * bar_width
            
            # Color based on change
            color = '#4CAF50'  # Green default
            if action.get('target_prior'):
                if target < action['target_prior']:
                    color = '#f44336'  # Red for decrease
                elif target == action['target_prior']:
                    color = '#2196F3'  # Blue for no change
            
            bars.append(f"""
                <div style="position: absolute; bottom: 0; left: {left_pct:.1f}%; width: {bar_width * 0.8:.1f}%; height: {height_pct:.1f}%; background-color: {color}; opacity: 0.8;">
                    <div style="position: absolute; bottom: -20px; left: 0; right: 0; font-size: 9px; text-align: center; color: #666;">
                        {action.get('date_short', '')}
                    </div>
                    <div style="position: absolute; top: -18px; left: 0; right: 0; font-size: 10px; text-align: center; font-weight: 500;">
                        ${target:.0f}
                    </div>
                </div>
            """)
        
        return f"""
            <div style="background-color: #fff; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                <p style="margin: 0 0 16px 0; color: #333; font-size: 16px; font-weight: 600;">
                    Price Target Trend - {symbol}
                </p>
                <div style="position: relative; height: 150px; margin: 30px 0 30px 0; background: linear-gradient(to top, #f5f5f5 0%, #f5f5f5 50%, #fafafa 50%, #fafafa 100%); border-radius: 4px;">
                    {''.join(bars)}
                </div>
                <div style="text-align: center; color: #999; font-size: 11px; margin-top: 10px;">
                    <span style="display: inline-block; width: 12px; height: 12px; background-color: #4CAF50; margin-right: 4px;"></span> Upgrade
                    <span style="display: inline-block; width: 12px; height: 12px; background-color: #f44336; margin: 0 4px 0 12px;"></span> Downgrade
                    <span style="display: inline-block; width: 12px; height: 12px; background-color: #2196F3; margin: 0 4px 0 12px;"></span> Reiterated
                </div>
            </div>
        """
    
    def _create_price_target_table(self, recent_actions: List[Dict[str, Any]]) -> str:
        """Create a table showing the 15 most recent price target changes.
        
        Args:
            recent_actions: List of recent analyst actions
            
        Returns:
            HTML string for the table
        """
        if not recent_actions:
            return ""
        
        rows = []
        for action in recent_actions[:15]:  # Show up to 15 most recent
            firm = action.get('firm', 'Unknown')
            date = action.get('date', '')
            rating = action.get('rating', '')
            target = action.get('target')
            target_prior = action.get('target_prior')
            action_type = action.get('action', 'Updates')
            
            # Format price target with change indicator showing previous price
            if target:
                if target_prior and target_prior != target:
                    if target > target_prior:
                        target_str = f'<span style="color: #4CAF50;">↑</span> ${target:.0f} <span style="color: #999; font-size: 11px;">(from ${target_prior:.0f})</span>'
                    else:
                        target_str = f'<span style="color: #f44336;">↓</span> ${target:.0f} <span style="color: #999; font-size: 11px;">(from ${target_prior:.0f})</span>'
                else:
                    target_str = f"${target:.0f}"
            else:
                target_str = "N/A"
            
            # Get rating color
            rating_lower = rating.lower() if rating else ''
            if 'buy' in rating_lower or 'outperform' in rating_lower or 'overweight' in rating_lower:
                rating_color = '#4CAF50'
            elif 'hold' in rating_lower or 'neutral' in rating_lower:
                rating_color = '#FF9800'
            elif 'sell' in rating_lower or 'underperform' in rating_lower:
                rating_color = '#f44336'
            else:
                rating_color = '#666'
            
            rows.append(f"""
                <tr style="border-bottom: 1px solid #f0f0f0;">
                    <td style="padding: 8px 4px; color: #666; font-size: 13px;">{date}</td>
                    <td style="padding: 8px 4px; color: #333; font-size: 13px;">{firm}</td>
                    <td style="padding: 8px 4px; color: #666; font-size: 13px;">{action_type}</td>
                    <td style="padding: 8px 4px; color: {rating_color}; font-size: 13px; font-weight: 500;">{rating}</td>
                    <td style="padding: 8px 4px; color: #333; font-size: 13px; font-weight: 500;">{target_str}</td>
                </tr>
            """)
        
        if not rows:
            return ""
        
        return f"""
            <div style="background-color: #fff; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                <p style="margin: 0 0 12px 0; color: #333; font-size: 16px; font-weight: 600;">
                    Recent Analyst Actions (Last 15 Changes)
                </p>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="border-bottom: 2px solid #e0e0e0;">
                            <th style="padding: 8px 4px; text-align: left; color: #666; font-size: 12px; font-weight: 600;">Date</th>
                            <th style="padding: 8px 4px; text-align: left; color: #666; font-size: 12px; font-weight: 600;">Analyst</th>
                            <th style="padding: 8px 4px; text-align: left; color: #666; font-size: 12px; font-weight: 600;">Action</th>
                            <th style="padding: 8px 4px; text-align: left; color: #666; font-size: 12px; font-weight: 600;">Rating</th>
                            <th style="padding: 8px 4px; text-align: left; color: #666; font-size: 12px; font-weight: 600;">Price Target</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows)}
                    </tbody>
                </table>
            </div>
        """
    
    def _format_polygon_section(self, stock: Dict[str, Any]) -> str:
        """Format the Polygon analyst data section for a stock.
        
        Args:
            stock: Stock dictionary with Polygon data
            
        Returns:
            HTML string for Polygon section
        """
        # Get Polygon data
        polygon_consensus = stock.get('polygon_consensus')
        polygon_trend_7d = stock.get('polygon_trend_7d')
        polygon_trend_30d = stock.get('polygon_trend_30d')
        polygon_analyst_count = stock.get('polygon_analyst_count', 0)
        polygon_recent_actions = stock.get('polygon_recent_actions', [])
        
        # Skip section if no Polygon data
        if not polygon_consensus and polygon_analyst_count == 0:
            return ""
        
        # Format recent actions
        actions_html = ""
        if polygon_recent_actions:
            action_rows = []
            for action in polygon_recent_actions[:3]:  # Show max 3 recent actions
                firm = action.get('firm', 'Unknown')
                date = action.get('date', '')
                rating = action.get('rating', '')
                target = action.get('target')
                target_prior = action.get('target_prior')
                
                # Format price target change
                if target:
                    if target_prior and target_prior != target:
                        if target > target_prior:
                            target_str = f"↑ ${target:.0f}"
                        else:
                            target_str = f"↓ ${target:.0f}"
                    else:
                        target_str = f"${target:.0f}"
                else:
                    target_str = "N/A"
                
                # Get rating emoji
                rating_lower = rating.lower() if rating else ''
                if 'buy' in rating_lower or 'outperform' in rating_lower or 'overweight' in rating_lower:
                    emoji = '🟢'
                elif 'hold' in rating_lower or 'neutral' in rating_lower:
                    emoji = '🟡'
                elif 'sell' in rating_lower or 'underperform' in rating_lower:
                    emoji = '🔴'
                else:
                    emoji = '⚪'
                
                action_rows.append(f"""
                    <tr>
                        <td style="padding: 4px 0; color: #666; font-size: 13px;">{date}</td>
                        <td style="padding: 4px 8px; color: #333; font-size: 13px;">{firm}</td>
                        <td style="padding: 4px 8px; color: #333; font-size: 13px;">{emoji} {rating}</td>
                        <td style="padding: 4px 0; color: #333; font-size: 13px; font-weight: 500;">{target_str}</td>
                    </tr>
                """)
            
            actions_html = f"""
                <div style="margin-top: 12px;">
                    <p style="margin: 0 0 8px 0; color: #666; font-size: 13px; font-weight: 500;">Recent Analyst Actions:</p>
                    <table style="width: 100%; border-collapse: collapse;">
                        {''.join(action_rows)}
                    </table>
                </div>
            """
        
        return f"""
            <!-- Polygon Analyst Data Section -->
            <div style="background-color: #fff; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                <p style="margin: 0 0 12px 0; color: #333; font-size: 16px; font-weight: 600;">
                    Analyst Sentiment (Polygon)
                </p>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 6px 0; color: #666; font-size: 14px; width: 25%;">Consensus Target:</td>
                        <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500; width: 25%;">
                            {f"${polygon_consensus:.0f}" if polygon_consensus else "N/A"}
                        </td>
                        <td style="padding: 6px 0; color: #666; font-size: 14px; width: 25%;">Analysts:</td>
                        <td style="padding: 6px 0; color: #333; font-size: 14px; font-weight: 500; width: 25%;">
                            {polygon_analyst_count if polygon_analyst_count > 0 else "N/A"}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; color: #666; font-size: 14px;">7-Day Trend:</td>
                        <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500;">
                            {polygon_trend_7d if polygon_trend_7d else "N/A"}
                        </td>
                        <td style="padding: 6px 0; color: #666; font-size: 14px;">30-Day Trend:</td>
                        <td style="padding: 6px 0; color: #333; font-size: 14px; font-weight: 500;">
                            {polygon_trend_30d if polygon_trend_30d else "N/A"}
                        </td>
                    </tr>
                </table>
                {actions_html}
            </div>
        """
    
    def format_investment_evaluation(self, text: Optional[str]) -> str:
        """Format investment evaluation text into structured HTML.
        
        Parses AI-generated text to detect patterns like markdown headers, bullet points, 
        scores, sections, and formats them into readable HTML.
        
        Args:
            text: Raw investment evaluation text
            
        Returns:
            Formatted HTML string
        """
        if not text:
            return "Investment evaluation analysis not available"
        
        import re
        
        lines = text.split('\n')
        html_parts = []
        in_list = False
        
        for line in lines:
            original_line = line
            line = line.strip()
            
            # Skip empty lines
            if not line:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                continue
            
            # Skip separator lines (just dashes)
            if line == '--' or line == '---':
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                # Add a subtle separator
                html_parts.append('<hr style="border: none; border-top: 1px solid #e0e0e0; margin: 12px 0;">')
                continue
            
            # Check for markdown headers (###, ##, #)
            if line.startswith('###'):
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                header_text = line.replace('###', '').strip()
                html_parts.append(f'<p style="margin: 16px 0 8px 0; color: #333; font-size: 16px; font-weight: 600;">{header_text}</p>')
                continue
            elif line.startswith('##'):
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                header_text = line.replace('##', '').strip()
                html_parts.append(f'<p style="margin: 16px 0 8px 0; color: #333; font-size: 17px; font-weight: 600;">{header_text}</p>')
                continue
            elif line.startswith('#'):
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                header_text = line.replace('#', '').strip()
                html_parts.append(f'<p style="margin: 16px 0 8px 0; color: #333; font-size: 18px; font-weight: 600;">{header_text}</p>')
                continue
            
            # Check for Total Score pattern
            if 'Total Score:' in line:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                # Extract and highlight the score
                score_match = re.search(r'(\d+(?:\.\d+)?)/(\d+)', line)
                if score_match:
                    score_num = float(score_match.group(1))
                    score_denom = float(score_match.group(2))
                    score_pct = (score_num / score_denom) * 100 if score_denom > 0 else 0
                    
                    # Color based on score percentage
                    if score_pct >= 70:
                        color = '#4CAF50'  # Green
                    elif score_pct >= 50:
                        color = '#FF9800'  # Orange
                    else:
                        color = '#f44336'  # Red
                    
                    html_parts.append(f'<p style="margin: 16px 0 12px 0; padding: 12px; background-color: #f8f9fa; border-radius: 6px; color: #333; font-size: 16px; font-weight: 600;">Total Score: <span style="color: {color}; font-size: 18px;">{score_match.group(1)}/{score_match.group(2)}</span></p>')
                else:
                    html_parts.append(f'<p style="margin: 12px 0 8px 0; color: #333; font-size: 15px; font-weight: 600;">{line}</p>')
                continue
            
            # Check for section headers with scores (lines with "Score:" pattern)
            if ':' in line and ('Score' in line or 'score' in line) and '(' in line:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                # Extract score if present
                score_match = re.search(r'\(.*?(\d+(?:\.\d+)?)[/-](\d+).*?\)', line)
                if score_match:
                    section_text = line.split('(')[0].strip().rstrip(':')
                    score = f"{score_match.group(1)}/{score_match.group(2)}"
                    html_parts.append(f'<p style="margin: 12px 0 8px 0; color: #333; font-size: 15px; font-weight: 600;">{section_text}: <span style="color: #0066cc;">{score}</span></p>')
                else:
                    html_parts.append(f'<p style="margin: 12px 0 8px 0; color: #333; font-size: 15px; font-weight: 600;">{line}</p>')
            
            # Check for bullet points
            elif line.startswith(('-', '•', '*', '·')) or (len(line) > 2 and line[0].isdigit() and line[1] in '.):'):
                if not in_list:
                    html_parts.append('<ul style="margin: 8px 0 12px 20px; padding: 0; list-style-type: disc;">')
                    in_list = True
                # Remove bullet character and clean up
                if line[0] in '-•*·':
                    bullet_text = line[1:].strip()
                else:
                    # Handle numbered lists
                    bullet_text = re.sub(r'^\d+[.)]\s*', '', line)
                html_parts.append(f'<li style="margin: 4px 0; color: #333; font-size: 14px; line-height: 1.5;">{bullet_text}</li>')
            
            # Check for Summary: or other section headers ending with colon
            elif line.endswith(':') and len(line) < 50:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                html_parts.append(f'<p style="margin: 12px 0 8px 0; color: #333; font-size: 15px; font-weight: 600;">{line}</p>')
            
            # Check for key-value pairs (but not section headers)
            elif ':' in line and not line.endswith(':') and not ('Score' in line or 'score' in line):
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                parts = line.split(':', 1)
                if len(parts) == 2 and len(parts[0]) < 30:  # Only treat as key-value if key is reasonably short
                    key = parts[0].strip()
                    value = parts[1].strip()
                    html_parts.append(f'<p style="margin: 8px 0; color: #333; font-size: 14px;"><span style="font-weight: 500;">{key}:</span> {value}</p>')
                else:
                    html_parts.append(f'<p style="margin: 8px 0; color: #333; font-size: 14px; line-height: 1.5;">{line}</p>')
            
            # Regular paragraph
            else:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                html_parts.append(f'<p style="margin: 8px 0; color: #333; font-size: 14px; line-height: 1.5;">{line}</p>')
        
        # Close any open list
        if in_list:
            html_parts.append('</ul>')
        
        # Wrap in a container div
        formatted_html = f'''
        <div style="background-color: #fff; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
            {''.join(html_parts)}
        </div>
        '''
        
        return formatted_html
    
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
    
    def create_email_html(self, stocks: List[Dict[str, Any]], put_call_ratio: Optional[str] = None) -> str:
        """Create HTML content for the email.
        
        Args:
            stocks: List of stock dictionaries with gainer information
            
        Returns:
            HTML string for email body
        """
        if not stocks:
            # Format put/call ratio section for no gainers
            put_call_section = ""
            if put_call_ratio:
                try:
                    ratio_float = float(put_call_ratio)
                    if ratio_float > 1.0:
                        color = "#cc0000"
                        sentiment = "Bearish"
                    elif ratio_float < 1.0:
                        color = "#00aa00"
                        sentiment = "Bullish"
                    else:
                        color = "#666666"
                        sentiment = "Neutral"
                    
                    put_call_section = f"""
                        <div style="background-color: #f5f5f5; border-radius: 8px; padding: 12px 20px; margin-bottom: 30px; text-align: center;">
                            <span style="color: #666; font-size: 14px; font-weight: 500;">Market Sentiment</span>
                            <span style="margin: 0 10px; color: #ccc;">|</span>
                            <span style="color: #333; font-size: 14px;">Put/Call Ratio: </span>
                            <span style="color: {color}; font-size: 14px; font-weight: 600;">{put_call_ratio}</span>
                            <span style="color: {color}; font-size: 12px; margin-left: 8px;">({sentiment})</span>
                        </div>
                    """
                except:
                    put_call_section = f"""
                        <div style="background-color: #f5f5f5; border-radius: 8px; padding: 12px 20px; margin-bottom: 30px; text-align: center;">
                            <span style="color: #666; font-size: 14px; font-weight: 500;">Market Sentiment</span>
                            <span style="margin: 0 10px; color: #ccc;">|</span>
                            <span style="color: #333; font-size: 14px;">Put/Call Ratio: {put_call_ratio}</span>
                        </div>
                    """
            
            return f"""
            <html>
                <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 0; background-color: #ffffff;">
                    <div style="max-width: 700px; margin: 0 auto; padding: 40px 20px;">
                        {put_call_section}
                        <p style="color: #666; text-align: center; font-size: 16px; margin-top: 20px;">No stocks gained 10% or more today.</p>
                        <p style="color: #999; font-size: 14px; text-align: center; margin-top: 40px;">
                            Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
                        </p>
                    </div>
                </body>
            </html>
            """
        
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
            
            # Get investment evaluation
            investment_evaluation = stock.get('investment_evaluation', None)
            
            # Get Polygon recent actions for visualizations
            polygon_recent_actions = stock.get('polygon_recent_actions', [])
            
            # Get financial metrics
            gross_margin = stock.get('gross_margin', None)
            rd_margin = stock.get('rd_margin', None)
            ebitda_margin = stock.get('ebitda_margin', None)
            net_income_margin = stock.get('net_income_margin', None)
            long_term_debt = stock.get('long_term_debt', None)
            cash_and_equivalents = stock.get('cash_and_equivalents', None)
            
            # Get consensus price target history from Polygon (prioritize) or FMP (fallback)
            # Use Polygon data if available, otherwise fall back to FMP
            pt_consensus_current = stock.get('polygon_consensus') or stock.get('pt_consensus_current', None)
            pt_consensus_7d = stock.get('polygon_consensus_7d') or stock.get('pt_consensus_7d', None)
            pt_consensus_30d = stock.get('polygon_consensus_30d') or stock.get('pt_consensus_30d', None)
            # For 90d/180d, use Polygon 90d if available, else FMP 180d
            pt_consensus_90d = stock.get('polygon_consensus_90d', None)
            pt_consensus_180d = stock.get('pt_consensus_180d', None)
            pt_change_7d = stock.get('pt_change_7d', None)
            pt_change_30d = stock.get('pt_change_30d', None)
            pt_change_180d = stock.get('pt_change_180d', None)
            
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
            
            def format_pt_with_change(current, historical, change):
                """Format price target with change."""
                if historical is not None:
                    return f"${historical:.0f}"
                return "N/A"
            
            # Format scores
            competitive_display = f"{competitive_score}/10" if competitive_score is not None else "N/A"
            growth_score_display = f"{market_growth_score}/10" if market_growth_score is not None else "N/A"
            
            # Create price target table (chart removed per user request)
            price_target_table = self._create_price_target_table(polygon_recent_actions) if polygon_recent_actions else ""
            
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
                            <!-- Fifth row - Price Target Consensus History (7d, 30d) -->
                            <tr>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">PT Now:</td>
                                <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500;">{f"${pt_consensus_current:.0f}" if pt_consensus_current else "N/A"}</td>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">PT 7d ago:</td>
                                <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500;">{f"${pt_consensus_7d:.0f}" if pt_consensus_7d else "N/A"}</td>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">PT 30d ago:</td>
                                <td style="padding: 6px 0; color: #333; font-size: 14px; font-weight: 500;">{f"${pt_consensus_30d:.0f}" if pt_consensus_30d else "N/A"}</td>
                            </tr>
                            <!-- Sixth row - Price Target 90d (Polygon) or 180d (FMP) -->
                            <tr>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">{"PT 90d ago:" if pt_consensus_90d is not None else "PT 180d:"}</td>
                                <td colspan="5" style="padding: 6px 0; color: #333; font-size: 14px; font-weight: 500;">{f"${pt_consensus_90d:.0f}" if pt_consensus_90d is not None else format_pt_with_change(pt_consensus_current, pt_consensus_180d, pt_change_180d)}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <!-- Revenue Growth Projection for 2030 -->
                    <p style="margin: 0 0 8px 0; color: #333; font-size: 16px; font-weight: 600;">
                        Revenue Growth Projection for 2030
                    </p>
                    <p style="margin: 0 0 16px 0; color: #333; font-size: 16px; line-height: 1.5;">
                        {revenue_projection_2030 if revenue_projection_2030 else "Revenue growth projection analysis not available"}
                    </p>
                    
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
                    
                    <!-- Price Target Table -->
                    {price_target_table}
                    
                    <!-- Analyst Price Targets (Legacy text format) -->
                    <p style="margin: 0 0 8px 0; color: #333; font-size: 16px; font-weight: 600;">
                        Analyst Price Target Summary
                    </p>
                    <p style="margin: 0 0 20px 0; color: #333; font-size: 16px; line-height: 1.5;">
                        {analyst_price_targets if analyst_price_targets else "No additional analyst price target information available"}
                    </p>
                    
                    <!-- Investment Evaluation -->
                    <p style="margin: 0 0 8px 0; color: #333; font-size: 16px; font-weight: 600;">
                        Investment Evaluation
                    </p>
                    {self.format_investment_evaluation(investment_evaluation)}
                    
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
        
        # Format put/call ratio section
        put_call_section = ""
        if put_call_ratio:
            try:
                ratio_float = float(put_call_ratio)
                # Color code based on ratio (>1 = bearish/red, <1 = bullish/green)
                if ratio_float > 1.0:
                    color = "#cc0000"
                    sentiment = "Bearish"
                elif ratio_float < 1.0:
                    color = "#00aa00"
                    sentiment = "Bullish"
                else:
                    color = "#666666"
                    sentiment = "Neutral"
                
                put_call_section = f"""
                    <div style="background-color: #f5f5f5; border-radius: 8px; padding: 12px 20px; margin-bottom: 30px; text-align: center;">
                        <span style="color: #666; font-size: 14px; font-weight: 500;">Market Sentiment</span>
                        <span style="margin: 0 10px; color: #ccc;">|</span>
                        <span style="color: #333; font-size: 14px;">Put/Call Ratio: </span>
                        <span style="color: {color}; font-size: 14px; font-weight: 600;">{put_call_ratio}</span>
                        <span style="color: {color}; font-size: 12px; margin-left: 8px;">({sentiment})</span>
                    </div>
                """
            except:
                # If we can't parse the ratio, just show it without color coding
                put_call_section = f"""
                    <div style="background-color: #f5f5f5; border-radius: 8px; padding: 12px 20px; margin-bottom: 30px; text-align: center;">
                        <span style="color: #666; font-size: 14px; font-weight: 500;">Market Sentiment</span>
                        <span style="margin: 0 10px; color: #ccc;">|</span>
                        <span style="color: #333; font-size: 14px;">Put/Call Ratio: {put_call_ratio}</span>
                    </div>
                """
        
        html = f"""
        <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 0; background-color: #ffffff;">
                <div style="max-width: 700px; margin: 0 auto; padding: 40px 20px;">
                    {put_call_section}
                    
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
                   dry_run: bool = False, put_call_ratio: Optional[str] = None) -> bool:
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
            html_content = self.create_email_html(stocks, put_call_ratio)
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