
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'rol', 'is_staff', 'is_active')
    list_filter = ('rol', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Rol y asignación', {'fields': ('rol', 'docente')}),
    )


# Register your models here.
