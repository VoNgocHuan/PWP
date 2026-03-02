"""API for the ticketing system."""
from flask_restful import Api
from .models import app
from .resources.user import UserCollection, UserItem
from .resources.event import EventCollection, EventItem
from .resources.ticket import TicketCollection, TicketItem
from .resources.order import OrderCollection, OrderItem

api = Api(app)

api.add_resource(UserCollection, "/api/users/")
api.add_resource(UserItem, "/api/users/<user:user>/")

api.add_resource(EventCollection, "/api/events/")
api.add_resource(EventItem, "/api/events/<event:event>/")

api.add_resource(TicketCollection, "/api/events/<event:event>/tickets/")
api.add_resource(TicketItem, "/api/events/<event:event>/tickets/<ticket:ticket>/")

api.add_resource(OrderCollection, "/api/orders/")
api.add_resource(OrderItem, "/api/orders/<order:order>/")
