#!/usr/bin/env python3
"""Test email sending for a single specified stock."""

import argparse
from config import Config
from api_client import FMPAPIClient
from email_sender import EmailSender

def main():
    parser = argparse.ArgumentParser(description='Send test email for a single stock')
    parser.add_argument('symbol', help='Stock symbol (e.g., AAPL, TSLA)')
    parser.add_argument('--name', help='Company name (optional)')
    parser.add_argument('--gain', type=float, default=15.0, help='Gain percentage (default: 15.0)')
    parser.add_argument('--price', type=float, default=100.0, help='Stock price (default: 100.0)')
    parser.add_argument('--market-cap', type=float, default=1_000_000_000, help='Market cap (default: 1B)')
    
    args = parser.parse_args()
    
    # Create test stock data
    test_stock = [{
        'symbol': args.symbol.upper(),
        'name': args.name or f'{args.symbol} Company',
        'changesPercentage': args.gain,
        'price': args.price,
        'mktCap': args.market_cap
    }]
    
    # Load config and enrich with Perplexity data
    config = Config()
    
    if config.perplexity_api_key:
        with FMPAPIClient(config.fmp_api_key) as api:
            # Fetch real company profile to get accurate name
            print(f"Fetching company profile for {args.symbol.upper()}...")
            profile = api.get_company_profile(args.symbol.upper())
            if profile and 'companyName' in profile:
                # Use real company name from FMP
                test_stock[0]['name'] = profile['companyName']
                print(f"Using company name: {test_stock[0]['name']}")
            
            # Check technical nature first
            print(f"Checking technical nature...")
            test_stock = api.check_technical_nature(test_stock, config.perplexity_api_key)
            
            # Check if it's technical
            if test_stock[0].get('is_technical') is False:
                print(f"Note: {test_stock[0]['name']} is not a technical/engineering-heavy company")
            
            # Fetch remaining Perplexity data
            print(f"Fetching detailed company data...")
            test_stock = api.enrich_with_descriptions(test_stock, config.perplexity_api_key)
            
            # Fetch Polygon analyst data
            if config.polygon_api_key:
                print(f"Fetching analyst ratings from Polygon...")
                test_stock = api.enrich_with_polygon_data(test_stock, config.polygon_api_key)
    
    # Fetch put/call ratio
    put_call_ratio = None
    if config.perplexity_api_key:
        print("Fetching put/call ratio...")
        from perplexity_client import PerplexityClient
        with PerplexityClient(config.perplexity_api_key) as perplexity:
            put_call_ratio = perplexity.get_put_call_ratio()
        if put_call_ratio:
            print(f"Put/Call Ratio: {put_call_ratio}")
    
    # Send email
    print("Sending email...")
    sender = EmailSender(
        config.smtp_server, 
        config.smtp_port, 
        config.email_sender, 
        config.email_password
    )
    
    if sender.send_email(config.email_recipient, test_stock, put_call_ratio=put_call_ratio):
        print(f"✓ Email sent successfully for {args.symbol}")
    else:
        print("✗ Failed to send email")

if __name__ == "__main__":
    main()