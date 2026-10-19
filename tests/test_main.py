import pytest
from django_scopes import scopes_disabled
from pretix.base.models import Event, Item, Order
from pretix.base.signals import order_approved, order_changed, order_paid, order_placed

from pretix_regid.models import RegistrationID


def regid_of(order):
    r = RegistrationID.objects.filter(order=order).first()
    return r.regid if r else None


@pytest.fixture
def configured(event, item):
    event.settings.regid__products = [str(item.pk)]
    event.settings.regid__set_on = "paid"
    return event


@pytest.mark.django_db
def test_defaults(event):
    assert event.settings.regid__products == []
    assert event.settings.regid__set_on == "never"
    assert event.settings.regid__set_on_changed is False


@pytest.mark.django_db
def test_no_regid_without_products(event, item, make_order):
    event.settings.regid__set_on = "paid"
    order = make_order(item)
    order_paid.send(event, order=order)
    assert regid_of(order) is None


@pytest.mark.django_db
def test_no_regid_for_unselected_product(configured, other_item, make_order):
    order = make_order(other_item)
    order_paid.send(configured, order=order)
    assert regid_of(order) is None


@pytest.mark.django_db
def test_no_regid_when_trigger_disabled(configured, item, make_order):
    order = make_order(item)
    order_placed.send(configured, order=order)
    order_approved.send(configured, order=order)
    order_changed.send(configured, order=order)
    assert regid_of(order) is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "setting,value,signal",
    [
        ("regid__set_on", "placed", order_placed),
        ("regid__set_on", "approved", order_approved),
        ("regid__set_on", "paid", order_paid),
        ("regid__set_on_changed", True, order_changed),
    ],
)
def test_trigger(event, item, make_order, setting, value, signal):
    event.settings.regid__products = [str(item.pk)]
    event.settings.set(setting, value)
    order = make_order(item)
    signal.send(event, order=order)
    assert regid_of(order) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["never", "placed", "approved"])
def test_only_selected_trigger_fires(event, item, make_order, value):
    event.settings.regid__products = [str(item.pk)]
    event.settings.regid__set_on = value
    order = make_order(item)
    order_paid.send(event, order=order)
    assert regid_of(order) is None


@pytest.mark.django_db
def test_mixed_order_gets_regid(configured, item, other_item, make_order):
    order = make_order(other_item, item)
    order_paid.send(configured, order=order)
    assert regid_of(order) == 1


@pytest.mark.django_db
def test_regids_increment_and_are_stable(configured, item, make_order):
    o1, o2, o3 = make_order(item), make_order(item), make_order(item)
    order_paid.send(configured, order=o1)
    order_paid.send(configured, order=o2)
    order_paid.send(configured, order=o1)
    order_paid.send(configured, order=o3)
    assert (regid_of(o1), regid_of(o2), regid_of(o3)) == (1, 2, 3)
    assert RegistrationID.objects.count() == 3


@pytest.mark.django_db
def test_regids_are_per_event(configured, item, make_order, organizer):
    ev2 = Event.objects.create(
        organizer=organizer,
        name="Other",
        slug="other",
        date_from=configured.date_from,
        plugins="pretix_regid",
    )
    item2 = Item.objects.create(event=ev2, name="Ticket", default_price=1)
    ev2.settings.regid__products = [str(item2.pk)]
    ev2.settings.regid__set_on = "paid"

    order_paid.send(configured, order=make_order(item))
    o2 = make_order(item2)
    order_paid.send(ev2, order=o2)
    assert regid_of(o2) == 1


@pytest.mark.django_db
def test_payment_confirmation_assigns_regid(configured, item, make_order):
    order = make_order(item)
    with scopes_disabled():
        payment = order.payments.create(provider="manual", amount=order.total)
        payment.confirm()
        order.refresh_from_db()
    assert order.status == Order.STATUS_PAID
    assert regid_of(order) == 1


@pytest.mark.django_db
def test_plugin_disabled(configured, item, make_order):
    configured.disable_plugin("pretix_regid")
    configured.save()
    order = make_order(item)
    order_paid.send(configured, order=order)
    assert regid_of(order) is None


def settings_url(event):
    return "/control/event/%s/%s/regid/" % (event.organizer.slug, event.slug)


