#!/usr/bin/env python3
"""Setup GitHub token for deep research triggers."""

import os
import re
import sys

def setup_github_token():
    """Guide user through setting up GitHub token and updating trigger.html."""
    
    print("Deep Research Setup - GitHub Token Configuration")
    print("=" * 50)
    print()
    print("To enable one-click research reports from emails, we need to set up a GitHub token.")
    print()
    print("Steps:")
    print("1. Go to: https://github.com/settings/tokens/new")
    print("2. Set token name: 'Daily Top Gainers Research'")
    print("3. Set expiration: 90 days (or longer)")
    print("4. Select scopes: 'repo' and 'workflow'")
    print("5. Click 'Generate token' and copy the token")
    print()
    
    token = input("Paste your GitHub token here (starts with ghp_): ").strip()
    
    if not token.startswith('ghp_'):
        print("Error: Invalid token format. GitHub tokens start with 'ghp_'")
        return False
    
    # Update trigger.html with the token
    trigger_path = os.path.join(os.path.dirname(__file__), 'docs', 'trigger.html')
    
    try:
        with open(trigger_path, 'r') as f:
            content = f.read()
        
        # Replace the placeholder token
        updated_content = re.sub(
            r"const GITHUB_TOKEN = 'ghp_' \+ 'PLACEHOLDER_TOKEN';",
            f"const GITHUB_TOKEN = '{token}';",
            content
        )
        
        with open(trigger_path, 'w') as f:
            f.write(updated_content)
        
        print()
        print("✓ Token configured successfully!")
        print()
        print("Next steps:")
        print("1. Commit and push changes: git add -A && git commit -m 'Configure GitHub token' && git push")
        print("2. Enable GitHub Pages:")
        print("   - Go to: https://github.com/Shredderman555/daily_top_gainers/settings/pages")
        print("   - Source: Deploy from a branch")
        print("   - Branch: main")
        print("   - Folder: /docs")
        print("   - Click Save")
        print()
        print("3. Wait 2-3 minutes for GitHub Pages to deploy")
        print("4. Your research buttons in emails will now work without login!")
        
        return True
        
    except Exception as e:
        print(f"Error updating trigger.html: {e}")
        return False

if __name__ == "__main__":
    success = setup_github_token()
    sys.exit(0 if success else 1)