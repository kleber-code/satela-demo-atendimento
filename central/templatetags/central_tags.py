import re

from django import template
from django.utils import timezone
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()
_neg = re.compile(r"\*\*(.+?)\*\*")


@register.filter
def fmt(texto):
    """Escapa o texto e aplica **negrito** e quebras de linha (seguro contra XSS)."""
    s = conditional_escape(texto or "")
    s = _neg.sub(r"<strong>\1</strong>", str(s))
    return mark_safe(s.replace("\n", "<br>"))


@register.filter
def hora(dt):
    return timezone.localtime(dt).strftime("%H:%M") if dt else ""


@register.filter
def quando(dt):
    if not dt:
        return ""
    loc, hoje = timezone.localtime(dt), timezone.localdate()
    if loc.date() == hoje:
        return loc.strftime("%H:%M")
    if (hoje - loc.date()).days == 1:
        return "ontem"
    return loc.strftime("%d/%m")


@register.filter
def espera(dt):
    if not dt:
        return ""
    s = int((timezone.now() - dt).total_seconds())
    if s < 60:
        return "agora"
    if s < 3600:
        return f"{s // 60} min"
    if s < 86400:
        return f"{s // 3600} h"
    return f"{s // 86400} d"


@register.filter
def estrelas(n):
    return "★" * int(n or 0) + "☆" * (5 - int(n or 0))
