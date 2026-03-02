"""Resources for managing events in the ticketing application."""
from flask import request, Response
from flask_restful import Resource
from jsonschema import Draft7Validator, validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import (
    BadRequest,
    Conflict,
    NotFound,
    UnsupportedMediaType,
)
from werkzeug.routing import BaseConverter

from ..models import db, Event, app

class EventCollection(Resource):
    """Resource for the collection of events, accessible at /events."""
    def get(self):
        """Get a list of all events."""
        response_data = []
        events = Event.query.all()
        for event in events:
            response_data.append(event.serialize())
        return response_data

    def post(self):
        """Create a new event. 
        The request body must be JSON and conform to the event schema."""
        from ..api import api 
        if not request.is_json:
            raise UnsupportedMediaType

        try:
            validate(request.json,
                Event.json_schema(),
                format_checker=Draft7Validator.FORMAT_CHECKER,
            )
        except ValidationError as e:
            raise BadRequest(str(e)) from e

        event = Event()
        event.deserialize(request.json)

        try:
            db.session.add(event)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict("Invalid event data") from exc

        return Response(
            status=201,
            headers={
                "Location": api.url_for(
                    EventItem,
                    event=event
                )
            },
        )

class EventItem(Resource):
    """Resource for a single event, identified by its ID in the URL."""
    def get(self, event):
        """Get details of a single event."""
        return event.serialize()

    def put(self, event):
        """Update an event, 
        but only if there are no existing orders for its tickets."""
        if not request.is_json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                Event.json_schema(),
                format_checker=Draft7Validator.FORMAT_CHECKER,
            )
        except ValidationError as e:
            raise BadRequest(str(e)) from e

        event.deserialize(request.json)

        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict("Invalid event update") from exc

        return Response(status=204)

    def delete(self, event):
        """Delete an event only if there are no existing orders for its tickets."""
        try:
            db.session.delete(event)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict("Cannot delete event with existing orders") from exc
        return Response(status=204)

class EventConverter(BaseConverter):
    """URL converter for Event resources, allowing us to use event IDs in URLs"""
    def to_python(self, value):
        event = db.session.get(Event, value)
        if event is None:
            raise NotFound
        return event

    def to_url(self, value):
        return str(value.id)

app.url_map.converters["event"] = EventConverter