@pytest.mark.django_db
def test_settings_view_saves(admin_client, event, item, other_item):
    r = admin_client.get(settings_url(event))
    assert r.status_code == 200
    assert "Ticket" in r.content.decode()

    r = admin_client.post(
        settings_url(event),
        {
            "regid__products": [str(item.pk)],
            "regid__set_on": "approved",
            "regid__set_on_changed": "on",
        },
    )
    assert r.status_code == 302
    event.settings.flush()
    assert event.settings.regid__products == [str(item.pk)]
    assert event.settings.regid__set_on == "approved"
    assert event.settings.regid__set_on_changed is True

    r = admin_client.get(settings_url(event))
    assert r.context["form"].initial["regid__products"] == [str(item.pk)]


@pytest.mark.django_db
def test_settings_view_requires_login(client, event):
    r = client.get(settings_url(event))
    assert r.status_code == 302
    assert "/control/login" in r["Location"]


@pytest.mark.django_db
def test_control_order_page_shows_regid(admin_client, configured, item, make_order):
    order = make_order(item)
    order_paid.send(configured, order=order)
    r = admin_client.get(
        "/control/event/%s/%s/orders/%s/"
        % (configured.organizer.slug, configured.slug, order.code)
    )
    assert r.status_code == 200
    assert "registration ID is: <strong>1</strong>" in r.content.decode()


def search(client, event, query):
    r = client.get(
        "/control/event/%s/%s/orders/" % (event.organizer.slug, event.slug),
        {"query": query},
    )
    assert r.status_code == 200
    return {o.code for o in r.context["orders"]}


@pytest.mark.django_db
def test_order_search_by_regid(admin_client, configured, item, make_order):
    o1, o2 = make_order(item), make_order(item)
    order_paid.send(configured, order=o1)
    order_paid.send(configured, order=o2)
    assert search(admin_client, configured, "2") == {o2.code}
    assert search(admin_client, configured, " 1 ") == {o1.code}
    assert search(admin_client, configured, "3") == set()


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["abc", "²", "99999999999999999999"])
def test_order_search_ignores_non_regid_queries(
    admin_client, configured, item, make_order, query
):
    order_paid.send(configured, order=make_order(item))
    assert search(admin_client, configured, query) == set()


@pytest.mark.django_db
def test_order_search_by_regid_plugin_disabled(
    admin_client, configured, item, make_order
):
    order_paid.send(configured, order=make_order(item))
    configured.disable_plugin("pretix_regid")
    configured.save()
    assert search(admin_client, configured, "1") == set()


@pytest.mark.django_db
def test_order_search_by_regid_api(configured, item, make_order, organizer):
    from pretix.base.models import Team
    from rest_framework.test import APIClient

    order = make_order(item)
    order_paid.send(configured, order=order)
    team = Team.objects.create(
        organizer=organizer, all_events=True, all_event_permissions=True
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + team.tokens.create(name="t").token)
    r = client.get(
        "/api/v1/organizers/%s/events/%s/orders/" % (organizer.slug, configured.slug),
        {"search": "1"},
    )
    assert r.status_code == 200
    assert [o["code"] for o in r.data["results"]] == [order.code]


def _regid_layout_variable(event):
    from pretix.base.signals import layout_text_variables

    for _receiver, response in layout_text_variables.send(event):
        if "pretix_regid_regid" in (response or {}):
            return response["pretix_regid_regid"]
    return None


@pytest.mark.django_db
def test_layout_text_variable(configured, item, make_order):
    with_regid = make_order(item)
    order_paid.send(configured, order=with_regid)
    without_regid = make_order(item)

    var = _regid_layout_variable(configured)
    assert var is not None

    op = with_regid.positions.first()
    assert var["evaluate"](op, with_regid, configured) == "1"
    other_op = without_regid.positions.first()
    assert var["evaluate"](other_op, without_regid, configured) == ""
    assert var["evaluate_bulk"]([op, other_op]) == ["1", ""]


@pytest.mark.django_db
def test_layout_text_variable_plugin_disabled(configured):
    configured.disable_plugin("pretix_regid")
    configured.save()
    assert _regid_layout_variable(configured) is None
