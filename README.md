# Stock Alerts - Daily 10%+ Gainers Email Notification

A Python script that automatically fetches daily stock market gainers and sends email notifications for stocks that gained 10% or more.

## Features

- Fetches real-time stock gainers from Financial Modeling Prep API
- Filters stocks with 10%+ daily gains
- Sends formatted HTML emails with stock details
- Includes command-line options for testing and dry runs
- Comprehensive logging to track script execution
- Production-ready error handling

## Prerequisites

- Python 3.7 or higher
- A Financial Modeling Prep API key
- A Gmail account with App Password enabled

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd daily_top_gainers
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

4. Configure your environment variables in `.env` (see Configuration section)

## Configuration

### Getting a Financial Modeling Prep API Key

1. Visit [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs/)
2. Sign up for a free account
3. Navigate to your dashboard to get your API key
4. Add the API key to your `.env` file

### Setting up Gmail App Password

1. Go to your [Google Account settings](https://myaccount.google.com/)
2. Navigate to Security
3. Enable 2-Step Verification if not already enabled
4. Go to [App passwords](https://myaccount.google.com/apppasswords)
5. Generate a new app password for "Mail"
6. Use this 16-character password in your `.env` file (not your regular Gmail password)

### Environment Variables

Update your `.env` file with the following:

```env
# Financial Modeling Prep API Key
FMP_API_KEY=your_actual_api_key_here

# Email Configuration
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_16_char_app_password
EMAIL_RECIPIENT=recipient@example.com

# SMTP Configuration (Gmail defaults)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## Usage

### Basic Usage

Run the script to fetch gainers and send email:
```bash
python main.py --test
```

### Command Line Options

- `--test`: Send email immediately (useful for testing)
- `--dry-run`: Preview the email without sending it

Examples:
```bash
# Test the script by sending email immediately
python main.py --test

# Preview email content without sending
python main.py --dry-run

# Both test and dry-run (preview immediately)
python main.py --test --dry-run
```

### Scheduling Daily Emails

To receive daily emails, set up a cron job (Linux/Mac) or Task Scheduler (Windows).

#### Linux/Mac (cron)
```bash
# Edit crontab
crontab -e

# Add this line to run at 4:30 PM Eastern Time daily
30 16 * * * cd /path/to/daily_top_gainers && /usr/bin/python3 main.py --test >> cron.log 2>&1
```

#### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create a new task
3. Set trigger to daily at your preferred time
4. Set action to run: `python.exe "C:\path\to\daily_top_gainers\main.py" --test`

## Email Format

The email includes:
- Subject line with count of 10%+ gainers
- HTML table with the following columns:
  - Stock Symbol
  - Company Name
  - Percentage Gain
  - Current Price
  - Previous Close Price
- Stocks sorted by gain percentage (highest first)
- Timestamp of when the email was generated

If no stocks gained 10%+ that day, the email will indicate "No stocks gained 10%+ today".

## Logging

All script activities are logged to `stock_alerts.log` including:
- API requests and responses
- Email sending status
- Error messages
- Daily statistics

## Troubleshooting

### Common Issues

1. **Authentication Error**: Ensure you're using an App Password, not your regular Gmail password
2. **API Errors**: Check your API key is valid and you haven't exceeded rate limits
3. **No Email Received**: Check spam folder and verify SMTP settings
4. **SSL/TLS Errors**: Ensure your Python installation has proper SSL certificates

### Debug Mode

View detailed logs:
```bash
tail -f stock_alerts.log
```

## Project Structure

```
daily_top_gainers/
├── main.py           # Entry point with CLI interface
├── config.py         # Configuration management
├── api_client.py     # Financial Modeling Prep API client
├── email_sender.py   # Email sending functionality
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variables template
├── .gitignore        # Git ignore rules
├── README.md         # This file
└── stock_alerts.log  # Generated log file
```

## Security Notes

- Never commit your `.env` file to version control
- Use environment variables for all sensitive data
- App passwords are more secure than regular passwords for automated scripts
- API keys should be kept confidential

## License

This project is provided as-is for educational and personal use.