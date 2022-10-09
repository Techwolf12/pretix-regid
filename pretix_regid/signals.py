# Register your receivers here
import logging
from django.dispatch import receiver
from django.template.loader import get_template
from pretix.base.models import Event, Order
from pretix.base.signals import order_approved
from pretix.control.signals import order_info as control_order_info
from pretix.presale.signals import order_info

from .models import RegistrationID

logger = logging.getLogger(__name__)


# Once the order gets approved, add a registration ID to the order
@receiver(order_approved, dispatch_uid="pretix_regid")
def order_approved(order: Order, *args, **kwargs):
    event: Event = order.event
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
    logger.info("RegID Created:" + str(regid.regid))


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
