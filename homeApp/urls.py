from django.contrib import admin
from django.urls import path,include
from homeApp import views

urlpatterns = [
    #path('',views.index),
    path('', views.main_service_list, name='main_service_list'),

    path("get_reviews/", views.get_reviews, name="get_reviews"),
]
