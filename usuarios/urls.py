from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Registro
    path('registro/', views.selector_registro, name='selector_registro'),
    path('registro/docente/', views.registro_docente, name='registro_docente'),
    path('registro/nino/', views.registro_nino, name='registro_nino'),

    # Dashboards
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('docente_dashboard/', views.docente_dashboard, name='docente_dashboard'),
    path('nino_dashboard/', views.nino_dashboard, name='nino_dashboard'),

    # Administración de usuarios (admin)
    path('lista_usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('crear_usuario/', views.crear_usuario, name='crear_usuario'),

    # Progreso (docente)
    path('progreso/', views.ver_progreso_ninos, name='ver_progreso_ninos'),

    # Actividades (niño)
    path('menu_actividades/', views.menu_actividades, name='menu_actividades'),
    path('actividad/imagen-palabra/', views.actividad_imagen_palabra, name='actividad_imagen_palabra'),
    path('actividad/vocal-faltante/', views.actividad_vocal_faltante, name='actividad_vocal_faltante'),
    path('actividad/silaba-inicial/', views.actividad_silaba_inicial, name='actividad_silaba_inicial'),
    
    path(
    "actividad/objetos-iguales/<int:nivel>/",
    views.actividad_objetos_iguales,
    name="actividad_objetos_iguales",
),
]
