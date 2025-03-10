from django.contrib import admin
from django.urls import path
from loginApp import views 

urlpatterns = [
    path('login/',views.login_view, name = 'login'),
    path('register/',views.register_view),
    path('logout/',views.logout),

]
