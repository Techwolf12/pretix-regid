import base64
import hmac
import logging
from collections import defaultdict
from django import forms
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Exists, OuterRef
from django.forms.widgets import CheckboxSelectMultiple, RadioSelect
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import FormView, ListView, TemplateView
from django_scopes import scopes_disabled
from i18nfield.forms import I18nFormField, I18nTextInput
from django.conf import settings
from pretix.base.forms import SettingsForm
from pretix.base.models import (
    Event,
    Order,
    OrderPosition,
    OrderRefund,
    Question,
    SubEvent,
)
from pretix.base.views.metrics import unauthed_response
from pretix.base.views.tasks import AsyncAction
from pretix.control.permissions import EventPermissionRequiredMixin
from pretix.control.views import UpdateView
from pretix.control.views.event import EventSettingsFormView, EventSettingsViewMixin
from pretix.control.views.orders import OrderView
from pretix.multidomain.urlreverse import eventreverse
from pretix.presale.views import EventViewMixin
from pretix.presale.views.order import OrderDetailMixin
from pretix.helpers.compat import CompatDeleteView

logger = logging.getLogger(__name__)


class RoomsharingSettingsForm(SettingsForm):
    regid__products = forms.MultipleChoiceField(
        choices=[],
        label=_("Registration ID products"),
        required=False,
        widget=CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        event = kwargs.get("obj")
        super().__init__(*args, **kwargs)

        choices = (
            (str(i["id"]), i["name"]) for i in event.items.values("name", "id").all()
        )

        self.fields["regid__products"].choices = choices
        self.fields["regid__products"].initial = event.settings.regid__products



class SettingsView(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = RoomsharingSettingsForm
    template_name = "pretix_regid/settings.html"
    permission = "can_change_settings"

    def get_success_url(self):
        return reverse(
            "plugins:pretix_regid:control.regid.settings",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )