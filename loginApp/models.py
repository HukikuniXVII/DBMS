from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# Create your models here.
class Customer(AbstractUser):
    email = models.EmailField(unique=True) 
    phone = models.CharField(max_length=15, unique=True, null=False, blank=False)  
    address = models.TextField(null=False, blank=False)  
    birth_date = models.DateField(null=False, blank=False)  
    last_login = models.DateTimeField(default=timezone.now)

    # ตั้งค่า USERNAME_FIELD เป็น email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'phone', 'address', 'birth_date']

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return self.email