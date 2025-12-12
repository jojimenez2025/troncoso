# usuarios/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied
from functools import wraps
import random  # <- lo usamos para desordenar los objetos

from .forms import RegistroDocenteForm, RegistroNinoForm
from .models import Usuario, Progreso
from actividades.models import Actividad


def role_required(role_name):
    """
    Decorador para restringir vistas por rol.
    Uso: @role_required('nino') o @role_required('docente')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if getattr(request.user, "rol", None) != role_name:
                raise PermissionDenied("No tienes permiso para acceder a esta página.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# ============================================================
# 1. FUNCIONES AUXILIARES PARA ROLES
# ============================================================

def es_administrador(user):
    return user.is_authenticated and user.rol == 'administrador'


def es_docente(user):
    return user.is_authenticated and user.rol == 'docente'


def es_nino(user):
    return user.is_authenticated and user.rol == 'nino'


# ============================================================
# 2. CONFIGURACIÓN DE NIVELES PARA "OBJETOS IGUALES"
# ============================================================

NIVELES_OBJETOS_IGUALES = {
    1: [
        {"id": "bota", "emoji": "👢"},
        {"id": "llave", "emoji": "🔑"},
        {"id": "pera", "emoji": "🍐"},
    ],
    2: [
        {"id": "coche", "emoji": "🚗"},
        {"id": "pelota", "emoji": "⚽"},
        {"id": "reloj", "emoji": "⏰"},
    ],
    3: [
        {"id": "manzana", "emoji": "🍎"},
        {"id": "libro", "emoji": "📚"},
        {"id": "tren", "emoji": "🚂"},
    ],
    # Más adelante puedes añadir niveles 4, 5, 6...
}


# ============================================================
# 3. AUTENTICACIÓN (LOGIN / LOGOUT)
# ============================================================

def login_usuario(request):
    """
    Vista de inicio de sesión común para admin, docentes y niños.
    Redirige al dashboard según el rol.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.rol == 'administrador':
                return redirect('admin_dashboard')
            elif user.rol == 'docente':
                return redirect('docente_dashboard')
            else:  # 'nino'
                return redirect('nino_dashboard')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, 'usuarios/login.html')


@login_required
def logout_view(request):
    """
    Cerrar sesión y regresar a la página principal.
    """
    logout(request)
    return redirect('inicio')


# ============================================================
# 4. PANTALLA SELECTOR DE REGISTRO
# ============================================================

def selector_registro(request):
    """
    Pantalla donde el usuario elige si quiere registrarse como docente o como niño.
    """
    return render(request, "usuarios/selector_registro.html")


# ============================================================
# 5. REGISTRO DE DOCENTES Y NIÑOS
# ============================================================

def registro_docente(request):
    """
    Registro abierto de docentes.
    Asigna automáticamente rol = 'docente'.
    Además valida que el nombre de usuario no esté repetido.
    """
    if request.method == "POST":
        form = RegistroDocenteForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            if Usuario.objects.filter(username=username).exists():
                form.add_error(
                    "username",
                    "Este nombre de usuario ya está en uso. Por favor, elige otro."
                )
            else:
                try:
                    user = form.save()  # el form ya pone rol='docente'
                except IntegrityError:
                    form.add_error(
                        "username",
                        "Ocurrió un problema guardando el usuario. Intenta con otro nombre."
                    )
                else:
                    messages.success(request, "Docente registrado correctamente.")
                    login(request, user)
                    return redirect('docente_dashboard')
    else:
        form = RegistroDocenteForm()

    return render(request, "usuarios/registro_docente.html", {"form": form})


def registro_nino(request):
    """
    Registro de niños.
    Pide el usuario del docente para vincularlo automáticamente.
    """
    if request.method == "POST":
        form = RegistroNinoForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Niño registrado correctamente.")
            login(request, user)
            return redirect('nino_dashboard')
    else:
        form = RegistroNinoForm()

    return render(request, "usuarios/registro_nino.html", {"form": form})


# ============================================================
# 6. DASHBOARDS POR ROL
# ============================================================

@login_required
@user_passes_test(es_administrador)
def admin_dashboard(request):
    return render(request, 'usuarios/admin_dashboard.html')


@login_required
@user_passes_test(es_docente)
def docente_dashboard(request):
    """
    Dashboard del docente: puede ver a sus niños asignados.
    """
    ninos = Usuario.objects.filter(docente=request.user, rol='nino')
    contexto = {
        'ninos': ninos,
    }
    return render(request, 'usuarios/docente_dashboard.html', contexto)


@login_required
@user_passes_test(es_nino)
def nino_dashboard(request):
    return render(request, 'usuarios/nino_dashboard.html')


# ============================================================
# 7. ADMINISTRACIÓN DE USUARIOS (SOLO ADMIN)
# ============================================================

@login_required
@user_passes_test(es_administrador)
def lista_usuarios(request):
    """
    Muestra una lista de todos los usuarios registrados.
    """
    usuarios = Usuario.objects.all().order_by('rol', 'username')
    return render(request, 'usuarios/lista_usuarios.html', {'usuarios': usuarios})


@login_required
@user_passes_test(es_administrador)
def crear_usuario(request):
    """
    Crea un usuario desde el panel de administrador.
    Por ahora utiliza el mismo formulario de docentes y los crea como 'docente'.
    """
    if request.method == 'POST':
        form = RegistroDocenteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect('lista_usuarios')
    else:
        form = RegistroDocenteForm()

    return render(request, 'usuarios/crear_usuario.html', {'form': form})


# ============================================================
# 8. GESTIÓN DE PROGRESO (SOLO DOCENTE)
# ============================================================

