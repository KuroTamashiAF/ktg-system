from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.




class Section(models.Model):
    """Участок"""

    name = models.CharField(max_length=50, verbose_name="Название участка")

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Участок"
        verbose_name_plural = "Участки"


class User(AbstractUser):
    patronim = models.CharField(
        max_length=99, blank=True, verbose_name="Отчество"
    )  # Отчество
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Участок",
    )
    ROLE_CHOICES = (
        ("admin", "Администратор"),
        ("mechanic", "Механник"),
        ("dispatcher", "Диспетчер"),
        ("viewer", "Просмотр"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="viewer")

    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.patronim]
        return " ".join(p for p in parts if p).strip() or self.username

    def __str__(self):
        return f"{self.username} {self.get_full_name()} {self.role}"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
