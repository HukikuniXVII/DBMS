from django.contrib import admin
from django.urls import path,include
from serviceApp import views
from .views import payment_methods,user_data,booking_history

urlpatterns = [
    path('service/',views.service),
    path('review/',views.review),
    path('account/',views.account),
    path('admin-services/',views.a_service),
    path('admin-bookings/',views.admin_bookings, name='admin-bookings'),
    path('ad/',views.a_dashboard),
    path('admin-employees/',views.a_emp),
    path('admin-payments/',views.a_playment),
    path('admin-reviews/',views.a_review),
    path('admin-users/',views.a_users),
    path('save-booking/', views.save_booking),
    path('booking1/', views.booking_view, name='booking'),
    path('api/payment-methods/', payment_methods, name='payment_methods'),
    path('api/user-data/', user_data, name='user_data'),
    path('api/booking-history/', booking_history, name='booking_history'),
]
