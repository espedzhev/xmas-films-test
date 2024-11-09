import pytest

from core.models import Screening
from core.serializers import ScreeningSerializer


@pytest.mark.django_db
def test_screening_serializer_with_sold_out(
    create_film,
    create_cinema,
    create_screening,
    create_reservation,
):
    cinema = create_cinema(name="Cinema A")
    film = create_film(name="Film A")
    screening = create_screening(film=film, cinema=cinema, capacity=5)
    create_reservation(screening=screening, quantity=5)

    screening_with_sold_out = Screening.objects.with_sold_out().get()
    serializer = ScreeningSerializer(screening_with_sold_out)
    data = serializer.data

    assert data["sold_out"] is True


@pytest.mark.django_db
def test_screening_serializer_with_sold_out(
    create_film,
    create_cinema,
    create_screening,
):
    cinema = create_cinema(name="Cinema A")
    film = create_film(name="Film A")
    create_screening(film=film, cinema=cinema, capacity=5)

    screening_with_sold_out = Screening.objects.with_sold_out().get()
    serializer = ScreeningSerializer(screening_with_sold_out)
    data = serializer.data

    assert data["sold_out"] is False
