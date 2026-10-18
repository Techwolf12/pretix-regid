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

    regid__set_on_placed = forms.BooleanField(
        required=False,
        label=_("Set Registration ID on placed"),
        help_text=_(
            "Set the registration ID on placed orders. If you leave the rest empty, it will only set it once the order is placed"
        ),
    )

    regid__set_on_approved = forms.BooleanField(
        required=False,
        label=_("Set Registration ID on approved"),
        help_text=_(
            "Set the registration ID on approved orders. If you leave the rest empty, it will only set it once the order is approved"
        ),
    )

    regid__set_on_paid = forms.BooleanField(
        required=False,
        label=_("Set Registration ID on paid"),
        help_text=_(
            "Set the registration ID on paid orders. If you leave the rest empty, it will only set it once the order is paid"
        ),
    )

    regid__set_on_changed = forms.BooleanField(
        required=False,
        label=_("Set Registration ID on order changed"),
        help_text=_("Set the registration ID when a order has a change in products."),
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
