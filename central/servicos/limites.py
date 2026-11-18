"""Proteção de custo: limites por IP/sessão e teto global diário de chamadas à IA.

Os contadores ficam no banco (tabela EventoUso) para valerem entre os workers do gunicorn.
Endereços IP são guardados apenas como hash.
"""
import hashlib
import random
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from ..models import EventoUso


def ip_cliente(request):
    """IP do cliente. Considera apenas o proxy confiável mais próximo (PROXY_HOPS) do X-Forwarded-For."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    partes = [p.strip() for p in xff.split(",") if p.strip()]
    hops = max(settings.PROXY_HOPS, 0)
    if partes and hops and len(partes) >= hops:
        return partes[-hops]
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def hash_ip(ip):
    return hashlib.sha256((settings.SECRET_KEY + "|" + ip).encode()).hexdigest()[:32]


def _inicio_do_dia():
    return timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)


def _contar(tipo, chave, desde):
    return EventoUso.objects.filter(tipo=tipo, chave=chave, criado_em__gte=desde).count()


def _limpar():
    if random.random() < 0.02:
        EventoUso.objects.filter(criado_em__lt=timezone.now() - timedelta(days=3)).delete()


class Resultado:
    def __init__(self, ok, motivo="", espera=0):
        self.ok, self.motivo, self.espera = ok, motivo, espera

    def __bool__(self):
        return self.ok


def checar_e_registrar_mensagem(ip, sessao):
    """Valida os 4 limites (IP/min, IP/dia, sessão/min, sessão/dia) e registra o uso se passou."""
    agora = timezone.now()
    h_ip, h_se = hash_ip(ip), (sessao or "")[:64]
    minuto, dia = agora - timedelta(minutes=1), _inicio_do_dia()
    if _contar("msg_ip", h_ip, minuto) >= settings.LIMITE_IP_POR_MINUTO or (
        h_se and _contar("msg_sessao", h_se, minuto) >= settings.LIMITE_SESSAO_POR_MINUTO
    ):
        return Resultado(False, "Você está enviando mensagens rápido demais. Aguarde alguns segundos e tente de novo.", 30)
    if _contar("msg_ip", h_ip, dia) >= settings.LIMITE_IP_POR_DIA or (
        h_se and _contar("msg_sessao", h_se, dia) >= settings.LIMITE_SESSAO_POR_DIA
    ):
        return Resultado(False, "Você atingiu o limite diário de mensagens da demonstração. Volte amanhã!", 3600)
    EventoUso.objects.create(tipo="msg_ip", chave=h_ip)
    if h_se:
        EventoUso.objects.create(tipo="msg_sessao", chave=h_se)
    _limpar()
    return Resultado(True)


def ia_usada_hoje():
    return EventoUso.objects.filter(tipo="ia", criado_em__gte=_inicio_do_dia()).count()


def ia_restante():
    return max(settings.TETO_IA_DIARIO - ia_usada_hoje(), 0)


def consumir_ia():
    """Reserva uma chamada de IA do teto diário global. False se o teto foi atingido."""
    if ia_usada_hoje() >= settings.TETO_IA_DIARIO:
        return False
    EventoUso.objects.create(tipo="ia")
    return True
