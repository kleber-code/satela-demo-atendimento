"""Métricas do dashboard, calculadas a partir das conversas."""
from collections import Counter
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from ..models import Agendamento, Chamado, Conversa, Mensagem
from . import limites
from .horario import sla_minutos


def _fmt_dur(seg):
    if seg is None:
        return "—"
    seg = int(seg)
    if seg < 60:
        return f"{seg}s"
    if seg < 3600:
        return f"{seg // 60} min {seg % 60:02d}s"
    return f"{seg // 3600}h {(seg % 3600) // 60:02d}min"


def calcular(dias=7):
    agora = timezone.now()
    desde = agora - timedelta(days=dias)
    convs = list(Conversa.objects.filter(criada_em__gte=desde).select_related("cliente"))
    total = len(convs)

    resolvidas = [c for c in convs if c.status == "resolvida"]
    pelo_bot = [c for c in resolvidas if c.resolvida_pelo_bot]
    taxa_bot = round(100 * len(pelo_bot) / len(resolvidas)) if resolvidas else 0
    # % de conversas que nunca precisaram de humano
    sem_humano = [c for c in convs if not c.bot_falhou and c.status in ("bot", "resolvida") and c.primeira_resposta_humana_em is None]
    contencao = round(100 * len(sem_humano) / total) if total else 0

    t_bot = [(c.primeira_resposta_em - c.criada_em).total_seconds() for c in convs if c.primeira_resposta_em and c.primeira_resposta_humana_em is None]
    t_hum = [
        (c.primeira_resposta_humana_em - (c.aguardando_desde or c.criada_em)).total_seconds()
        for c in convs if c.primeira_resposta_humana_em and c.primeira_resposta_humana_em >= (c.aguardando_desde or c.criada_em)
    ]
    media = lambda l: sum(l) / len(l) if l else None
    sla = sla_minutos() * 60
    no_prazo = round(100 * sum(1 for t in t_hum if t <= sla) / len(t_hum)) if t_hum else 100

    notas = [c.csat for c in convs if c.csat]
    csat_media = round(sum(notas) / len(notas), 1) if notas else None
    dist_csat = [Counter(notas).get(i, 0) for i in range(1, 6)]

    por_hora = [0] * 24
    por_dia = Counter()
    for c in convs:
        loc = timezone.localtime(c.criada_em)
        por_hora[loc.hour] += 1
        por_dia[loc.date()] += 1
    hoje = timezone.localdate()
    serie_dias = [((hoje - timedelta(days=dias - 1 - i)), por_dia.get(hoje - timedelta(days=dias - 1 - i), 0)) for i in range(dias)]

    status = Counter(c.status for c in convs)
    acoes = Counter(
        m.acao["nome"] for m in Mensagem.objects.filter(tipo="acao", criada_em__gte=desde) if m.acao
    )
    falhas = Counter(c.motivo_falha for c in convs if c.bot_falhou)

    return {
        "dias": dias,
        "total": total,
        "abertas": sum(1 for c in convs if c.status != "resolvida"),
        "taxa_bot": taxa_bot,
        "contencao": contencao,
        "tempo_bot": _fmt_dur(media(t_bot)),
        "tempo_humano": _fmt_dur(media(t_hum)),
        "sla_prazo": no_prazo,
        "sla_min": sla_minutos(),
        "csat": csat_media,
        "csat_n": len(notas),
        "dist_csat": dist_csat,
        "por_hora": por_hora,
        "serie_dias": serie_dias,
        "status": [(k, status.get(k, 0)) for k in ("bot", "aguardando", "atendimento", "resolvida")],
        "acoes": acoes.most_common(),
        "falhas": falhas.most_common(),
        "pico_hora": max(range(24), key=lambda h: por_hora[h]) if total else None,
        "ia_usada": limites.ia_usada_hoje(),
        "ia_teto": settings.TETO_IA_DIARIO,
        "agendamentos": Agendamento.objects.count(),
        "chamados": Chamado.objects.count(),
    }
