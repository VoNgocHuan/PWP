"""Resources for managing users in the ticketing application."""
from flask import request, Response, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import (
    BadRequest,
    Conflict,
    UnsupportedMediaType,
)
#from werkzeug.routing import BaseConverter

from .. import db
from ..models import User

class UserCollection(Resource):
    """Resource for the collection of users."""
    def get(self):
        """Get a list of all users."""
        response_data = []
        users = User.query.all()
        for user in users:
            response_data.append(user.serialize())
        return response_data

    def post(self):
        """Create a new user."""
        #from ..api import api   
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
        return user.serialize()

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

        return Response(status=204)

    def delete(self, user):
        """Delete a user."""
        db.session.delete(user)
        db.session.commit()
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
