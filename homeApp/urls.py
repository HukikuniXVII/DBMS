from django.contrib import admin
from django.urls import path,include
from homeApp import views

urlpatterns = [
    #path('',views.index),
    path('', views.index, name='index'),
    path("get_reviews/", views.get_reviews, name="get_reviews"),

]
