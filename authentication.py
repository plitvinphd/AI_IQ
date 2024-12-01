# authentication.py

import hashlib
import os
import json

def hash_password(password):
    """
    Hash a password for storing.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """
    Verify a stored password against one provided by user.
    """
    return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()

def save_user_credentials(username, password, api_keys):
    """
    Save user credentials and API keys securely.
    """
    credentials = {
        'username': username,
        'password': hash_password(password),
        'api_keys': api_keys
    }
    with open(f'{username}_credentials.json', 'w') as f:
        json.dump(credentials, f)

def load_user_credentials(username):
    """
    Load user credentials and API keys.
    """
    try:
        with open(f'{username}_credentials.json', 'r') as f:
            credentials = json.load(f)
        return credentials
    except FileNotFoundError:
        return None
