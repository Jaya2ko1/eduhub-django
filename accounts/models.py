from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True)
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

    ROLE_CHOICES = [ (ADMIN , "admin"),
                    (TEACHER , "teacher"),
                    (STUDENT , "student"),
                ]
    role = models.CharField(max_length=20,choices=ROLE_CHOICES,default=STUDENT)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # Django superusers always act as EduHub admins.
        if self.is_superuser and self.role != self.ADMIN:
            self.role = self.ADMIN
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = {*update_fields, "role"}
        super().save(*args, **kwargs)
