"""Resources for managing orders in the ticketing application."""
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
from ..models import Order, User, Ticket

class OrderCollection(Resource):
    """Resource for managing collections of orders."""
    def get(self):
        """Get a list of all orders."""
        response_data = []
        orders = Order.query.all()
        for order in orders:
            response_data.append(order.serialize())
        return response_data

    def post(self):
        """Create a new order."""
        #from ..api import api
        if not request.is_json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Order.json_schema())
        except ValidationError as e:
            raise BadRequest(str(e)) from e

        user = User.query.get(request.json["user_id"])
        ticket = Ticket.query.get(request.json["ticket_id"])

        if user is None or ticket is None:
            raise NotFound

        if ticket.remaining <= 0:
            raise Conflict("Ticket sold out")

        order = Order(user=user, ticket=ticket)

        ticket.remaining -= 1

        try:
            db.session.add(order)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict("Could not create order") from exc

        return Response(
            status=201,
            headers={
                "Location": url_for("api.orderitem", order=order)
            }
        )

class OrderItem(Resource):
    """Resource for managing a single order, identified by its ID in the URL."""
    def get(self, order):
        """Get details of a single order."""
        return order.serialize()

    def delete(self, order):
        """Delete an order."""
        ticket = order.ticket
        ticket.remaining += 1
        try:
            db.session.delete(order)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict("Could not delete order") from exc
        return Response(status=204)
    
class UserOrderCollection(Resource):
    """Resource for managing collections of orders for a specific user."""
    def get(self, user):
        """Get a list of all orders for a specific user."""
        response_data = []
        orders = Order.query.filter_by(user_id=user.id).all()
        for order in orders:
            response_data.append(order.serialize())
        return response_data

# class OrderConverter(BaseConverter):
#     """URL converter for Order resources"""
#     def to_python(self, value):
#         """Convert a URL component (order ID) to an Order object."""
#         order = db.session.get(Order, value)
#         if order is None:
#             raise NotFound
#         return order

#     def to_url(self, value):
#         """Convert an Order object to a URL component (its ID)."""
#         return str(value.id)

# app.url_map.converters["order"] = OrderConverter
