from django.conf import settings
from django.contrib.auth.models import User

from ..models import Perfil

DEMO_USUARIOS = {
    "atendente": ("demo_atendente", "Rafael Lima", "atendente", "#3b6ea8"),
    "supervisor": ("demo_supervisora", "Marina Duarte", "supervisor", "#1b7a55"),
}
EQUIPE = [
    ("camila.torres", "Camila Torres", "atendente", "#a8613b"),
    ("diego.alves", "Diego Alves", "atendente", "#7a4aa8"),
]


def garantir_usuario(username, nome, papel, cor):
    user, criado = User.objects.get_or_create(username=username, defaults={"first_name": nome.split()[0]})
    if criado:
        user.set_unusable_password()  # só entra pelo botão do modo demonstração
        user.save()
    Perfil.objects.update_or_create(user=user, defaults={"nome": nome, "papel": papel, "cor": cor})
    return user


def usuario_demo(papel):
    return garantir_usuario(*DEMO_USUARIOS[papel])


def garantir_equipe():
    for papel in DEMO_USUARIOS:
        usuario_demo(papel)
    for dados in EQUIPE:
        garantir_usuario(*dados)


def garantir_admin():
    """Superusuário só existe se DEMO_ADMIN_PASSWORD estiver definida."""
    if not settings.DEMO_ADMIN_PASSWORD:
        return None
    user, _ = User.objects.get_or_create(username="admin", defaults={"is_staff": True, "is_superuser": True})
    user.is_staff = user.is_superuser = True
    user.set_password(settings.DEMO_ADMIN_PASSWORD)
    user.save()
    Perfil.objects.update_or_create(user=user, defaults={"nome": "Administrador", "papel": "supervisor", "cor": "#222222"})
    return user
