"""Resources for managing events in the ticketing application."""
from flask import request, Response, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, UnsupportedMediaType

from .. import db
from ..models import Event
from ..auth import require_auth
from ..cache import get_cache

CACHE_TTL_LIST = 300
CACHE_TTL_ITEM = 120

class EventCollection(Resource):
    """Resource for the collection of events, accessible at /events."""
    def get(self):
        """Get a list of all events."""
        cache = get_cache()
        cached = cache.get("events:all")
        if cached is not None:
            return cached

        response_data = []
        events = Event.query.all()
        for event in events:
            response_data.append(event.serialize())
        
        cache.set("events:all", response_data, CACHE_TTL_LIST)
        return response_data

    @require_auth
    def post(self):
        """Create a new event. 
        The request body must be JSON and conform to the event schema."""
        if not request.is_json:
            raise UnsupportedMediaType

        try:
            validate(request.json,
                Event.json_schema()
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

        cache = get_cache()
        cache.delete("events:all")

        return Response(status=201, headers={
            "Location": url_for("api.eventitem", event=event)
        })

class EventItem(Resource):
    """Resource for a single event, identified by its ID in the URL."""
    def get(self, event):
        """Get details of a single event."""
        cache = get_cache()
        cached = cache.get(f"event:{event.id}")
        if cached is not None:
            return cached

        serialized = event.serialize()
        cache.set(f"event:{event.id}", serialized, CACHE_TTL_ITEM)
        return serialized

    @require_auth
    def put(self, event):
        """Update an event, 
        but only if there are no existing orders for its tickets."""
        if not request.is_json:
            raise UnsupportedMediaType
        try:
            validate(request.json,
                Event.json_schema(),
            )
        except ValidationError as e:
            raise BadRequest(str(e)) from e

        event.deserialize(request.json)

        has_orders = any(ticket.orders for ticket in event.ticket)
        if has_orders:
            from werkzeug.exceptions import Conflict
            raise Conflict("Cannot update event with existing orders")

        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict("Invalid event data") from exc
        
        cache = get_cache()
        cache.delete(f"event:{event.id}")
        cache.delete("events:all")
        
        return Response(status=204)

    @require_auth
    def delete(self, event):
        """Delete an event only if there are no existing orders for its tickets."""
        try:
            db.session.delete(event)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict("Cannot delete event with existing orders") from exc
        
        cache = get_cache()
        cache.delete(f"event:{event.id}")
        cache.delete("events:all")
        
        return Response(status=204)

# class EventConverter(BaseConverter):
#     """URL converter for Event resources, allowing us to use event IDs in URLs"""
#     def to_python(self, value):
#         event = db.session.get(Event, value)
#         if event is None:
#             raise NotFound
#         return event

#     def to_url(self, value):
#         return str(value.id)

# app.url_map.converters["event"] = EventConverter
