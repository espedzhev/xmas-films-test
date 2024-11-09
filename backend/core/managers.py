"""
Add a ReservationManager with a custom create method.
- This should use the provided screening and quantity kwargs to sense-check the values are acceptable, given the current state of the data in the Reservation table.
- If there is an issue, a ValidationError should be rasied.
- The method should make use of transaction.atomic and select_for_update to guard against race conditions
- Tests should be added to cover this ne
"""
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum

if TYPE_CHECKING:
    from .models import Reservation, Screening


class ReservationManager(models.Manager):
    @transaction.atomic
    def create(
        self,
        screening: "Screening",
        quantity: int,
        **kwargs: dict[str, Any],
    ) -> "Reservation":
        from .models import Reservation, Screening

        screening: Screening = Screening.objects.select_for_update().get(pk=screening.pk)

        # aggregate all reservations for a given movie screening
        total_reserved: int = (
            Reservation.objects.filter(screening__pk=screening.pk)
            .aggregate(Sum("quantity"))
            .get("quantity__sum", 0)
        ) or 0

        # make sure there are enough free seats
        if total_reserved + quantity > screening.capacity:
            raise ValidationError("The number of seats requested exceeds the available capacity.")

        return super().create(screening=screening, quantity=quantity, **kwargs)
