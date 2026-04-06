"""Database seeding commands for the Ticketing API.

This module provides functions to seed the database with initial
sample data for development and testing purposes.
"""
import click
from datetime import datetime, timedelta
from decimal import Decimal
from . import db
from .models import User, Event, Ticket, Order


def seed_database():
    """Seed the database with initial data.

    Creates sample users, events, and tickets if the database
    is empty. Prints a message if data already exists.
    """
    if User.query.first():
        click.echo("Database already seeded. Skipping.")
        return
    
    users = [
        User(name="Alice Wonderland", email="alice@example.com"),
        User(name="Bob Smith", email="bob@example.com"),
    ]
    for user in users:
        user.set_password("password123")
    db.session.add_all(users)
    
    events = [
        Event(
            title="Summer Concert",
            venue="Central Park Arena",
            city="Helsinki",
            description="A great summer concert featuring local bands",
            starts_at=datetime.now() + timedelta(days=30),
            status="active"
        ),
        Event(
            title="Tech Conference 2026",
            venue="Convention Center",
            city="Oulu",
            description="Annual technology conference",
            starts_at=datetime.now() + timedelta(days=60),
            status="active"
        ),
    ]
    db.session.add_all(events)
    db.session.commit()
    
    tickets = [
        Ticket(event=events[0], name="Standard", price=Decimal("25.00"), capacity=100, remaining=100),
        Ticket(event=events[0], name="VIP", price=Decimal("50.00"), capacity=20, remaining=20),
        Ticket(event=events[1], name="Early Bird", price=Decimal("75.00"), capacity=50, remaining=50),
        Ticket(event=events[1], name="Regular", price=Decimal("100.00"), capacity=100, remaining=100),
    ]
    db.session.add_all(tickets)
    db.session.commit()
    
    click.echo("Database seeded successfully!")
    click.echo(f"Created {len(users)} users, {len(events)} events, {len(tickets)} tickets")


def register_commands(app):
    """Register CLI commands for the Flask app.

    Args:
        app: Flask application instance
    """
    @app.cli.command("seed-db")
    def seed_db_command():
        """Seed the database with initial data."""
        seed_database()