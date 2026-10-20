import logging
from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from pretix.base.forms import SettingsForm
from pretix.base.models import Event
from pretix.control.views.event import EventSettingsFormView, EventSettingsViewMixin

logger = logging.getLogger(__name__)


class RegistrationIDSettingsForm(SettingsForm):
    regid__products = forms.MultipleChoiceField(
        choices=[],
        label=_("Registration ID products"),
        required=False,
        widget=CheckboxSelectMultiple,
        help_text=_(
            "Registration IDs are only generated for orders that contain at least one of "
            "these products. If no product is selected, no registration IDs are generated."
        ),
    )

    regid__set_on = forms.ChoiceField(
        choices=[
            ("never", _("Never")),
            ("placed", _("When the order is placed")),
            ("approved", _("When the order is approved")),
            ("paid", _("When the order is paid")),
        ],
        label=_("Set Registration ID"),
        help_text=_(
            "Only orders that require approval are ever approved. If you choose "
            '"When the order is approved", other orders don\'t get a registration ID.'
        ),
    )

    regid__set_on_changed = forms.BooleanField(
        required=False,
        label=_("Set Registration ID on order changed"),
        help_text=_(
            "Also set a registration ID when an order without one is changed so that it "
            "now contains one of the selected products. Orders that already have a "
            "registration ID keep it."
        ),
    )

    regid__hide_from_customer = forms.BooleanField(
        required=False,
        label=_("Hide registration ID from customers"),
        help_text=_(
            "Don't show the registration ID on the customer's order page. It is still "
            "assigned and visible in the backend and the API. It is only printed on "
            "tickets or badges if you add it to their layout yourself."
        ),
    )

    def __init__(self, *args, **kwargs):
        event = kwargs.get("obj")
        super().__init__(*args, **kwargs)

        self.fields["regid__products"].choices = [
            (str(item.pk), str(item.name)) for item in event.items.all()
        ]


class SettingsView(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = RegistrationIDSettingsForm
    template_name = "pretix_regid/settings.html"
    permission = "event.settings.general:write"

    def get_success_url(self):
        return reverse(
            "plugins:pretix_regid:control.regid.settings",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )
