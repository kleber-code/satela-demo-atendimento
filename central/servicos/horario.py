from django.utils import timezone

from ..models import Configuracao


def sla_minutos():
    return Configuracao.carregar().sla_minutos


def dentro_do_expediente(agora=None, cfg=None):
    cfg = cfg or Configuracao.carregar()
    agora = timezone.localtime(agora or timezone.now())
    dias = {int(d) for d in cfg.dias_uteis.split(",") if d.strip().isdigit()}
    return agora.weekday() in dias and cfg.hora_inicio <= agora.hour < cfg.hora_fim


def descricao_horario(cfg=None):
    cfg = cfg or Configuracao.carregar()
    nomes = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    dias = sorted(int(d) for d in cfg.dias_uteis.split(",") if d.strip().isdigit())
    if not dias:
        return "sem expediente"
    faixa = f"{nomes[dias[0]]} a {nomes[dias[-1]]}" if len(dias) > 1 else nomes[dias[0]]
    return f"{faixa}, {cfg.hora_inicio:02d}h às {cfg.hora_fim:02d}h"
