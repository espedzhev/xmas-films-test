"""
Add a ReservationManager with a custom create method.
- This should use the provided screening and quantity kwargs to sense-check the values are acceptable, given the current state of the data in the Reservation table.
- If there is an issue, a ValidationError should be rasied.
- The method should make use of transaction.atomic and select_for_update to guard against race conditions
- Tests should be added to cover this ne
"""
from django.db import models, transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError


class ReservationManager(models.Manager):
    @transaction.atomic
    def create(self, screening, quantity, **kwargs):
        from .models import Screening, Reservation

        screening: Screening = Screening.objects.select_for_update().get(pk=screening.pk)

        # aggregate all reservations for a given movie screening
        screening_reservations_sum: int = (
            Reservation.objects.filter(screening=screening)
            .aggregate(Sum("quantity"))
            .get("quantity__sum", 0)
        ) or 0

        # make sure there are enough free seats
        if screening_reservations_sum + quantity > screening.capacity:
            raise ValidationError("The number of seats requested exceeds the available capacity.")

        return super().create(screening=screening, quantity=quantity, **kwargs)
