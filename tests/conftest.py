import pytest
from datetime import timedelta
from decimal import Decimal
from django.utils.timezone import now
from django_scopes import scopes_disabled
from pretix.base.models import Event, Item, Order, OrderPosition, Organizer, Team, User


@pytest.fixture
def organizer():
    return Organizer.objects.create(name="Dummy", slug="dummy")


@pytest.fixture
def event(organizer):
    return Event.objects.create(
        organizer=organizer,
        name="Dummy",
        slug="dummy",
        date_from=now(),
        plugins="pretix_regid",
    )


@pytest.fixture
def item(event):
    return Item.objects.create(
        event=event, name="Ticket", default_price=Decimal("23.00")
    )


@pytest.fixture
def other_item(event):
    return Item.objects.create(
        event=event, name="T-Shirt", default_price=Decimal("10.00")
    )


@pytest.fixture
def make_order():
    counter = iter(range(1, 1000))

    def make(*items):
        event = items[0].event
        with scopes_disabled():
            order = Order.objects.create(
                code="ORDER%d" % next(counter),
                event=event,
                email="dummy@dummy.test",
                status=Order.STATUS_PENDING,
                datetime=now(),
                expires=now() + timedelta(days=10),
                total=sum(i.default_price for i in items),
                sales_channel=event.organizer.sales_channels.get(identifier="web"),
            )
            for i in items:
                OrderPosition.objects.create(
                    order=order, item=i, variation=None, price=i.default_price
                )
        return order

    return make


@pytest.fixture
def admin_client(client, organizer, event):
    user = User.objects.create_user("dummy@dummy.dummy", "dummy")
    team = Team.objects.create(
        organizer=organizer, all_events=True, all_event_permissions=True
    )
    team.members.add(user)
    client.login(email="dummy@dummy.dummy", password="dummy")
    return client


@pytest.fixture(autouse=True)
def no_scopes():
    # pretix activates the organizer scope before plugin signals fire. Outside
    # of a request we have no scope, so disable scoping for the tests.
    with scopes_disabled():
        yield
