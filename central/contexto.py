from django.conf import settings

from .models import perfil_de

SECOES = {
    "caixa": "caixa", "conversa": "caixa", "metricas": "metricas", "conhecimento": "kb", "artigo_novo": "kb",
    "artigo_editar": "kb", "treinar": "treinar", "respostas": "respostas", "operacoes": "operacoes", "configuracoes": "config",
}


def global_ctx(request):
    ctx = {"DEMO_MODE": settings.DEMO_MODE}
    rm = getattr(request, "resolver_match", None)
    ctx["secao"] = SECOES.get(rm.url_name, "") if rm else ""
    u = getattr(request, "user", None)
    if u is not None and u.is_authenticated:
        ctx["perfil"] = perfil_de(u)
    return ctx
