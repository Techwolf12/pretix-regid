# Register your receivers here
import json
import logging
from django import forms
from django.dispatch import receiver
from django.http import HttpRequest
from django.template.loader import get_template
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from pretix.base.i18n import LazyI18nString
from pretix.base.models import Event, Order, OrderPosition
from pretix.base.services.cart import CartError
from pretix.base.settings import settings_hierarkey
from pretix.base.signals import (
    logentry_display,
    order_approved
)
from .models import RegistrationID

logger = logging.getLogger(__name__)

# Once the order gets approved, add a registration ID to the order
@receiver(order_approved, dispatch_uid="pretix_regid")
def order_approved(order: Order, *args, **kwargs):
    event = order.event
    try:
        all_regids_in_event = RegistrationID.objects.all().filter(event = event).order_by('-regid')
    except RegistrationID.DoesNotExist:
        all_regids_in_event = None

    if all_regids_in_event == None or all_regids_in_event.count() == 0:
        # We either have no previous results or no results matching the event, so we set the regid to 1
        new_regid = 1
    else:
        # Results are ordered by regid, get the highest one and add one
        all_regids_in_event = all_regids_in_event[:1].get()
        new_regid = all_regids_in_event.regid + 1
    
    regid = RegistrationID(regid = new_regid, event = event, order = order)
    regid.save()
    logger.info("RegID Created:" + str(regid.regid))


# TODO Remove when order is cancelled?
# TODO Recycle old reg id's?