import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import hashlib

# Simple in-memory session store (in production, use Redis or a database)
sessions = {}

security = HTTPBearer()

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    return hash_password(password) == hashed

def create_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)

def create_session(username: str) -> dict:
    """Create a new session for a user."""
    token = create_session_token()
    session_data = {
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24)
    }
    sessions[token] = session_data
    return {"token": token, "expires_at": session_data["expires_at"].isoformat()}

def validate_session(token: str) -> Optional[dict]:
    """Validate a session token."""
    session = sessions.get(token)
    if not session:
        return None

    # Check if session has expired
    if datetime.now() > session["expires_at"]:
        del sessions[token]
        return None

    return session

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user with username and password."""
    # Get credentials from environment
    env_username = os.getenv("ADMIN_USERNAME", "admin")
    env_password_hash = os.getenv("ADMIN_PASSWORD_HASH")

    # If no hash is set, hash the default password
    if not env_password_hash:
        default_password = os.getenv("ADMIN_PASSWORD", "changeme")
        env_password_hash = hash_password(default_password)

    return username == env_username and verify_password(password, env_password_hash)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Dependency to get the current authenticated user.

    Supports two authentication methods:
    1. Session token (from login, expires in 24 hours)
    2. Static API key (from environment variable, never expires)
    """
    token = credentials.credentials

    # Check if it's a static API key
    api_key = os.getenv("API_KEY")
    if api_key and token == api_key:
        return {
            "username": "api_user",
            "auth_type": "api_key",
            "created_at": None,
            "expires_at": None
        }

    # Check if it's a session token
    session = validate_session(token)
    if session:
        return {
            **session,
            "auth_type": "session"
        }

    # Neither valid session token nor API key
    raise HTTPException(
        status_code=401,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

def cleanup_expired_sessions():
    """Remove expired sessions from the store."""
    now = datetime.now()
    expired_tokens = [token for token, session in sessions.items() if now > session["expires_at"]]
    for token in expired_tokens:
        del sessions[token]
