from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError, OperationalError
from models import app, db, User, Event, Ticket, Order

def seed():
    alice = User(name="Alice Smith", email="alice.smith@hotmail.com")
    bob = User(name="Bob Johnson", email="bob.johnson@gmail.com")
    charlie = User(name="Charlie Brown", email="charlie.brown@yahoo.com")

    now = datetime.now()

    conference = Event(title="Winter Symposium", venue="Helsinki Conference Center", city="Helsinki", description="A one-day symposium with talks and networking.", starts_at=now + timedelta(days=30, hours=9), ends_at=now + timedelta(days=30, hours=17))
    concert = Event(title="Rock Concert", venue="45 Special", city="Oulu", description="Live rock night with local bands and a late DJ set.", starts_at=now + timedelta(days=18, hours=20), ends_at=now + timedelta(days=19, hours=1))
    festival = Event(title="Summer Music Festival", venue="Ainolan Puisto", city="Oulu", description="Outdoor festival with multiple acts, food stalls, and activities.", starts_at=now + timedelta(days=90, hours=12), ends_at=now + timedelta(days=90, hours=22))
    gig = Event(title="Indie Gig", venue="Club Teatria", city="Oulu", description="Indie gig night with support acts.", starts_at=now + timedelta(days=40, hours=20), ends_at=now + timedelta(days=41, hours=0))
    screening = Event(title="Documentary Screening", venue="Kulttuuritalo Valve", city="Oulu", description="Evening screening + short discussion after the film.", starts_at=now + timedelta(days=22, hours=18), ends_at=now + timedelta(days=22, hours=20))
    symphony = Event(title="Symphony Evening", venue="Oulun Musiikkikeskus (Madetojan sali)", city="Oulu", description="Orchestra concert in Madetojan sali.", starts_at=now + timedelta(days=35, hours=19), ends_at=now + timedelta(days=35, hours=21))
    esports = Event(title="Esports Cup", venue="Ouluhalli", city="Oulu", description="Tournament day with audience seating and finals in the evening.", starts_at=now + timedelta(days=55, hours=12), ends_at=now + timedelta(days=55, hours=20))
    match = Event(title="Match Day", venue="Raatin stadion", city="Oulu", description="Match day event with gates opening earlier for fan activities.", starts_at=now + timedelta(days=65, hours=16), ends_at=now + timedelta(days=65, hours=19))

    db.session.add_all([alice, bob, charlie, conference, concert, festival, gig, screening, symphony, esports, match])
    db.session.flush()

    conf_standard = Ticket(event=conference, name="Standard", price=59.90, capacity=300, remaining=300)
    conf_student = Ticket(event=conference, name="Student", price=29.90, capacity=120, remaining=120)

    concert_standard = Ticket(event=concert, name="Standard", price=18.00, capacity=350, remaining=350)
    concert_vip = Ticket(event=concert, name="VIP", price=45.00, capacity=40, remaining=40)

    festival_day = Ticket(event=festival, name="Day Pass", price=35.00, capacity=2000, remaining=2000)
    festival_vip = Ticket(event=festival, name="VIP", price=79.00, capacity=150, remaining=150)

    gig_standard = Ticket(event=gig, name="Standard", price=22.00, capacity=1000, remaining=1000)

    screening_standard = Ticket(event=screening, name="Standard", price=12.00, capacity=180, remaining=180)

    symphony_standard = Ticket(event=symphony, name="Standard", price=39.90, capacity=600, remaining=600)
    symphony_vip = Ticket(event=symphony, name="VIP", price=79.90, capacity=60, remaining=60)

    esports_standard = Ticket(event=esports, name="Standard", price=10.00, capacity=800, remaining=800)

    match_standard = Ticket(event=match, name="Standard", price=15.00, capacity=2500, remaining=2500)
    match_vip = Ticket(event=match, name="VIP", price=49.00, capacity=150, remaining=150)

    db.session.add_all([
        conf_standard, conf_student,
        concert_standard, concert_vip,
        festival_day, festival_vip,
        gig_standard,
        screening_standard,
        symphony_standard, symphony_vip,
        esports_standard,
        match_standard, match_vip
    ])
    db.session.flush()

    for _ in range(2):
        db.session.add(Order(user=alice, ticket=concert_standard, status="not_used"))
        concert_standard.remaining -= 2

        db.session.add(Order(user=alice, ticket=symphony_vip, status="not_used"))
        symphony_vip.remaining -= 1

        db.session.add(Order(user=bob, ticket=conf_standard, status="not_used"))
        conf_standard.remaining -= 1

    for _ in range(3):
        db.session.add(Order(user=bob, ticket=gig_standard, status="not_used"))
        gig_standard.remaining -= 3

        db.session.add(Order(user=charlie, ticket=screening_standard, status="used"))
        screening_standard.remaining -= 1

        db.session.add(Order(user=charlie, ticket=match_vip, status="not_used"))
        match_vip.remaining -= 1


if __name__ == "__main__":
    with app.app_context():
        try:
            db.drop_all()
            db.create_all()
            seed()
            db.session.commit()
            print("OK, done!")
        except (IntegrityError, OperationalError, ValueError) as e:
            db.session.rollback()
            print("ERROR:", e)