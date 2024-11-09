import pytest


@pytest.mark.django_db
def test_screenings_sold_out_status_true(
    client,
    create_film,
    create_cinema,
    create_screening,
    create_reservation,
):
    cinema = create_cinema(name="Cinema A")
    film = create_film(name="Film A", live=True)
    screening = create_screening(film=film, cinema=cinema, capacity=5)
    create_reservation(screening=screening, quantity=5)

    response = client.get("/api/screenings/")
    assert response.status_code == 200

    data = response.json()
    assert [x["sold_out"] for x in data] == [True]


@pytest.mark.django_db
def test_screening_sold_out_status_false(
    client,
    create_film,
    create_cinema,
    create_screening,
    create_reservation,
):
    cinema = create_cinema(name="Cinema A")
    film = create_film(name="Film A", live=True)
    screening = create_screening(film=film, cinema=cinema, capacity=10)
    create_reservation(screening=screening, quantity=4)

    response = client.get("/api/screenings/")
    assert response.status_code == 200

    data = response.json()
    assert [x["sold_out"] for x in data] == [False]
