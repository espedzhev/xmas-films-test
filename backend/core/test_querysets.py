import pytest

from core.models import Screening


@pytest.mark.django_db
def test_screening_with_sold_out(
    create_film,
    create_cinema,
    create_screening,
    create_reservation,
):
    cinema = create_cinema(name="Cinema A")
    film = create_film(name="Film A")
    screening = create_screening(film=film, cinema=cinema, capacity=5)
    create_reservation(screening=screening, quantity=5)

    screenings = Screening.objects.with_sold_out().values_list("sold_out", flat=True)
    assert list(screenings) == [True]


@pytest.mark.django_db
def test_screening_not_sold_out(
    create_film,
    create_cinema,
    create_screening,
    create_reservation,
):
    cinema = create_cinema(name="Cinema A")
    film = create_film(name="Film B")
    screening = create_screening(film=film, cinema=cinema, capacity=10)
    create_reservation(screening=screening, quantity=5)

    screenings = Screening.objects.with_sold_out().values_list("sold_out", flat=True)
    assert list(screenings) == [False]


@pytest.mark.django_db
def test_screening_sold_out_no_reservations(create_film, create_cinema, create_screening):
    cinema = create_cinema(name="Cinema B")
    film = create_film(name="Film B")
    create_screening(film=film, cinema=cinema, capacity=10)

    screenings = Screening.objects.with_sold_out().values_list("sold_out", flat=True)
    assert list(screenings) == [False]
