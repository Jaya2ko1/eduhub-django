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
