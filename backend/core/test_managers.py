import pytest
from django.core.exceptions import ValidationError
from core.models import Reservation


@pytest.mark.django_db
def test_reservation_manager_create_within_capacity(create_screening, create_access_code):
    screening = create_screening(capacity=10)
    access_code = create_access_code(value="ABC123")

    reservation = Reservation.objects.create(
        screening=screening,
        quantity=5,
        name="Test reservation",
        email="email@test.com",
        access_code=access_code,
    )

    assert Reservation.objects.count() == 1
    assert reservation.quantity == 5


@pytest.mark.django_db
def test_reservation_manager_create_exceeding_capacity(create_screening, create_access_code):
    screening = create_screening(capacity=10)
    access_code = create_access_code(value="ABC123")

    Reservation.objects.create(
        screening=screening,
        quantity=8,
        name="Test user1",
        email="user1@test.com",
        access_code=access_code,
    )

    with pytest.raises(ValidationError) as error:
        Reservation.objects.create(
            screening=screening,
            quantity=3,
            name="Test user2",
            email="user2@test.com",
            access_code=access_code,
        )

    error_msg = "['The number of seats requested exceeds the available capacity.']"
    assert str(error.value) == error_msg
    assert Reservation.objects.count() == 1


@pytest.mark.django_db
def test_reservation_manager_create_exact_capacity(create_screening, create_access_code):
    screening = create_screening(capacity=10)
    access_code = create_access_code(value="ABC123")

    reservation = Reservation.objects.create(
        screening=screening,
        quantity=10,
        name="Test exactuser",
        email="exactuser@test.com",
        access_code=access_code,
    )

    assert Reservation.objects.count() == 1
    assert reservation.quantity == 10


@pytest.mark.django_db
def test_reservation_manager_create_exact_capacity_multiple_reservations(
    create_screening, create_access_code
):
    screening = create_screening(capacity=10)
    access_code = create_access_code(value="ABC123")

    Reservation.objects.create(
        screening=screening,
        quantity=8,
        name="Test user1",
        email="user1@test.com",
        access_code=access_code,
    )

    Reservation.objects.create(
        screening=screening,
        quantity=2,
        name="Test user2",
        email="user2@test.com",
        access_code=access_code,
    )

    reservations = Reservation.objects.values_list("quantity", flat=True)

    assert len(reservations) == 2
    assert sum(reservations) == 10
