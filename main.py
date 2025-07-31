#!/usr/bin/env python3
"""
Stock Alerts - Daily email notifications for stocks with 10%+ gains.

This script fetches daily stock gainers from Financial Modeling Prep API
and sends email alerts for stocks that gained 10% or more.
"""

import argparse
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any

from config import Config
from api_client import FMPAPIClient
from email_sender import EmailSender


# Configure logging
def setup_logging(log_file: str = 'stock_alerts.log') -> None:
    """Set up logging configuration."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger with file handler only
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file)
        ]
    )
    
    # Add console handler only for errors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(console_handler)


def sort_by_gain_percentage(stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort stocks by gain percentage in descending order.
    
    Args:
        stocks: List of stock dictionaries
        
    Returns:
        Sorted list of stocks
    """
    def get_change_percent(stock: Dict[str, Any]) -> float:
        try:
            change_value = stock.get('changesPercentage', 0)
            # Handle both string and float formats
            if isinstance(change_value, str):
                return float(change_value.replace('%', ''))
            else:
                return float(change_value)
        except (ValueError, TypeError):
            return 0.0
    
    return sorted(stocks, key=get_change_percent, reverse=True)


def main() -> None:
    """Main function to fetch gainers and send email alerts."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Send email alerts for stocks with 10%+ daily gains'
    )
    parser.add_argument(
        '--test', 
        action='store_true',
        help='Send email immediately for testing'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Preview email without sending'
    )
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Clean progress display
    if args.test:
        print("Stock Alerts - Test Run")
    else:
        print("Stock Alerts")
    print("━" * 24)
    
    logger.info("=== Stock Alerts Started ===")
    logger.info(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load configuration
        config = Config()
        logger.info("Configuration loaded successfully")
        
        # Initialize API client
        with FMPAPIClient(config.fmp_api_key) as api_client:
            # Fetch daily gainers
            print("✓ Fetching gainers...", end="", flush=True)
            logger.info("Fetching daily stock gainers...")
            all_gainers = api_client.get_daily_gainers()
            print(f" ({len(all_gainers)} found)")
            
            # Filter for 10%+ gainers
            high_gainers = api_client.filter_by_gain_percentage(all_gainers, min_gain=10.0)
            
            # Sort by gain percentage
            sorted_gainers = sort_by_gain_percentage(high_gainers)
            
            logger.info(f"Total gainers: {len(all_gainers)}")
            logger.info(f"10%+ gainers: {len(sorted_gainers)}")
            
            # Enrich with market cap data and apply filters
            if sorted_gainers:
                print("✓ Applying filters...", end="", flush=True)
                logger.info("Fetching company profile data...")
                sorted_gainers = api_client.enrich_with_market_cap(sorted_gainers)
                
                initial_count = len(sorted_gainers)
                
                # Filter by market cap (minimum $300M)
                logger.info("Applying market cap filter ($300M minimum)...")
                sorted_gainers = api_client.filter_by_market_cap(sorted_gainers, min_market_cap=300_000_000)
                after_market_cap = len(sorted_gainers)
                
                # Filter by industry (exclude biotechnology/pharmaceutical)
                logger.info("Applying industry filter (excluding biotechnology)...")
                sorted_gainers = api_client.filter_by_industry(sorted_gainers, exclude_biotech=True)
                after_industry = len(sorted_gainers)
                
                # Re-sort after filtering (in case order changed)
                sorted_gainers = sort_by_gain_percentage(sorted_gainers)
                
                # Show filter results
                print(f" ({initial_count} → {after_market_cap} → {after_industry} qualify)")
            
            # Enrich with company descriptions, growth rates, and P/S ratios if Perplexity API is configured
            if sorted_gainers and config.perplexity_api_key:
                print("\nFetching company data:")
                
                def progress_callback(company, success, data_type=None):
                    if success:
                        if data_type == "growth":
                            print(f"  → {company} growth rate ✓")
                        elif data_type == "ps_ratio":
                            print(f"  → {company} P/S ratio ✓")
                        else:
                            print(f"  → {company} description ✓")
                    else:
                        # data_type contains error message when success is False
                        print(f"  → {company} ✗ ({data_type})")
                
                sorted_gainers = api_client.enrich_with_descriptions(
                    sorted_gainers,
                    config.perplexity_api_key,
                    progress_callback=progress_callback
                )
                
                # Count successful fetches
                desc_successful = sum(1 for stock in sorted_gainers if stock.get('description'))
                growth_successful = sum(1 for stock in sorted_gainers if stock.get('growth_rate'))
                ps_successful = sum(1 for stock in sorted_gainers if stock.get('ps_ratio') is not None)
                print(f"✓ Data fetching complete (descriptions: {desc_successful}/{len(sorted_gainers)}, growth rates: {growth_successful}/{len(sorted_gainers)}, P/S ratios: {ps_successful}/{len(sorted_gainers)})")
            
            # Log top gainers
            if sorted_gainers:
                logger.info("Top 5 gainers after all filters:")
                for i, stock in enumerate(sorted_gainers[:5], 1):
                    symbol = stock.get('symbol', 'N/A')
                    change = stock.get('changesPercentage', 'N/A')
                    logger.info(f"  {i}. {symbol}: {change}")
            
            # Send email if --test flag is set or if it's a regular run
            if args.test or not args.dry_run:
                email_sender = EmailSender(
                    smtp_server=config.smtp_server,
                    smtp_port=config.smtp_port,
                    sender_email=config.email_sender,
                    sender_password=config.email_password
                )
                
                print("\n✓ Sending email...", end="", flush=True)
                logger.info(f"Sending email to {config.email_recipient}...")
                success = email_sender.send_email(
                    recipient=config.email_recipient,
                    stocks=sorted_gainers,
                    dry_run=args.dry_run
                )
                
                if success:
                    print(" Done!")
                    print(f"\nEmail sent to: {config.email_recipient}")
                    logger.info("Email sent successfully!")
                else:
                    print(" Failed!")
                    logger.error("Failed to send email")
                    sys.exit(1)
            else:
                logger.info("Dry run mode - email not sent")
        
        logger.info("=== Stock Alerts Completed Successfully ===")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()