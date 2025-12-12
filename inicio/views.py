# inicio/views.py
from django.shortcuts import render

def inicio(request):
    # Renderiza la página principal de tu app
    return render(request, 'inicio/inicio.html')

