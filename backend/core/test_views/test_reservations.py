import pytest

from core.models import Reservation


@pytest.mark.django_db
def test_successful_reservation(client, create_screening, create_access_code):
    screening = create_screening()
    create_access_code(value="ABC123")
    response = client.post(
        "/api/reservations/",
        {
            "screening": screening.slug,
            "name": "Name",
            "email": "email@example.com",
            "quantity": 1,
            "access_code": "ABC123",
        },
    )
    assert response.status_code == 201
    reservation = Reservation.objects.first()
    assert reservation.screening == screening
    assert reservation.name == "Name"
    assert reservation.email == "email@example.com"
    assert reservation.quantity == 1
    assert reservation.access_code.value == "ABC123"


@pytest.mark.django_db
def test_unsuccessful_reservation_quantity_greater_than_max(
    client, create_screening, create_access_code
):
    screening = create_screening(capacity=10)
    create_access_code(value="ABC123")
    response = client.post(
        "/api/reservations/",
        {
            "screening": screening.slug,
            "name": "Name",
            "email": "email@example.com",
            "quantity": 5,
            "access_code": "ABC123",
        },
    )
    assert response.status_code == 400
    assert Reservation.objects.count() == 0
    data = response.json()
    assert data["quantity"] == ["Ensure this value is less than or equal to 4."]


@pytest.mark.django_db
def test_unsuccessful_reservation_quantity_less_than_min(
    client, create_screening, create_access_code
):
    screening = create_screening(capacity=10)
    create_access_code(value="ABC123")
    response = client.post(
        "/api/reservations/",
        {
            "screening": screening.slug,
            "name": "Name",
            "email": "email@example.com",
            "quantity": 0,
            "access_code": "ABC123",
        },
    )
    assert response.status_code == 400
    assert Reservation.objects.count() == 0
    data = response.json()
    assert data["quantity"] == ["Ensure this value is greater than or equal to 1."]


@pytest.mark.django_db
def test_unsuccessful_reservation_missing_screening(client, create_access_code):
    create_access_code(value="ABC123")
    response = client.post(
        "/api/reservations/",
        {
            "name": "Name",
            "email": "email@example.com",
            "quantity": 2,
            "access_code": "ABC123",
        },
    )
    assert response.status_code == 400
    assert Reservation.objects.count() == 0
    data = response.json()
    assert data["screening"] == ["This field is required."]


@pytest.mark.django_db
def test_unsuccessful_reservation_missing_name(client, create_access_code, create_screening):
    screening = create_screening(capacity=1)
    create_access_code(value="ABC123")
    response = client.post(
        "/api/reservations/",
        {
            "screening": screening.slug,
            "email": "email@example.com",
            "quantity": 2,
            "access_code": "ABC123",
        },
    )
    assert response.status_code == 400
    assert Reservation.objects.count() == 0
    data = response.json()
    assert data["name"] == ["This field is required."]


@pytest.mark.django_db
def test_unsuccessful_reservation_missing_email(client, create_access_code, create_screening):
    screening = create_screening(capacity=1)
    create_access_code(value="ABC123")
    response = client.post(
        "/api/reservations/",
        {
            "screening": screening.slug,
            "quantity": 1,
            "access_code": "ABC123",
        },
    )
    assert response.status_code == 400
    assert Reservation.objects.count() == 0
    data = response.json()
    assert data["email"] == ["Please add your email"]


@pytest.mark.django_db
def test_unsuccessful_reservation_missing_quantity(client, create_access_code, create_screening):
    screening = create_screening(capacity=1)
    create_access_code(value="ABC123")
    response = client.post(
        "/api/reservations/",
        {
            "screening": screening.slug,
            "email": "email@example.com",
            "access_code": "ABC123",
        },
    )
    assert response.status_code == 400
    assert Reservation.objects.count() == 0
    data = response.json()
    assert data["quantity"] == ["This field is required."]


@pytest.mark.django_db
def test_unsuccessful_reservation_missing_access_code(client, create_screening):
    screening = create_screening(capacity=1)
    response = client.post(
        "/api/reservations/",
        {
            "name": "Name",
            "screening": screening.slug,
            "email": "email@example.com",
            "quantity": 1,
        },
    )
    assert response.status_code == 400
    assert Reservation.objects.count() == 0
    data = response.json()
    assert data["access_code"] == ["This field is required."]


@pytest.mark.django_db
def test_screenings_with_no_capacity(client, create_screening, create_reservation):
    screening = create_screening(capacity=1)
    create_reservation(screening)
    response = client.get("/api/screenings/")
    assert response.status_code == 200
    assert response.json() == []
