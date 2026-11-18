import re
from functools import wraps

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Agendamento, Artigo, Chamado, Configuracao, Conversa, Etiqueta, Mensagem, Pedido, RespostaRapida, perfil_de,
)
from .servicos import atendimento, graficos, horario, kb, limites
from .servicos import metricas as srv_metricas

STATUS_ROTULOS = dict(Conversa.STATUS)
MOTIVOS = {
    "nao_soube": "Sem resposta na base",
    "pediu_humano": "Cliente pediu humano",
    "ia_indisponivel": "IA indisponível / sem chave",
    "limite_ia": "Teto diário de IA atingido",
}


def supervisor_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *a, **kw):
        if not perfil_de(request.user).eh_supervisor:
            raise PermissionDenied
        return view(request, *a, **kw)

    return wrapper


def _pode_agir(user, conversa):
    p = perfil_de(user)
    return p.eh_supervisor or conversa.atribuido_id in (None, user.id)


# ------------------------------------------------------------------ caixa de entrada

def _filtrar(request):
    qs = Conversa.objects.select_related("cliente", "atribuido__perfil").prefetch_related("etiquetas")
    status = request.GET.get("status", "")
    if status in STATUS_ROTULOS:
        qs = qs.filter(status=status)
    elif status == "abertas":
        qs = qs.exclude(status="resolvida")
    if request.GET.get("minhas") == "1":
        qs = qs.filter(atribuido=request.user)
    et = request.GET.get("etiqueta", "")
    if et.isdigit():
        qs = qs.filter(etiquetas__pk=int(et))
    q = request.GET.get("q", "").strip()[:80]
    if q:
        cond = Q(cliente__nome__icontains=q) | Q(mensagens__texto__icontains=q)
        m = re.fullmatch(r"(?:AT-?)?0*(\d+)", q, re.I)
        if m:
            cond |= Q(pk=int(m.group(1)))
        qs = qs.filter(cond).distinct()
    return qs.order_by("-atualizada_em")[:80]


def _contagens():
    base = {s: 0 for s, _ in Conversa.STATUS}
    for c in Conversa.objects.values_list("status", flat=True):
        base[c] += 1
    return base


@login_required
def caixa(request):
    contexto = _contexto_lista(request)
    sel = request.GET.get("c", "")
    contexto["pane"] = ""
    if sel.isdigit():
        conversa = Conversa.objects.filter(pk=int(sel)).first()
        if conversa:
            contexto["pane"] = _render_painel(request, conversa)
            contexto["selecionada"] = conversa.pk
    return render(request, "central/caixa.html", contexto)


def _contexto_lista(request):
    return {
        "conversas": _filtrar(request),
        "contagens": _contagens(),
        "etiquetas": Etiqueta.objects.all(),
        "filtro": {k: request.GET.get(k, "") for k in ("status", "q", "etiqueta", "minhas")},
        "selecionada": int(request.GET["c"]) if request.GET.get("c", "").isdigit() else None,
        "agora": timezone.now(),
    }


@login_required
def caixa_lista(request):
    return render(request, "central/_lista.html", _contexto_lista(request))


def _render_painel(request, conversa):
    if conversa.nao_lidas:
        conversa.nao_lidas = 0
        conversa.save(update_fields=["nao_lidas"])
    msgs = conversa.mensagens.select_related("usuario__perfil")
    ultimo = max((m.id for m in msgs), default=0)
    return render_to_string("central/_conversa.html", {
        "c": conversa,
        "mensagens": msgs,
        "ultimo": ultimo,
        "etiquetas": Etiqueta.objects.all(),
        "etiquetas_ids": set(conversa.etiquetas.values_list("pk", flat=True)),
        "atendentes": User.objects.filter(perfil__isnull=False).select_related("perfil").order_by("perfil__nome"),
        "rapidas": RespostaRapida.objects.all(),
        "pode_agir": _pode_agir(request.user, conversa),
        "estado": _estado(conversa),
        "agora": timezone.now(),
        "aberto": horario.dentro_do_expediente(),
    }, request=request)


