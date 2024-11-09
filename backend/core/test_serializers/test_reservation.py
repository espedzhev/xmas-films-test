import pytest

from core.serializers import Reservation, ReservationSerializer


@pytest.mark.django_db
def test_reservation_serializer_access_code_validation_successful(
    create_screening, create_access_code
):
    screening = create_screening()
    access_code = create_access_code(value="ABC123")

    reservation_serializer = ReservationSerializer(
        data={
            "name": "Name",
            "email": "email@test.com",
            "quantity": 1,
            "screening": screening.slug,
            "access_code": access_code,
        }
    )
    assert reservation_serializer.is_valid()
    reservation_serializer.save()
    assert Reservation.objects.count() == 1


@pytest.mark.django_db
def test_reservation_serializer_access_code_already_used(
    create_screening, create_access_code, create_film, create_cinema
):
    cinema_1 = create_cinema("Cinema 1")
    film_1 = create_film("Film 1")
    screening_1 = create_screening(film=film_1, cinema=cinema_1)
    access_code = create_access_code(value="ABC123")

    reservation_serializer_1 = ReservationSerializer(
        data={
            "name": "Name",
            "email": "email@test.com",
            "quantity": 1,
            "screening": screening_1.slug,
            "access_code": access_code,
        }
    )
    assert reservation_serializer_1.is_valid()
    reservation_serializer_1.save()
    assert Reservation.objects.count() == 1

    cinema_2 = create_cinema("Cinema 2")
    film_2 = create_film("Film 2")
    screening_2 = create_screening(film=film_2, cinema=cinema_2)

    reservation_serializer_2 = ReservationSerializer(
        data={
            "name": "Name",
            "email": "email2@test.com",
            "quantity": 1,
            "screening": screening_2.slug,
            "access_code": access_code,
        }
    )
    assert reservation_serializer_2.is_valid() is not True
    assert (
        reservation_serializer_2.errors["access_code"][0]
        == "Sorry, this code has already been used-up"
    )
    assert Reservation.objects.count() == 1


@pytest.mark.django_db
def test_reservation_serializer_email_already_used(
    create_screening, create_access_code, create_film, create_cinema
):
    cinema_1 = create_cinema("Cinema 1")
    film_1 = create_film("Film 1")
    screening_1 = create_screening(film=film_1, cinema=cinema_1)
    access_code = create_access_code(value="ABC123", max_usages=1000)

    reservation_serializer_1 = ReservationSerializer(
        data={
            "name": "Name",
            "email": "email@test.com",
            "quantity": 1,
            "screening": screening_1.slug,
            "access_code": access_code,
        }
    )
    assert reservation_serializer_1.is_valid()
    reservation_serializer_1.save()
    assert Reservation.objects.count() == 1

    cinema_2 = create_cinema("Cinema 2")
    film_2 = create_film("Film 2")
    screening_2 = create_screening(film=film_2, cinema=cinema_2)

    reservation_serializer_2 = ReservationSerializer(
        data={
            "name": "Name",
            "email": "email@test.com",
            "quantity": 1,
            "screening": screening_2.slug,
            "access_code": access_code,
        }
    )
    assert reservation_serializer_2.is_valid() is not True
    assert (
        reservation_serializer_2.errors["email"][0]
        == "Sorry, only one screening per person is allowed"
    )
    assert Reservation.objects.count() == 1


@pytest.mark.django_db
def test_reservation_serializer_access_code_valid_for_success(
    create_screening, create_access_code, create_film, create_cinema
):
    cinema = create_cinema("Cinema 1")
    film = create_film("Film 1")
    screening = create_screening(film=film, cinema=cinema)
    access_code = create_access_code(value="ABC123", max_usages=1000, valid_for=film)

    reservation_serializer = ReservationSerializer(
        data={
            "name": "Name",
            "email": "email@test.com",
            "quantity": 1,
            "screening": screening.slug,
            "access_code": access_code,
        }
    )
    assert reservation_serializer.is_valid() is True
    reservation_serializer.save()
    assert Reservation.objects.count() == 1


@pytest.mark.django_db
def test_reservation_serializer_access_code_valid_for_failure(
    create_screening, create_access_code, create_film, create_cinema
):
    cinema = create_cinema("Cinema 1")
    film_1 = create_film("Film 1")
    film_2 = create_film("Film 2")
    screening = create_screening(film=film_1, cinema=cinema)
    access_code = create_access_code(value="ABC123", max_usages=1000, valid_for=film_2)

    reservation_serializer = ReservationSerializer(
        data={
            "name": "Name",
            "email": "email@test.com",
            "quantity": 1,
            "screening": screening.slug,
            "access_code": access_code,
        }
    )
    assert reservation_serializer.is_valid() is not True
    assert (
        reservation_serializer.errors["access_code"][0]
        == "Sorry, this code is not valid for this film"
    )
