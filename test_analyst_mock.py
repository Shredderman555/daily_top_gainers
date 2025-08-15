#!/usr/bin/env python3
"""
Mock demonstration of analyst price target tracking.
Since the Benzinga endpoint requires separate authentication,
this shows what the data structure and analysis would look like.
"""

from datetime import datetime, timedelta
import random

def generate_mock_analyst_data(ticker, days_back=180):
    """
    Generate mock analyst rating data to demonstrate the structure.
    In production, this would come from the API.
    """
    firms = [
        "Morgan Stanley", "Goldman Sachs", "Bank of America",
        "Barclays", "Citi", "UBS", "Wells Fargo", "JPMorgan",
        "Wedbush", "Piper Sandler", "KeyBanc", "Loop Capital"
    ]
    
    ratings = ["Buy", "Outperform", "Neutral", "Underperform", "Sell"]
    
    # Generate mock data
    data = []
    current_date = datetime.now()
    
    # Create 15-20 analyst updates over the period
    num_updates = random.randint(15, 20)
    
    for i in range(num_updates):
        days_ago = random.randint(1, days_back)
        date = current_date - timedelta(days=days_ago)
        
        firm = random.choice(firms)
        rating = random.choice(ratings)
        
        # Generate price targets (for AAPL-like stock around $200)
        base_price = 200
        pt_current = base_price + random.randint(-50, 50)
        pt_prior = pt_current + random.randint(-15, 15)
        
        data.append({
            'date': date.strftime("%Y-%m-%d"),
            'firm': firm,
            'rating': rating,
            'price_target': pt_current,
            'price_target_prior': pt_prior if random.random() > 0.3 else None,
            'action': random.choice(['Maintains', 'Raises', 'Lowers', 'Initiates'])
        })
    
    # Sort by date descending
    data.sort(key=lambda x: x['date'], reverse=True)
    
    return data

def display_analyst_history(ticker, data):
    """Display analyst price target history."""
    
    print(f"\n{'='*80}")
    print(f"ANALYST PRICE TARGET HISTORY FOR {ticker}")
    print(f"{'='*80}\n")
    
    print(f"Found {len(data)} analyst updates in the last 180 days:\n")
    
    # Group by timeframe
    recent = []
    last_week = []
    last_month = []
    older = []
    
    today = datetime.now()
    
    for item in data:
        date = datetime.strptime(item['date'], "%Y-%m-%d")
        days_ago = (today - date).days
        
        if days_ago <= 7:
            last_week.append(item)
        elif days_ago <= 30:
            last_month.append(item)
        elif days_ago <= 90:
            recent.append(item)
        else:
            older.append(item)
    
    # Display by timeframe
    if last_week:
        print("📅 LAST 7 DAYS")
        print("-" * 40)
        for item in last_week:
            display_rating(item)
    
    if last_month:
        print("\n📅 LAST 30 DAYS")
        print("-" * 40)
        for item in last_month:
            display_rating(item)
    
    if recent:
        print("\n📅 LAST 90 DAYS")
        print("-" * 40)
        for item in recent[:5]:  # Show first 5
            display_rating(item)
        if len(recent) > 5:
            print(f"   ... and {len(recent) - 5} more\n")
    
    if older:
        print(f"\n📅 OLDER (90-180 days): {len(older)} updates\n")
    
    # Calculate statistics
    print("="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    all_targets = [d['price_target'] for d in data if d['price_target']]
    if all_targets:
        avg_target = sum(all_targets) / len(all_targets)
        min_target = min(all_targets)
        max_target = max(all_targets)
        median_target = sorted(all_targets)[len(all_targets)//2]
        
        print(f"\n📊 Current Consensus (all analysts):")
        print(f"   Average Target: ${avg_target:.2f}")
        print(f"   Median Target: ${median_target:.2f}")
        print(f"   Range: ${min_target:.0f} - ${max_target:.0f}")
        
        # Recent trend (last 30 days)
        recent_data = last_week + last_month
        if recent_data:
            recent_targets = [d['price_target'] for d in recent_data]
            recent_avg = sum(recent_targets) / len(recent_targets)
            print(f"\n📈 Recent Trend (last 30 days):")
            print(f"   Average Target: ${recent_avg:.2f}")
            print(f"   Number of Updates: {len(recent_data)}")
            
            # Count actions
            raises = sum(1 for d in recent_data if d['action'] == 'Raises')
            lowers = sum(1 for d in recent_data if d['action'] == 'Lowers')
            maintains = sum(1 for d in recent_data if d['action'] == 'Maintains')
            
            print(f"   Actions: {raises} raises, {lowers} lowers, {maintains} maintains")

def display_rating(item):
    """Display a single rating update."""
    date = datetime.strptime(item['date'], "%Y-%m-%d")
    date_str = date.strftime("%b %d")
    
    firm = item['firm']
    action = item['action']
    rating = item['rating']
    pt = item['price_target']
    pt_prior = item['price_target_prior']
    
    # Format the display
    if pt_prior and pt != pt_prior:
        change = pt - pt_prior
        if change > 0:
            change_str = f"↑ ${pt_prior}→${pt}"
        else:
            change_str = f"↓ ${pt_prior}→${pt}"
    else:
        change_str = f"${pt}"
    
    # Color code rating
    rating_emoji = {
        'Buy': '🟢',
        'Outperform': '🟢',
        'Neutral': '🟡',
        'Underperform': '🔴',
        'Sell': '🔴'
    }.get(rating, '⚪')
    
    print(f"   {date_str} | {firm:20s} | {action:10s} | {rating_emoji} {rating:12s} | {change_str}")

def main():
    """Main function to demonstrate analyst tracking."""
    import sys
    
    # Get ticker
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    
    print("\n" + "="*80)
    print("ANALYST PRICE TARGET TRACKER (Demo)")
    print("="*80)
    print("\nNOTE: This is using mock data to demonstrate the functionality.")
    print("In production, this would connect to the Benzinga API through Polygon.\n")
    
    # Generate and display mock data
    data = generate_mock_analyst_data(ticker)
    display_analyst_history(ticker, data)
    
    print("\n💡 To implement with real data:")
    print("   1. Set up Benzinga API access through Polygon")
    print("   2. Replace generate_mock_analyst_data() with API call")
    print("   3. Parse the JSON response into the same structure")

if __name__ == "__main__":
    main()