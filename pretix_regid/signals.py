import logging
from django.db import transaction
from django.db.models import Max, Q
from django.dispatch import receiver
from django.template.loader import get_template
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from pretix.base.models import Event, Order
from pretix.base.settings import settings_hierarkey
from pretix.base.signals import (
    layout_text_variables,
    order_approved,
    order_changed,
    order_paid,
    order_placed,
)
from pretix.control.signals import (
    nav_event_settings,
    order_info as control_order_info,
    order_search_filter_q,
)
from pretix.presale.signals import order_info

from .models import RegistrationID

logger = logging.getLogger(__name__)

settings_hierarkey.add_default("regid__products", "[]", list)
settings_hierarkey.add_default("regid__set_on", "never", str)
settings_hierarkey.add_default("regid__set_on_changed", "False", bool)
settings_hierarkey.add_default("regid__hide_from_customer", "False", bool)


def order_needs_regid(order: Order) -> bool:
    products = order.event.settings.regid__products
    return any(str(p.item_id) in products for p in order.positions.all())


def set_regid_on_order(order: Order):
    event: Event = order.event

    if not order_needs_regid(order):
        return

    with transaction.atomic():
        # Lock the event row so concurrent orders can't be handed the same ID
        Event.objects.select_for_update().only("pk").get(pk=event.pk)

        if RegistrationID.objects.filter(order=order).exists():
            return

        highest = RegistrationID.objects.filter(event=event).aggregate(m=Max("regid"))[
            "m"
        ]
        regid = RegistrationID.objects.create(
            event=event, order=order, regid=(highest or 0) + 1
        )

    logger.info("Registration ID %s created for order %s", regid.regid, order.code)


@receiver(order_placed, dispatch_uid="pretix_regid_order_placed")
def on_order_placed(sender: Event, order: Order, **kwargs):
    if sender.settings.regid__set_on == "placed":
        set_regid_on_order(order)


@receiver(order_approved, dispatch_uid="pretix_regid_order_approved")
def on_order_approved(sender: Event, order: Order, **kwargs):
    if sender.settings.regid__set_on == "approved":
        set_regid_on_order(order)


@receiver(order_paid, dispatch_uid="pretix_regid_order_paid")
def on_order_paid(sender: Event, order: Order, **kwargs):
    if sender.settings.regid__set_on == "paid":
        set_regid_on_order(order)


@receiver(order_changed, dispatch_uid="pretix_regid_order_changed")
def on_order_changed(sender: Event, order: Order, **kwargs):
    if sender.settings.regid__set_on_changed:
        set_regid_on_order(order)


# Lets the order search (control and API) find orders by registration ID. This is a
# global signal, so it also runs for events that don't have the plugin enabled.
@receiver(order_search_filter_q, dispatch_uid="pretix_regid_order_search_filter_q")
def on_order_search_filter_q(sender, query, **kwargs):
    query = query.strip()
    # Cap the length so the value fits the integer column
    if not (query.isascii() and query.isdigit()) or len(query) > 9:
        return Q()
    if sender is not None and "pretix_regid" not in sender.get_plugins():
        return Q()

    regids = RegistrationID.objects.filter(regid=int(query))
    if sender is not None:
        regids = regids.filter(event=sender)
    return Q(pk__in=regids.values("order_id"))


def _regid_of_order(order: Order) -> str:
    regid = RegistrationID.objects.filter(order=order).first()
    return str(regid.regid) if regid else ""


def _regids_of_positions(positions) -> list:
    regids = dict(
        RegistrationID.objects.filter(
            order_id__in={op.order_id for op in positions}
        ).values_list("order_id", "regid")
    )
    return [str(regids.get(op.order_id, "")) for op in positions]


@receiver(layout_text_variables, dispatch_uid="pretix_regid_layout_text_variables")
def on_layout_text_variables(sender: Event, **kwargs):
    # Usable on tickets and badges, and included in the check-in API's pdf_data.
    return {
        "pretix_regid_regid": {
            "label": _("Registration ID"),
            "editor_sample": "42",
            "evaluate": lambda op, order, ev: _regid_of_order(order),
            "evaluate_bulk": _regids_of_positions,
        },
    }


# TODO Remove when order is cancelled?
# TODO Recycle old reg id's?


@receiver(control_order_info, dispatch_uid="pretix_regid_control_order_info")
def on_control_order_info(sender: Event, request, order: Order, **kwargs):
    template = get_template("pretix_regid/control_order_info.html")
    ctx = {
        "order": order,
        "event": sender,
        "request": request,
        "regid": RegistrationID.objects.filter(order=order).first(),
    }
    return template.render(ctx, request=request)


@receiver(order_info, dispatch_uid="pretix_regid_order_info")
def on_order_info(sender: Event, order: Order, **kwargs):
    if sender.settings.regid__hide_from_customer:
        return ""
    template = get_template("pretix_regid/order_info.html")
    ctx = {
        "order": order,
        "event": sender,
        "regid": RegistrationID.objects.filter(order=order).first(),
    }
    return template.render(ctx)


@receiver(nav_event_settings, dispatch_uid="pretix_regid_nav_event_settings")
def navbar_settings(sender: Event, request, **kwargs):
    if not request.user.has_event_permission(
        request.organizer,
        request.event,
        "event.settings.general:write",
        request=request,
    ):
        return []
    url = resolve(request.path_info)
    return [
        {
            "label": _("Registration ID"),
            "url": reverse(
                "plugins:pretix_regid:control.regid.settings",
                kwargs={
                    "event": request.event.slug,
                    "organizer": request.organizer.slug,
                },
            ),
            "active": url.namespace == "plugins:pretix_regid"
            and url.url_name == "control.regid.settings",
        }
    ]
