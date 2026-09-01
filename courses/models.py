from django.db import models
from categories.models import Category
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()

# Create your models here.

class Course(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=150,unique=True)
    slug = models.SlugField(max_length=100,unique=True,blank=True)
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="courses")
    instructor = models.ForeignKey(User,on_delete=models.PROTECT,related_name="instructor",limit_choices_to={"role": User.TEACHER},)
    thumbnail = models.ImageField(upload_to="courses",default="courses/default.png")
    short_description = models.TextField(max_length=200)
    full_description = models.TextField(max_length=500)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='draft')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        
    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):

        self.slug = slugify(self.title)
        
        super().save(*args, **kwargs)

   