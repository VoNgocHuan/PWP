"""Event resources for the Ticketing API.

This module provides REST API endpoints for event management:
- EventCollection: List all events, create new events
- EventItem: Get, update, delete a single event
"""
import json
from flask import request, Response, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from .. import db
from ..models import Event, Ticket
from ..auth import require_auth
from ..cache import get_cache
from ..utils import MasonBuilder, LINK_RELATIONS_URL, create_error_response, MASON

CACHE_TTL_LIST = 300
"""Cache TTL for event list (seconds)."""

CACHE_TTL_ITEM = 120
"""Cache TTL for single event (seconds)."""


class EventCollection(Resource):
    """Event collection resource.

    Provides GET to list all events, and POST to create new events.
    """
    def get(self):
        """Get a list of all events."""
        cache = get_cache()
        cached = cache.get("events:all")
        if cached is not None:
            return Response(json.dumps(cached), 200, mimetype=MASON)

        body = MasonBuilder(items=[])
        body.add_namespace("ticketing", LINK_RELATIONS_URL)
        
        events = Event.query.all()
        for event in events:
            serialized = event.serialize()
            tickets = Ticket.query.filter_by(event_id=event.id).all()
            serialized["tickets"] = [t.serialize() for t in tickets]
            
            item = MasonBuilder(**serialized)
            item.add_control("self", url_for("api.eventitem", event=event))
            item.add_control("profile", "/api/profiles/event/")
            item.add_control("ticketing:tickets", url_for("api.ticketcollection", event=event))
            body["items"].append(item)
        
        body.add_control("self", url_for("api.eventcollection"))
        body.add_control_post(
            "ticketing:add-event",
            "Create new event",
            url_for("api.eventcollection"),
            Event.json_schema()
        )
        
        cache.set("events:all", dict(body), CACHE_TTL_LIST)
        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_auth
    def post(self):
        """Create a new event. 
        The request body must be JSON and conform to the event schema."""
        if not request.is_json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(request.json, Event.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        event = Event()
        event.deserialize(request.json)

        try:
            db.session.add(event)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            return create_error_response(409, "Conflict", "Invalid event data")

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
            return Response(json.dumps(cached), 200, mimetype=MASON)

        body = MasonBuilder(**event.serialize())
        body.add_namespace("ticketing", LINK_RELATIONS_URL)
        
        tickets = Ticket.query.filter_by(event_id=event.id).all()
        body["tickets"] = [t.serialize() for t in tickets]
        
        body.add_control("self", url_for("api.eventitem", event=event))
        body.add_control("collection", url_for("api.eventcollection"))
        body.add_control("profile", "/api/profiles/event/")
        body.add_control("ticketing:tickets", url_for("api.ticketcollection", event=event))
        
        body.add_control_post(
            "ticketing:add-ticket",
            "Add ticket to event",
            url_for("api.ticketcollection", event=event),
            Ticket.json_schema()
        )
        
        body.add_control_put(
            "edit",
            "Edit this event",
            url_for("api.eventitem", event=event),
            Event.json_schema()
        )
        
        body.add_control_delete(
            "ticketing:delete",
            "Delete this event",
            url_for("api.eventitem", event=event)
        )
        
        cache.set(f"event:{event.id}", dict(body), CACHE_TTL_ITEM)
        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_auth
    def put(self, event):
        """Update an event, 
        but only if there are no existing orders for its tickets."""
        if not request.is_json:
            return create_error_response(415, "Unsupported media type", "Use JSON")
        
        try:
            validate(request.json, Event.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        event.deserialize(request.json)

        has_orders = any(ticket.orders for ticket in event.ticket)
        if has_orders:
            return create_error_response(409, "Conflict", "Cannot update event with existing orders")

        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            return create_error_response(409, "Conflict", "Invalid event data")
        
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
            return create_error_response(409, "Conflict", "Cannot delete event with existing orders")
        
        cache = get_cache()
        cache.delete(f"event:{event.id}")
        cache.delete("events:all")
        
        return Response(status=204)