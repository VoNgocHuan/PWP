"""Resources for managing tickets in the ticketing application."""
from flask import request, Response, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import (
    BadRequest,
    Conflict,
    NotFound,
    UnsupportedMediaType,
)
#from werkzeug.routing import BaseConverter

from .. import db
from ..models import Ticket

class TicketCollection(Resource):
    """Resource for the collection of tickets for a specific event"""
    def get(self, event):
        """Get a list of all tickets for the given event."""
        response_data = []
        #tickets = Ticket.query.all()
        tickets = Ticket.query.filter_by(event_id=event.id).all()
        for ticket in tickets:
            response_data.append(ticket.serialize())
        return response_data

    def post(self, event):
        """Create a new ticket for the given event."""
        #from ..api import api
        if not request.is_json:    
            raise UnsupportedMediaType
        try:
            validate(request.json, Ticket.json_schema())
        except ValidationError as e:
            raise BadRequest(str(e)) from e

        ticket = Ticket()
        ticket.deserialize(request.json)
        ticket.event = event

        try:
            db.session.add(ticket)
            db.session.commit()
        except IntegrityError  as exc:
            db.session.rollback()
            raise Conflict("Ticket name must be unique per event") from exc 

        return Response(
            status=201,
            headers={
                "Location": url_for("api.ticketitem", event=event, ticket=ticket)        
            },
        )

class TicketItem(Resource):
    """Resource for a single ticket, identified by its ID in the URL."""
    def get(self, event, ticket):
        """Get details of a single ticket."""
        if ticket.event != event:
            raise NotFound
        return ticket.serialize()

    def delete(self, event, ticket):
        """Delete a ticket."""
        if ticket.event != event:
            raise NotFound

        try:
            db.session.delete(ticket)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict("Cannot delete ticket with existing orders") from exc
        return Response(status=204)

# class TicketConverter(BaseConverter):
#     """URL converter for Ticket resources."""
#     def to_python(self, value):
#         """Convert a URL component (ticket ID) to a Ticket object."""
#         ticket = db.session.get(Ticket, value)
#         if ticket is None:
#             raise NotFound
#         return ticket

#     def to_url(self, value):
#         """Convert a Ticket object to a URL component (its ID)."""
#         return str(value.id)

# app.url_map.converters["ticket"] = TicketConverter
