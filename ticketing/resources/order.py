"""Resources for managing orders in the ticketing application."""
from flask import request, Response, url_for, g
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import (
    BadRequest,
    Conflict,
    NotFound,
    UnsupportedMediaType,
)

from .. import db
from ..models import Order, User, Ticket
from ..auth import require_auth

class OrderCollection(Resource):
    @require_auth
    def get(self):
        """Get a list of all orders."""
        response_data = []
        orders = Order.query.all()
        for order in orders:
            response_data.append(order.serialize())
        return response_data

    @require_auth
    def post(self):
        """Create a new order."""
        if not request.is_json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Order.json_schema())
        except ValidationError as e:
            raise BadRequest(str(e)) from e

        user = db.session.get(User, request.json["user_id"])
        ticket = db.session.get(Ticket, request.json["ticket_id"])

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
    @require_auth
    def get(self, order):
        """Get details of a single order."""
        return order.serialize()

    @require_auth
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
    @require_auth
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
