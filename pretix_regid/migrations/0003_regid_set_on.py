from django.core.cache import cache
from django.db import migrations

# Old checkbox settings, in the order they win if several were enabled. "placed"
# fires for every order. "paid" beats "approved" because orders that don't need
# approval are never approved, so they'd stop getting a registration ID.
OLD_KEYS = [
    ("regid__set_on_placed", "placed"),
    ("regid__set_on_paid", "paid"),
    ("regid__set_on_approved", "approved"),
]


def merge_triggers(apps, schema_editor):
    EventSettingsStore = apps.get_model("pretixbase", "Event_SettingsStore")
    old = EventSettingsStore.objects.filter(key__in=[k for k, _ in OLD_KEYS])

    enabled = {}
    for setting in old.filter(value="True"):
        enabled.setdefault(setting.object_id, set()).add(setting.key)

    for event_id, keys in enabled.items():
        value = next(v for k, v in OLD_KEYS if k in keys)
        EventSettingsStore.objects.update_or_create(
            object_id=event_id, key="regid__set_on", defaults={"value": value}
        )

    event_ids = set(old.values_list("object_id", flat=True))
    old.delete()
    cache.delete_many(["hierarkey_event_{}".format(i) for i in event_ids])


class Migration(migrations.Migration):

    dependencies = [
        ("pretix_regid", "0002_registrationid_id"),
        ("pretixbase", "0298_pluggable_permissions"),
    ]

    operations = [
        migrations.RunPython(merge_triggers, migrations.RunPython.noop),
    ]
