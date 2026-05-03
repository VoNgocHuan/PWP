"""Flask application for the Email Auxiliary Service.

This module provides the REST API endpoints for the email service.
The service listens for order notifications and sends confirmation emails.
"""
import json
import logging
from flask import Flask, request, Response

try:
    from .config import config
    from .service import send_confirmation_email, validate_order_data
except ImportError:
    from config import config
    from service import send_confirmation_email, validate_order_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
LOGGER = logging.getLogger("email-service")


def create_app(config_name="default"):
    """Create and configure the Flask application.

    Args:
        config_name: Name of the configuration to use

    Returns:
        Flask: Configured Flask application
    """
    flask_app = Flask(__name__)
    flask_app.config.from_object(config[config_name])

    @flask_app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint.

        Returns:
            Response: JSON health status
        """
        return Response(
            json.dumps({
                "status": "healthy",
                "service": "email-service",
                "smtp_enabled": flask_app.config["SMTP_ENABLED"],
                "smtp_host": flask_app.config["SMTP_HOST"],
                "smtp_port": flask_app.config["SMTP_PORT"]
            }),
            200,
            mimetype="application/json"
        )

    @flask_app.route("/notify/order", methods=["POST"])
    def notify_order():
        """Handle order notification from the main API.

        Receives order data and sends a confirmation email to the buyer.
        This endpoint is called by the main API when a ticket is purchased.

        Expected JSON body:
        {
            "user_email": "buyer@example.com",
            "user_name": "John Doe",
            "event_title": "Rock Concert",
            "ticket_name": "VIP",
            "order_id": 42
        }

        Returns:
            Response: JSON success/error response
        """
        if not request.is_json:
            LOGGER.warning("Invalid request: not JSON")
            return Response(
                json.dumps({"error": "Unsupported media type", "message": "Use JSON"}),
                415,
                mimetype="application/json"
            )

        data = request.json

        is_valid, error_msg = validate_order_data(data)
        if not is_valid:
            LOGGER.warning("Invalid order data: %s", error_msg)
            return Response(
                json.dumps({"error": "Validation error", "message": error_msg}),
                400,
                mimetype="application/json"
            )

        try:
            success = send_confirmation_email(
                recipient_email=data["user_email"],
                recipient_name=data["user_name"],
                event_title=data["event_title"],
                ticket_name=data["ticket_name"],
                order_id=data["order_id"]
            )

            if success:
                LOGGER.info("Order notification processed for order #%s", data["order_id"])
                return Response(
                    json.dumps({
                        "message": "Email sent successfully",
                        "order_id": data["order_id"]
                    }),
                    200,
                    mimetype="application/json"
                )

            LOGGER.error("Failed to send email for order #%s", data["order_id"])
            return Response(
                json.dumps({"error": "Failed to send email"}),
                500,
                mimetype="application/json"
            )

        except Exception as exc:
            LOGGER.exception("Error processing order notification: %s", exc)
            return Response(
                json.dumps({"error": "Internal server error"}),
                500,
                mimetype="application/json"
            )

    return flask_app


application = create_app()


if __name__ == "__main__":
    cfg = config["default"]
    LOGGER.info("Starting email service on %s:%s", cfg.SERVICE_HOST, cfg.SERVICE_PORT)
    application.run(host=cfg.SERVICE_HOST, port=cfg.SERVICE_PORT, debug=cfg.DEBUG)
