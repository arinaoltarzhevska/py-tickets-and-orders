from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint


class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    actors = models.ManyToManyField(to=Actor)
    genres = models.ManyToManyField(to=Genre)

    class Meta:
        indexes = [
            models.Index(fields=["title"])
        ]

    def __str__(self) -> str:
        return self.title


class CinemaHall(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self) -> str:
        return self.name


class MovieSession(models.Model):
    show_time = models.DateTimeField()
    cinema_hall = models.ForeignKey(to=CinemaHall,
                                    on_delete=models.CASCADE,
                                    related_name="movie_sessions")
    movie = models.ForeignKey(to=Movie,
                              on_delete=models.CASCADE,
                              related_name="movie_sessions")

    def __str__(self) -> str:
        return f"{self.movie.title} " \
               f"{str(self.show_time.strftime('%Y-%m-%d %H:%M:%S'))}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders")

    def __str__(self) -> str:
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S")

    class Meta:
        ordering = ["-created_at"]


class User(AbstractUser):
    pass


class Ticket(models.Model):
    movie_session = models.ForeignKey(
        to=MovieSession,
        on_delete=models.CASCADE,
        related_name="tickets")
    order = models.ForeignKey(
        to=Order,
        on_delete=models.CASCADE,
        related_name="tickets")
    row = models.IntegerField()
    seat = models.IntegerField()

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["movie_session", "row", "seat"],
                name="unique_ticket"
            )
        ]

    def __str__(self) -> str:
        return f"{self.movie_session} (row: {self.row}, seat: {self.seat})"

    def clean(self) -> None:
        max_row = self.movie_session.cinema_hall.rows
        max_seats_in_row = self.movie_session.cinema_hall.seats_in_row
        if self.row > max_row:
            raise ValidationError({
                "row": f"row number must be in available range: "
                       f"(1, rows): (1, {self.movie_session.cinema_hall.rows})"
            })
        if self.seat > max_seats_in_row:
            raise ValidationError({
                "seat": f"seat number must be in available range: "
                        f"(1, seats_in_row): "
                        f"(1, {self.movie_session.cinema_hall.seats_in_row})"
            })

    def save(self, *args, **kwargs) -> callable:
        self.full_clean()
        return super(Ticket, self).save(*args, **kwargs)
