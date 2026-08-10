from django.db import models
from django.utils.text import slugify
 
# Create your models here.

class Category(models.Model):
    category = models.CharField(max_length=30,unique=True)
    description = models.TextField(max_length=500)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=100,unique=True,blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Category"
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.category

    def save(self, *args, **kwargs):

        self.slug = slugify(self.category)

        super().save(*args, **kwargs)