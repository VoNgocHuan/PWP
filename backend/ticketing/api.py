"""API for the ticketing system."""
from flask import Blueprint
from flask_restful import Api
from .resources.user import UserCollection, UserItem, AuthLogin, AuthLogout
from .resources.event import EventCollection, EventItem
from .resources.ticket import TicketCollection, TicketItem
from .resources.order import OrderCollection, OrderItem, UserOrderCollection
from . import views

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api_bp.add_url_rule("/", "entry", views.entry)

api.add_resource(AuthLogin, "/auth/login/")
api.add_resource(AuthLogout, "/auth/logout/")

api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>/")

api.add_resource(EventCollection, "/events/")
api.add_resource(EventItem, "/events/<event:event>/")

api.add_resource(TicketCollection, "/events/<event:event>/tickets/")
api.add_resource(TicketItem, "/events/<event:event>/tickets/<ticket:ticket>/")

api.add_resource(OrderCollection, "/orders/")
api.add_resource(OrderItem, "/orders/<order:order>/")
api.add_resource(UserOrderCollection, "/users/<user:user>/orders/")