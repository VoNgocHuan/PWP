"""API route registration for the Ticketing API.

This module registers all REST API endpoints and views:
- Entry point: /api/
- Link relations: /api/link-relations/
- Profile pages: /api/profiles/<resource>/
- User endpoints: /api/users/, /api/auth/login/, /api/auth/logout/
- Event endpoints: /api/events/
- Ticket endpoints: /api/events/<id>/tickets/
- Order endpoints: /api/orders/
"""
from flask import Blueprint
from flask_restful import Api
from .resources.user import UserCollection, UserItem, AuthLogin, AuthLogout
from .resources.event import EventCollection, EventItem
from .resources.ticket import TicketCollection, TicketItem
from .resources.order import OrderCollection, OrderItem, UserOrderCollection
from . import views

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

# Entry point and hypermedia documentation
api_bp.add_url_rule("/", "entry", views.entry)
api_bp.add_url_rule("/link-relations/", "link_relations", views.link_relations)

# Profile pages
api_bp.add_url_rule("/profiles/user/", "profile_user", views.profile_user)
api_bp.add_url_rule("/profiles/event/", "profile_event", views.profile_event)
api_bp.add_url_rule("/profiles/ticket/", "profile_ticket", views.profile_ticket)
api_bp.add_url_rule("/profiles/order/", "profile_order", views.profile_order)

# Authentication endpoints
api.add_resource(AuthLogin, "/auth/login/")
api.add_resource(AuthLogout, "/auth/logout/")

# User endpoints
api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>/")

# Event endpoints
api.add_resource(EventCollection, "/events/")
api.add_resource(EventItem, "/events/<event:event>/")

# Ticket endpoints
api.add_resource(TicketCollection, "/events/<event:event>/tickets/")
api.add_resource(TicketItem, "/events/<event:event>/tickets/<ticket:ticket>/")

# Order endpoints
api.add_resource(OrderCollection, "/orders/")
api.add_resource(OrderItem, "/orders/<order:order>/")
api.add_resource(UserOrderCollection, "/users/<user:user>/orders/")