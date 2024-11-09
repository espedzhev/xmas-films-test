from rest_framework import serializers

from .models import AccessCode, Cinema, Film, Reservation, Screening


class CinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cinema
        fields = ["id", "name", "slug", "address", "lat", "lng"]


class FilmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Film
        fields = [
            "id",
            "name",
            "slug",
            "release_date",
            "genre",
            "certificate",
            "description",
            "running_time",
            "image_1",
            "image_2",
            "showing_from",
            "copyright",
            "sold_out",
        ]


class ScreeningSerializer(serializers.ModelSerializer):
    sold_out = serializers.SerializerMethodField()

    class Meta:
        model = Screening
        fields = [
            "id",
            "slug",
            "film_slug",
            "cinema_slug",
            "time_slug",
            "starts_at",
            "capacity",
            "sold_out",
        ]

    film_slug = serializers.SerializerMethodField()
    cinema_slug = serializers.SerializerMethodField()
    time_slug = serializers.SerializerMethodField()

    def get_film_slug(self, obj):
        return obj.film.slug

    def get_cinema_slug(self, obj):
        return obj.cinema.slug

    def get_time_slug(self, obj):
        return obj.starts_at.strftime("%Y-%m-%d-%H-%M")

    def get_sold_out(self, obj):
        return getattr(obj, "sold_out", False)


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = "__all__"
        extra_kwargs = {
            "email": {
                "error_messages": {
                    "required": "Please add your email",
                    "invalid": "Please add a valid email",
                },
            },
            "name": {
                "error_messages": {"blank": "Please add your name"},
            },
        }

    screening = serializers.SlugRelatedField(
        queryset=Screening.objects.all(),
        slug_field="slug",
        error_messages={
            "does_not_exist": "Sorry this screening is not valid",
            "null": "Please add a screening",
        },
    )

    access_code = serializers.SlugRelatedField(
        queryset=AccessCode.objects.all(),
        slug_field="value",
        error_messages={
            "does_not_exist": "Sorry this access code is not valid",
            "null": "Please add an access code",
        },
    )

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Ensure this value is greater than or equal to 1.")
        return value

    def validate_email(self, value):
        if Reservation.objects.filter(email=value).exists():
            raise serializers.ValidationError("Sorry, only one screening per person is allowed")
        return value

    def validate_access_code(self, value):
        existing_usages = value.reservation_set.count()
        if existing_usages >= value.max_usages:
            raise serializers.ValidationError("Sorry, this code has already been used-up")
        return value

    def validate(self, data):
        if data["access_code"].valid_for is not None:
            if data["screening"].film != data["access_code"].valid_for:
                raise serializers.ValidationError(
                    {"access_code": "Sorry, this code is not valid for this film"}
                )
        return data
