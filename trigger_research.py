#!/usr/bin/env python3
"""Trigger deep research generation via GitHub Actions API."""

import argparse
import requests
import os
from urllib.parse import quote


def trigger_deep_research(symbol: str, company_name: str = None, github_token: str = None):
    """Trigger deep research workflow via GitHub API.
    
    Args:
        symbol: Stock symbol
        company_name: Optional company name
        github_token: GitHub personal access token
    """
    if not github_token:
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            print("Error: GitHub token required. Set GITHUB_TOKEN environment variable.")
            return False
    
    # GitHub API endpoint for triggering workflow
    owner = "Shredderman555"
    repo = "daily_top_gainers"
    workflow_id = "deep-research.yml"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
    
    # Prepare payload
    payload = {
        "ref": "main",
        "inputs": {
            "symbol": symbol
        }
    }
    
    if company_name:
        payload["inputs"]["company_name"] = company_name
    
    # Headers
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }
    
    # Make request
    print(f"Triggering deep research for {symbol}...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 204:
        print("✓ Deep research workflow triggered successfully!")
        print(f"Check progress at: https://github.com/{owner}/{repo}/actions")
        return True
    else:
        print(f"✗ Failed to trigger workflow: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Trigger deep research report generation via GitHub Actions'
    )
    parser.add_argument('symbol', help='Stock symbol (e.g., AAPL, MSFT)')
    parser.add_argument('--name', help='Company name (optional)')
    parser.add_argument('--token', help='GitHub personal access token (or set GITHUB_TOKEN env var)')
    
    args = parser.parse_args()
    
    success = trigger_deep_research(args.symbol, args.name, args.token)
    exit(0 if success else 1)


if __name__ == "__main__":
    main()