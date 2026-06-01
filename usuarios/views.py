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
def actividad_imagen_palabra(request, nivel=1):
    """
    Bloque 3: Imagen y palabra.
    El niño observa una imagen de animal y selecciona la palabra correcta.
    """

    ejercicios = {
        1: {
            "titulo": "Imagen y palabra",
            "nombre_actividad": "Imagen y palabra - Perro",
            "descripcion": "Relacionar la imagen de un perro con la palabra PERRO.",
            "instruccion": "Mira la imagen. Toca la palabra correcta.",
            "imagen": "🐶",
            "respuesta": "perro",
            "palabras": [
                {"id": "perro", "texto": "PERRO"},
                {"id": "gato", "texto": "GATO"},
                {"id": "pato", "texto": "PATO"},
                {"id": "caballo", "texto": "CABALLO"},
            ],
        },

        2: {
            "titulo": "Imagen y palabra",
            "nombre_actividad": "Imagen y palabra - Gato",
            "descripcion": "Relacionar la imagen de un gato con la palabra GATO.",
            "instruccion": "Mira la imagen. Toca la palabra correcta.",
            "imagen": "🐱",
            "respuesta": "gato",
            "palabras": [
                {"id": "perro", "texto": "PERRO"},
                {"id": "gato", "texto": "GATO"},
                {"id": "pato", "texto": "PATO"},
                {"id": "vaca", "texto": "VACA"},
            ],
        },

        3: {
            "titulo": "Imagen y palabra",
            "nombre_actividad": "Imagen y palabra - Pato",
            "descripcion": "Relacionar la imagen de un pato con la palabra PATO.",
            "instruccion": "Mira la imagen. Toca la palabra correcta.",
            "imagen": "🦆",
            "respuesta": "pato",
            "palabras": [
                {"id": "pato", "texto": "PATO"},
                {"id": "gato", "texto": "GATO"},
                {"id": "conejo", "texto": "CONEJO"},
                {"id": "pez", "texto": "PEZ"},
            ],
        },

        4: {
            "titulo": "Imagen y palabra",
            "nombre_actividad": "Imagen y palabra - Caballo",
            "descripcion": "Relacionar la imagen de un caballo con la palabra CABALLO.",
            "instruccion": "Mira la imagen. Toca la palabra correcta.",
            "imagen": "🐴",
            "respuesta": "caballo",
            "palabras": [
                {"id": "vaca", "texto": "VACA"},
                {"id": "caballo", "texto": "CABALLO"},
                {"id": "perro", "texto": "PERRO"},
                {"id": "gato", "texto": "GATO"},
            ],
        },

        5: {
            "titulo": "Imagen y palabra",
            "nombre_actividad": "Imagen y palabra - Vaca",
            "descripcion": "Relacionar la imagen de una vaca con la palabra VACA.",
            "instruccion": "Mira la imagen. Toca la palabra correcta.",
            "imagen": "🐄",
            "respuesta": "vaca",
            "palabras": [
                {"id": "vaca", "texto": "VACA"},
                {"id": "caballo", "texto": "CABALLO"},
                {"id": "conejo", "texto": "CONEJO"},
                {"id": "pez", "texto": "PEZ"},
            ],
        },

        6: {
            "titulo": "Imagen y palabra",
            "nombre_actividad": "Imagen y palabra - Conejo",
            "descripcion": "Relacionar la imagen de un conejo con la palabra CONEJO.",
            "instruccion": "Mira la imagen. Toca la palabra correcta.",
            "imagen": "🐰",
            "respuesta": "conejo",
            "palabras": [
                {"id": "conejo", "texto": "CONEJO"},
                {"id": "gato", "texto": "GATO"},
                {"id": "pato", "texto": "PATO"},
                {"id": "perro", "texto": "PERRO"},
            ],
        },

        7: {
            "titulo": "Imagen y palabra",
            "nombre_actividad": "Imagen y palabra - Pez",
            "descripcion": "Relacionar la imagen de un pez con la palabra PEZ.",
            "instruccion": "Mira la imagen. Toca la palabra correcta.",
            "imagen": "🐟",
            "respuesta": "pez",
            "palabras": [
                {"id": "pez", "texto": "PEZ"},
                {"id": "pato", "texto": "PATO"},
                {"id": "vaca", "texto": "VACA"},
                {"id": "conejo", "texto": "CONEJO"},
            ],
        },
    }

    if nivel not in ejercicios:
        return redirect("menu_actividades")

    ejercicio = ejercicios[nivel]

    palabras = ejercicio["palabras"].copy()
    random.shuffle(palabras)

    if request.method == "POST":
        completado = request.POST.get("completado") == "1"

        if completado:
            actividad, _ = Actividad.objects.get_or_create(
                nombre=ejercicio["nombre_actividad"],
                defaults={
                    "descripcion": ejercicio["descripcion"]
                }
            )

            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )

            siguiente_nivel = nivel + 1

            if siguiente_nivel in ejercicios:
                return redirect("actividad_imagen_palabra_nivel", nivel=siguiente_nivel)
            else:
                messages.success(
                    request,
                    "✅ ¡Muy bien! Terminaste el bloque de imagen y palabra."
                )
                return redirect("menu_actividades")

    contexto = {
        "nivel": nivel,
        "titulo_actividad": ejercicio["titulo"],
        "instruccion_texto": ejercicio["instruccion"],
        "imagen": ejercicio["imagen"],
        "respuesta": ejercicio["respuesta"],
        "palabras": palabras,
    }

    return render(request, "usuarios/actividad_imagen_palabra.html", contexto)

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
    Actividad de asociación por niveles.
    Los primeros niveles trabajan objetos iguales.
    Los últimos niveles trabajan objetos que guardan relación.
    """

    ejercicios = {
        1: {
            "titulo": "Objetos iguales",
            "instruccion": "Arrastra cada dibujo de abajo y suéltalo encima del dibujo igual de arriba.",
            "nombre_actividad": "Objetos iguales - Nivel 1",
            "descripcion": "Emparejar objetos iguales: bota, llave y pera.",
            "superiores": [
                {"id": "bota", "emoji": "👢"},
                {"id": "llave", "emoji": "🔑"},
                {"id": "pera", "emoji": "🍐"},
            ],
            "inferiores": [
                {"id": "bota", "emoji": "👢"},
                {"id": "llave", "emoji": "🔑"},
                {"id": "pera", "emoji": "🍐"},
            ],
        },

        2: {
            "titulo": "Objetos iguales",
            "instruccion": "Arrastra cada dibujo de abajo y suéltalo encima del dibujo igual de arriba.",
            "nombre_actividad": "Objetos iguales - Nivel 2",
            "descripcion": "Emparejar objetos iguales: zapato, sombrero y reloj.",
            "superiores": [
                {"id": "zapato", "emoji": "👟"},
                {"id": "sombrero", "emoji": "👒"},
                {"id": "reloj", "emoji": "⏰"},
            ],
            "inferiores": [
                {"id": "zapato", "emoji": "👟"},
                {"id": "sombrero", "emoji": "👒"},
                {"id": "reloj", "emoji": "⏰"},
            ],
        },

        3: {
            "titulo": "Objetos relacionados",
            "instruccion": "Arrastra cada dibujo de abajo y suéltalo encima del dibujo que se relaciona.",
            "nombre_actividad": "Objetos relacionados - Nivel 3",
            "descripcion": "Relacionar tortuga con tortuga, queso con queso y teléfono con radio.",
            "superiores": [
                {"id": "tortuga", "emoji": "🐢"},
                {"id": "queso", "emoji": "🧀"},
                {"id": "telefono", "emoji": "☎️"},
            ],
            "inferiores": [
                {"id": "tortuga", "emoji": "🐢"},
                {"id": "queso", "emoji": "🧀"},
                {"id": "telefono", "emoji": "📻"},
            ],
        },

        4: {
            "titulo": "Objetos relacionados",
            "instruccion": "Arrastra cada dibujo de abajo y suéltalo encima del dibujo que se relaciona.",
            "nombre_actividad": "Objetos relacionados - Nivel 4",
            "descripcion": "Relacionar uvas, tambor y abrigo con objetos similares.",
            "superiores": [
                {"id": "uvas", "emoji": "🍇"},
                {"id": "tambor", "emoji": "🥁"},
                {"id": "abrigo", "emoji": "🧥"},
            ],
            "inferiores": [
                {"id": "uvas", "emoji": "🍇"},
                {"id": "tambor", "emoji": "🥁"},
                {"id": "abrigo", "emoji": "🧥"},
            ],
        },

        5: {
            "titulo": "Objetos relacionados",
            "instruccion": "Arrastra cada dibujo de abajo y suéltalo encima del dibujo que se relaciona.",
            "nombre_actividad": "Objetos relacionados - Nivel 5",
            "descripcion": "Relacionar hoja con árbol, vestido con abrigo y fresa con plátano.",
            "superiores": [
                {"id": "arbol", "emoji": "🍃"},
                {"id": "ropa", "emoji": "👗"},
                {"id": "fruta", "emoji": "🍓"},
            ],
            "inferiores": [
                {"id": "arbol", "emoji": "🌳"},
                {"id": "ropa", "emoji": "🧥"},
                {"id": "fruta", "emoji": "🍌"},
            ],
        },

        6: {
            "titulo": "Objetos relacionados",
            "instruccion": "Arrastra cada dibujo de abajo y suéltalo encima del dibujo que se relaciona.",
            "nombre_actividad": "Objetos relacionados - Nivel 6",
            "descripcion": "Relacionar naranja con jugo, almohada con cama y asiento con carro.",
            "superiores": [
                {"id": "jugo", "emoji": "🍊"},
                {"id": "cama", "emoji": "🛏️"},
                {"id": "carro", "emoji": "💺"},
            ],
            "inferiores": [
                {"id": "jugo", "emoji": "🧃"},
                {"id": "cama", "emoji": "🛌"},
                {"id": "carro", "emoji": "🚗"},
            ],
        },
    }

    if nivel not in ejercicios:
        return redirect("menu_actividades")

    ejercicio = ejercicios[nivel]

    objetos = ejercicio["superiores"]
    objetos_desordenados = ejercicio["inferiores"].copy()
    random.shuffle(objetos_desordenados)

    if request.method == "POST":
        completado = request.POST.get("completado") == "1"

        if completado:
            actividad, _ = Actividad.objects.get_or_create(
                nombre=ejercicio["nombre_actividad"],
                defaults={
                    "descripcion": ejercicio["descripcion"]
                },
            )

            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )

            siguiente_nivel = nivel + 1

            if siguiente_nivel in ejercicios:
                return redirect("actividad_objetos_iguales", nivel=siguiente_nivel)
            else:
                messages.success(
                    request,
                    "✅ ¡Muy bien! Terminaste el bloque de asociación de objetos."
                )
                return redirect("menu_actividades")

    contexto = {
        "nivel": nivel,
        "titulo_actividad": ejercicio["titulo"],
        "instruccion_texto": ejercicio["instruccion"],
        "objetos": objetos,
        "objetos_desordenados": objetos_desordenados,
    }

    return render(request, "usuarios/actividad_objetos_iguales.html", contexto)

@login_required
@user_passes_test(es_nino)
def actividad_unir_dibujos(request, nivel=1):
    """
    Nueva sección basada en el Ejercicio 3:
    unir dibujos de la izquierda con su pareja de la derecha mediante líneas.
    """

    ejercicios = {
        1: {
            "titulo": "Unir dibujos iguales",
            "nombre_actividad": "Unir dibujos - Nivel 1",
            "descripcion": "Unir pato, silla y pelota con sus iguales.",
            "instruccion": "Toca un dibujo de la izquierda y después toca su pareja de la derecha.",
            "izquierda": [
                {"id": "pato", "emoji": "🐤"},
                {"id": "silla", "emoji": "🪑"},
                {"id": "pelota", "emoji": "⚽"},
            ],
            "derecha": [
                {"id": "pelota", "emoji": "⚽"},
                {"id": "pato", "emoji": "🐤"},
                {"id": "silla", "emoji": "🪑"},
            ],
        },
        2: {
            "titulo": "Unir dibujos iguales",
            "nombre_actividad": "Unir dibujos - Nivel 2",
            "descripcion": "Unir sol, esponja y short con sus iguales.",
            "instruccion": "Une cada dibujo con el que es igual.",
            "izquierda": [
                {"id": "sol", "emoji": "☀️"},
                {"id": "esponja", "emoji": "🧽"},
                {"id": "short", "emoji": "🩳"},
            ],
            "derecha": [
                {"id": "short", "emoji": "🩳"},
                {"id": "sol", "emoji": "☀️"},
                {"id": "esponja", "emoji": "🧽"},
            ],
        },
        3: {
            "titulo": "Unir dibujos iguales",
            "nombre_actividad": "Unir dibujos - Nivel 3",
            "descripcion": "Unir manzanas de diferentes colores.",
            "instruccion": "Busca la manzana igual y únela con una línea.",
            "izquierda": [
                {"id": "manzana_amarilla", "emoji": "🍏"},
                {"id": "manzana_roja", "emoji": "🍎"},
                {"id": "manzana_verde", "emoji": "🟢"},
            ],
            "derecha": [
                {"id": "manzana_roja", "emoji": "🍎"},
                {"id": "manzana_verde", "emoji": "🟢"},
                {"id": "manzana_amarilla", "emoji": "🍏"},
            ],
        },
        4: {
            "titulo": "Unir dibujos relacionados",
            "nombre_actividad": "Unir dibujos - Nivel 4",
            "descripcion": "Unir naranja, vaca y lámpara con dibujos relacionados.",
            "instruccion": "Une cada dibujo con el que se parece o se relaciona.",
            "izquierda": [
                {"id": "naranja", "emoji": "🍊"},
                {"id": "vaca", "emoji": "🐄"},
                {"id": "lampara", "emoji": "💡"},
            ],
            "derecha": [
                {"id": "vaca", "emoji": "🐂"},
                {"id": "lampara", "emoji": "🛋️"},
                {"id": "naranja", "emoji": "🟠"},
            ],
        },
        5: {
            "titulo": "Unir dibujos relacionados",
            "nombre_actividad": "Unir dibujos - Nivel 5",
            "descripcion": "Unir animales, relojes y payasos relacionados.",
            "instruccion": "Busca el dibujo que se relaciona y únelo.",
            "izquierda": [
                {"id": "animal", "emoji": "🦁"},
                {"id": "reloj", "emoji": "🕰️"},
                {"id": "payaso", "emoji": "🤡"},
            ],
            "derecha": [
                {"id": "payaso", "emoji": "🤡"},
                {"id": "animal", "emoji": "🐕"},
                {"id": "reloj", "emoji": "⌚"},
            ],
        },
        6: {
            "titulo": "Unir dibujos relacionados",
            "nombre_actividad": "Unir dibujos - Nivel 6",
            "descripcion": "Unir tren, cuchillo y canasta con objetos relacionados.",
            "instruccion": "Une cada dibujo con el que corresponde.",
            "izquierda": [
                {"id": "transporte", "emoji": "🚆"},
                {"id": "cuchillo", "emoji": "🔪"},
                {"id": "basquet", "emoji": "🏀"},
            ],
            "derecha": [
                {"id": "transporte", "emoji": "✈️"},
                {"id": "basquet", "emoji": "🏀"},
                {"id": "cuchillo", "emoji": "🥄"},
            ],
        },
        7: {
            "titulo": "Unir dibujos relacionados",
            "nombre_actividad": "Unir dibujos - Nivel 7",
            "descripcion": "Unir carro, llave y cafetera con objetos relacionados.",
            "instruccion": "Une cada dibujo con su pareja relacionada.",
            "izquierda": [
                {"id": "carro", "emoji": "🚗"},
                {"id": "llave", "emoji": "🔑"},
                {"id": "cafe", "emoji": "☕"},
            ],
            "derecha": [
                {"id": "cafe", "emoji": "☕"},
                {"id": "carro", "emoji": "🛞"},
                {"id": "llave", "emoji": "🏠"},
            ],
        },
        
                8: {
            "titulo": "Unir dibujos iguales",
            "nombre_actividad": "Unir dibujos - Nivel 8",
            "descripcion": "Unir cinco objetos iguales: pez, vaso, lápiz, zapato y pan.",
            "instruccion": "Toca un dibujo de la izquierda y después toca el dibujo igual de la derecha.",
            "izquierda": [
                {"id": "pez", "emoji": "🐟"},
                {"id": "vaso", "emoji": "🥛"},
                {"id": "lapiz", "emoji": "✏️"},
                {"id": "zapato", "emoji": "👟"},
                {"id": "pan", "emoji": "🥐"},
            ],
            "derecha": [
                {"id": "pan", "emoji": "🥐"},
                {"id": "zapato", "emoji": "👟"},
                {"id": "pez", "emoji": "🐟"},
                {"id": "lapiz", "emoji": "✏️"},
                {"id": "vaso", "emoji": "🥛"},
            ],
        },

        9: {
            "titulo": "Unir dibujos iguales",
            "nombre_actividad": "Unir dibujos - Nivel 9",
            "descripcion": "Unir motocicleta, olla, fresa y zapato.",
            "instruccion": "Une cada dibujo de la izquierda con su igual de la derecha.",
            "izquierda": [
                {"id": "moto", "emoji": "🛵"},
                {"id": "zapato", "emoji": "👟"},
                {"id": "olla", "emoji": "🍲"},
                {"id": "fresa", "emoji": "🍓"},
            ],
            "derecha": [
                {"id": "olla", "emoji": "🍲"},
                {"id": "fresa", "emoji": "🍓"},
                {"id": "zapato", "emoji": "👟"},
                {"id": "moto", "emoji": "🛵"},
            ],
        },

        10: {
            "titulo": "Unir dibujos iguales",
            "nombre_actividad": "Unir dibujos - Nivel 10",
            "descripcion": "Unir mesas de diferentes formas.",
            "instruccion": "Busca la mesa igual y únela con una línea.",
            "izquierda": [
                {"id": "mesa_redonda", "emoji": "🟠"},
                {"id": "mesa_madera", "emoji": "🟫"},
                {"id": "mesa_verde", "emoji": "🟩"},
                {"id": "mesa_cajon", "emoji": "🗄️"},
                {"id": "mesa_mantel", "emoji": "🟪"},
            ],
            "derecha": [
                {"id": "mesa_cajon", "emoji": "🗄️"},
                {"id": "mesa_redonda", "emoji": "🟠"},
                {"id": "mesa_madera", "emoji": "🟫"},
                {"id": "mesa_mantel", "emoji": "🟪"},
                {"id": "mesa_verde", "emoji": "🟩"},
            ],
        },

        11: {
            "titulo": "Unir dibujos relacionados",
            "nombre_actividad": "Unir dibujos - Nivel 11",
            "descripcion": "Unir objetos que guardan relación.",
            "instruccion": "Une cada dibujo de la izquierda con el dibujo que se relaciona.",
            "izquierda": [
                {"id": "comida", "emoji": "🍕"},
                {"id": "calzado", "emoji": "👞"},
                {"id": "arbol", "emoji": "🌲"},
                {"id": "mano", "emoji": "🤚"},
                {"id": "animal_marino", "emoji": "🦭"},
            ],
            "derecha": [
                {"id": "animal_marino", "emoji": "🦭"},
                {"id": "arbol", "emoji": "🌳"},
                {"id": "comida", "emoji": "🥣"},
                {"id": "calzado", "emoji": "👠"},
                {"id": "mano", "emoji": "🖐️"},
            ],
        },

        12: {
            "titulo": "Unir dibujos relacionados",
            "nombre_actividad": "Unir dibujos - Nivel 12",
            "descripcion": "Unir muñeca, maleta, tren y comida con objetos relacionados.",
            "instruccion": "Busca el dibujo que se relaciona y únelo.",
            "izquierda": [
                {"id": "muneca", "emoji": "🧍‍♀️"},
                {"id": "maleta", "emoji": "🧳"},
                {"id": "tren", "emoji": "🚆"},
                {"id": "comida", "emoji": "🥧"},
            ],
            "derecha": [
                {"id": "comida", "emoji": "🥖"},
                {"id": "maleta", "emoji": "🧳"},
                {"id": "muneca", "emoji": "👧"},
                {"id": "tren", "emoji": "🚊"},
            ],
        },

        13: {
            "titulo": "Unir dibujos relacionados",
            "nombre_actividad": "Unir dibujos - Nivel 13",
            "descripcion": "Unir acciones con objetos.",
            "instruccion": "Une cada acción con el objeto que corresponde.",
            "izquierda": [
                {"id": "escribir", "emoji": "✍️"},
                {"id": "dormir", "emoji": "😴"},
                {"id": "leer", "emoji": "📖"},
                {"id": "jugar", "emoji": "⚽"},
            ],
            "derecha": [
                {"id": "leer", "emoji": "📖"},
                {"id": "jugar", "emoji": "⚽"},
                {"id": "escribir", "emoji": "✏️"},
                {"id": "dormir", "emoji": "🛏️"},
            ],
        },

        14: {
            "titulo": "Unir dibujos relacionados",
            "nombre_actividad": "Unir dibujos - Nivel 14",
            "descripcion": "Unir objetos de uso cotidiano con su relación.",
            "instruccion": "Une cada dibujo con el objeto que corresponde.",
            "izquierda": [
                {"id": "dientes", "emoji": "🪥"},
                {"id": "luz", "emoji": "💡"},
                {"id": "bebe", "emoji": "🍼"},
                {"id": "vista", "emoji": "👁️"},
                {"id": "ropa", "emoji": "🪝"},
            ],
            "derecha": [
                {"id": "vista", "emoji": "👓"},
                {"id": "ropa", "emoji": "🚪"},
                {"id": "bebe", "emoji": "👶"},
                {"id": "luz", "emoji": "💡"},
                {"id": "dientes", "emoji": "🥛"},
            ],
        },

        15: {
            "titulo": "Unir dibujos relacionados",
            "nombre_actividad": "Unir dibujos - Nivel 15",
            "descripcion": "Unir objetos y animales con elementos relacionados.",
            "instruccion": "Une cada dibujo de la izquierda con el que se relaciona de la derecha.",
            "izquierda": [
                {"id": "animal", "emoji": "🦓"},
                {"id": "computadora", "emoji": "💻"},
                {"id": "clavo", "emoji": "🔨"},
                {"id": "lluvia", "emoji": "🌧️"},
                {"id": "pie", "emoji": "🦶"},
            ],
            "derecha": [
                {"id": "clavo", "emoji": "🔩"},
                {"id": "pie", "emoji": "🧦"},
                {"id": "computadora", "emoji": "🖱️"},
                {"id": "animal", "emoji": "🐄"},
                {"id": "lluvia", "emoji": "☂️"},
            ],
        },
    }

    if nivel not in ejercicios:
        return redirect("menu_actividades")

    ejercicio = ejercicios[nivel]

    izquierda = ejercicio["izquierda"]
    derecha = ejercicio["derecha"].copy()
    random.shuffle(derecha)

    if request.method == "POST":
        completado = request.POST.get("completado") == "1"

        if completado:
            actividad, _ = Actividad.objects.get_or_create(
                nombre=ejercicio["nombre_actividad"],
                defaults={
                    "descripcion": ejercicio["descripcion"]
                }
            )

            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )

            siguiente_nivel = nivel + 1

            if siguiente_nivel in ejercicios:
                return redirect("actividad_unir_dibujos", nivel=siguiente_nivel)
            else:
                messages.success(
                    request,
                    "✅ ¡Muy bien! Terminaste la sección de unir dibujos."
                )
                return redirect("menu_actividades")

    contexto = {
        "nivel": nivel,
        "titulo_actividad": ejercicio["titulo"],
        "instruccion_texto": ejercicio["instruccion"],
        "izquierda": izquierda,
        "derecha": derecha,
    }

    return render(request, "usuarios/actividad_unir_dibujos.html", contexto)

@login_required
@user_passes_test(es_nino)
def actividad_buscar_iguales(request, nivel=1):
    """
    Ejercicio 4:
    Se muestra un dibujo modelo arriba y el niño debe seleccionar
    todos los dibujos iguales que aparecen abajo.
    """

    ejercicios = {
        1: {
            "titulo": "Buscar dibujos iguales",
            "nombre_actividad": "Buscar iguales - Nivel 1",
            "descripcion": "Buscar todas las cajas iguales al modelo.",
            "instruccion": "Mira el dibujo de arriba. Busca abajo todos los dibujos iguales.",
            "modelo": {"id": "caja", "emoji": "📦"},
            "opciones": [
                {"id": "caja", "emoji": "📦"},
                {"id": "silla", "emoji": "🪑"},
                {"id": "caja", "emoji": "📦"},
                {"id": "pera", "emoji": "🍐"},
                {"id": "caja", "emoji": "📦"},
                {"id": "television", "emoji": "📺"},
            ],
        },

        2: {
            "titulo": "Buscar dibujos iguales",
            "nombre_actividad": "Buscar iguales - Nivel 2",
            "descripcion": "Buscar todas las motocicletas iguales al modelo.",
            "instruccion": "Busca todos los dibujos iguales al modelo de arriba.",
            "modelo": {"id": "moto", "emoji": "🛵"},
            "opciones": [
                {"id": "moto", "emoji": "🛵"},
                {"id": "zapato", "emoji": "👟"},
                {"id": "moto", "emoji": "🛵"},
                {"id": "telefono", "emoji": "☎️"},
                {"id": "moto", "emoji": "🛵"},
                {"id": "olla", "emoji": "🍲"},
            ],
        },

        3: {
            "titulo": "Buscar dibujos iguales",
            "nombre_actividad": "Buscar iguales - Nivel 3",
            "descripcion": "Buscar todas las camisetas iguales al modelo.",
            "instruccion": "Toca todos los dibujos que sean iguales al de arriba.",
            "modelo": {"id": "camiseta", "emoji": "👕"},
            "opciones": [
                {"id": "camiseta", "emoji": "👕"},
                {"id": "abrigo", "emoji": "🧥"},
                {"id": "camiseta", "emoji": "👕"},
                {"id": "short", "emoji": "🩳"},
                {"id": "camiseta", "emoji": "👕"},
                {"id": "vestido", "emoji": "👗"},
            ],
        },

        4: {
            "titulo": "Buscar dibujos iguales",
            "nombre_actividad": "Buscar iguales - Nivel 4",
            "descripcion": "Buscar todos los peces iguales al modelo.",
            "instruccion": "Mira bien el dibujo modelo y toca todos los iguales.",
            "modelo": {"id": "pez", "emoji": "🐟"},
            "opciones": [
                {"id": "pez", "emoji": "🐟"},
                {"id": "manzana", "emoji": "🍎"},
                {"id": "pez", "emoji": "🐟"},
                {"id": "camion", "emoji": "🚚"},
                {"id": "pez", "emoji": "🐟"},
                {"id": "lapiz", "emoji": "✏️"},
                {"id": "zapato", "emoji": "👟"},
                {"id": "pez", "emoji": "🐟"},
            ],
        },

        5: {
            "titulo": "Buscar dibujos iguales",
            "nombre_actividad": "Buscar iguales - Nivel 5",
            "descripcion": "Buscar todos los autobuses iguales al modelo.",
            "instruccion": "Selecciona todos los dibujos iguales al modelo.",
            "modelo": {"id": "bus", "emoji": "🚌"},
            "opciones": [
                {"id": "bus", "emoji": "🚌"},
                {"id": "auto", "emoji": "🚗"},
                {"id": "bus", "emoji": "🚌"},
                {"id": "canasta", "emoji": "🧺"},
                {"id": "tren", "emoji": "🚆"},
                {"id": "bus", "emoji": "🚌"},
                {"id": "pelota", "emoji": "⚽"},
                {"id": "bus", "emoji": "🚌"},
            ],
        },

        6: {
            "titulo": "Buscar dibujos iguales",
            "nombre_actividad": "Buscar iguales - Nivel 6",
            "descripcion": "Buscar todos los soles iguales al modelo.",
            "instruccion": "Toca todos los dibujos iguales al dibujo de arriba.",
            "modelo": {"id": "sol", "emoji": "☀️"},
            "opciones": [
                {"id": "sol", "emoji": "☀️"},
                {"id": "luna", "emoji": "🌙"},
                {"id": "sol", "emoji": "☀️"},
                {"id": "estrella", "emoji": "⭐"},
                {"id": "sol", "emoji": "☀️"},
                {"id": "platano", "emoji": "🍌"},
                {"id": "sol", "emoji": "☀️"},
                {"id": "pelota", "emoji": "🏀"},
            ],
        },
    }

    if nivel not in ejercicios:
        return redirect("menu_actividades")

    ejercicio = ejercicios[nivel]
    opciones = ejercicio["opciones"].copy()
    random.shuffle(opciones)

    if request.method == "POST":
        completado = request.POST.get("completado") == "1"

        if completado:
            actividad, _ = Actividad.objects.get_or_create(
                nombre=ejercicio["nombre_actividad"],
                defaults={
                    "descripcion": ejercicio["descripcion"]
                }
            )

            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )

            siguiente_nivel = nivel + 1

            if siguiente_nivel in ejercicios:
                return redirect("actividad_buscar_iguales", nivel=siguiente_nivel)
            else:
                messages.success(
                    request,
                    "✅ ¡Muy bien! Terminaste la sección de buscar dibujos iguales."
                )
                return redirect("menu_actividades")

    contexto = {
        "nivel": nivel,
        "titulo_actividad": ejercicio["titulo"],
        "instruccion_texto": ejercicio["instruccion"],
        "modelo": ejercicio["modelo"],
        "opciones": opciones,
    }

    return render(request, "usuarios/actividad_buscar_iguales.html", contexto)

@login_required
@user_passes_test(es_nino)
def actividad_buscar_dos_modelos(request, nivel=1):
    """
    Ejercicio 5:
    Se muestran dos dibujos modelo arriba.
    El niño debe seleccionar todos los dibujos iguales a esos modelos.
    """

    ejercicios = {
        1: {
            "titulo": "Buscar dos modelos",
            "nombre_actividad": "Buscar dos modelos - Nivel 1",
            "descripcion": "Buscar sillas y lápices iguales a los modelos.",
            "instruccion": "Mira los dos dibujos de arriba. Busca abajo todos los dibujos iguales.",
            "modelos": [
                {"id": "silla", "emoji": "🪑"},
                {"id": "lapiz", "emoji": "✏️"},
            ],
            "opciones": [
                {"id": "silla", "emoji": "🪑"},
                {"id": "lapiz", "emoji": "✏️"},
                {"id": "silla", "emoji": "🪑"},
                {"id": "lapiz", "emoji": "✏️"},
                {"id": "silla", "emoji": "🪑"},
                {"id": "lapiz", "emoji": "✏️"},
            ],
        },

        2: {
            "titulo": "Buscar dos modelos",
            "nombre_actividad": "Buscar dos modelos - Nivel 2",
            "descripcion": "Buscar autos y manzanas iguales a los modelos.",
            "instruccion": "Selecciona todos los dibujos iguales a los dos modelos de arriba.",
            "modelos": [
                {"id": "auto", "emoji": "🚗"},
                {"id": "manzana", "emoji": "🍎"},
            ],
            "opciones": [
                {"id": "auto", "emoji": "🚗"},
                {"id": "manzana", "emoji": "🍎"},
                {"id": "auto", "emoji": "🚗"},
                {"id": "manzana", "emoji": "🍎"},
                {"id": "auto", "emoji": "🚗"},
                {"id": "manzana", "emoji": "🍎"},
            ],
        },

        3: {
            "titulo": "Buscar dos modelos",
            "nombre_actividad": "Buscar dos modelos - Nivel 3",
            "descripcion": "Buscar ositos y bicicletas iguales a los modelos.",
            "instruccion": "Toca todos los dibujos iguales a los dos modelos.",
            "modelos": [
                {"id": "oso", "emoji": "🧸"},
                {"id": "bicicleta", "emoji": "🚲"},
            ],
            "opciones": [
                {"id": "oso", "emoji": "🧸"},
                {"id": "bicicleta", "emoji": "🚲"},
                {"id": "oso", "emoji": "🧸"},
                {"id": "bicicleta", "emoji": "🚲"},
                {"id": "oso", "emoji": "🧸"},
                {"id": "bicicleta", "emoji": "🚲"},
            ],
        },

        4: {
            "titulo": "Buscar dos modelos",
            "nombre_actividad": "Buscar dos modelos - Nivel 4",
            "descripcion": "Buscar mesas y gatos entre más dibujos.",
            "instruccion": "Busca abajo todos los dibujos iguales a los dos modelos.",
            "modelos": [
                {"id": "mesa", "emoji": "🟫"},
                {"id": "gato", "emoji": "🐈"},
            ],
            "opciones": [
                {"id": "mesa", "emoji": "🟫"},
                {"id": "gato", "emoji": "🐈"},
                {"id": "mesa", "emoji": "🟫"},
                {"id": "gato", "emoji": "🐈"},
                {"id": "auto", "emoji": "🚗"},
                {"id": "pelota", "emoji": "⚽"},
                {"id": "mesa", "emoji": "🟫"},
                {"id": "gato", "emoji": "🐈"},
                {"id": "manzana", "emoji": "🍎"},
                {"id": "sol", "emoji": "☀️"},
            ],
        },

        5: {
            "titulo": "Buscar dos modelos",
            "nombre_actividad": "Buscar dos modelos - Nivel 5",
            "descripcion": "Buscar vasos y flores entre más dibujos.",
            "instruccion": "Mira los modelos y selecciona todos los dibujos iguales.",
            "modelos": [
                {"id": "vaso", "emoji": "🥛"},
                {"id": "flor", "emoji": "🌼"},
            ],
            "opciones": [
                {"id": "vaso", "emoji": "🥛"},
                {"id": "flor", "emoji": "🌼"},
                {"id": "vaso", "emoji": "🥛"},
                {"id": "flor", "emoji": "🌼"},
                {"id": "lapiz", "emoji": "✏️"},
                {"id": "botella", "emoji": "🧴"},
                {"id": "vaso", "emoji": "🥛"},
                {"id": "flor", "emoji": "🌼"},
                {"id": "oso", "emoji": "🧸"},
                {"id": "vaso", "emoji": "🥛"},
            ],
        },

        6: {
            "titulo": "Buscar dos modelos",
            "nombre_actividad": "Buscar dos modelos - Nivel 6",
            "descripcion": "Buscar ropa y caballos entre muchos dibujos.",
            "instruccion": "Selecciona solo los dibujos iguales a los modelos de arriba.",
            "modelos": [
                {"id": "ropa", "emoji": "👚"},
                {"id": "caballo", "emoji": "🐴"},
            ],
            "opciones": [
                {"id": "ropa", "emoji": "👚"},
                {"id": "caballo", "emoji": "🐴"},
                {"id": "ropa", "emoji": "👚"},
                {"id": "caballo", "emoji": "🐴"},
                {"id": "sombrero", "emoji": "👒"},
                {"id": "auto", "emoji": "🚗"},
                {"id": "ave", "emoji": "🐦"},
                {"id": "zapato", "emoji": "👟"},
                {"id": "ropa", "emoji": "👚"},
                {"id": "caballo", "emoji": "🐴"},
                {"id": "maleta", "emoji": "🧳"},
                {"id": "caballo", "emoji": "🐴"},
            ],
        },
    }

    if nivel not in ejercicios:
        return redirect("menu_actividades")

    ejercicio = ejercicios[nivel]

    opciones = ejercicio["opciones"].copy()
    random.shuffle(opciones)

    ids_modelos = [modelo["id"] for modelo in ejercicio["modelos"]]

    if request.method == "POST":
        completado = request.POST.get("completado") == "1"

        if completado:
            actividad, _ = Actividad.objects.get_or_create(
                nombre=ejercicio["nombre_actividad"],
                defaults={
                    "descripcion": ejercicio["descripcion"]
                }
            )

            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )

            siguiente_nivel = nivel + 1

            if siguiente_nivel in ejercicios:
                return redirect("actividad_buscar_dos_modelos", nivel=siguiente_nivel)
            else:
                messages.success(
                    request,
                    "✅ ¡Muy bien! Terminaste la sección de buscar dos modelos."
                )
                return redirect("menu_actividades")

    contexto = {
        "nivel": nivel,
        "titulo_actividad": ejercicio["titulo"],
        "instruccion_texto": ejercicio["instruccion"],
        "modelos": ejercicio["modelos"],
        "opciones": opciones,
        "ids_modelos": ids_modelos,
    }

    return render(request, "usuarios/actividad_buscar_dos_modelos.html", contexto)

@login_required
@user_passes_test(es_nino)
def actividad_buscar_por_filas(request, nivel=1):
    """
    Ejercicio 6:
    En cada fila hay un dibujo modelo a la izquierda.
    El niño debe seleccionar los dibujos iguales al modelo dentro de esa misma fila.
    """

    ejercicios = {
        1: {
            "titulo": "Buscar por filas",
            "nombre_actividad": "Buscar por filas - Nivel 1",
            "descripcion": "Buscar dibujos iguales al modelo en tres filas.",
            "instruccion": "Mira el dibujo de la izquierda. Busca en esa fila los dibujos iguales.",
            "filas": [
                {
                    "modelo": {"id": "olla", "emoji": "🍲"},
                    "opciones": [
                        {"id": "olla", "emoji": "🍲"},
                        {"id": "pez", "emoji": "🐟"},
                        {"id": "olla", "emoji": "🍲"},
                        {"id": "zapato", "emoji": "👟"},
                    ],
                },
                {
                    "modelo": {"id": "auto", "emoji": "🚗"},
                    "opciones": [
                        {"id": "auto", "emoji": "🚗"},
                        {"id": "auto", "emoji": "🚗"},
                        {"id": "olla", "emoji": "🍲"},
                        {"id": "pelota", "emoji": "⚽"},
                    ],
                },
                {
                    "modelo": {"id": "pelota", "emoji": "⚽"},
                    "opciones": [
                        {"id": "pelota", "emoji": "⚽"},
                        {"id": "camiseta", "emoji": "👕"},
                        {"id": "pelota", "emoji": "⚽"},
                        {"id": "maleta", "emoji": "🧳"},
                    ],
                },
            ],
        },

        2: {
            "titulo": "Buscar por filas",
            "nombre_actividad": "Buscar por filas - Nivel 2",
            "descripcion": "Buscar dibujos iguales en filas con más opciones.",
            "instruccion": "Selecciona en cada fila todos los dibujos iguales al modelo.",
            "filas": [
                {
                    "modelo": {"id": "telefono", "emoji": "☎️"},
                    "opciones": [
                        {"id": "telefono", "emoji": "☎️"},
                        {"id": "telefono", "emoji": "☎️"},
                        {"id": "sombrero", "emoji": "👒"},
                        {"id": "reloj", "emoji": "⏰"},
                        {"id": "telefono", "emoji": "☎️"},
                    ],
                },
                {
                    "modelo": {"id": "sol", "emoji": "☀️"},
                    "opciones": [
                        {"id": "luna", "emoji": "🌙"},
                        {"id": "sol", "emoji": "☀️"},
                        {"id": "sol", "emoji": "☀️"},
                        {"id": "estrella", "emoji": "⭐"},
                        {"id": "sol", "emoji": "☀️"},
                    ],
                },
                {
                    "modelo": {"id": "camiseta", "emoji": "👕"},
                    "opciones": [
                        {"id": "camiseta", "emoji": "👕"},
                        {"id": "abrigo", "emoji": "🧥"},
                        {"id": "camiseta", "emoji": "👕"},
                        {"id": "vestido", "emoji": "👗"},
                        {"id": "camiseta", "emoji": "👕"},
                    ],
                },
            ],
        },

        3: {
            "titulo": "Buscar por filas",
            "nombre_actividad": "Buscar por filas - Nivel 3",
            "descripcion": "Buscar dibujos iguales con distractores parecidos.",
            "instruccion": "Busca con cuidado los dibujos iguales al modelo de cada fila.",
            "filas": [
                {
                    "modelo": {"id": "manzana", "emoji": "🍎"},
                    "opciones": [
                        {"id": "manzana", "emoji": "🍎"},
                        {"id": "pera", "emoji": "🍐"},
                        {"id": "manzana", "emoji": "🍎"},
                        {"id": "platano", "emoji": "🍌"},
                        {"id": "manzana", "emoji": "🍎"},
                    ],
                },
                {
                    "modelo": {"id": "vaso", "emoji": "🥛"},
                    "opciones": [
                        {"id": "botella", "emoji": "🧴"},
                        {"id": "vaso", "emoji": "🥛"},
                        {"id": "vaso", "emoji": "🥛"},
                        {"id": "taza", "emoji": "☕"},
                        {"id": "vaso", "emoji": "🥛"},
                    ],
                },
                {
                    "modelo": {"id": "silla", "emoji": "🪑"},
                    "opciones": [
                        {"id": "silla", "emoji": "🪑"},
                        {"id": "mesa", "emoji": "🟫"},
                        {"id": "silla", "emoji": "🪑"},
                        {"id": "cama", "emoji": "🛏️"},
                        {"id": "silla", "emoji": "🪑"},
                    ],
                },
            ],
        },

        4: {
            "titulo": "Buscar por filas",
            "nombre_actividad": "Buscar por filas - Nivel 4",
            "descripcion": "Buscar dibujos iguales aumentando la cantidad de opciones.",
            "instruccion": "Mira cada modelo y toca todos los dibujos iguales en su fila.",
            "filas": [
                {
                    "modelo": {"id": "caja", "emoji": "📦"},
                    "opciones": [
                        {"id": "caja", "emoji": "📦"},
                        {"id": "casa", "emoji": "🏠"},
                        {"id": "caja", "emoji": "📦"},
                        {"id": "silla", "emoji": "🪑"},
                        {"id": "caja", "emoji": "📦"},
                        {"id": "television", "emoji": "📺"},
                    ],
                },
                {
                    "modelo": {"id": "flor", "emoji": "🌼"},
                    "opciones": [
                        {"id": "flor", "emoji": "🌼"},
                        {"id": "arbol", "emoji": "🌳"},
                        {"id": "flor", "emoji": "🌼"},
                        {"id": "hoja", "emoji": "🍃"},
                        {"id": "flor", "emoji": "🌼"},
                        {"id": "sol", "emoji": "☀️"},
                    ],
                },
                {
                    "modelo": {"id": "zapato", "emoji": "👟"},
                    "opciones": [
                        {"id": "bota", "emoji": "👢"},
                        {"id": "zapato", "emoji": "👟"},
                        {"id": "zapato", "emoji": "👟"},
                        {"id": "sandalia", "emoji": "🩴"},
                        {"id": "zapato", "emoji": "👟"},
                        {"id": "calcetin", "emoji": "🧦"},
                    ],
                },
            ],
        },

        5: {
            "titulo": "Buscar por filas",
            "nombre_actividad": "Buscar por filas - Nivel 5",
            "descripcion": "Buscar dibujos iguales en cuatro filas.",
            "instruccion": "En cada fila, selecciona solo los dibujos iguales al modelo.",
            "filas": [
                {
                    "modelo": {"id": "perro", "emoji": "🐶"},
                    "opciones": [
                        {"id": "perro", "emoji": "🐶"},
                        {"id": "gato", "emoji": "🐱"},
                        {"id": "perro", "emoji": "🐶"},
                        {"id": "caballo", "emoji": "🐴"},
                    ],
                },
                {
                    "modelo": {"id": "lapiz", "emoji": "✏️"},
                    "opciones": [
                        {"id": "lapiz", "emoji": "✏️"},
                        {"id": "libro", "emoji": "📖"},
                        {"id": "lapiz", "emoji": "✏️"},
                        {"id": "pluma", "emoji": "🖊️"},
                    ],
                },
                {
                    "modelo": {"id": "cama", "emoji": "🛏️"},
                    "opciones": [
                        {"id": "cama", "emoji": "🛏️"},
                        {"id": "silla", "emoji": "🪑"},
                        {"id": "mesa", "emoji": "🟫"},
                        {"id": "cama", "emoji": "🛏️"},
                    ],
                },
                {
                    "modelo": {"id": "pelota", "emoji": "🏀"},
                    "opciones": [
                        {"id": "pelota", "emoji": "🏀"},
                        {"id": "pelota", "emoji": "🏀"},
                        {"id": "auto", "emoji": "🚗"},
                        {"id": "tren", "emoji": "🚆"},
                    ],
                },
            ],
        },
    }

    if nivel not in ejercicios:
        return redirect("menu_actividades")

    ejercicio = ejercicios[nivel]

    filas = []
    for fila in ejercicio["filas"]:
        opciones = fila["opciones"].copy()
        random.shuffle(opciones)
        filas.append({
            "modelo": fila["modelo"],
            "opciones": opciones,
        })

    if request.method == "POST":
        completado = request.POST.get("completado") == "1"

        if completado:
            actividad, _ = Actividad.objects.get_or_create(
                nombre=ejercicio["nombre_actividad"],
                defaults={
                    "descripcion": ejercicio["descripcion"]
                }
            )

            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )

            siguiente_nivel = nivel + 1

            if siguiente_nivel in ejercicios:
                return redirect("actividad_buscar_por_filas", nivel=siguiente_nivel)
            else:
                messages.success(
                    request,
                    "✅ ¡Muy bien! Terminaste la sección de buscar por filas."
                )
                return redirect("menu_actividades")

    contexto = {
        "nivel": nivel,
        "titulo_actividad": ejercicio["titulo"],
        "instruccion_texto": ejercicio["instruccion"],
        "filas": filas,
    }

    return render(request, "usuarios/actividad_buscar_por_filas.html", contexto)

@login_required
@user_passes_test(es_nino)
def actividad_foto_palabra(request, nivel=1):
    """
    Bloque 2: Foto y palabra.
    El niño observa una fotografía y selecciona la palabra correcta.
    """

    ejercicios = {
        1: {
            "titulo": "Foto y palabra",
            "nombre_actividad": "Foto y palabra - Nivel 1",
            "descripcion": "Relacionar la foto de mamá con la palabra MAMÁ.",
            "instruccion": "Mira la foto. Toca la palabra correcta.",
            "foto": "usuarios/fotos/mama.png",
            "respuesta": "mama",
            "palabras": [
                {"id": "mama", "texto": "MAMÁ"},
                {"id": "papa", "texto": "PAPÁ"},
                {"id": "nino", "texto": "YO"},
            ],
        },

        2: {
            "titulo": "Foto y palabra",
            "nombre_actividad": "Foto y palabra - Nivel 2",
            "descripcion": "Relacionar la foto de papá con la palabra PAPÁ.",
            "instruccion": "Mira la foto. Toca la palabra correcta.",
            "foto": "usuarios/fotos/papa.png",
            "respuesta": "papa",
            "palabras": [
                {"id": "mama", "texto": "MAMÁ"},
                {"id": "papa", "texto": "PAPÁ"},
                {"id": "nino", "texto": "YO"},
            ],
        },

        3: {
            "titulo": "Foto y palabra",
            "nombre_actividad": "Foto y palabra - Nivel 3",
            "descripcion": "Relacionar la foto del niño con la palabra YO.",
            "instruccion": "Mira la foto. Toca la palabra correcta.",
            "foto": "usuarios/fotos/nino.png",
            "respuesta": "nino",
            "palabras": [
                {"id": "mama", "texto": "MAMÁ"},
                {"id": "papa", "texto": "PAPÁ"},
                {"id": "nino", "texto": "YO"},
            ],
        },

        4: {
            "titulo": "Foto y palabra",
            "nombre_actividad": "Foto y palabra - Nivel 4",
            "descripcion": "Reforzar la relación foto de mamá con palabra.",
            "instruccion": "Observa la foto y selecciona su palabra.",
            "foto": "usuarios/fotos/mama.png",
            "respuesta": "mama",
            "palabras": [
                {"id": "papa", "texto": "PAPÁ"},
                {"id": "nino", "texto": "YO"},
                {"id": "mama", "texto": "MAMÁ"},
            ],
        },

        5: {
            "titulo": "Foto y palabra",
            "nombre_actividad": "Foto y palabra - Nivel 5",
            "descripcion": "Reforzar la relación foto de papá con palabra.",
            "instruccion": "Observa la foto y selecciona su palabra.",
            "foto": "usuarios/fotos/papa.png",
            "respuesta": "papa",
            "palabras": [
                {"id": "nino", "texto": "YO"},
                {"id": "mama", "texto": "MAMÁ"},
                {"id": "papa", "texto": "PAPÁ"},
            ],
        },

        6: {
            "titulo": "Foto y palabra",
            "nombre_actividad": "Foto y palabra - Nivel 6",
            "descripcion": "Reforzar la relación foto del niño con palabra.",
            "instruccion": "Observa la foto y selecciona su palabra.",
            "foto": "usuarios/fotos/nino.png",
            "respuesta": "nino",
            "palabras": [
                {"id": "mama", "texto": "MAMÁ"},
                {"id": "nino", "texto": "YO"},
                {"id": "papa", "texto": "PAPÁ"},
            ],
        },
    }

    if nivel not in ejercicios:
        return redirect("menu_actividades")

    ejercicio = ejercicios[nivel]

    palabras = ejercicio["palabras"].copy()
    random.shuffle(palabras)

    if request.method == "POST":
        completado = request.POST.get("completado") == "1"

        if completado:
            actividad, _ = Actividad.objects.get_or_create(
                nombre=ejercicio["nombre_actividad"],
                defaults={
                    "descripcion": ejercicio["descripcion"]
                }
            )

            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )

            siguiente_nivel = nivel + 1

            if siguiente_nivel in ejercicios:
                return redirect("actividad_foto_palabra", nivel=siguiente_nivel)
            else:
                messages.success(
                    request,
                    "✅ ¡Muy bien! Terminaste el bloque de foto y palabra."
                )
                return redirect("menu_actividades")

    contexto = {
        "nivel": nivel,
        "titulo_actividad": ejercicio["titulo"],
        "instruccion_texto": ejercicio["instruccion"],
        "foto": ejercicio["foto"],
        "respuesta": ejercicio["respuesta"],
        "palabras": palabras,
    }

    return render(request, "usuarios/actividad_foto_palabra.html", contexto)

@login_required
@user_passes_test(es_nino)
def actividad_recompensa_estrellas(request):
    """
    Bloque 5: Juego breve de recompensa.
    El niño toca estrellas y al finalizar se guarda el progreso.
    """

    if request.method == "POST":
        completado = request.POST.get("completado") == "1"

        if completado:
            actividad, _ = Actividad.objects.get_or_create(
                nombre="Juego de recompensa - Atrapa estrellas",
                defaults={
                    "descripcion": "Juego breve de recompensa para motivar al niño."
                }
            )

            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )

            messages.success(
                request,
                "⭐ ¡Muy bien! Terminaste el juego de recompensa."
            )

            return redirect("menu_actividades")

    return render(request, "usuarios/actividad_recompensa_estrellas.html")

@login_required
@user_passes_test(es_nino)
def actividad_memoria_figuras(request):
    """
    Bloque de recompensa:
    Juego de memoria con 6 pares de figuras.
    Cada vez que inicia, se seleccionan 6 figuras aleatorias
    de una lista de 20.
    """

    if request.method == "POST":
        completado = request.POST.get("completado") == "1"

        if completado:
            actividad, _ = Actividad.objects.get_or_create(
                nombre="Juego de recompensa - Memoria de figuras",
                defaults={
                    "descripcion": "Juego de memoria con cartas y figuras aleatorias."
                }
            )

            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )

            messages.success(
                request,
                "🧠 ¡Muy bien! Terminaste el juego de memoria."
            )

            return redirect("menu_actividades")

    figuras_base = [
        {"id": "perro", "emoji": "🐶"},
        {"id": "gato", "emoji": "🐱"},
        {"id": "pato", "emoji": "🦆"},
        {"id": "vaca", "emoji": "🐄"},
        {"id": "conejo", "emoji": "🐰"},
        {"id": "pez", "emoji": "🐟"},
        {"id": "caballo", "emoji": "🐴"},
        {"id": "oso", "emoji": "🐻"},
        {"id": "estrella", "emoji": "⭐"},
        {"id": "sol", "emoji": "☀️"},
        {"id": "luna", "emoji": "🌙"},
        {"id": "flor", "emoji": "🌼"},
        {"id": "arbol", "emoji": "🌳"},
        {"id": "manzana", "emoji": "🍎"},
        {"id": "pera", "emoji": "🍐"},
        {"id": "pelota", "emoji": "⚽"},
        {"id": "auto", "emoji": "🚗"},
        {"id": "tren", "emoji": "🚆"},
        {"id": "casa", "emoji": "🏠"},
        {"id": "zapato", "emoji": "👟"},
    ]

    # Tomamos 6 figuras diferentes de las 20
    seleccionadas = random.sample(figuras_base, 6)

    cartas = []

    # Cada figura se agrega dos veces para formar pares
    for figura in seleccionadas:
        cartas.append({
            "id": figura["id"],
            "emoji": figura["emoji"],
        })
        cartas.append({
            "id": figura["id"],
            "emoji": figura["emoji"],
        })

    # Revolvemos las cartas
    random.shuffle(cartas)

    contexto = {
        "cartas": cartas,
    }

    return render(request, "usuarios/actividad_memoria_figuras.html", contexto)

@login_required
@user_passes_test(es_nino)
def actividad_colorear_dibujo(request):
    """
    Bloque de recompensa:
    Juego para colorear un dibujo aleatorio.
    El niño escoge un color y toca partes del dibujo.
    """

    if request.method == "POST":
        completado = request.POST.get("completado") == "1"

        if completado:
            actividad, _ = Actividad.objects.get_or_create(
                nombre="Juego de recompensa - Colorear dibujo",
                defaults={
                    "descripcion": "Juego de colorear un dibujo usando una paleta de colores."
                }
            )

            Progreso.objects.create(
                nino=request.user,
                actividad=actividad,
            )

            messages.success(
                request,
                "🎨 ¡Muy bien! Terminaste el juego de colorear."
            )

            return redirect("menu_actividades")

    dibujos = [
        {"id": "casa", "nombre": "Casa"},
        {"id": "flor", "nombre": "Flor"},
        {"id": "pez", "nombre": "Pez"},
        {"id": "sol", "nombre": "Sol"},
        {"id": "arbol", "nombre": "Árbol"},
        {"id": "auto", "nombre": "Auto"},
        {"id": "mariposa", "nombre": "Mariposa"},
        {"id": "estrella", "nombre": "Estrella"},
        {"id": "barco", "nombre": "Barco"},
        {"id": "corazon", "nombre": "Corazón"},
    ]

    ultimo_dibujo = request.session.get("ultimo_dibujo_colorear")

    disponibles = [d for d in dibujos if d["id"] != ultimo_dibujo]

    dibujo = random.choice(disponibles)

    request.session["ultimo_dibujo_colorear"] = dibujo["id"]

    contexto = {
        "dibujo_id": dibujo["id"],
        "dibujo_nombre": dibujo["nombre"],
    }

    return render(request, "usuarios/actividad_colorear_dibujo.html", contexto)


