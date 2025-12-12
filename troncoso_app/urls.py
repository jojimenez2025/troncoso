# troncoso_app/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Página principal
    path('', include('inicio.urls')),          # http://127.0.0.1:8000/  -> vista inicio

    # Rutas de usuarios (login, dashboards, etc.)
    path('usuarios/', include('usuarios.urls')),
]


