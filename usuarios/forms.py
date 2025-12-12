# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario


class RegistroDocenteForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]
        # 👇 Aquí quitamos los textos de ayuda por defecto
        help_texts = {
            "username": "",
            "password1": "",
            "password2": "",
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = "docente"
        if commit:
            user.save()
        return user


class RegistroNinoForm(UserCreationForm):
    docente_username = forms.CharField(label="Usuario del docente")

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "password1", "password2"]
        # 👇 También sin textos de ayuda
        help_texts = {
            "username": "",
            "password1": "",
            "password2": "",
        }

    def save(self, commit=True):
        docente_username = self.cleaned_data["docente_username"]

        try:
            docente = Usuario.objects.get(username=docente_username, rol="docente")
        except Usuario.DoesNotExist:
            raise forms.ValidationError("No existe un docente con ese nombre de usuario.")

        user = super().save(commit=False)
        user.rol = "nino"
        user.docente = docente
        if commit:
            user.save()
        return user


