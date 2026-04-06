"""Authentication utilities for the Ticketing API.

This module provides JWT-based authentication:
- create_token: Creates a JWT token for a user
- verify_token: Verifies a JWT token and returns the user_id
- require_auth: Decorator to protect endpoints
- blacklist: Set of revoked tokens for logout functionality
"""
import jwt
from functools import wraps
from flask import request, g, current_app
from werkzeug.exceptions import Unauthorized

from . import db
from .models import User

blacklist = set()
"""Set of revoked JWT tokens for logout functionality."""


def create_token(user_id):
    """Create a JWT token for a user.

    Args:
        user_id: The ID of the user to create a token for

    Returns:
        str: Encoded JWT token
    """
    payload = {
        "user_id": user_id
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def verify_token(token):
    """Verify a JWT token and return the user_id.

    Args:
        token: The JWT token to verify

    Returns:
        int or None: user_id if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Decorator to require authentication for an endpoint.

    This decorator checks for a valid JWT token in the Authorization
    header. If valid, the current user is stored in g.current_user.

    Args:
        f: The function to decorate

    Returns:
        The decorated function that requires authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise Unauthorized("Authorization header missing")
        
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise Unauthorized("Invalid authorization scheme")
        except ValueError:
            raise Unauthorized("Invalid authorization header format")
        
        user_id = verify_token(token)
        if user_id is None:
            raise Unauthorized("Invalid or expired token")
        
        if token in blacklist:
            raise Unauthorized("Token has been revoked")
        
        user = db.session.get(User, user_id)
        if user is None:
            raise Unauthorized("User not found")
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function