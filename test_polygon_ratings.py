#!/usr/bin/env python3
"""Test script to fetch analyst price target history using Polygon API."""

from polygon import RESTClient
from datetime import datetime, timedelta
import sys

# API Configuration
API_KEY = "P_QrzKzuvur6ysG9X_EI983sP0j4rud2"

def fetch_analyst_ratings(ticker, limit=100):
    """
    Fetch analyst ratings and price targets for a ticker using Polygon API.
    
    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of results to fetch
    
    Returns:
        List of analyst ratings
    """
    print(f"\nFetching analyst ratings for {ticker}...")
    
    # Initialize the client
    client = RESTClient(API_KEY)
    
    # Fetch ratings
    ratings = []
    try:
        for rating in client.list_benzinga_ratings(
            ticker=ticker,
            limit=limit,
            sort="date.desc"
        ):
            ratings.append(rating)
    except Exception as e:
        print(f"Error fetching ratings: {e}")
        return []
    
    print(f"Found {len(ratings)} analyst updates")
    return ratings

def display_analyst_history(ticker, ratings):
    """
    Display formatted analyst price target history.
    
    Args:
        ticker: Stock ticker symbol
        ratings: List of analyst ratings from Polygon API
    """
    print(f"\n{'='*80}")
    print(f"ANALYST PRICE TARGET HISTORY FOR {ticker}")
    print(f"{'='*80}\n")
    
    if not ratings:
        print("No analyst ratings found")
        return
    
    # Group by timeframe
    recent_7d = []
    recent_30d = []
    recent_90d = []
    older = []
    
    today = datetime.now()
    
    for rating in ratings:
        # Parse date from rating
        if hasattr(rating, 'date'):
            try:
                # Handle both string and datetime objects
                if isinstance(rating.date, str):
                    date = datetime.strptime(rating.date[:10], "%Y-%m-%d")
                else:
                    date = rating.date
                
                days_ago = (today - date).days
                
                if days_ago <= 7:
                    recent_7d.append(rating)
                elif days_ago <= 30:
                    recent_30d.append(rating)
                elif days_ago <= 90:
                    recent_90d.append(rating)
                else:
                    older.append(rating)
            except Exception as e:
                print(f"Error parsing date: {e}")
                older.append(rating)
    
    # Display recent updates (last 7 days)
    if recent_7d:
        print("📅 LAST 7 DAYS")
        print("-" * 40)
        for rating in recent_7d[:5]:  # Show first 5
            display_single_rating(rating)
        if len(recent_7d) > 5:
            print(f"   ... and {len(recent_7d) - 5} more\n")
    
    # Display last 30 days
    if recent_30d:
        print("\n📅 LAST 30 DAYS")
        print("-" * 40)
        for rating in recent_30d[:5]:  # Show first 5
            display_single_rating(rating)
        if len(recent_30d) > 5:
            print(f"   ... and {len(recent_30d) - 5} more\n")
    
    # Display last 90 days
    if recent_90d:
        print("\n📅 LAST 90 DAYS")
        print("-" * 40)
        for rating in recent_90d[:5]:  # Show first 5
            display_single_rating(rating)
        if len(recent_90d) > 5:
            print(f"   ... and {len(recent_90d) - 5} more\n")
    
    # Show older count
    if older:
        print(f"\n📅 OLDER (90+ days): {len(older)} updates\n")
    
    # Calculate and display statistics
    display_statistics(ratings)

def display_single_rating(rating):
    """Display a single analyst rating update."""
    try:
        # Parse date
        if hasattr(rating, 'date'):
            if isinstance(rating.date, str):
                date = datetime.strptime(rating.date[:10], "%Y-%m-%d")
            else:
                date = rating.date
            date_str = date.strftime("%b %d")
        else:
            date_str = "N/A"
        
        # Get firm name - check multiple possible attribute names
        firm = getattr(rating, 'firm', None) or getattr(rating, 'analyst_firm', 'Unknown Firm')
        if len(firm) > 20:
            firm = firm[:17] + "..."
        
        # Get action - check multiple possible attribute names
        action = getattr(rating, 'rating_action', None) or getattr(rating, 'action', 'Updates')
        if action:
            action = action.capitalize()
        
        # Get rating - check multiple possible attribute names
        rating_current = getattr(rating, 'rating', None) or getattr(rating, 'rating_current', '')
        
        # Get price targets
        pt_current = getattr(rating, 'price_target', None)
        pt_prior = getattr(rating, 'price_target_prior', None)
        
        # Format price target change
        if pt_current:
            if pt_prior and pt_prior != pt_current:
                change = pt_current - pt_prior
                if change > 0:
                    pt_str = f"↑ ${pt_prior:.0f}→${pt_current:.0f}"
                else:
                    pt_str = f"↓ ${pt_prior:.0f}→${pt_current:.0f}"
            else:
                pt_str = f"${pt_current:.0f}"
        else:
            pt_str = "N/A"
        
        # Rating emoji - handle lowercase ratings
        rating_lower = rating_current.lower() if rating_current else ''
        rating_emoji = {
            'buy': '🟢',
            'strong buy': '🟢',
            'outperform': '🟢',
            'overweight': '🟢',
            'positive': '🟢',
            'hold': '🟡',
            'neutral': '🟡',
            'market perform': '🟡',
            'equal weight': '🟡',
            'sell': '🔴',
            'underperform': '🔴',
            'underweight': '🔴',
            'negative': '🔴'
        }.get(rating_lower, '⚪')
        
        print(f"   {date_str} | {firm:20s} | {action:10s} | {rating_emoji} {rating_current:12s} | {pt_str}")
        
    except Exception as e:
        print(f"   Error displaying rating: {e}")

