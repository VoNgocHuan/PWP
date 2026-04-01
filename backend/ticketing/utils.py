"""Utility functions for the ticketing application."""
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from . import db
from .models import User, Event, Ticket, Order

class UserConverter(BaseConverter):
    """URL converter for User resources"""
    def to_python(self, value):
        """Convert a user ID from the URL to a User object."""
        user = db.session.get(User, value)
        if user is None:
            raise NotFound
        return user

    def to_url(self, value):
        """Convert a User object to a URL component (ID)."""
        return str(value.id)


class EventConverter(BaseConverter):
    """URL converter for Event resources"""
    def to_python(self, value):
        """Convert an event ID from the URL to an Event object."""
        event = db.session.get(Event, value)
        if event is None:
            raise NotFound
        return event

    def to_url(self, value):
        """Convert an Event object to a URL component(ID)."""
        return str(value.id)


class TicketConverter(BaseConverter):
    """URL converter for Ticket resources"""
    def to_python(self, value):
        """Convert a ticket ID from the URL to a Ticket object."""
        ticket = db.session.get(Ticket, value)
        if ticket is None:
            raise NotFound
        return ticket

    def to_url(self, value):
        """Convert a Ticket object to a URL component (ID)."""
        return str(value.id)


class OrderConverter(BaseConverter):
    """URL converter for Order resources"""
    def to_python(self, value):
        """Convert an order ID from the URL to an Order object."""
        order = db.session.get(Order, value)
        if order is None:
            raise NotFound
        return order

    def to_url(self, value):
        """Convert an Order object to a URL component (ID)."""
        return str(value.id)