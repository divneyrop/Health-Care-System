from django.urls import path

from . import views

app_name = 'hospital_staff'

urlpatterns = [
    path('staff/dashboard/', views.dashboard, name='dashboard'),
]
