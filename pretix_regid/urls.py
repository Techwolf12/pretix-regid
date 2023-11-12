from django.urls import re_path

from .views import SettingsView

urlpatterns = [
    re_path(
        r"^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/regid/",
        SettingsView.as_view(),
        name="control.regid.settings",
    ),
]
