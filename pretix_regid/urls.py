from django.urls import re_path
from pretix.api.urls import event_router

from .api import RegistrationIDViewSet
from .views import SettingsView

urlpatterns = [
    re_path(
        r"^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/regid/$",
        SettingsView.as_view(),
        name="control.regid.settings",
    ),
]

event_router.register("regid", RegistrationIDViewSet, basename="regid")
