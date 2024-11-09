from typing import Self
from django.db import models
from django.db.models import Sum, Case, When, BooleanField, Subquery
from django.forms import IntegerField


class ScreeningQuerySet(models.QuerySet):
    # FIXME I would name it annotate_sold_out as `with_sold_out` implies filtering rather than annotation
    def with_sold_out(self) -> Self:
        """
        Annotate each Screening instance with a boolean field 'sold_out'
        indicating whether it is sold out
        """
        from .models import Reservation

        total_reserved = (
            Reservation.objects.filter(screening=models.OuterRef("pk"))
            .values("screening")
            .annotate(total_reserved=Sum("quantity"))
            .values_list("total_reserved", flat=True)
        )

        return self.annotate(
            sold_out=Case(
                When(
                    capacity__lte=Subquery(total_reserved, output_field=IntegerField()),
                    then=True,
                ),
                default=False,
                output_field=BooleanField(),
            )
        )
