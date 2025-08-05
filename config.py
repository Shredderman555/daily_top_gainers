"""Configuration management for the stock alerts application."""

import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv


class Config:
    """Application configuration loaded from environment variables."""
    
    def __init__(self):
        """Initialize configuration by loading environment variables."""
        load_dotenv()
        self._validate_config()
    
    @property
    def fmp_api_key(self) -> str:
        """Get Financial Modeling Prep API key."""
        return os.getenv('FMP_API_KEY', '')
    
    @property
    def email_sender(self) -> str:
        """Get sender email address."""
        return os.getenv('EMAIL_SENDER', '')
    
    @property
    def email_password(self) -> str:
        """Get email password."""
        return os.getenv('EMAIL_PASSWORD', '')
    
    @property
    def email_recipient(self) -> str:
        """Get recipient email address."""
        return os.getenv('EMAIL_RECIPIENT', '')
    
    @property
    def smtp_server(self) -> str:
        """Get SMTP server address."""
        return os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    
    @property
    def smtp_port(self) -> int:
        """Get SMTP server port."""
        port_str = os.getenv('SMTP_PORT', '587')
        try:
            return int(port_str)
        except ValueError:
            print(f"Error: Invalid SMTP_PORT value: '{port_str}'. Must be a number (e.g., 587).")
            print("Please check your GitHub Secrets or environment variables.")
            # Default to 587 for Gmail
            return 587
    
    @property
    def perplexity_api_key(self) -> str:
        """Get Perplexity API key."""
        return os.getenv('PERPLEXITY_API_KEY', '')
    
    def _validate_config(self) -> None:
        """Validate that all required configuration values are present."""
        required_vars = {
            'FMP_API_KEY': self.fmp_api_key,
            'EMAIL_SENDER': self.email_sender,
            'EMAIL_PASSWORD': self.email_password,
            'EMAIL_RECIPIENT': self.email_recipient
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
            print("Please create a .env file based on .env.example and fill in all values.")
            sys.exit(1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            'email_sender': self.email_sender,
            'email_recipient': self.email_recipient,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'api_configured': bool(self.fmp_api_key),
            'email_configured': bool(self.email_password),
            'perplexity_configured': bool(self.perplexity_api_key)
        }