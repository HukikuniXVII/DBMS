from django.contrib import admin
from .models import Customer

class login_admin(admin.ModelAdmin):
    list_display = ["email","phone","password","address","birth_date", "last_login"]


admin.site.register(Customer, login_admin)