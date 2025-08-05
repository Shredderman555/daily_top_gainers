# Deep Research Feature

This feature allows you to generate comprehensive investment research reports for stocks using Perplexity's sonar-deep-research model.

## How It Works

1. **From Email**: Each stock card in the daily alerts email now includes a "Generate Deep Research Report" button
2. **Manual Trigger**: You can also trigger research reports manually using the command line or GitHub Actions

## Usage Methods

### Method 1: Email Button (Simplest)
1. Click the "Generate Deep Research Report" button in any stock card
2. You'll be redirected to GitHub Actions (requires GitHub login)
3. Click "Run workflow" and confirm the stock symbol
4. The research report will be emailed to you in 2-5 minutes

### Method 2: Command Line (Direct)
```bash
# Basic usage
python deep_research.py AAPL

# With company name (faster, skips lookup)
python deep_research.py AAPL --name "Apple Inc."
```

### Method 3: GitHub Actions Web UI
1. Go to https://github.com/Shredderman555/daily_top_gainers/actions
2. Click on "Generate Deep Research Report" workflow
3. Click "Run workflow"
4. Enter the stock symbol and optionally the company name
5. Click "Run workflow"

### Method 4: API Trigger
```bash
# Set your GitHub token
export GITHUB_TOKEN=your_github_personal_access_token

# Trigger research
python trigger_research.py AAPL --name "Apple Inc."
```

## Research Report Contents

The deep research report includes:

- **Company Overview**: What they do in 100 words or less
- **Key Metrics**: Market cap, revenue growth, P/S ratios, margins, R&D spending
- **Competitive Analysis**: 
  - Competitive advantage score (0-10)
  - Competitive landscape overview
  - Detailed competitive advantage analysis
  - Market share evolution predictions
- **Valuation Analysis**:
  - Expected IRR calculation
  - Revenue projections and reasoning
  - P/S ratio projections and reasoning
  - Exit valuation factors

## Requirements

- Perplexity API key with access to sonar-deep-research model
- GitHub account (for email button method)
- GitHub personal access token (for API trigger method)

## Processing Time

Deep research reports typically take 30-60 seconds to generate due to the comprehensive analysis performed by the sonar-deep-research model.

## Rate Limits

- Perplexity may have rate limits on deep research requests
- GitHub Actions has usage limits based on your plan
- Be mindful of API costs when generating multiple reports