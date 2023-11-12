# Register your receivers here
import logging
from django.dispatch import receiver
from django.template.loader import get_template
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from pretix.base.models import Event, Order
from pretix.base.signals import order_approved, order_placed, order_changed, order_paid
from pretix.control.signals import nav_event_settings, order_info as control_order_info
from pretix.presale.signals import order_info

from .models import RegistrationID

logger = logging.getLogger(__name__)


def set_regid_on_order(order: Order):
    event: Event = order.event
    set_regid = False

    # Check if order Positions have a product for which we need to create a regid
    for orderPos in order.positions.all():
        if str(orderPos.item.id) in event.settings.regid__products:
            set_regid = True

    # Check for existing reg id on order
    try:
        regid_order = (
            RegistrationID.objects.all().filter(event=event, order=order).order_by("-regid")
        )
    except RegistrationID.DoesNotExist:
        regid_order = None

    # If there exists a RegID, or we don't have a OrderPosition that needs one, do nothing.
    if set_regid is False:
        logger.info("We don't need a regid for this order based on products")
        return

    if regid_order is not None and regid_order.count() > 0:
        logger.info("Order changed with existing regid, keeping")
        return
    
    try:
        all_regids_in_event = (
            RegistrationID.objects.all().filter(event=event).order_by("-regid")
        )
    except RegistrationID.DoesNotExist:
        all_regids_in_event = None

    if all_regids_in_event is None or all_regids_in_event.count() == 0:
        # We either have no previous results or no results matching the event, so we set the regid to 1
        new_regid = 1
    else:
        # Results are ordered by regid, get the highest one and add one
        all_regids_in_event = all_regids_in_event[:1].get()
        new_regid = all_regids_in_event.regid + 1

    regid = RegistrationID(regid=new_regid, event=event, order=order)
    regid.save()
    logger.info("Registration ID Created:" + str(regid.regid))


# Once the order gets approved, add a registration ID to the order
@receiver(order_approved, dispatch_uid="pretix_regid")
def order_approved(order: Order, *args, **kwargs):
    event: Event = order.event
    if event.settings.regid__approved:
        set_regid_on_order(order)

# Once the order gets placed, add a registration ID to the order
@receiver(order_placed, dispatch_uid="pretix_regid")
def order_placed(order: Order, *args, **kwargs):
    event: Event = order.event
    if event.settings.regid__placed:
        set_regid_on_order(order)

# Once the order gets changed, add a registration ID to the order
@receiver(order_changed, dispatch_uid="pretix_regid")
def order_changed(order: Order, *args, **kwargs):
    event: Event = order.event
    if event.settings.regid__changed:
        set_regid_on_order(order)

# Once the order gets paid, add a registration ID to the order
@receiver(order_paid, dispatch_uid="pretix_regid")
def order_paid(order: Order, *args, **kwargs):
    event: Event = order.event
    if event.settings.regid__paid:
        set_regid_on_order(order)

# TODO Remove when order is cancelled?
# TODO Recycle old reg id's?

# Show Registration ID
@receiver(control_order_info, dispatch_uid="regid_control_order_info")
def control_order_info(sender: Event, request, order: Order, **kwargs):
    template = get_template("pretix_regid/control_order_info.html")
    try:
        regid_from_order = RegistrationID.objects.get(order=order)
    except RegistrationID.DoesNotExist:
        regid_from_order = None

    ctx = {
        "order": order,
        "event": sender,
        "request": request,
        "regid": regid_from_order,
    }

    return template.render(ctx, request=request)


@receiver(order_info, dispatch_uid="regid_order_info")
def order_info(sender: Event, order: Order, **kwargs):
    template = get_template("pretix_regid/order_info.html")
    try:
        regid_from_order = RegistrationID.objects.get(order=order)
    except RegistrationID.DoesNotExist:
        regid_from_order = None

    ctx = {
        "order": order,
        "event": sender,
        "regid": regid_from_order,
    }

    return template.render(ctx)

@receiver(nav_event_settings, dispatch_uid="pretix_regid")
def navbar_settings(sender, request, **kwargs):
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