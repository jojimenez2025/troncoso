# inicio/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),  # <- ESTE nombre usamos en {% url 'inicio' %}
]