@login_required
@user_passes_test(es_docente)
def ver_progreso_ninos(request):
    """
    Muestra el progreso de todos los niños asignados al docente actual.
    """
    ninos = Usuario.objects.filter(docente=request.user, rol='nino')
    progreso = (
        Progreso.objects
        .filter(nino__in=ninos)
        .select_related('nino', 'actividad')
        .order_by('nino__username', '-fecha_completado')
    )

    return render(request, 'usuarios/ver_progreso_ninos.html', {
        'progreso': progreso
    })


# ============================================================
# 9. ACTIVIDADES (SOLO NIÑO)
# ============================================================

@login_required
@user_passes_test(es_nino)
def menu_actividades(request):
    return render(request, 'usuarios/menu_actividades.html')


@login_required
@user_passes_test(es_nino)
def actividad_imagen_palabra(request):
    """
    Actividad: relacionar imagen de un PERRO con la palabra escrita 'perro'.
    Si acierta, se registra progreso.
    """
    resultado = None

    if request.method == 'POST':
        respuesta = request.POST.get('respuesta', '').strip().lower()
        if respuesta == 'perro':
            resultado = "✅ ¡Muy bien! Has acertado."
            actividad, _ = Actividad.objects.get_or_create(
                nombre='Imagen y palabra: PERRO',
                defaults={
                    'descripcion': 'Relacionar la imagen de un perro con la palabra escrita.',
                }
            )
            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )
        else:
            resultado = "❌ Intenta de nuevo."

    return render(request, 'usuarios/actividad_imagen_palabra.html', {'resultado': resultado})


@login_required
@user_passes_test(es_nino)
def actividad_vocal_faltante(request):
    """
    Actividad: seleccionar la vocal que falta en la palabra 'MANO' (M _ N O).
    """
    resultado = None
    palabra = "M _ N O"

    if request.method == "POST":
        respuesta = request.POST.get("respuesta", "").strip().lower()
        correcta = "a"

        if respuesta == correcta:
            resultado = "✅ ¡Correcto! La palabra es MANO."
            actividad, _ = Actividad.objects.get_or_create(
                nombre="Vocal faltante: MANO",
                defaults={
                    "descripcion": "Seleccionar la vocal que falta en la palabra MANO."
                },
            )
            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )
        else:
            resultado = "❌ Intenta de nuevo."

    contexto = {
        "palabra": palabra,
        "resultado": resultado,
    }
    return render(request, "usuarios/actividad_vocal_faltante.html", contexto)


@login_required
@user_passes_test(es_nino)
def actividad_silaba_inicial(request):
    """
    Actividad: elegir la sílaba inicial correcta de la palabra 'casa' (respuesta: 'ca').
    """
    resultado = None

    if request.method == 'POST':
        respuesta = request.POST.get('respuesta', '').strip().lower()
        if respuesta == 'ca':
            resultado = "✅ ¡Muy bien! La sílaba inicial de CASA es 'ca'."
            actividad, _ = Actividad.objects.get_or_create(
                nombre='Sílaba inicial: CASA',
                defaults={
                    'descripcion': 'Identificar la sílaba inicial de la palabra CASA.',
                }
            )
            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )
        else:
            resultado = "❌ Intenta de nuevo. Pista: piensa en cómo empieza la palabra."

    return render(request, 'usuarios/actividad_silaba_inicial.html', {'resultado': resultado})


@login_required
@user_passes_test(es_nino)
def actividad_objetos_iguales(request, nivel=1):
    """
    Actividad de 'Objetos iguales' con varios niveles.
    Nivel 1: bota, llave, pera
    Nivel 2: tenis, sombrero, reloj
    Nivel 3: teléfonos
    """

    # Catálogo de objetos por nivel
    objetos_nivel = {
        1: [
            {"id": "bota",     "emoji": "👢"},
            {"id": "llave",    "emoji": "🔑"},
            {"id": "pera",     "emoji": "🍐"},
        ],
        2: [
            {"id": "tenis",    "emoji": "👟"},
            {"id": "sombrero", "emoji": "👒"},
            {"id": "reloj",    "emoji": "⏰"},
        ],
        3: [
            {"id": "tel_azul",   "emoji": "📱"},
            {"id": "tel_verde",  "emoji": "☎️"},
            {"id": "tel_morado", "emoji": "📞"},
        ],
    }

    # Si el nivel pedido no existe, cae en el 1
    if nivel not in objetos_nivel:
        nivel = 1

    objetos = objetos_nivel[nivel]
    objetos_desordenados = objetos.copy()
    random.shuffle(objetos_desordenados)

    max_nivel = max(objetos_nivel.keys())

    if request.method == "POST":
        completado = request.POST.get("completado") == "1"

        if completado:
            actividad, _ = Actividad.objects.get_or_create(
                nombre=f"Objetos iguales - Nivel {nivel}",
                defaults={
                    "descripcion": f"Emparejar objetos iguales (nivel {nivel})."
                },
            )

            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )

            # Ir automáticamente al siguiente nivel
            if nivel < max_nivel:
                messages.success(
                    request,
                    "✅ ¡Muy bien! Vamos al siguiente ejercicio."
                )
                return redirect("actividad_objetos_iguales", nivel=nivel + 1)
            else:
                messages.success(
                    request,
                    "✅ Has terminado todos los ejercicios de objetos iguales."
                )
                return redirect("menu_actividades")

    contexto = {
        "nivel": nivel,
        "objetos": objetos,
        "objetos_desordenados": objetos_desordenados,
    }
    return render(request, "usuarios/actividad_objetos_iguales.html", contexto)



