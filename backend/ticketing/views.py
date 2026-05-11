"""Entry point and profile views for the Ticketing API.

This module provides the entry point at /api/, profile pages for 
documenting resource attributes, and link relations documentation.
"""
import json
from flask import url_for, request, Response
from .utils import MasonBuilder, LINK_RELATIONS_URL, MASON


def entry():
    """Entry point for the API.

    Returns a Mason-formatted document with hypermedia controls
    to the main collections (users, events, orders) and login.
    Clients should start here to discover available actions.
    """
    body = MasonBuilder()
    body.add_namespace("ticketing", LINK_RELATIONS_URL)
    
    body["@controls"] = {
        "ticketing:users-all": {
            "href": url_for("api.usercollection"),
            "title": "All users"
        },
        "ticketing:events-all": {
            "href": url_for("api.eventcollection"),
            "title": "All events"
        },
        "ticketing:orders": {
            "href": url_for("api.ordercollection"),
            "title": "My orders"
        },
        "ticketing:login": {
            "href": url_for("api.authlogin"),
            "method": "POST",
            "title": "Login"
        }
    }
    
    return Response(json.dumps(body), 200, mimetype=MASON)


def link_relations():
    """Link relations documentation.

    Returns an HTML page documenting all custom link relations
    used in the Ticketing API. Each link relation is described
    with its name and purpose.
    """
    html = """
    <html>
    <head><title>Ticketing API Link Relations</title></head>
    <body>
        <h1>Link Relations</h1>
        <ul>
            <li><a href="#ticketing:users-all">ticketing:users-all</a> - List all users</li>
            <li><a href="#ticketing:events-all">ticketing:events-all</a> - List all events</li>
            <li><a href="#ticketing:orders">ticketing:orders</a> - User's orders</li>
            <li><a href="#ticketing:login">ticketing:login</a> - Login</li>
            <li><a href="#ticketing:logout">ticketing:logout</a> - Logout</li>
            <li><a href="#ticketing:add-user">ticketing:add-user</a> - Register new user</li>
            <li><a href="#ticketing:add-event">ticketing:add-event</a> - Create event</li>
            <li><a href="#ticketing:add-ticket">ticketing:add-ticket</a> - Add ticket to event</li>
            <li><a href="#ticketing:buy">ticketing:buy</a> - Buy ticket</li>
            <li><a href="#ticketing:delete">ticketing:delete</a> - Delete resource</li>
            <li><a href="#ticketing:cancel">ticketing:cancel</a> - Cancel order</li>
        </ul>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


def profile_user():
    """User profile documentation.

    Returns an HTML page describing the attributes of User resources.
    Attributes: id, name, email, status, created_at.
    """
    html = """
    <html>
    <head><title>User Profile</title></head>
    <body>
        <h1>User Profile</h1>
        <p>Attributes: id, name, email, status, created_at</p>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


def profile_event():
    """Event profile documentation.

    Returns an HTML page describing the attributes of Event resources.
    Attributes: id, title, venue, city, description, starts_at, ends_at, status.
    """
    html = """
    <html>
    <head><title>Event Profile</title></head>
    <body>
        <h1>Event Profile</h1>
        <p>Attributes: id, title, venue, city, description, starts_at, ends_at, status</p>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


def profile_ticket():
    """Ticket profile documentation.

    Returns an HTML page describing the attributes of Ticket resources.
    Attributes: id, name, price, capacity, remaining.
    """
    html = """
    <html>
    <head><title>Ticket Profile</title></head>
    <body>
        <h1>Ticket Profile</h1>
        <p>Attributes: id, name, price, capacity, remaining</p>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


def profile_order():
    """Order profile documentation.

    Returns an HTML page describing the attributes of Order resources.
    Attributes: id, user_id, ticket_id, status, created_at.
    """
    html = """
    <html>
    <head><title>Order Profile</title></head>
    <body>
        <h1>Order Profile</h1>
        <p>Attributes: id, user_id, ticket_id, status, created_at</p>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")