def display_statistics(ratings):
    """Display summary statistics for analyst ratings."""
    print("="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    # Extract all current price targets
    all_targets = []
    recent_targets = []
    
    today = datetime.now()
    
    for rating in ratings:
        pt = getattr(rating, 'price_target', None)
        if pt and pt > 0:
            all_targets.append(pt)
            
            # Check if recent (last 30 days)
            if hasattr(rating, 'date'):
                try:
                    if isinstance(rating.date, str):
                        date = datetime.strptime(rating.date[:10], "%Y-%m-%d")
                    else:
                        date = rating.date
                    
                    if (today - date).days <= 30:
                        recent_targets.append(pt)
                except:
                    pass
    
    if all_targets:
        # Overall statistics
        avg_target = sum(all_targets) / len(all_targets)
        min_target = min(all_targets)
        max_target = max(all_targets)
        median_target = sorted(all_targets)[len(all_targets)//2]
        
        print(f"\n📊 Current Consensus (all {len(all_targets)} analysts with price targets):")
        print(f"   Average Target: ${avg_target:.2f}")
        print(f"   Median Target: ${median_target:.2f}")
        print(f"   Range: ${min_target:.0f} - ${max_target:.0f}")
        
        # Recent trend
        if recent_targets:
            recent_avg = sum(recent_targets) / len(recent_targets)
            print(f"\n📈 Recent Trend (last 30 days, {len(recent_targets)} updates):")
            print(f"   Average Target: ${recent_avg:.2f}")
            
            # Compare to overall
            if recent_avg > avg_target:
                trend = f"↑ {((recent_avg/avg_target - 1) * 100):.1f}% above overall average"
            elif recent_avg < avg_target:
                trend = f"↓ {((1 - recent_avg/avg_target) * 100):.1f}% below overall average"
            else:
                trend = "→ Same as overall average"
            print(f"   Trend: {trend}")
    
    # Count rating actions
    actions = {}
    for rating in ratings[:30]:  # Last 30 updates
        action = getattr(rating, 'action', 'Unknown')
        actions[action] = actions.get(action, 0) + 1
    
    if actions:
        print(f"\n📋 Recent Actions (last {min(30, len(ratings))} updates):")
        for action, count in sorted(actions.items(), key=lambda x: x[1], reverse=True):
            print(f"   {action}: {count}")

def main():
    """Main function to run the test."""
    # Get ticker from command line or use default
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    else:
        ticker = input("Enter stock ticker (e.g., AAPL, CRWD): ").upper()
    
    if not ticker:
        ticker = "AAPL"  # Default
    
    # Get limit from command line
    limit = 100  # Default
    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except:
            pass
    
    print("\n" + "="*80)
    print("POLYGON ANALYST RATINGS TRACKER")
    print("="*80)
    print(f"\nUsing Polygon API with Benzinga data")
    print(f"Ticker: {ticker}")
    print(f"Fetching up to {limit} recent analyst updates...")
    
    # Fetch and display data
    ratings = fetch_analyst_ratings(ticker, limit)
    
    if ratings:
        display_analyst_history(ticker, ratings)
        
        # Show sample raw data for debugging
        print("\n" + "="*80)
        print("SAMPLE RAW DATA (First Rating)")
        print("="*80)
        first_rating = ratings[0]
        print(f"\nAvailable attributes:")
        for attr in dir(first_rating):
            if not attr.startswith('_'):
                value = getattr(first_rating, attr, None)
                if not callable(value):
                    print(f"   {attr}: {value}")
    else:
        print("\nNo data retrieved. Please check:")
        print("1. The ticker symbol is valid")
        print("2. The API key has access to Benzinga data")
        print("3. Your network connection is working")

if __name__ == "__main__":
    main()