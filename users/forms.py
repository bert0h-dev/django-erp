from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User

class LoginForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'No se pudo iniciar sesión. Revisa tu usuario y contraseña.',
    }

    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe tu usuario',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe tu contraseña',
            'autocomplete': 'current-password',
        })
    )

    class Meta:
        model = User
        fields = ['username', 'password']