#!/usr/bin/env python3
"""
Price Target Alerts - Daily notifications for analyst price target changes.

This script monitors a watchlist of stocks and sends email alerts for all
price target changes (raises, cuts, reiterations) from the last 24 hours.
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from config import Config
from polygon_client import PolygonClient
from email_sender import EmailSender
from api_client import FMPAPIClient


# Configure logging
def setup_logging(log_file: str = 'price_target_alerts.log') -> None:
    """Set up logging configuration."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_watchlist(file_path: str = 'watchlist.txt') -> List[str]:
    """Load ticker symbols from watchlist file.
    
    Args:
        file_path: Path to watchlist file
        
    Returns:
        List of ticker symbols
    """
    watchlist = []
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    watchlist.append(line.upper())
    except FileNotFoundError:
        logging.error(f"Watchlist file not found: {file_path}")
        sys.exit(1)
    
    return watchlist


def get_current_price(api_client: FMPAPIClient, ticker: str) -> Optional[float]:
    """Get current stock price.
    
    Args:
        api_client: FMP API client
        ticker: Stock ticker symbol
        
    Returns:
        Current price or None if not available
    """
    try:
        profile = api_client.get_company_profile(ticker)
        if profile and 'price' in profile:
            return profile['price']
    except Exception as e:
        logging.warning(f"Could not fetch price for {ticker}: {e}")
    
    return None


def calculate_upside(current_price: float, target_price: float) -> float:
    """Calculate percentage upside/downside to target.
    
    Args:
        current_price: Current stock price
        target_price: Analyst price target
        
    Returns:
        Percentage difference
    """
    if current_price and current_price > 0:
        return ((target_price - current_price) / current_price) * 100
    return 0


def collect_price_target_changes(
    polygon_client: PolygonClient,
    fmp_client: FMPAPIClient,
    watchlist: List[str]
) -> Dict[str, List[Dict[str, Any]]]:
    """Collect all price target changes from the last 24 hours.
    
    Args:
        polygon_client: Polygon API client
        fmp_client: FMP API client for stock prices
        watchlist: List of tickers to monitor
        
    Returns:
        Dictionary with raises, cuts, and reiterations
    """
    logger = logging.getLogger(__name__)
    
    all_changes = {
        'raises': [],
        'cuts': [],
        'reiterations': []
    }
    
    cutoff_date = datetime.now() - timedelta(days=1)
    
    for ticker in watchlist:
        logger.info(f"Checking {ticker}...")
        
        try:
            # Get daily price target changes
            changes = polygon_client.get_daily_price_target_changes(ticker, cutoff_date)
            
            if changes:
                # Get current price for upside calculation
                current_price = get_current_price(fmp_client, ticker)
                
                # Get company name
                profile = fmp_client.get_company_profile(ticker)
                company_name = profile.get('companyName', ticker) if profile else ticker
                
                for change in changes:
                    change['company_name'] = company_name
                    change['current_price'] = current_price
                    
                    if current_price:
                        change['upside'] = calculate_upside(current_price, change['new_target'])
                    else:
                        change['upside'] = None
                    
                    # Categorize the change
                    if change['change_pct'] > 0.1:  # More than 0.1% is a raise
                        all_changes['raises'].append(change)
                    elif change['change_pct'] < -0.1:  # Less than -0.1% is a cut
                        all_changes['cuts'].append(change)
                    else:  # Between -0.1% and 0.1% is a reiteration
                        all_changes['reiterations'].append(change)
        
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            continue
    
    # Sort each category by magnitude of change
    all_changes['raises'].sort(key=lambda x: x['change_pct'], reverse=True)
    all_changes['cuts'].sort(key=lambda x: x['change_pct'])
    all_changes['reiterations'].sort(key=lambda x: x.get('ticker', ''))
    
    return all_changes


def main() -> None:
    """Main function to check price targets and send alerts."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Send daily alerts for analyst price target changes'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (send email immediately)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview email without sending'
    )
    parser.add_argument(
        '--watchlist',
        default='watchlist.txt',
        help='Path to watchlist file (default: watchlist.txt)'
    )
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("Price Target Alerts")
    print("━" * 20)
    
    logger.info("=== Price Target Alerts Started ===")
    logger.info(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load configuration
        config = Config()
        logger.info("Configuration loaded successfully")
        
        # Load watchlist
        watchlist = load_watchlist(args.watchlist)
        logger.info(f"Loaded {len(watchlist)} tickers from watchlist")
        print(f"✓ Monitoring {len(watchlist)} stocks")
        
        # Initialize clients
        with PolygonClient(config.polygon_api_key) as polygon_client, \
             FMPAPIClient(config.fmp_api_key) as fmp_client:
            
            # Collect price target changes
            print("✓ Checking for price target changes...")
            all_changes = collect_price_target_changes(
                polygon_client, fmp_client, watchlist
            )
            
            # Count total changes
            total_changes = (
                len(all_changes['raises']) +
                len(all_changes['cuts']) +
                len(all_changes['reiterations'])
            )
            
            print(f"✓ Found {total_changes} price target changes")
            print(f"  - {len(all_changes['raises'])} raises")
            print(f"  - {len(all_changes['cuts'])} cuts")
            print(f"  - {len(all_changes['reiterations'])} reiterations")
            
            # Send email if there are any changes
            if total_changes > 0 or args.test:
                # Initialize email sender
                email_sender = EmailSender(
                    smtp_server=config.smtp_server,
                    smtp_port=config.smtp_port,
                    sender_email=config.email_sender,
                    sender_password=config.email_password
                )
                
                # Send email
                if args.dry_run:
                    print("\n[DRY RUN MODE - Email Preview]")
                    email_sender.send_price_target_alert(
                        recipient=config.email_recipient,
                        changes=all_changes,
                        watchlist_count=len(watchlist),
                        dry_run=True
                    )
                else:
                    success = email_sender.send_price_target_alert(
                        recipient=config.email_recipient,
                        changes=all_changes,
                        watchlist_count=len(watchlist)
                    )
                    
                    if success:
                        print("✓ Email sent successfully")
                        logger.info(f"Email sent to {config.email_recipient}")
                    else:
                        print("✗ Failed to send email")
                        logger.error("Failed to send email")
            else:
                print("✓ No price target changes in the last 24 hours")
                logger.info("No changes to report")
        
        logger.info("=== Price Target Alerts Completed ===")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()