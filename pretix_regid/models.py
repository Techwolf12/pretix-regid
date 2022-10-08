from django.db import models
from pretix.base.models import LoggedModel


class RegistrationID(LoggedModel):
    event = models.ForeignKey(
        "pretixbase.Event", on_delete=models.CASCADE, related_name="regids"
    )
    order = models.OneToOneField(
        on_delete=models.CASCADE, related_name="regids", to="pretixbase.Order"
    )
    regid = models.PositiveIntegerField(verbose_name="RegistrationID")

    class Meta:
        unique_together = (("event", "order"),)
        ordering = ("order",)

    def __str__(self):
        return self.name
