"""Resources for managing users in the ticketing application."""
from flask import request, Response, url_for, g
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import (
    BadRequest,
    Conflict,
    UnsupportedMediaType,
    Unauthorized,
)

from .. import db
from ..models import User
from ..auth import create_token, require_auth
from ..cache import get_cache

CACHE_TTL = 300

class AuthLogin(Resource):
    def post(self):
        """Login user and return JWT token."""
        if not request.is_json:
            raise UnsupportedMediaType

        data = request.json
        if not data or "email" not in data or "password" not in data:
            raise BadRequest("Email and password are required")

        user = User.query.filter_by(email=data["email"]).first()
        if user is None or not user.check_password(data["password"]):
            raise Unauthorized("Invalid email or password")

        if user.status == "disabled":
            raise Unauthorized("User account is disabled")

        token = create_token(user.id)
        return {"token": token, "user_id": user.id}, 200

class AuthLogout(Resource):
    @require_auth
    def post(self):
        """Logout user by revoking token."""
        from ..auth import blacklist
        auth_header = request.headers.get("Authorization")
        token = auth_header.split(" ")[1]
        blacklist.add(token)
        return {"message": "Logged out successfully"}, 200

class UserCollection(Resource):
    def get(self):
        """Get a list of all users."""
        cache = get_cache()
        cached = cache.get("users:all")
        if cached is not None:
            return cached

        response_data = []
        users = User.query.all()
        for user in users:
            response_data.append(user.serialize())
        
        cache.set("users:all", response_data, CACHE_TTL)
        return response_data

    @require_auth
    def post(self):
        """Create a new user."""
        if not request.is_json:
            raise UnsupportedMediaType

        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(str(e)) from e

        user = User()
        user.deserialize(request.json)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict("Email already exists") from exc

        cache = get_cache()
        cache.delete("users:all")

        return Response(
            status=201,
            headers={
                "Location": url_for("api.useritem", user=user)
            },
        )

class UserItem(Resource):
    """Resource for a single user"""
    def get(self, user):
        """Get details of a single user."""
        cache = get_cache()
        cached = cache.get(f"user:{user.id}")
        if cached is not None:
            return cached

        serialized = user.serialize()
        cache.set(f"user:{user.id}", serialized, CACHE_TTL)
        return serialized

    @require_auth
    def put(self, user):
        """Update a user's information. 
        The request body must be JSON and conform to the user schema."""
        if not request.is_json:
            raise UnsupportedMediaType

        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(str(e)) from e

        user.deserialize(request.json)

        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict("Email already exists") from exc

        cache = get_cache()
        cache.delete(f"user:{user.id}")
        cache.delete("users:all")

        return Response(status=204)

    @require_auth
    def delete(self, user):
        """Delete a user."""
        db.session.delete(user)
        db.session.commit()
        
        cache = get_cache()
        cache.delete(f"user:{user.id}")
        cache.delete("users:all")
        
        return Response(status=204)

# class UserConverter(BaseConverter):
#     """URL converter for User resources."""
#     def to_python(self, value):
#         """Convert a URL component (user ID) to a User object."""
#         user = db.session.get(User, value)
#         if user is None:
#             raise NotFound
#         return user

#     def to_url(self, value):
#         """Convert a User object to a URL component (its ID)."""
#         return str(value.id)

# app.url_map.converters["user"] = UserConverter
