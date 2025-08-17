#!/usr/bin/env python3
"""
Check recent price target changes for any stock.

Usage:
    python3 check_price_targets.py TICKER [DAYS]
    
Examples:
    python3 check_price_targets.py WULF        # Last 7 days for WULF
    python3 check_price_targets.py NVDA 30     # Last 30 days for NVDA
"""

import sys
from datetime import datetime, timedelta
from config import Config
from polygon_client import PolygonClient


def format_change(change_pct):
    """Format percentage change with color."""
    if change_pct > 0:
        return f"\033[92m+{change_pct:.1f}%\033[0m"  # Green
    elif change_pct < 0:
        return f"\033[91m{change_pct:.1f}%\033[0m"  # Red
    else:
        return f"{change_pct:.1f}%"


def main():
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 check_price_targets.py TICKER [DAYS]")
        print("Example: python3 check_price_targets.py WULF")
        print("Example: python3 check_price_targets.py NVDA 30")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    days = 7  # Default
    
    if len(sys.argv) > 2:
        try:
            days = int(sys.argv[2])
        except ValueError:
            print(f"Error: Days must be a number, got '{sys.argv[2]}'")
            sys.exit(1)
    
    # Load config
    config = Config()
    
    # Initialize Polygon client
    with PolygonClient(config.polygon_api_key) as client:
        # Fetch analyst ratings
        print(f"Fetching {ticker} analyst ratings...")
        ratings = client.fetch_analyst_ratings(ticker, limit=100)
        
        if not ratings:
            print(f"No analyst ratings found for {ticker}")
            sys.exit(0)
        
        # Filter for requested time period
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_changes = []
        
        for rating in ratings:
            # Parse date
            if hasattr(rating, 'date'):
                try:
                    if isinstance(rating.date, str):
                        rating_date = datetime.strptime(rating.date[:10], "%Y-%m-%d")
                    else:
                        rating_date = rating.date
                except:
                    continue
                
                if rating_date >= cutoff_date:
                    # Get price target info
                    current_target = getattr(rating, 'price_target', None)
                    previous_target = getattr(rating, 'previous_price_target', None)
                    firm = getattr(rating, 'firm', 'Unknown')
                    rating_value = getattr(rating, 'rating', '')
                    action = getattr(rating, 'rating_action', '') or getattr(rating, 'action', '')
                    
                    if current_target:
                        change_pct = 0
                        change_type = "New Coverage"
                        
                        if previous_target:
                            change_pct = ((current_target - previous_target) / previous_target) * 100
                            if change_pct > 0.1:
                                change_type = "\033[92mRaised\033[0m"  # Green
                            elif change_pct < -0.1:
                                change_type = "\033[91mLowered\033[0m"  # Red
                            else:
                                change_type = "Reiterated"
                        
                        recent_changes.append({
                            'date': rating_date,
                            'firm': firm,
                            'action': action,
                            'rating': rating_value,
                            'previous_target': previous_target,
                            'current_target': current_target,
                            'change_pct': change_pct,
                            'change_type': change_type
                        })
        
        # Display results
        print(f"\n{'='*70}")
        print(f"{ticker} Price Target Changes - Last {days} Days")
        print(f"{'='*70}\n")
        
        if recent_changes:
            # Sort by date (most recent first)
            recent_changes.sort(key=lambda x: x['date'], reverse=True)
            
            # Summary stats
            raises = sum(1 for c in recent_changes if c['change_pct'] > 0.1)
            cuts = sum(1 for c in recent_changes if c['change_pct'] < -0.1)
            reiterations = sum(1 for c in recent_changes if -0.1 <= c['change_pct'] <= 0.1 and c['previous_target'])
            new_coverage = sum(1 for c in recent_changes if not c['previous_target'])
            
            print(f"Summary: {raises} Raises | {cuts} Cuts | {reiterations} Reiterations | {new_coverage} New Coverage")
            print("-" * 70)
            
            for change in recent_changes:
                print(f"\nDate: {change['date'].strftime('%Y-%m-%d (%A)')}")
                print(f"Analyst: {change['firm']}")
                
                if change['action']:
                    print(f"Action: {change['action']}")
                if change['rating']:
                    print(f"Rating: {change['rating']}")
                
                if change['previous_target']:
                    print(f"Target: ${change['previous_target']:.2f} → ${change['current_target']:.2f} ({change['change_type']})")
                    if change['change_pct'] != 0:
                        print(f"Change: {format_change(change['change_pct'])}")
                else:
                    print(f"Target: ${change['current_target']:.2f} ({change['change_type']})")
                
                print("-" * 50)
        else:
            print(f"No price target changes found for {ticker} in the last {days} days")
        
        print(f"\nTotal changes found: {len(recent_changes)}")
        
        # Show average target if there are recent changes
        if recent_changes:
            current_targets = [c['current_target'] for c in recent_changes]
            avg_target = sum(current_targets) / len(current_targets)
            print(f"Average current target: ${avg_target:.2f}")


if __name__ == "__main__":
    main()