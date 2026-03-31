"""Authentication utilities for the ticketing application."""
import jwt
from functools import wraps
from flask import request, g, current_app
from werkzeug.exceptions import Unauthorized

from . import db
from .models import User

blacklist = set()

def create_token(user_id):
    """Create a JWT token for a user."""
    payload = {
        "user_id": user_id
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

def verify_token(token):
    """Verify a JWT token and return the user_id."""
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require authentication for an endpoint."""
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