from django.contrib import admin
from serviceApp.models import Booking, Service, Staff

class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "price", "duration"]

class BookingAdmin(admin.ModelAdmin):
    list_display = ["service", "staff", "customer_name", "booking_date", "payment_method"]

    def customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}" if obj.customer else 'ลูกค้าขาจร'

    def payment_method(self, obj):
        return obj.payment.payment_method if obj.payment else 'No payment'

    payment_method.short_description = 'Payment Method'  

class StaffAdmin(admin.ModelAdmin):
    list_display = ["staff_id", "name", "speciality", "role", "commission_rate", "phone", "birthdate", "status"]

admin.site.register(Booking, BookingAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Staff, StaffAdmin)
