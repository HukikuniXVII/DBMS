from django.contrib import admin
from django.urls import path,include
from serviceApp import views

urlpatterns = [
    path('service/',views.service),
    path('review/',views.review),
    path('admin-bookings/',views.admin_bookings, name='admin-bookings'),
    path('ad/',views.a_dashboard),
    path('admin-payments/',views.a_playment),
    path('admin-reviews/',views.a_review),
    path('save-booking/', views.save_booking),
    path('booking1/', views.booking_view, name='booking'),
    path('payment-methods/', views.payment_methods, name='payment_methods'),
    path('user-data/', views.user_data, name='user_data'),
    path('booking-history/', views.booking_history, name='booking_history'),
    path('account/', views.account_view, name='account'),
    path('admin-users/', views.admin_users_view, name='admin_users'),
    path('update-booking/<int:booking_id>/<str:status>/', views.update_booking_status, name='update_booking_status'),

    path('admin-employees/',views.manage_staffs,   name='manage_staffs'),
    path('admin-services/', views.manage_services),

    path('staff/edit/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    path('staff/delete/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('admin-employees/', views.add_staff, name='add_staff'),

    #path('admin-services/', views.manage_services, name='manage_services'),
    path('add-service/', views.add_service, name='add_service'),

    path('admin-services/', views.manage_services, name='manage_services'),
    path('add-service/', views.add_service, name='add_service'),
    path('edit-service/<int:service_id>/', views.edit_service, name='edit_service'),
    path('delete-service/<int:service_id>/', views.delete_service, name='delete_service'), 

    path('admin-services/', views.manage_services, name='admin-services'),
    path('edit-service/', views.edit_service, name='edit_service'),
]
