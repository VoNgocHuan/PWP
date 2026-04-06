"""Resources for managing orders in the ticketing application."""
import json
import logging
from flask import request, Response, url_for, g
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from .. import db
from ..models import Order, User, Ticket
from ..auth import require_auth
from ..cache import get_cache
from ..utils import MasonBuilder, LINK_RELATIONS_URL, create_error_response, MASON

logger = logging.getLogger("ticketing")


class OrderCollection(Resource):
    @require_auth
    def get(self):
        """Get a list of orders for the current user."""
        body = MasonBuilder(items=[])
        body.add_namespace("ticketing", LINK_RELATIONS_URL)
        
        orders = Order.query.filter_by(user_id=g.current_user.id).all()
        for order in orders:
            item = MasonBuilder(**order.serialize())
            item.add_control("self", url_for("api.orderitem", order=order))
            item.add_control("profile", "/api/profiles/order/")
            item.add_control("ticketing:ticket", url_for("api.ticketitem", event=order.ticket.event, ticket=order.ticket))
            body["items"].append(item)
        
        body.add_control("self", url_for("api.ordercollection"))
        body.add_control(
            "ticketing:buy",
            url_for("api.ordercollection"),
            method="POST",
            title="Buy ticket",
            schema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "integer"}
                },
                "required": ["ticket_id"]
            }
        )
        
        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_auth
    def post(self):
        """Create a new order for the current user."""
        if not request.is_json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(request.json, Order.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        user = g.current_user
        ticket = db.session.get(Ticket, request.json["ticket_id"])

        if ticket is None:
            return create_error_response(404, "Not found", "Ticket not found")

        if ticket.remaining <= 0:
            return create_error_response(409, "Conflict", "Ticket sold out")

        order = Order(user=user, ticket=ticket)

        ticket.remaining -= 1

        try:
            db.session.add(order)
            db.session.commit()
            
            cache = get_cache()
            cache.delete("events:all")
            cache.delete(f"event:{ticket.event_id}")
            cache.invalidate_pattern("event:*")
            
            logger.info(f"Order created: user_id={user.id}, ticket_id={ticket.id}, remaining={ticket.remaining}")
            
        except IntegrityError as exc:
            db.session.rollback()
            logger.error(f"Order creation failed: user_id={user.id}, ticket_id={ticket.id}, error={exc}")
            return create_error_response(409, "Conflict", "Could not create order")

        body = MasonBuilder(message="Order created successfully", order_id=order.id)
        return Response(json.dumps(body), 201, mimetype=MASON)


class OrderItem(Resource):
    @require_auth
    def get(self, order):
        """Get details of a single order (only if own order)."""
        if order.user_id != g.current_user.id:
            return create_error_response(403, "Forbidden", "Cannot view other user's order")
        
        body = MasonBuilder(**order.serialize())
        body.add_namespace("ticketing", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.orderitem", order=order))
        body.add_control("collection", url_for("api.ordercollection"))
        body.add_control("profile", "/api/profiles/order/")
        body.add_control("ticketing:ticket", url_for("api.ticketitem", event=order.ticket.event, ticket=order.ticket))
        
        body.add_control_delete(
            "ticketing:cancel",
            "Cancel this order",
            url_for("api.orderitem", order=order)
        )
        
        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_auth
    def delete(self, order):
        """Delete an order (only if own order)."""
        if order.user_id != g.current_user.id:
            return create_error_response(403, "Forbidden", "Cannot delete other user's order")
        
        ticket = order.ticket
        ticket.remaining += 1
        try:
            db.session.delete(order)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            return create_error_response(409, "Conflict", "Could not delete order")
        return Response(status=204)
    

class UserOrderCollection(Resource):
    @require_auth
    def get(self, user):
        """Get a list of all orders for a specific user (only if own)."""
        if user.id != g.current_user.id:
            return create_error_response(403, "Forbidden", "Cannot view other user's orders")
        
        body = MasonBuilder(items=[])
        body.add_namespace("ticketing", LINK_RELATIONS_URL)
        
        orders = Order.query.filter_by(user_id=user.id).all()
        for order in orders:
            item = MasonBuilder(**order.serialize())
            item.add_control("self", url_for("api.orderitem", order=order))
            body["items"].append(item)
        
        body.add_control("self", url_for("api.userordercollection", user=user))
        
        return Response(json.dumps(body), 200, mimetype=MASON)