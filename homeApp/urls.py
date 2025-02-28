from django.contrib import admin
from django.urls import path,include
from homeApp import views

urlpatterns = [
    path('',views.index)
]
