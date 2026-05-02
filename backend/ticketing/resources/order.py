"""Order resources for the Ticketing API.

This module provides REST API endpoints for order management:
- OrderCollection: List orders for current user, create new orders
- OrderItem: Get, cancel a single order
- UserOrderCollection: List orders for a specific user
"""
import json
import logging
import os
import requests
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


def send_email_notification(user, ticket, order):
    """Send order notification to the email auxiliary service.

    Args:
        user: The user who placed the order
        ticket: The ticket that was purchased
        order: The order that was created

    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    email_service_url = os.environ.get("EMAIL_SERVICE_URL", "http://localhost:5001")

    if not email_service_url:
        logger.debug("EMAIL_SERVICE_URL not set, skipping email notification")
        return False

    payload = {
        "user_email": user.email,
        "user_name": user.name,
        "event_title": ticket.event.title,
        "ticket_name": ticket.name,
        "order_id": order.id
    }

    try:
        response = requests.post(
            f"{email_service_url}/notify/order",
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            logger.info("Email notification sent for order #%s", order.id)
            return True
        else:
            logger.warning("Email notification failed for order #%s: %s", order.id, response.status_code)
            return False
    except requests.RequestException as exc:
        logger.warning("Failed to connect to email service: %s", exc)
        return False
    except Exception as exc:
        logger.warning("Unexpected error sending email notification: %s", exc)
        return False


class OrderCollection(Resource):
    """Order collection resource.

    Provides GET to list orders for the authenticated user,
    and POST to create new orders (buy tickets).
    """
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

            send_email_notification(user, ticket, order)
            
        except IntegrityError as exc:
            db.session.rollback()
            logger.error(f"Order creation failed: user_id={user.id}, ticket_id={ticket.id}, error={exc}")
            return create_error_response(409, "Conflict", "Could not create order")

        body = MasonBuilder(message="Order created successfully", order_id=order.id)
        return Response(json.dumps(body), 201, mimetype=MASON)


class OrderItem(Resource):
    """Order item resource.

    Provides GET to view a single order (own orders only),
    and DELETE to cancel an order.
    """
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
    """User order collection resource.

    Provides GET to list all orders for a specific user.
    Users can only view their own orders.
    """
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