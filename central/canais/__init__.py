"""Camada de canais: cada canal traduz o mundo externo (web, WhatsApp...) para o núcleo.

Veja canais/base.py para a interface e README.md para como plugar o WhatsApp (Hub da Satela).
"""
from .base import Canal, EntradaMensagem
from .web import CanalWeb
from .whatsapp import CanalWhatsApp

REGISTRO = {"web": CanalWeb(), "whatsapp": CanalWhatsApp()}


def obter(slug):
    """Canal pelo slug; cai no web (polling) para canais desconhecidos."""
    return REGISTRO.get(slug, REGISTRO["web"])
