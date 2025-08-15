#!/usr/bin/env python3
"""Test script to fetch analyst price target changes from Polygon API."""

import requests
import json
from datetime import datetime, timedelta
import sys

# API Configuration
API_KEY = "P_QrzKzuvur6ysG9X_EI983sP0j4rud2"
BASE_URL = "https://api.polygon.io/v1/meta/symbols"

def get_analyst_ratings(ticker, days_back=180):
    """
    Fetch analyst ratings and price target changes for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        days_back: Number of days to look back (default 180)
    
    Returns:
        List of analyst rating changes
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Format dates as YYYY-MM-DD
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Construct URL for Benzinga analyst ratings
    # Using the partners endpoint
    url = "https://api.polygon.io/v1/marketdata/biz/analyst-ratings"
    
    # Parameters
    params = {
        "apiKey": API_KEY,
        "ticker": ticker,
        "date.gte": start_str,
        "date.lte": end_str,
        "limit": 100,
        "sort": "date",
        "order": "desc"
    }
    
    try:
        print(f"\nFetching analyst ratings for {ticker}...")
        print(f"Date range: {start_str} to {end_str}")
        print(f"URL: {url}")
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def display_price_targets(data, ticker):
    """
    Display price target changes from the analyst data.
    
    Args:
        data: Response data from API
        ticker: Stock ticker symbol
    """
    if not data:
        print("No data to display")
        return
    
    print(f"\n{'='*80}")
    print(f"ANALYST PRICE TARGET HISTORY FOR {ticker}")
    print(f"{'='*80}\n")
    
    # Check if we have results
    if 'results' in data:
        ratings = data.get('results', [])
        
        if not ratings:
            print("No analyst ratings found for this period")
            return
        
        # Filter for entries with price targets
        price_target_changes = []
        
        for rating in ratings:
            if rating.get('price_target') or rating.get('adjusted_price_target'):
                price_target_changes.append(rating)
        
        if not price_target_changes:
            print("No price target changes found")
            return
        
        print(f"Found {len(price_target_changes)} price target updates:\n")
        
        # Display each price target change
        for i, rating in enumerate(price_target_changes, 1):
            print(f"{i}. {'-'*60}")
            
            # Extract key information
            date = rating.get('updated_date', rating.get('date', 'N/A'))
            firm = rating.get('analyst_firm', 'Unknown Firm')
            analyst = rating.get('analyst_name', '')
            action = rating.get('action', '')
            rating_current = rating.get('rating_current', '')
            rating_prior = rating.get('rating_prior', '')
            pt_current = rating.get('price_target', rating.get('adjusted_price_target'))
            pt_prior = rating.get('price_target_prior', rating.get('adjusted_price_target_prior'))
            
            # Format date
            if date != 'N/A':
                try:
                    date_obj = datetime.strptime(date[:10], "%Y-%m-%d")
                    date = date_obj.strftime("%B %d, %Y")
                except:
                    pass
            
            print(f"   Date: {date}")
            print(f"   Firm: {firm}")
            if analyst:
                print(f"   Analyst: {analyst}")
            
            # Show action
            if action:
                print(f"   Action: {action}")
            
            # Show rating change
            if rating_current:
                if rating_prior and rating_prior != rating_current:
                    print(f"   Rating: {rating_prior} → {rating_current}")
                else:
                    print(f"   Rating: {rating_current}")
            
            # Show price target change
            if pt_current:
                if pt_prior and pt_prior != pt_current:
                    change = pt_current - pt_prior
                    change_pct = (change / pt_prior * 100) if pt_prior else 0
                    if change > 0:
                        print(f"   Price Target: ${pt_prior:.0f} → ${pt_current:.0f} (+${change:.0f}, +{change_pct:.1f}%)")
                    else:
                        print(f"   Price Target: ${pt_prior:.0f} → ${pt_current:.0f} (${change:.0f}, {change_pct:.1f}%)")
                else:
                    print(f"   Price Target: ${pt_current:.0f}")
            
            print()
        
        # Calculate summary statistics
        print(f"{'='*80}")
        print("SUMMARY STATISTICS")
        print(f"{'='*80}\n")
        
        # Get all current price targets
        current_targets = [r.get('price_target', r.get('adjusted_price_target')) 
                          for r in price_target_changes 
                          if r.get('price_target') or r.get('adjusted_price_target')]
        
        if current_targets:
            avg_target = sum(current_targets) / len(current_targets)
            min_target = min(current_targets)
            max_target = max(current_targets)
            
            print(f"Total Updates: {len(price_target_changes)}")
            print(f"Average Target: ${avg_target:.2f}")
            print(f"Min Target: ${min_target:.2f}")
            print(f"Max Target: ${max_target:.2f}")
            print(f"Range: ${min_target:.0f} - ${max_target:.0f}")
        
    else:
        print("Unexpected response format")
        print(f"Response: {json.dumps(data, indent=2)}")

def main():
    """Main function to run the test."""
    # Get ticker from command line or use default
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    else:
        ticker = input("Enter stock ticker (e.g., AAPL): ").upper()
    
    if not ticker:
        ticker = "AAPL"  # Default
    
    # Get number of days to look back
    days = 180  # Default to 6 months
    if len(sys.argv) > 2:
        try:
            days = int(sys.argv[2])
        except:
            pass
    
    # Fetch and display data
    data = get_analyst_ratings(ticker, days)
    display_price_targets(data, ticker)

if __name__ == "__main__":
    main()