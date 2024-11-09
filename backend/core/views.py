from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control

from rest_framework import generics, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError

from .models import Cinema, Film, Reservation, Screening
from .serializers import (
    CinemaSerializer,
    FilmSerializer,
    ReservationSerializer,
    ScreeningSerializer,
)


@method_decorator(cache_control(max_age=60), name="dispatch")
class FilmViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Film.objects.all().filter(live=True)
    serializer_class = FilmSerializer
    lookup_field = "slug"


@method_decorator(cache_control(max_age=60), name="dispatch")
class CinemaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Cinema.objects.all()
    serializer_class = CinemaSerializer
    lookup_field = "slug"


@method_decorator(cache_control(max_age=60), name="dispatch")
class ScreeningViewSet(viewsets.ReadOnlyModelViewSet):
    # fmt: off
    queryset = (
        Screening.objects
        .select_related("film", "cinema")
        .filter(film__live=True)
        .with_sold_out()
    )
    # fmt: on
    serializer_class = ScreeningSerializer
    lookup_field = "slug"


class ReservationCreateView(generics.CreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def perform_create(self, serializer):
        try:
            serializer.save()
        except ValidationError as exc:
            raise DRFValidationError({"quantity": [exc.message]}) from exc
