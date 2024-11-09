import logging
import string
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator
from django.db import models, transaction
from django.utils.text import slugify

import qrcode
from django_lifecycle import AFTER_CREATE, AFTER_UPDATE, LifecycleModel, hook
from hashids import Hashids

from .managers import ReservationManager
from .utils import tz_date_formatted

logger = logging.getLogger(__name__)

hashids = Hashids(min_length=16, alphabet=string.ascii_uppercase + string.digits)


class Cinema(models.Model):
    class Meta:
        ordering = ["name"]

    name = models.CharField(max_length=128)
    slug = models.CharField(max_length=128, unique=True, db_index=True)
    address = models.TextField(blank=True)
    lat = models.FloatField(blank=True, null=True)
    lng = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Film(models.Model):
    class Meta:
        ordering = ["id"]

    name = models.CharField(max_length=128)
    slug = models.CharField(max_length=128, unique=True, db_index=True)
    release_date = models.CharField(max_length=16)
    genre = models.CharField(max_length=32)
    showing_from = models.CharField(max_length=32)
    certificate = models.CharField(max_length=16)
    description = models.TextField()
    running_time = models.CharField(max_length=16)
    image_1 = models.ImageField(upload_to="film_images")
    image_2 = models.ImageField(upload_to="film_images")
    copyright = models.TextField(blank=True)
    live = models.BooleanField(default=False)
    sold_out = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Screening(models.Model):
    class Meta:
        ordering = ["cinema__name", "starts_at"]

    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    slug = models.CharField(max_length=128, unique=True, db_index=True)
    starts_at = models.DateTimeField()
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE)
    capacity = models.IntegerField()

    def __str__(self):
        return f"{ self.film } | { self.cinema } | { tz_date_formatted(self.starts_at) }"

    def save(self, *args, **kwargs):
        self.slug = (
            f"{self.film.slug}-{self.cinema.slug}-{self.starts_at.strftime('%Y-%m-%d-%H-%M')}"
        )
        super().save(*args, **kwargs)


class AccessCode(models.Model):
    class Meta:
        ordering = ["id"]

    value = models.CharField(max_length=36, db_index=True, unique=True)
    max_usages = models.IntegerField(default=1)
    valid_for = models.ForeignKey(Film, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.value


class Reservation(LifecycleModel):
    class Meta:
        ordering = ["-created_at"]

    objects = ReservationManager()

    created_at = models.DateTimeField(auto_now_add=True)
    reservation_id = models.CharField(max_length=16, blank=True)
    name = models.CharField(max_length=128)
    email = models.EmailField(help_text="Changes will trigger an updated confirmation email")
    access_code = models.ForeignKey(AccessCode, on_delete=models.PROTECT)
    screening = models.ForeignKey(
        Screening,
        on_delete=models.PROTECT,
        help_text="Changes will trigger an updated confirmation email",
    )
    quantity = models.IntegerField(
        validators=[MaxValueValidator(4)],
        help_text="Changes will trigger an updated confirmation email, \
or cancellation email if set to 0",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{ self.access_code } | { self.screening }"

    @hook(AFTER_CREATE)
    def after_create(self):
        self.set_reservation_id()
        self.allocate_tickets()
        self.send_confirmation_email()

    @hook(AFTER_UPDATE, when="quantity", has_changed=True)
    def after_quantity_update(self):
        self.allocate_tickets()
        if self.quantity == 0:
            self.send_cancellation_email()
        else:
            self.send_confirmation_email()

    @hook(AFTER_UPDATE, when="screening", has_changed=True)
    def after_screening_update(self):
        self.allocate_tickets()
        self.send_confirmation_email()

    def set_reservation_id(self):
        self.reservation_id = hashids.encode(self.id)
        self.save()

    def allocate_tickets(self):
        tickets = self.ticket_set.all()

        for ticket in self.ticket_set.all():
            if ticket.film != self.screening.film:
                ticket.reservation = None
                ticket.save(update_fields=["reservation"])

        tickets = self.ticket_set.all()
        ticket_count = tickets.count()
        if ticket_count > self.quantity:
            extra_tickets = tickets[self.quantity :]
            for extra_ticket in extra_tickets:
                extra_ticket.reservation = None
                extra_ticket.save(update_fields=["reservation"])

        elif ticket_count < self.quantity:
            with transaction.atomic():
                tickets = Ticket.objects.filter(
                    reservation__isnull=True, film=self.screening.film
                ).select_for_update()[: self.quantity - ticket_count]
                for ticket in tickets:
                    ticket.reservation = self
                    ticket.save(update_fields=["reservation"])
            for ticket in tickets:
                ticket.create_image()

    def get_details(self):
        quantity = self.quantity
        film = self.screening.film.name
        cinema = self.screening.cinema.name
        time = tz_date_formatted(self.screening.starts_at)
        details = f"{quantity} x {film}, Cineworld {cinema}, {time}"
        return details

    def send_confirmation_email(self):
        print("Sending confirmation email for reservation:", self.reservation_id)
        print("Tickets are:", self.ticket_set.all())

    def send_cancellation_email(self):
        print("Sending cancellation email for reservation", self.reservation_id)
        print("Tickets are:", self.ticket_set.all())


class Ticket(models.Model):
    class Meta:
        ordering = ["id"]

    code = models.CharField(max_length=24, db_index=True, unique=True)
    image = models.ImageField(upload_to="qr_code_images", blank=True)
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True)
    film = models.ForeignKey(Film, on_delete=models.CASCADE, null=True, blank=True)

    def create_image(self):
        if self.image:
            return
        image = qrcode.make(self.code)
        buffer = BytesIO()
        image.save(buffer)
        self.image.save(f"{self.code}.jpg", ContentFile(buffer.getvalue()))
        self.save()

    def __str__(self):
        return self.code
