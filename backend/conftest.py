from django.utils import timezone

import pytest
from hashids import Hashids

from core.models import AccessCode, Cinema, Film, Reservation, Screening

hashids = Hashids(min_length=8)


@pytest.fixture
def create_access_code():
    def func(value=None, max_usages=None, valid_for=None):
        if max_usages is None:
            max_usages = 1
        if value is None:
            previous_access_code = AccessCode.objects.all().order_by("pk").last()
            if previous_access_code is None:
                next_pk = 0
            else:
                next_pk = previous_access_code.pk + 1
            value = hashids.encode(next_pk)
        return AccessCode.objects.create(value=value, max_usages=max_usages, valid_for=valid_for)

    return func


@pytest.fixture
def access_code(create_access_code):
    return create_access_code()


@pytest.fixture
def create_reservation(create_access_code):
    def func(
        screening,
        name="Name",
        email="email@example.com",
        quantity=1,
        access_code=None,
    ):
        if access_code is None:
            access_code = create_access_code()
        return Reservation.objects.create(
            screening=screening, name=name, email=email, access_code=access_code, quantity=quantity
        )

    return func


@pytest.fixture
def create_film():
    def func(name="Film", live=False):
        return Film.objects.create(name=name, live=live)

    return func


@pytest.fixture
def create_cinema():
    def func(name="Cinema"):
        return Cinema.objects.create(name=name)

    return func


@pytest.fixture
def create_screening(create_film, create_cinema):
    def func(capacity=100, film=None, cinema=None):
        if film is None:
            film = create_film()
        if cinema is None:
            cinema = create_cinema()
        return Screening.objects.create(
            film=film, starts_at=timezone.now(), cinema=cinema, capacity=capacity
        )

    return func
