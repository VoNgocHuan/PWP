"""Utility functions for the ticketing application."""
import json
from flask import request, Response
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from . import db
from .models import User, Event, Ticket, Order

LINK_RELATIONS_URL = "/api/link-relations#"
ERROR_PROFILE = "/api/profiles/error-profile/"
MASON = "application/vnd.mason+json"


def create_error_response(status_code, title, message=None):
    """
    Create a Mason-formatted error response.
    :param int status_code: HTTP status code
    :param str title: Short title for the error
    :param str message: Longer human-readable description
    :return: Flask Response object with Mason error format
    """
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)


class MasonBuilder(dict):
    """Dictionary subclass that builds Mason hypermedia documents."""
    
    def add_namespace(self, ns, uri):
        """Add a namespace for custom link relations."""
        if "@namespaces" not in self:
            self["@namespaces"] = {}
        self["@namespaces"][ns] = {"name": uri}
    
    def add_control(self, rel, href, **kwargs):
        """Add a hypermedia control."""
        if "@controls" not in self:
            self["@controls"] = {}
        self["@controls"][rel] = {"href": href}
        self["@controls"][rel].update(kwargs)
    
    def add_control_post(self, rel, title, href, schema):
        """Add a POST control with schema."""
        self.add_control(rel, href, method="POST", title=title, schema=schema, encoding="json")
    
    def add_control_put(self, rel, title, href, schema):
        """Add a PUT control with schema."""
        self.add_control(rel, href, method="PUT", title=title, schema=schema, encoding="json")
    
    def add_control_delete(self, rel, title, href):
        """Add a DELETE control."""
        self.add_control(rel, href, method="DELETE", title=title)
    
    def add_error(self, title, details):
        """Add an error message to the document."""
        self["@error"] = {
            "@message": title,
            "@messages": [details] if details else []
        }


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