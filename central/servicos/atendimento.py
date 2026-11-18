"""Operações do ciclo de vida de uma conversa (independentes de canal e de tela)."""
import random

from django.utils import timezone

from .. import canais
from ..models import Cliente, Configuracao, Conversa, Mensagem
from . import horario, ia, limites

CORES = ["#1b7a55", "#3b6ea8", "#a8613b", "#7a4aa8", "#a83b6e", "#3b8ea8", "#8a7a1b", "#5b6b8c"]


def nova_conversa(nome="", canal="web", sessao_chave=""):
    cliente = Cliente.objects.create(
        nome=nome or f"Visitante {random.randint(1000, 9999)}", cor=random.choice(CORES)
    )
    return Conversa.objects.create(cliente=cliente, canal=canal, sessao_chave=sessao_chave)


def adicionar_mensagem(conversa, tipo, texto, usuario=None, fontes=None, acao=None, fallback=False, criada_em=None):
    agora = criada_em or timezone.now()
    m = Mensagem.objects.create(
        conversa=conversa, tipo=tipo, texto=texto, usuario=usuario,
        fontes=fontes or [], acao=acao, fallback=fallback, criada_em=agora,
    )
    if tipo in ("cliente", "bot", "atendente"):
        conversa.ultima_previa = texto.replace("\n", " ")[:140]
    conversa.atualizada_em = agora
    if tipo == "cliente":
        conversa.nao_lidas += 1
    if tipo in ("bot", "atendente") and not conversa.primeira_resposta_em:
        conversa.primeira_resposta_em = agora
    if tipo == "atendente" and not conversa.primeira_resposta_humana_em:
        conversa.primeira_resposta_humana_em = agora
    conversa.save()
    if tipo in ("bot", "atendente"):
        try:
            canais.obter(conversa.canal).enviar(conversa, m)
        except NotImplementedError:
            pass
    return m


def registrar_mensagem_cliente(conversa, texto):
    """Grava a mensagem do cliente (reabrindo conversa resolvida). Não aciona o bot."""
    if conversa.status == "resolvida":
        conversa.status = "bot"
        conversa.resolvida_em = None
        conversa.resolvida_pelo_bot = False
        conversa.save()
    return adicionar_mensagem(conversa, "cliente", texto)


def _transcricao(conversa, limite=14):
    linhas = []
    for m in conversa.mensagens.filter(tipo__in=["cliente", "bot", "atendente", "acao"]).order_by("-criada_em", "-id")[:limite][::-1]:
        quem = {"cliente": "Cliente", "bot": "Bot", "atendente": "Atendente", "acao": "Ação"}[m.tipo]
        linhas.append(f"{quem}: {m.texto[:300]}")
    return "\n".join(linhas)


def resumo_heuristico(conversa):
    cliente = list(conversa.mensagens.filter(tipo="cliente").values_list("texto", flat=True))
    acoes = list(conversa.mensagens.filter(tipo="acao").values_list("texto", flat=True))
    if not cliente:
        return "Conversa sem mensagens do cliente."
    partes = [f"Primeiro pedido: \"{cliente[0][:140]}\"."]
    if len(cliente) > 1:
        partes.append(f"Última mensagem: \"{cliente[-1][:140]}\".")
    if acoes:
        partes.append("Ações já feitas: " + "; ".join(acoes[-3:]) + ".")
    return " ".join(partes)


def gerar_resumo(conversa):
    """Resumo para o atendente humano: IA se houver chave e teto, senão heurística local."""
    if ia.configurada() and limites.consumir_ia():
        try:
            r = ia.chat(
                [
                    {"role": "system", "content": "Resuma a conversa abaixo em no máximo 3 frases curtas, em português, para um atendente humano que vai assumir: assunto, o que já foi feito e o que o cliente espera. Sem saudações."},
                    {"role": "user", "content": _transcricao(conversa)},
                ],
                stream=False,
                max_tokens=220,
            )
            if r["content"].strip():
                return r["content"].strip()[:700]
        except ia.IAIndisponivel:
            pass
    return resumo_heuristico(conversa)


def transferir_para_humano(conversa, motivo, falha=True, categoria="nao_soube"):
    """Coloca a conversa na fila humana, registra resumo (nota interna) e avisa o cliente."""
    cfg = Configuracao.carregar()
    conversa.status = "aguardando"
    conversa.aguardando_desde = timezone.now()
    conversa.atribuido = None
    if falha:
        conversa.bot_falhou = True
        conversa.motivo_falha = categoria
    conversa.resumo_ia = gerar_resumo(conversa)
    conversa.save()
    adicionar_mensagem(
        conversa, "nota", f"Resumo da IA para o atendente: {conversa.resumo_ia}\nMotivo da transferência: {motivo}"
    )
    aviso = "Vou chamar um atendente humano para continuar com você. Já deixei um resumo da conversa para você não precisar repetir nada."
    if not horario.dentro_do_expediente(cfg=cfg):
        aviso += "\n\n" + cfg.msg_fora_expediente + f" (Horário: {horario.descricao_horario(cfg)}.)"
    else:
        aviso += f" Tempo médio de espera: até {cfg.sla_minutos} min."
    return adicionar_mensagem(conversa, "sistema", aviso)


def resolver(conversa, por_bot=False, usuario=None):
    conversa.status = "resolvida"
    conversa.resolvida_em = timezone.now()
    conversa.resolvida_pelo_bot = por_bot and not conversa.bot_falhou
    conversa.nao_lidas = 0
    conversa.save()
    adicionar_mensagem(
        conversa, "sistema",
        "Atendimento encerrado." if por_bot else f"Conversa resolvida por {usuario.perfil.nome if usuario else 'atendente'}.",
    )


def processar_entrada(entrada, conversa=None):
    """Ponto de entrada genérico dos canais: texto do cliente -> bot. Retorna a conversa."""
    from . import bot

    if conversa is None:
        conversa = (
            Conversa.objects.filter(canal=entrada.canal, sessao_chave=entrada.identificador)
            .exclude(status="resolvida").first()
        ) or nova_conversa(entrada.nome, entrada.canal, entrada.identificador)
    registrar_mensagem_cliente(conversa, entrada.texto)
    bot.responder(conversa, entrada.texto)
    return conversa
