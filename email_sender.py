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
    
    def format_investment_evaluation_html(self, eval_data: Dict[str, Any]) -> str:
        """Format investment evaluation data as HTML.
        
        Args:
            eval_data: Parsed evaluation data
            
        Returns:
            HTML string for investment evaluation section
        """
        if not eval_data or 'total_score' not in eval_data:
            return ""
        
        # Determine color based on category
        category = eval_data.get('category', '').lower()
        if 'generational' in category:
            color = '#00aa00'
            badge_bg = '#e6ffe6'
        elif 'strong buy' in category:
            color = '#008800'
            badge_bg = '#e6ffe6'
        elif 'buy' in category and 'strong' not in category:
            color = '#006600'
            badge_bg = '#f0fff0'
        elif 'watch' in category:
            color = '#ff8800'
            badge_bg = '#fff4e6'
        elif 'pass' in category:
            color = '#cc0000'
            badge_bg = '#ffe6e6'
        elif 'avoid' in category:
            color = '#880000'
            badge_bg = '#ffcccc'
        else:
            color = '#666666'
            badge_bg = '#f5f5f5'
        
        score = eval_data.get('total_score', 0)
        category_text = eval_data.get('category', 'Not Evaluated')
        comparison = eval_data.get('comparison', '')
        reasoning = eval_data.get('key_reasoning', '')
        
        # Build HTML - simplified to show only the score
        html = f"""
        <!-- Investment Evaluation -->
        <div style="background-color: #fff; border-radius: 8px; padding: 16px; margin-bottom: 20px; border: 2px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <p style="margin: 0; color: #333; font-size: 18px; font-weight: 700;">
                    Investment Evaluation
                </p>
                <span style="background-color: {badge_bg}; color: {color}; padding: 6px 12px; border-radius: 6px; font-size: 16px; font-weight: 600;">
                    {score}/20
                </span>
            </div>
        </div>"""
        
        # Add the full evaluation text if available
        full_text = eval_data.get('full_text', '')
        if full_text:
            html += f"""
            <!-- Detailed Investment Analysis -->
            <p style="margin: 20px 0 8px 0; color: #333; font-size: 16px; font-weight: 600;">
                Detailed Investment Analysis
            </p>
            <p style="margin: 0 0 16px 0; color: #333; font-size: 16px; line-height: 1.5; white-space: pre-wrap;">
{full_text}
            </p>
            """
        
        return html
    
    def parse_investment_evaluation(self, evaluation: Optional[str]) -> Dict[str, Any]:
        """Parse investment evaluation text into structured data.
        
        Args:
            evaluation: Investment evaluation text from API
            
        Returns:
            Dictionary with parsed evaluation data
        """
        if not evaluation:
            return {}
        
        result = {}
        
        # Parse total score - look for various patterns
        import re
        # Try pattern like "scores 12/20" or "12/20" at the beginning
        total_match = re.search(r'scores?\s*(\d+)/20', evaluation, re.IGNORECASE)
        if not total_match:
            # Try simpler pattern
            total_match = re.search(r'(\d+)/20', evaluation)
        if total_match:
            result['total_score'] = int(total_match.group(1))
        
        # Parse category - look for patterns like "(Buy – good opportunity)" within first 500 chars
        first_part = evaluation[:500]
        category_match = re.search(r'\(([^)]*(?:Buy|Pass|Watch|Avoid|Generational)[^)]*)\)', first_part, re.IGNORECASE)
        if category_match:
            category_text = category_match.group(1)
            # Clean up category text to extract just the category
            if '–' in category_text:
                result['category'] = category_text.split('–')[0].strip()
            elif '-' in category_text:
                result['category'] = category_text.split('-')[0].strip()
            else:
                result['category'] = category_text.strip()
        
        # Parse comparison - look for "resembles" or "similar to"
        comparison_match = re.search(r'(?:resembles?|similar to)\s+([^.,:]+)', evaluation, re.IGNORECASE)
        if comparison_match:
            result['comparison'] = comparison_match.group(1).strip()
        
        # Parse key reasoning
        reasoning_match = re.search(r'KEY REASONING:\s*([^\n]+(?:\n[^\n]+)?)', evaluation)
        if reasoning_match:
            result['key_reasoning'] = reasoning_match.group(1).strip()
        
        # Parse individual scores
        scores = {}
        score_patterns = [
            (r'Technical Innovation:\s*([-\d]+)', 'tech_innovation'),
            (r'Technical Complexity:\s*([-\d]+)', 'tech_complexity'),
            (r'Technical Risk:\s*([-\d]+)', 'tech_risk'),
            (r'Irreplaceable Assets:\s*([-\d]+)', 'irreplaceable'),
            (r'Revenue Quality:\s*([-\d]+)', 'revenue_quality'),
            (r'Unit Economics:\s*([-\d]+)', 'unit_economics'),
            (r'Growth Runway:\s*([-\d]+)', 'growth_runway'),
            (r'Market Position:\s*([-\d]+)', 'market_position'),
            (r'Valuation:\s*([-\d]+)', 'valuation')
        ]
        
        for pattern, key in score_patterns:
            match = re.search(pattern, evaluation)
            if match:
                scores[key] = int(match.group(1))
        
        result['scores'] = scores
        
        # Parse quick tests
        tests = {}
        test_patterns = [
            (r'Technical Test:\s*.*?(Yes|No)', 'technical_test'),
            (r'Business Test:\s*.*?(Yes|No|Maybe)', 'business_test'),
            (r'Growth Test:\s*.*?(Yes|No|Maybe)', 'growth_test'),
            (r'Moat Test:\s*.*?(Yes|No)', 'moat_test'),
            (r'Price Test:\s*.*?(Yes|No)', 'price_test')
        ]
        
        for pattern, key in test_patterns:
            match = re.search(pattern, evaluation, re.IGNORECASE)
            if match:
                tests[key] = match.group(1)
        
        result['quick_tests'] = tests
        
        return result
    
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
            eval_data = self.parse_investment_evaluation(investment_evaluation)
            # Keep the full evaluation text for display
            eval_data['full_text'] = investment_evaluation
            
            # Get financial metrics
            gross_margin = stock.get('gross_margin', None)
            rd_margin = stock.get('rd_margin', None)
            ebitda_margin = stock.get('ebitda_margin', None)
            net_income_margin = stock.get('net_income_margin', None)
            long_term_debt = stock.get('long_term_debt', None)
            cash_and_equivalents = stock.get('cash_and_equivalents', None)
            
            # Get consensus price target history
            pt_consensus_current = stock.get('pt_consensus_current', None)
            pt_consensus_7d = stock.get('pt_consensus_7d', None)
            pt_consensus_30d = stock.get('pt_consensus_30d', None)
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
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">PT 7d:</td>
                                <td style="padding: 6px 16px 6px 0; color: #333; font-size: 14px; font-weight: 500;">{format_pt_with_change(pt_consensus_current, pt_consensus_7d, pt_change_7d)}</td>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">PT 30d:</td>
                                <td style="padding: 6px 0; color: #333; font-size: 14px; font-weight: 500;">{format_pt_with_change(pt_consensus_current, pt_consensus_30d, pt_change_30d)}</td>
                            </tr>
                            <!-- Sixth row - Price Target 180d -->
                            <tr>
                                <td style="padding: 6px 0; color: #666; font-size: 14px;">PT 180d:</td>
                                <td colspan="5" style="padding: 6px 0; color: #333; font-size: 14px; font-weight: 500;">{format_pt_with_change(pt_consensus_current, pt_consensus_180d, pt_change_180d)}</td>
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
                    
                    <!-- Analyst Price Targets -->
                    <p style="margin: 0 0 8px 0; color: #333; font-size: 16px; font-weight: 600;">
                        Analyst Price Target Changes
                    </p>
                    <p style="margin: 0 0 20px 0; color: #333; font-size: 16px; line-height: 1.5;">
                        {analyst_price_targets if analyst_price_targets else "No recent analyst price target changes available"}
                    </p>
                    
                    {self.format_investment_evaluation_html(eval_data)}
                    
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