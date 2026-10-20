from django.utils.translation import gettext_lazy

from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2026.3 or above to run this plugin!")


class PluginApp(PluginConfig):
    name = "pretix_regid"
    verbose_name = "Registration ID"

    class PretixPluginMeta:
        name = gettext_lazy("Registration ID")
        author = "Christiaan de Die le Clercq (techwolf12)"
        description = gettext_lazy(
            "Pretix plugin to add an automatic registration ID to approved orders"
        )
        visible = True
        version = __version__
        category = "FEATURE"
        compatibility = "pretix>=2026.3.0"
        settings_links = [
            (
                (gettext_lazy("Settings"), gettext_lazy("Registration ID")),
                "plugins:pretix_regid:control.regid.settings",
                {},
            ),
        ]

    def ready(self):
        from . import signals  # NOQA
