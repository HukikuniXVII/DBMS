from django.contrib import admin
from django.urls import path,include
from serviceApp import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('ad/',views.a_dashboard),

    path('save-booking/', views.save_booking),
    path('booking1/', views.booking_view, name='booking'),
    path('payment-methods/', views.payment_methods, name='payment_methods'),
    path('user-data/', views.user_data, name='user_data'),
    path('booking-history/', views.booking_history, name='booking_history'),
    path('account/', views.account_view, name='account'),
    path('update-booking/<int:booking_id>/<str:status>/', views.update_booking_status, name='update_booking_status'),
    path('get-service-duration/<int:service_id>/', views.get_service_duration, name='get_service_duration'),
    

    path('edit-service/<int:service_id>/', views.edit_service, name='edit_service'),
    path('delete-service/<int:service_id>/', views.delete_service, name='delete_service'), 

    path('admin-services/', views.manage_services, name='admin-services'),
    path('edit-service/', views.edit_service, name='edit_service'),

    path('edit-profile/<int:user_id>/', views.edit_profile, name='edit_profile'),

    path('admin-users/', views.admin_users_view, name='admin_users'),

    # REVIEW home
    path('review/',views.review),
    path('submit_review/', views.submit_review, name='submit_review'),
    path("get_review_stats/", views.get_review_stats, name="get_review_stats"),
    path("get_reviews/", views.get_reviews, name="get_reviews"),

    # SERVICE home
    path('service/', views.service_list, name='services_list'),

    # REVIEW admin
    path('admin-reviews/', views.manage_reviews, name='admin_reviews'),

    # BOOKING admin
    path('admin-bookings/add/', views.add_booking, name='add_booking'),
    path('admin-bookings/', views.booking_list, name='admin-bookings'),
    

    # PAYMENT admin
    path('admin-payments/',views.admin_payments, name='admin-payments'),

    # SERVICE admin
    path('add-service/', views.add_service, name='add_service'),
    path('admin-services/', views.manage_services, name='manage_services'),

    # EMPLOYEES admin
    path('admin-employees-add-staff/', views.add_staff,name='add_staff'),
    path('admin-employees/',views.manage_staffs,  name='manage_staff'),
    path('staff/edit/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    path('staff/delete/<int:staff_id>/', views.delete_staff, name='delete_staff'),

    # USER admin
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),

    # TIMESLOT admin
    path('admin-timeslot/', views.admin_timeslot, name='admin_timeslot'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)