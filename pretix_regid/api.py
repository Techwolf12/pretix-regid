from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from pretix.api.serializers.order import OrderSerializer
from pretix.base.models import Checkin, Order, OrderFee, OrderPosition, QuestionAnswer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from .models import RegistrationID


class RegistrationIDViewSet(viewsets.ViewSet):
    """Look up an order by its registration ID.

    Returns the same data as pretix's order endpoint, plus ``regid``.
    """

    permission = "event.orders:read"
    lookup_field = "regid"
    lookup_value_regex = r"\d{1,9}"

    def retrieve(self, request, regid=None, **kwargs):
        if "pretix_regid" not in request.event.get_plugins():
            raise NotFound()

        regid = get_object_or_404(
            RegistrationID.objects.all(), event=request.event, regid=int(regid)
        )
        order = get_object_or_404(
            Order.objects.filter(pk=regid.order_id)
            .select_related("invoice_address", "customer", "sales_channel")
            .prefetch_related(
                Prefetch("fees", queryset=OrderFee.objects.all()),
                "payments",
                "refunds",
                "refunds__payment",
                Prefetch(
                    "positions",
                    queryset=OrderPosition.objects.prefetch_related(
                        Prefetch(
                            "checkins",
                            queryset=Checkin.objects.select_related("device"),
                        ),
                        "print_logs",
                        "item",
                        "variation",
                        Prefetch(
                            "answers",
                            queryset=QuestionAnswer.objects.prefetch_related(
                                "options", "question"
                            ).order_by("question__position"),
                        ),
                        "seat",
                    ),
                ),
            )
        )

        serializer = OrderSerializer(
            instance=order,
            context={
                "request": request,
                "event": request.event,
                "auth": request.auth,
                "pdf_data": False,
                "include": request.query_params.getlist("include"),
                "exclude": request.query_params.getlist("exclude"),
            },
        )
        return Response({"regid": regid.regid, **serializer.data})

    @action(detail=False, url_path=r"by-order/(?P<code>[^/]+)", url_name="by-order")
    def by_order(self, request, code=None, **kwargs):
        """Look up the registration ID of an order by its order code.

        ``regid`` is ``null`` if the order has no registration ID.
        """
        if "pretix_regid" not in request.event.get_plugins():
            raise NotFound()

        order = get_object_or_404(Order, event=request.event, code=code)
        regid = RegistrationID.objects.filter(order=order).first()
        return Response({"order": order.code, "regid": regid.regid if regid else None})
