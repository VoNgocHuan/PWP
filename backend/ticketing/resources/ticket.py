"""Ticket resources for the Ticketing API.

This module provides REST API endpoints for ticket management:
- TicketCollection: List tickets for an event, create new tickets
- TicketItem: Get, delete a single ticket
"""
import json
from flask import request, Response, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from .. import db
from ..models import Ticket
from ..auth import require_auth
from ..cache import get_cache
from ..utils import MasonBuilder, LINK_RELATIONS_URL, create_error_response, MASON

CACHE_TTL = 120
"""Cache TTL for ticket resources (seconds)."""


class TicketCollection(Resource):
    """Ticket collection resource for a specific event.

    Provides GET to list all tickets for an event,
    and POST to create new tickets.
    """
    def get(self, event):
        """Get a list of all tickets for the given event."""
        cache = get_cache()
        cached = cache.get(f"event:{event.id}:tickets")
        if cached is not None:
            return Response(json.dumps(cached), 200, mimetype=MASON)

        body = MasonBuilder(items=[])
        body.add_namespace("ticketing", LINK_RELATIONS_URL)
        
        tickets = Ticket.query.filter_by(event_id=event.id).all()
        for ticket in tickets:
            item = MasonBuilder(**ticket.serialize())
            item.add_control("self", url_for("api.ticketitem", event=event, ticket=ticket))
            item.add_control("profile", "/api/profiles/ticket/")
            body["items"].append(item)
        
        body.add_control("self", url_for("api.ticketcollection", event=event))
        body.add_control("up", url_for("api.eventitem", event=event))
        
        cache.set(f"event:{event.id}:tickets", dict(body), CACHE_TTL)
        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_auth
    def post(self, event):
        """Create a new ticket for the given event."""
        if not request.is_json:
            return create_error_response(415, "Unsupported media type", "Use JSON")
        
        try:
            validate(request.json, Ticket.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        ticket = Ticket()
        ticket.deserialize(request.json)
        ticket.event = event

        try:
            db.session.add(ticket)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            return create_error_response(409, "Conflict", "Ticket name must be unique per event")

        cache = get_cache()
        cache.delete(f"event:{event.id}:tickets")

        return Response(
            status=201,
            headers={
                "Location": url_for("api.ticketitem", event=event, ticket=ticket)        
            },
        )


class TicketItem(Resource):
    """Ticket item resource.

    Provides GET to view a single ticket, and DELETE to remove it.
    """
    def get(self, event, ticket):
        """Get details of a single ticket."""
        if ticket.event != event:
            return create_error_response(404, "Not found", "Ticket not found")
        
        cache = get_cache()
        cached = cache.get(f"ticket:{ticket.id}")
        if cached is not None:
            return Response(json.dumps(cached), 200, mimetype=MASON)

        body = MasonBuilder(**ticket.serialize())
        body.add_namespace("ticketing", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.ticketitem", event=event, ticket=ticket))
        body.add_control("collection", url_for("api.ticketcollection", event=event))
        body.add_control("profile", "/api/profiles/ticket/")
        body.add_control("up", url_for("api.eventitem", event=event))
        body.add_control(
            "ticketing:buy",
            url_for("api.ordercollection"),
            method="POST",
            title="Buy this ticket",
            schema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "integer", "default": ticket.id}
                },
                "required": ["ticket_id"]
            }
        )
        
        body.add_control_delete(
            "ticketing:delete",
            "Delete this ticket",
            url_for("api.ticketitem", event=event, ticket=ticket)
        )
        
        cache.set(f"ticket:{ticket.id}", dict(body), CACHE_TTL)
        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_auth
    def delete(self, event, ticket):
        """Delete a ticket."""
        if ticket.event != event:
            return create_error_response(404, "Not found", "Ticket not found")

        try:
            db.session.delete(ticket)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            return create_error_response(409, "Conflict", "Cannot delete ticket with existing orders")
        
        cache = get_cache()
        cache.delete(f"ticket:{ticket.id}")
        cache.delete(f"event:{event.id}:tickets")
        
        return Response(status=204)