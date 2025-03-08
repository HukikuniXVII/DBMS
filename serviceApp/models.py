from django.db import models
from django.contrib.auth.models import User 
from django.utils import timezone
from loginApp.models import Customer
import datetime
from django.conf import settings

class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    speciality = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    phone = models.CharField(max_length=15)
    birthdate = models.DateField(null=True, blank=True, default="1970-01-01")
    status = models.CharField(max_length=50, default="Available")

    def __str__(self):
        return self.name

class Service(models.Model):
    service_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(null=True, blank=True, default=None) 
    
    def __str__(self):
        return self.name

class TemporaryCustomer(models.Model):
    temp_customer_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

class TimeSlot(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('pending', 'Pending'),
        ('canceled', 'Canceled'),
    ]
    slot_id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL)
    slot_date = models.DateField(null=True, blank=True, default=datetime.date.today)
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')

class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comments = models.TextField(null=True, blank=True)
    review_date = models.DateField(default=datetime.date.today)

class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL)
    payment_date = models.DateField(null=True, blank=True, default=datetime.date(1970, 1, 1))
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # price 
    
    payment_method = models.CharField(
        max_length=10, 
        choices=[('Cash', 'Cash'), ('Transfer', 'Transfer')],  
        default='Transfer'
    )

    status = models.CharField(max_length=10, choices=[('Pending', 'Pending'), ('Paid', 'Paid')], default='Pending')
    note = models.TextField(null=True, blank=True)
    payment_proof = models.ImageField(upload_to='payment_proofs/', null=True, blank=True)

    def __str__(self):
        return f"Payment {self.payment_id}"


class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey('loginApp.Customer', null=True, blank=True, on_delete=models.SET_NULL)    
    temp_customer = models.ForeignKey(TemporaryCustomer, null=True, blank=True, on_delete=models.SET_NULL)
    slot = models.ForeignKey(TimeSlot, null=True, blank=True, on_delete=models.SET_NULL)
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL)
    review = models.ForeignKey(Review, null=True, blank=True, on_delete=models.SET_NULL)
    staff = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL)
    payment = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments_related_to_booking")
    booking_date = models.DateField()
    status = models.CharField(max_length=10, choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Cancelled', 'Cancelled')], default='Pending')
    walk_in = models.BooleanField(default=False)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # commissionrate * amount
    start_time = models.TimeField(null=True, blank=True)  
    end_time = models.TimeField(null=True, blank=True) 

    def __str__(self):
        return f"{self.service} with {self.staff} on {self.booking_date}"

    
from datetime import datetime

def parse_datetime(value):
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


