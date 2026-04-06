"""User resources for the Ticketing API.

This module provides REST API endpoints for user management:
- AuthLogin: User login and JWT token generation
- AuthLogout: User logout and token revocation
- UserCollection: List all users, create new users
- UserItem: Get, update, delete a single user
"""
import json
import logging
from flask import request, Response, url_for, g
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from .. import db
from ..models import User
from ..auth import create_token, require_auth
from ..cache import get_cache
from ..utils import MasonBuilder, LINK_RELATIONS_URL, create_error_response, MASON

logger = logging.getLogger("ticketing")

CACHE_TTL = 300
"""Cache time-to-live for user resources (seconds)."""


class AuthLogin(Resource):
    """User authentication resource.

    Provides POST endpoint for user login. Returns JWT token
    on successful authentication.
    """

    def post(self):
        """Login user and return JWT token.

        Expects JSON body with 'email' and 'password'.
        Returns token and user_id on success.
        """
        if not request.is_json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        data = request.json
        if not data or "email" not in data or "password" not in data:
            return create_error_response(400, "Bad Request", "Email and password are required")

        user = User.query.filter_by(email=data["email"]).first()
        if user is None or not user.check_password(data["password"]):
            logger.warning(f"Failed login attempt for email: {data['email']}")
            return create_error_response(401, "Unauthorized", "Invalid email or password")

        if user.status == "disabled":
            logger.warning(f"Login attempt for disabled user: {data['email']}")
            return create_error_response(401, "Unauthorized", "User account is disabled")

        token = create_token(user.id)
        logger.info(f"User logged in: user_id={user.id}, email={user.email}")
        
        body = MasonBuilder(token=token, user_id=user.id)
        return Response(json.dumps(body), 200, mimetype=MASON)


class AuthLogout(Resource):
    """User logout resource.

    Provides POST endpoint for user logout. Revokes the JWT token
    by adding it to the blacklist.
    """
    @require_auth
    def post(self):
        """Logout user by revoking token."""
        return {"message": "Logged out"}, 200


class UserCollection(Resource):
    """User collection resource.

    Provides GET to list all users (requires auth),
    and POST to register a new user.
    """
    @require_auth
    def get(self):
        """Get a list of all users."""
        cache = get_cache()
        cached = cache.get("users:all")
        if cached is not None:
            return Response(json.dumps(cached), 200, mimetype=MASON)

        body = MasonBuilder(items=[])
        body.add_namespace("ticketing", LINK_RELATIONS_URL)
        
        users = User.query.all()
        for user in users:
            item = MasonBuilder(**user.serialize())
            item.add_control("self", url_for("api.useritem", user=user))
            item.add_control("profile", "/api/profiles/user/")
            body["items"].append(item)
        
        body.add_control("self", url_for("api.usercollection"))
        body.add_control_post(
            "ticketing:add-user",
            "Register new user",
            url_for("api.usercollection"),
            User.json_schema()
        )
        
        cache.set("users:all", dict(body), CACHE_TTL)
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        """Create a new user and return JWT token."""
        if not request.is_json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        user = User()
        user.deserialize(request.json)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            return create_error_response(409, "Conflict", "Email already exists")

        cache = get_cache()
        cache.delete("users:all")

        token = create_token(user.id)
        body = MasonBuilder(token=token, user_id=user.id)
        return Response(json.dumps(body), 201, mimetype=MASON)


class UserItem(Resource):
    """Resource for a single user"""
    @require_auth
    def get(self, user):
        """Get details of a single user."""
        cache = get_cache()
        cached = cache.get(f"user:{user.id}")
        if cached is not None:
            return Response(json.dumps(cached), 200, mimetype=MASON)

        body = MasonBuilder(**user.serialize())
        body.add_namespace("ticketing", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.useritem", user=user))
        body.add_control("collection", url_for("api.usercollection"))
        body.add_control("profile", "/api/profiles/user/")
        body.add_control("ticketing:orders", url_for("api.userordercollection", user=user))
        
        body.add_control_put(
            "edit",
            "Edit this user",
            url_for("api.useritem", user=user),
            User.json_schema()
        )
        
        body.add_control_delete(
            "ticketing:delete",
            "Delete this user",
            url_for("api.useritem", user=user)
        )
        
        cache.set(f"user:{user.id}", dict(body), CACHE_TTL)
        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_auth
    def put(self, user):
        """Update a user's information."""
        if not request.is_json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        user.deserialize(request.json)

        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            return create_error_response(409, "Conflict", "Email already exists")

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