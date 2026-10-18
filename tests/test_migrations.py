import importlib
import pytest
from django.apps import apps
from pretix.base.models.event import Event_SettingsStore

# pretix's test settings disable migrations, so call the migration function directly
merge_triggers = importlib.import_module(
    "pretix_regid.migrations.0003_regid_set_on"
).merge_triggers


@pytest.mark.django_db
@pytest.mark.parametrize(
    "old,expected",
    [
        ({}, "never"),
        ({"regid__set_on_approved": "False"}, "never"),
        ({"regid__set_on_approved": "True"}, "approved"),
        ({"regid__set_on_paid": "True"}, "paid"),
        ({"regid__set_on_approved": "True", "regid__set_on_paid": "True"}, "paid"),
        ({"regid__set_on_placed": "True", "regid__set_on_paid": "True"}, "placed"),
    ],
)
def test_merge_triggers(event, old, expected):
    for key, value in old.items():
        Event_SettingsStore.objects.create(object=event, key=key, value=value)
    Event_SettingsStore.objects.create(
        object=event, key="regid__set_on_changed", value="True"
    )
    event.settings.flush()

    merge_triggers(apps, None)

    event.settings.flush()
    assert event.settings.regid__set_on == expected
    assert event.settings.regid__set_on_changed is True
    keys = set(
        Event_SettingsStore.objects.filter(object=event).values_list("key", flat=True)
    )
    assert not keys & {
        "regid__set_on_placed",
        "regid__set_on_approved",
        "regid__set_on_paid",
    }