def _estado(c):
    return f"{c.status}|{c.atribuido_id or 0}|{','.join(str(i) for i in sorted(c.etiquetas.values_list('pk', flat=True)))}"


@login_required
def conversa_painel(request, pk):
    c = get_object_or_404(Conversa, pk=pk)
    return HttpResponse(_render_painel(request, c))


@login_required
def conversa_mensagens(request, pk):
    c = get_object_or_404(Conversa, pk=pk)
    try:
        depois = int(request.GET.get("depois", 0))
    except ValueError:
        depois = 0
    novas = list(c.mensagens.filter(id__gt=depois).select_related("usuario__perfil"))
    if any(m.tipo == "cliente" for m in novas) and c.nao_lidas:
        c.nao_lidas = 0
        c.save(update_fields=["nao_lidas"])
    html = "".join(render_to_string("central/_mensagem.html", {"m": m}) for m in novas)
    return JsonResponse({"html": html, "ultimo": max([m.id for m in novas], default=depois), "estado": _estado(c)})


@login_required
@require_POST
def conversa_enviar(request, pk):
    c = get_object_or_404(Conversa, pk=pk)
    if not _pode_agir(request.user, c):
        raise PermissionDenied
    texto = request.POST.get("texto", "").strip()[:2000]
    if not texto:
        return JsonResponse({"erro": "Mensagem vazia."}, status=400)
    if request.POST.get("tipo") == "nota":
        atendimento.adicionar_mensagem(c, "nota", texto, usuario=request.user)
    else:
        if c.status in ("bot", "aguardando", "resolvida") or c.atribuido_id is None:
            c.status = "atendimento"
            c.atribuido = c.atribuido or request.user
            c.resolvida_em = None
            c.save()
        atendimento.adicionar_mensagem(c, "atendente", texto, usuario=request.user)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def conversa_acao(request, pk):
    c = get_object_or_404(Conversa, pk=pk)
    if not _pode_agir(request.user, c):
        raise PermissionDenied
    acao = request.POST.get("acao", "")
    nome = perfil_de(request.user).nome
    if acao == "assumir":
        c.atribuido, c.status = request.user, "atendimento"
        c.save()
        atendimento.adicionar_mensagem(c, "sistema", f"{nome} assumiu o atendimento.")
    elif acao == "atribuir":
        alvo = get_object_or_404(User, pk=request.POST.get("usuario", 0), perfil__isnull=False)
        c.atribuido = alvo
        if c.status in ("aguardando", "bot"):
            c.status = "atendimento"
        c.save()
        atendimento.adicionar_mensagem(c, "sistema", f"Conversa atribuída a {alvo.perfil.nome} por {nome}.")
    elif acao == "resolver":
        atendimento.resolver(c, por_bot=False, usuario=request.user)
    elif acao == "reabrir":
        c.status, c.resolvida_em, c.resolvida_pelo_bot = "atendimento", None, False
        c.atribuido = c.atribuido or request.user
        c.save()
        atendimento.adicionar_mensagem(c, "sistema", f"{nome} reabriu a conversa.")
    elif acao == "devolver_bot":
        c.status, c.atribuido, c.aguardando_desde = "bot", None, None
        c.save()
        atendimento.adicionar_mensagem(c, "sistema", f"{nome} devolveu a conversa ao assistente virtual.")
    elif acao == "etiqueta":
        e = get_object_or_404(Etiqueta, pk=request.POST.get("etiqueta", 0))
        c.etiquetas.remove(e) if c.etiquetas.filter(pk=e.pk).exists() else c.etiquetas.add(e)
    else:
        return JsonResponse({"erro": "Ação inválida."}, status=400)
    return JsonResponse({"ok": True})


# ------------------------------------------------------------------ métricas

