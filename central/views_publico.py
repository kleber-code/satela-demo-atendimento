import json

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from .models import Configuracao, Conversa, Mensagem
from .canais import obter as obter_canal
from .servicos import atendimento, demo as demo_srv, horario, limites


@require_GET
def saude(request):
    return HttpResponse("ok", content_type="text/plain")


def landing(request):
    total = Conversa.objects.count()
    bot = Conversa.objects.filter(resolvida_pelo_bot=True).count()
    resolvidas = Conversa.objects.filter(status="resolvida").count()
    return render(request, "central/landing.html", {
        "total": total,
        "pct_bot": round(100 * bot / resolvidas) if resolvidas else 0,
        "ia_real": bool(settings.SATELA_API_KEY),
    })


def entrar(request):
    if request.user.is_authenticated:
        return redirect("caixa")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next") if (request.GET.get("next", "").startswith("/")) else "caixa")
    return render(request, "central/login.html", {"form": form})


@require_POST
def entrar_demo(request, papel):
    if not settings.DEMO_MODE or papel not in demo_srv.DEMO_USUARIOS:
        raise Http404()
    user = demo_srv.usuario_demo(papel)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("caixa")


@require_POST
def sair(request):
    logout(request)
    return redirect("landing")


# ------------------------------------------------------------------ widget de demonstração

def _msg_publica(m):
    d = {"id": m.id, "tipo": m.tipo, "texto": m.texto, "hora": m.criada_em.astimezone().strftime("%H:%M")}
    if m.tipo == "atendente":
        d["autor"] = m.usuario.perfil.nome if m.usuario_id and hasattr(m.usuario, "perfil") else "Atendente"
    if m.fontes:
        d["fontes"] = [f["titulo"] for f in m.fontes]
    if m.fallback:
        d["fallback"] = True
    if m.tipo == "acao" and m.acao:
        d["acao"] = {"rotulo": m.acao.get("rotulo", ""), "ok": m.acao.get("ok", False)}
    return d


def _conversa_da_sessao(request):
    cid = request.session.get("conversa_id")
    if not cid:
        return None
    return Conversa.objects.filter(pk=cid, sessao_chave=request.session.session_key).first()


def _estado(conversa):
    return {"status": conversa.status, "csat": conversa.csat} if conversa else {"status": "novo", "csat": None}


def _visiveis(conversa, depois=0):
    return [
        _msg_publica(m)
        for m in conversa.mensagens.exclude(tipo="nota").filter(id__gt=depois).select_related("usuario__perfil")
    ]


def demo(request):
    if not request.session.session_key:
        request.session.save()
    conversa = _conversa_da_sessao(request)
    cfg = Configuracao.carregar()
    return render(request, "central/demo.html", {
        "cfg": cfg,
        "inicial": _visiveis(conversa) if conversa else [],
        "estado": _estado(conversa),
        "aberto": horario.dentro_do_expediente(cfg=cfg),
        "horario": horario.descricao_horario(cfg),
        "max_chars": settings.MENSAGEM_MAX_CHARS,
    })


def _json_corpo(request):
    try:
        return json.loads(request.body or b"{}")
    except ValueError:
        return {}


@require_POST
def api_enviar(request):
    corpo = _json_corpo(request)
    texto = str(corpo.get("texto", "")).strip()
    if not texto:
        return JsonResponse({"erro": "Digite uma mensagem."}, status=400)
    if len(texto) > settings.MENSAGEM_MAX_CHARS:
        return JsonResponse({"erro": f"Mensagem muito longa (máximo {settings.MENSAGEM_MAX_CHARS} caracteres)."}, status=400)
    if not request.session.session_key:
        request.session.save()
    chave = request.session.session_key
    ok = limites.checar_e_registrar_mensagem(limites.ip_cliente(request), chave)
    if not ok:
        return JsonResponse({"erro": ok.motivo, "espera": ok.espera}, status=429)
    canal = obter_canal("web")
    entrada = canal.receber({"sessao": chave, "texto": texto})
    conversa = _conversa_da_sessao(request)
    ultimo = conversa.mensagens.order_by("-id").values_list("id", flat=True).first() or 0 if conversa else 0
    if conversa is None:
        conversa = atendimento.nova_conversa(canal="web", sessao_chave=chave)
        request.session["conversa_id"] = conversa.pk
    atendimento.processar_entrada(entrada, conversa)
    conversa.refresh_from_db()
    return JsonResponse({"mensagens": _visiveis(conversa, ultimo), **_estado(conversa)})


@require_GET
def api_mensagens(request):
    conversa = _conversa_da_sessao(request)
    if not conversa:
        return JsonResponse({"mensagens": [], **_estado(None)})
    try:
        depois = int(request.GET.get("depois", 0))
    except ValueError:
        depois = 0
    return JsonResponse({"mensagens": _visiveis(conversa, depois), **_estado(conversa)})


@require_POST
def api_avaliar(request):
    conversa = _conversa_da_sessao(request)
    try:
        nota = int(_json_corpo(request).get("nota", 0))
    except (TypeError, ValueError):
        nota = 0
    if not conversa or not 1 <= nota <= 5:
        return JsonResponse({"erro": "Avaliação inválida."}, status=400)
    conversa.csat = nota
    conversa.save(update_fields=["csat"])
    return JsonResponse(_estado(conversa))


@require_POST
def api_encerrar(request):
    conversa = _conversa_da_sessao(request)
    if conversa and conversa.status != "resolvida":
        atendimento.resolver(conversa, por_bot=conversa.status == "bot")
        conversa.refresh_from_db()
    return JsonResponse(_estado(conversa))


@require_POST
def api_nova(request):
    request.session.pop("conversa_id", None)
    return JsonResponse({"ok": True})
