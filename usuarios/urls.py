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

    # Progreso(docente)
    path('progreso/', views.ver_progreso_ninos, name='ver_progreso_ninos'),

    path(
    "actividad/unir-dibujos/<int:nivel>/",
    views.actividad_unir_dibujos,
    name="actividad_unir_dibujos"),
    
    # Actividades (niño)
    path('menu_actividades/', views.menu_actividades, name='menu_actividades'),
    path('actividad/imagen-palabra/', views.actividad_imagen_palabra, name='actividad_imagen_palabra'),
    path(
    "actividad/imagen-palabra/<int:nivel>/",
    views.actividad_imagen_palabra,
    name="actividad_imagen_palabra_nivel",),
    
    path('actividad/vocal-faltante/', views.actividad_vocal_faltante, name='actividad_vocal_faltante'),
    path('actividad/silaba-inicial/', views.actividad_silaba_inicial, name='actividad_silaba_inicial'),
    
    path(
    "actividad/objetos-iguales/<int:nivel>/",
    views.actividad_objetos_iguales,
    name="actividad_objetos_iguales",),
    
    path(
    "actividad/buscar-iguales/<int:nivel>/",
    views.actividad_buscar_iguales,
    name="actividad_buscar_iguales",),
    
    path(
    "actividad/buscar-dos-modelos/<int:nivel>/",
    views.actividad_buscar_dos_modelos,
    name="actividad_buscar_dos_modelos",),
    
    path(
    "actividad/buscar-por-filas/<int:nivel>/",
    views.actividad_buscar_por_filas,
    name="actividad_buscar_por_filas",),
    
    path(
    "actividad/foto-palabra/<int:nivel>/",
    views.actividad_foto_palabra,
    name="actividad_foto_palabra",),
    
    path(
    "actividad/recompensa-estrellas/",
    views.actividad_recompensa_estrellas,
    name="actividad_recompensa_estrellas",),
    
    path(
    "actividad/memoria-figuras/",
    views.actividad_memoria_figuras,
    name="actividad_memoria_figuras",),
    
    path(
    "actividad/colorear-dibujo/",
    views.actividad_colorear_dibujo,
    name="actividad_colorear_dibujo",),
    
]