@login_required
def metricas(request):
    try:
        dias = int(request.GET.get("dias", 7))
    except ValueError:
        dias = 7
    dias = dias if dias in (7, 14, 30) else 7
    m = srv_metricas.calcular(dias)
    m["g_hora"] = graficos.barras(m["por_hora"], [f"{h}h" for h in range(24)], destaque=m["pico_hora"], titulo="Conversas por hora do dia")
    m["g_dias"] = graficos.linha([v for _, v in m["serie_dias"]], [d.strftime("%d/%m") for d, _ in m["serie_dias"]], titulo="Conversas por dia")
    m["g_status"] = graficos.rosca(
        [(STATUS_ROTULOS[s], v, f"g-s-{s}") for s, v in m["status"]], titulo="Conversas por status"
    )
    m["g_csat"] = graficos.barras(m["dist_csat"], ["1★", "2★", "3★", "4★", "5★"], largura=360, altura=170, titulo="Distribuição das notas de CSAT")
    mx = max([v for _, v in m["acoes"]], default=1)
    m["acoes_barras"] = [(n, v, round(100 * v / mx)) for n, v in m["acoes"]]
    m["falhas_rot"] = [(MOTIVOS.get(k, k), v) for k, v in m["falhas"]]
    m["status_legenda"] = [(STATUS_ROTULOS[s], v, f"s-{s}") for s, v in m["status"]]
    return render(request, "central/metricas.html", {"m": m})


# ------------------------------------------------------------------ base de conhecimento

class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        fields = ["titulo", "categoria", "palavras_chave", "conteudo", "ativo"]
        widgets = {"conteudo": forms.Textarea(attrs={"rows": 12})}


@login_required
def conhecimento(request):
    q = request.GET.get("q", "").strip()[:120]
    resultado = None
    if q:
        resultado = [(a, s, s >= kb.LIMIAR_CONFIANCA) for a, s in kb.buscar_texto(q, 5)]
    artigos = Artigo.objects.all()
    return render(request, "central/conhecimento.html", {
        "artigos": artigos, "q": q, "resultado": resultado, "limiar": kb.LIMIAR_CONFIANCA,
        "pode_editar": perfil_de(request.user).eh_supervisor,
    })


@supervisor_required
def artigo_form(request, pk=None):
    obj = get_object_or_404(Artigo, pk=pk) if pk else None
    inicial = {"titulo": request.GET.get("titulo", "")} if not obj else None
    form = ArtigoForm(request.POST or None, instance=obj, initial=inicial)
    if request.method == "POST" and form.is_valid():
        a = form.save(commit=False)
        a.atualizado_em = timezone.now()
        a.embedding = None  # conteúdo mudou: reindexar
        a.save()
        messages.success(request, "Artigo salvo.")
        return redirect("conhecimento")
    return render(request, "central/artigo_form.html", {"form": form, "obj": obj})


@supervisor_required
@require_POST
def artigo_excluir(request, pk):
    get_object_or_404(Artigo, pk=pk).delete()
    messages.success(request, "Artigo excluído.")
    return redirect("conhecimento")


# ------------------------------------------------------------------ treinar o bot

class TreinoForm(forms.ModelForm):
    class Meta:
        model = Configuracao
        fields = ["nome_bot", "instrucoes", "msg_boas_vindas", "bot_ativo"]
        widgets = {"instrucoes": forms.Textarea(attrs={"rows": 6}), "msg_boas_vindas": forms.Textarea(attrs={"rows": 3})}


@login_required
def treinar(request):
    pode = perfil_de(request.user).eh_supervisor
    cfg = Configuracao.carregar()
    if request.method == "POST":
        if not pode:
            raise PermissionDenied
        form = TreinoForm(request.POST, instance=cfg)
        if form.is_valid():
            form.save()
            messages.success(request, "Instruções do bot atualizadas. Já valem para a próxima mensagem.")
            return redirect("treinar")
    else:
        form = TreinoForm(instance=cfg)
    falhas = []
    for c in Conversa.objects.filter(bot_falhou=True).select_related("cliente").order_by("-atualizada_em")[:30]:
        pergunta = c.mensagens.filter(tipo="cliente").order_by("-criada_em").first()
        falhas.append({"c": c, "motivo": MOTIVOS.get(c.motivo_falha, c.motivo_falha or "Falha"), "pergunta": pergunta.texto if pergunta else ""})
    return render(request, "central/treinar.html", {"form": form, "falhas": falhas, "pode": pode, "cfg": cfg})


