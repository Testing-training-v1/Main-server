#!/usr/bin/env python3
"""
CircleCI-specific Dropbox authentication handler.

This module ensures that Dropbox authentication works in CircleCI
by hardcoding the necessary credentials and handling token refresh.
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Hardcoded credentials - same as in config.py
DROPBOX_APP_KEY = "2bi422xpd3xd962"
DROPBOX_APP_SECRET = "j3yx0b41qdvfu86"
DROPBOX_REFRESH_TOKEN = "RvyL03RE5qAAAAAAAAAAAVMVebvE7jDx8Okd0ploMzr85c6txvCRXpJAt30mxrKF"

def ensure_dropbox_auth():
    """Ensure Dropbox authentication is set up correctly in CircleCI."""
    # Set environment variables
    os.environ["DROPBOX_APP_KEY"] = DROPBOX_APP_KEY
    os.environ["DROPBOX_APP_SECRET"] = DROPBOX_APP_SECRET
    os.environ["DROPBOX_REFRESH_TOKEN"] = DROPBOX_REFRESH_TOKEN
    os.environ["DROPBOX_ENABLED"] = "True"
    
    # Create token file if it doesn't exist
    if not os.path.exists("dropbox_tokens.json"):
        with open("dropbox_tokens.json", "w") as f:
            json.dump({
                "refresh_token": DROPBOX_REFRESH_TOKEN,
                "app_key": DROPBOX_APP_KEY,
                "app_secret": DROPBOX_APP_SECRET
            }, f, indent=2)
        logger.info("Created dropbox_tokens.json")
    
    # Refresh the token
    refresh_access_token()
    
    logger.info("Dropbox authentication configured for CircleCI")
    
def refresh_access_token():
    """
    Refresh the Dropbox access token using the refresh token.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Refreshing Dropbox access token")
        
        # Use the hardcoded credentials
        token_url = "https://api.dropboxapi.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": DROPBOX_REFRESH_TOKEN,
            "client_id": DROPBOX_APP_KEY,
            "client_secret": DROPBOX_APP_SECRET
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            
            # Update environment variable
            os.environ["DROPBOX_ACCESS_TOKEN"] = access_token
            
            # Calculate expiry time
            expires_in = token_data.get("expires_in", 14400)  # Default 4 hours
            expiry_time = datetime.now() + timedelta(seconds=expires_in)
            expiry_iso = expiry_time.isoformat()
            
            # Create tokens dict
            tokens = {
                "access_token": access_token,
                "refresh_token": DROPBOX_REFRESH_TOKEN,
                "expiry_time": expiry_iso,
                "app_key": DROPBOX_APP_KEY,
                "app_secret": DROPBOX_APP_SECRET
            }
            
            # Save to file
            with open("dropbox_tokens.json", "w") as f:
                json.dump(tokens, f, indent=2)
            logger.info("Saved refreshed tokens to dropbox_tokens.json")
            
            # Try to update config if possible
            try:
                import config
                config.DROPBOX_ACCESS_TOKEN = access_token
                config.DROPBOX_TOKEN_EXPIRY = expiry_iso
            except (ImportError, AttributeError):
                pass
                
            logger.info("Successfully refreshed Dropbox access token")
            return True
        else:
            logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error refreshing access token: {e}")
        return False

# Auto-execute when imported in CircleCI
if os.environ.get("CIRCLECI") == "true" or os.environ.get("CIRCLECI_ENV") == "True":
    logger.info("CircleCI environment detected - ensuring Dropbox authentication")
    ensure_dropbox_auth()
