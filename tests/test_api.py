import pytest
from django.utils.timezone import now
from pretix.base.models import Event, Question, Team
from pretix.base.models.devices import generate_api_token
from pretix.base.signals import order_paid
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def team(organizer):
    return Team.objects.create(
        organizer=organizer, all_events=True, all_event_permissions=True
    )


@pytest.fixture
def token_client(team):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + team.tokens.create(name="t").token)
    return client


@pytest.fixture
def order_with_regid(event, item, make_order):
    event.settings.regid__products = [str(item.pk)]
    event.settings.regid__set_on = "paid"
    question = Question.objects.create(
        event=event, question="T-shirt size", type="S", identifier="SIZE"
    )
    question.items.add(item)
    order = make_order(item)
    order.positions.first().answers.create(question=question, answer="XL")
    order_paid.send(event, order=order)
    return order


def url(event, regid):
    return "/api/v1/organizers/%s/events/%s/regid/%s/" % (
        event.organizer.slug,
        event.slug,
        regid,
    )


def test_retrieve(token_client, event, item, order_with_regid):
    r = token_client.get(url(event, 1))
    assert r.status_code == 200
    data = r.data
    assert data["regid"] == 1
    assert data["code"] == order_with_regid.code
    assert data["status"] == "n"
    [position] = data["positions"]
    assert position["item"] == item.pk
    [answer] = position["answers"]
    assert answer["answer"] == "XL"
    assert answer["question_identifier"] == "SIZE"


def test_exclude(token_client, event, order_with_regid):
    r = token_client.get(url(event, 1), {"exclude": "positions"})
    assert r.status_code == 200
    assert "positions" not in r.data
    assert r.data["regid"] == 1


@pytest.mark.parametrize("regid", ["2", "0"])
def test_unknown_regid(token_client, event, order_with_regid, regid):
    assert token_client.get(url(event, regid)).status_code == 404


@pytest.mark.parametrize("regid", ["abc", "9999999999"])
def test_invalid_regid(token_client, event, order_with_regid, regid):
    assert token_client.get(url(event, regid)).status_code == 404


def test_no_list_endpoint(token_client, event, order_with_regid):
    r = token_client.get(
        "/api/v1/organizers/%s/events/%s/regid/" % (event.organizer.slug, event.slug)
    )
    assert r.status_code == 404


def test_read_only(token_client, event, order_with_regid):
    assert token_client.delete(url(event, 1)).status_code == 405
    assert token_client.put(url(event, 1), {}).status_code == 405


def test_regid_of_other_event(token_client, organizer, event, order_with_regid):
    other = Event.objects.create(
        organizer=organizer,
        name="Other",
        slug="other",
        date_from=now(),
        plugins="pretix_regid",
    )
    assert token_client.get(url(other, 1)).status_code == 404


def test_plugin_disabled(token_client, event, order_with_regid):
    event.disable_plugin("pretix_regid")
    event.save()
    assert token_client.get(url(event, 1)).status_code == 404


def test_requires_auth(event, order_with_regid):
    assert APIClient().get(url(event, 1)).status_code == 401


def test_requires_order_permission(organizer, event, order_with_regid):
    team = Team.objects.create(
        organizer=organizer,
        all_events=True,
        all_event_permissions=False,
        limit_event_permissions={"event.settings.general:write": True},
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + team.tokens.create(name="t").token)
    assert client.get(url(event, 1)).status_code == 403


def device_client(organizer, security_profile):
    device = organizer.devices.create(
        name="Scanner",
        all_events=True,
        initialized=now(),
        api_token=generate_api_token(),
        security_profile=security_profile,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Device " + device.api_token)
    return client


def test_device_full_access(organizer, event, order_with_regid):
    r = device_client(organizer, "full").get(url(event, 1))
    assert r.status_code == 200
    assert r.data["regid"] == 1


def test_device_pretixscan_profile_not_allowed(organizer, event, order_with_regid):
    # pretixSCAN profiles only allow a fixed list of pretix's own endpoints
    r = device_client(organizer, "pretixscan").get(url(event, 1))
    assert r.status_code == 403