# ------------------------------------------------------------------ respostas rápidas, config, operações

class RespostaForm(forms.ModelForm):
    class Meta:
        model = RespostaRapida
        fields = ["atalho", "titulo", "texto"]
        widgets = {"texto": forms.Textarea(attrs={"rows": 3})}

    def clean_atalho(self):
        a = self.cleaned_data["atalho"].strip().lower()
        return a if a.startswith("/") else "/" + a


@login_required
def respostas(request):
    if request.method == "POST":
        if request.POST.get("excluir"):
            RespostaRapida.objects.filter(pk=request.POST["excluir"]).delete()
            return redirect("respostas")
        obj = RespostaRapida.objects.filter(pk=request.POST.get("id") or 0).first()
        form = RespostaForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Resposta rápida salva.")
            return redirect("respostas")
    else:
        form = RespostaForm()
    return render(request, "central/respostas.html", {"form": form, "itens": RespostaRapida.objects.all()})


class ConfigForm(forms.ModelForm):
    class Meta:
        model = Configuracao
        fields = ["nome_empresa", "hora_inicio", "hora_fim", "dias_uteis", "msg_fora_expediente", "sla_minutos"]
        widgets = {"msg_fora_expediente": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        d = super().clean()
        if d.get("hora_inicio") is not None and d.get("hora_fim") is not None and d["hora_inicio"] >= d["hora_fim"]:
            raise forms.ValidationError("A hora de início deve ser menor que a de fim.")
        if d.get("dias_uteis") and not re.fullmatch(r"[0-6](,[0-6])*", d["dias_uteis"].replace(" ", "")):
            self.add_error("dias_uteis", "Use números de 0 a 6 separados por vírgula.")
        return d


@login_required
def configuracoes(request):
    pode = perfil_de(request.user).eh_supervisor
    cfg = Configuracao.carregar()
    if request.method == "POST":
        if not pode:
            raise PermissionDenied
        form = ConfigForm(request.POST, instance=cfg)
        if form.is_valid():
            form.save()
            messages.success(request, "Configurações salvas.")
            return redirect("configuracoes")
    else:
        form = ConfigForm(instance=cfg)
    limites_ctx = [
        ("Mensagens por minuto, por IP", settings.LIMITE_IP_POR_MINUTO),
        ("Mensagens por dia, por IP", settings.LIMITE_IP_POR_DIA),
        ("Mensagens por minuto, por sessão", settings.LIMITE_SESSAO_POR_MINUTO),
        ("Mensagens por dia, por sessão", settings.LIMITE_SESSAO_POR_DIA),
        ("Teto diário global de chamadas à IA", settings.TETO_IA_DIARIO),
        ("Tamanho máximo da mensagem", f"{settings.MENSAGEM_MAX_CHARS} caracteres"),
        ("Histórico enviado à IA", f"{settings.HISTORICO_MAX_MENSAGENS} mensagens"),
    ]
    return render(request, "central/configuracoes.html", {
        "form": form, "pode": pode, "limites": limites_ctx,
        "ia_usada": limites.ia_usada_hoje(), "ia_teto": settings.TETO_IA_DIARIO,
        "ia_chave": bool(settings.SATELA_API_KEY), "modelo": settings.SATELA_MODEL,
        "aberto": horario.dentro_do_expediente(cfg=cfg), "horario": horario.descricao_horario(cfg),
    })


@login_required
def operacoes(request):
    return render(request, "central/operacoes.html", {
        "pedidos": Pedido.objects.all()[:30],
        "agendamentos": Agendamento.objects.select_related("conversa").order_by("-criado_em")[:20],
        "chamados": Chamado.objects.select_related("conversa")[:20],
    })
