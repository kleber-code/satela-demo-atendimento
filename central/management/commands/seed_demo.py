"""Popula a demo: equipe, base de conhecimento, pedidos fictícios e ~40 conversas realistas.

Idempotente: dados-base usam update_or_create; as conversas só são criadas se não houver nenhuma.
  --se-vazio  não faz nada se já existirem conversas (usado no release do Procfile)
  --reset     apaga conversas e recria tudo
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from central.models import (
    Agendamento, Artigo, Chamado, Cliente, Configuracao, Conversa, Etiqueta, Mensagem, Pedido, RespostaRapida,
)
from central.seed_dados import ARTIGOS, ETIQUETAS, NOMES, PEDIDOS, RESPOSTAS_RAPIDAS, CENARIOS
from central.servicos import acoes, atendimento, demo

CORES = ["#1b7a55", "#3b6ea8", "#a8613b", "#7a4aa8", "#a83b6e", "#3b8ea8", "#8a7a1b", "#5b6b8c"]


class Command(BaseCommand):
    help = "Cria dados fictícios de demonstração."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Apaga conversas e recria tudo")
        parser.add_argument("--se-vazio", action="store_true", help="Só popula se não houver conversas")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["se_vazio"] and Conversa.objects.exists():
            self.stdout.write("Já existem conversas; nada a fazer.")
            demo.garantir_equipe()
            demo.garantir_admin()
            return
        if opts["reset"]:
            Conversa.objects.all().delete()
            Cliente.objects.all().delete()
            Agendamento.objects.all().delete()
            Chamado.objects.all().delete()
        Configuracao.carregar()
        demo.garantir_equipe()
        admin = demo.garantir_admin()
        self._base()
        if not Conversa.objects.exists():
            n = self._conversas()
            self.stdout.write(self.style.SUCCESS(f"{n} conversas criadas."))
        else:
            self.stdout.write("Conversas já existem; mantidas (use --reset para recriar).")
        self.stdout.write(self.style.SUCCESS("Demo pronta." + (" Superusuário 'admin' configurado." if admin else "")))

    # ---------------------------------------------------------------- dados-base
    def _base(self):
        for nome, cor in ETIQUETAS:
            Etiqueta.objects.update_or_create(nome=nome, defaults={"cor": cor})
        for titulo, categoria, chaves, conteudo in ARTIGOS:
            Artigo.objects.update_or_create(
                titulo=titulo, defaults={"categoria": categoria, "palavras_chave": chaves, "conteudo": conteudo, "ativo": True}
            )
        for atalho, titulo, texto in RESPOSTAS_RAPIDAS:
            RespostaRapida.objects.update_or_create(atalho=atalho, defaults={"titulo": titulo, "texto": texto})
        hoje = timezone.localdate()
        for numero, cliente, itens, valor, status, dias, rastreio in PEDIDOS:
            Pedido.objects.update_or_create(
                numero=numero,
                defaults={
                    "cliente_nome": cliente, "itens": itens, "valor": valor, "status": status, "rastreio": rastreio,
                    "previsao_entrega": None if status in ("cancelado", "aguardando_pagamento") else hoje + timedelta(days=dias),
                },
            )

    # ---------------------------------------------------------------- conversas
    def _conversas(self):
        rnd = random.Random(310)
        equipe = {
            "rafael": demo.usuario_demo("atendente"),
            "marina": demo.usuario_demo("supervisor"),
            "camila": demo.garantir_usuario(*demo.EQUIPE[0]),
            "diego": demo.garantir_usuario(*demo.EQUIPE[1]),
        }
        etiquetas = {e.nome: e for e in Etiqueta.objects.all()}
        artigos = {a.titulo: a for a in Artigo.objects.all()}
        agora = timezone.now()
        lista = []
        for cen in CENARIOS:
            lista += [cen] * cen["qtd"]
        lista = lista[:40]
        rnd.shuffle(lista)
        nomes = NOMES[:]
        rnd.shuffle(nomes)
        pedidos_validos = ["AUR-10421", "AUR-10422", "AUR-10423", "AUR-10424", "AUR-10425", "AUR-10426", "AUR-10428", "AUR-10430"]
        for i, cen in enumerate(lista):
            nome = nomes[i % len(nomes)]
            pedido = rnd.choice(pedidos_validos)
            inicio = self._inicio(rnd, agora, cen["janela"])
            self._criar(rnd, cen, nome, pedido, inicio, equipe, etiquetas, artigos, i)
        return len(lista)

    def _inicio(self, rnd, agora, janela):
        if janela == "recente":
            return agora - timedelta(minutes=rnd.randint(4, 300))
        # histórico: dias passados, concentrado em horário comercial
        dia = agora - timedelta(days=rnd.randint(0, 6))
        hora = rnd.choices(range(24), weights=[1, 0, 0, 0, 0, 1, 2, 4, 8, 12, 15, 14, 9, 10, 14, 15, 13, 9, 7, 8, 7, 5, 3, 2])[0]
        t = dia.replace(hour=hora, minute=rnd.randint(0, 59), second=rnd.randint(0, 59), microsecond=0)
        return t if t < agora - timedelta(hours=1) else t - timedelta(days=1)

    def _criar(self, rnd, cen, nome, pedido, inicio, equipe, etiquetas, artigos, idx):
        primeiro = nome.split()[0].lower()
        cliente = Cliente.objects.create(
            nome=nome, email=f"{primeiro}{idx}@exemplo.com.br", telefone=f"(11) 90000-{1000 + idx:04d}", cor=rnd.choice(CORES)
        )
        conv = Conversa.objects.create(cliente=cliente, canal=rnd.choice(["web", "web", "web", "whatsapp"]), criada_em=inicio, atualizada_em=inicio)
        t = inicio
        agente = equipe[cen["agente"]] if cen.get("agente") else None
        abertura = rnd.choice(cen["abre"])
        turnos = [("c", abertura.format(nome=primeiro.capitalize(), pedido=pedido))] + [
            (tp, *[x.format(nome=primeiro.capitalize(), pedido=pedido) if isinstance(x, str) else x for x in resto])
            for tp, *resto in cen["turnos"]
        ]
        msgs, momento_transf = [], None
        for tp, *dados in turnos:
            if tp == "c":
                t += timedelta(seconds=rnd.randint(25, 70) if msgs else 0)
                msgs.append(Mensagem(conversa=conv, tipo="cliente", texto=dados[0], criada_em=t))
            elif tp == "b":
                t += timedelta(seconds=rnd.randint(3, 9))
                fontes = [{"id": artigos[x].pk, "titulo": x} for x in (dados[1] if len(dados) > 1 else []) if x in artigos]
                msgs.append(Mensagem(conversa=conv, tipo="bot", texto=dados[0], fontes=fontes, criada_em=t))
            elif tp == "ia_acao":
                t += timedelta(seconds=rnd.randint(1, 3))
                nome_acao = dados[0]
                args = {k: (v.format(pedido=pedido) if isinstance(v, str) else v) for k, v in dados[1].items()}
                if nome_acao == "consultar_pedido":
                    res = acoes.consultar_pedido(args["numero"])
                elif nome_acao == "abrir_chamado":
                    res = acoes.abrir_chamado(conversa=conv, **args)
                    Chamado.objects.filter(pk=int(res["protocolo"][3:])).update(criado_em=t)
                else:
                    dia = timezone.localdate() + timedelta(days=rnd.randint(2, 9))
                    while dia.weekday() == 6:
                        dia += timedelta(days=1)
                    args["data"] = dia.isoformat()
                    res = acoes.agendar(conversa=conv, **args)
                    if res.get("ok"):
                        Agendamento.objects.filter(pk=res["id"]).update(criado_em=t)
                msgs.append(Mensagem(
                    conversa=conv, tipo="acao", texto=acoes.resumo_acao(nome_acao, res), criada_em=t,
                    acao={"nome": nome_acao, "rotulo": acoes.ROTULOS[nome_acao], "args": args, "resultado": res, "ok": bool(res.get("ok"))},
                ))
            elif tp == "bp":  # resposta do bot montada a partir do resultado real da consulta de pedido
                t += timedelta(seconds=rnd.randint(2, 5))
                res = next(m.acao["resultado"] for m in reversed(msgs) if m.tipo == "acao")
                partes = [f"Encontrei! Seu pedido {res['numero']} ({res['itens']}) está: {res['status']}."]
                if res.get("previsao_entrega"):
                    partes.append(f"Previsão de entrega: {res['previsao_entrega']}.")
                if res.get("rastreio"):
                    partes.append(f"Código de rastreio: {res['rastreio']}.")
                msgs.append(Mensagem(conversa=conv, tipo="bot", texto=" ".join(partes), criada_em=t))
            elif tp == "transf":
                t += timedelta(seconds=rnd.randint(2, 6))
                momento_transf = t
                resumo = dados[0]
                conv.resumo_ia = resumo
                msgs.append(Mensagem(conversa=conv, tipo="nota", texto=f"Resumo da IA para o atendente: {resumo}\nMotivo da transferência: {dados[1]}", criada_em=t))
                msgs.append(Mensagem(conversa=conv, tipo="sistema", criada_em=t + timedelta(seconds=1), texto=(
                    "Vou chamar um atendente humano para continuar com você. Já deixei um resumo da conversa para você não precisar repetir nada. "
                    "Tempo médio de espera: até 5 min.")))
                conv.bot_falhou, conv.motivo_falha = True, dados[2]
            elif tp == "h":
                espera = rnd.randint(40, 540) if not any(m.tipo == "atendente" for m in msgs) else rnd.randint(20, 150)
                t += timedelta(seconds=espera)
                msgs.append(Mensagem(conversa=conv, tipo="atendente", usuario=agente, texto=dados[0], criada_em=t))
            elif tp == "n":
                t += timedelta(seconds=rnd.randint(5, 40))
                msgs.append(Mensagem(conversa=conv, tipo="nota", usuario=agente, texto=dados[0], criada_em=t))
            elif tp == "s":
                t += timedelta(seconds=2)
                msgs.append(Mensagem(conversa=conv, tipo="sistema", texto=dados[0], criada_em=t))
        # pausa final: nas conversas "aguardando" a última fala é do cliente esperando; nas abertas, recente
        Mensagem.objects.bulk_create(msgs)

        status = cen["status"]
        conv.status = status
        conv.atribuido = agente if status in ("atendimento",) or (status == "resolvida" and cen.get("agente")) else None
        if status == "aguardando":
            conv.aguardando_desde = momento_transf or t
            conv.nao_lidas = rnd.randint(1, 3)
        if status == "resolvida":
            conv.resolvida_em = t + timedelta(seconds=rnd.randint(30, 600))
            conv.resolvida_pelo_bot = not cen.get("agente") and not conv.bot_falhou
            nota = rnd.choices([5, 4, 3, 2, None], weights=cen.get("csat", [5, 4, 1, 0, 2]))[0]
            conv.csat = nota
            Mensagem.objects.create(conversa=conv, tipo="sistema", criada_em=conv.resolvida_em, texto="Atendimento encerrado." if conv.resolvida_pelo_bot else f"Conversa resolvida por {agente.perfil.nome if agente else 'atendente'}.")
        ms = list(conv.mensagens.order_by("criada_em", "id"))
        resp = [m for m in ms if m.tipo in ("bot", "atendente")]
        conv.primeira_resposta_em = resp[0].criada_em if resp else None
        hum = [m for m in ms if m.tipo == "atendente"]
        conv.primeira_resposta_humana_em = hum[0].criada_em if hum else None
        visiveis = [m for m in ms if m.tipo in ("cliente", "bot", "atendente")]
        conv.ultima_previa = visiveis[-1].texto.replace("\n", " ")[:140] if visiveis else ""
        conv.atualizada_em = ms[-1].criada_em if ms else inicio_seguro(conv)
        conv.save()
        for nome_et in cen.get("etiquetas", []):
            conv.etiquetas.add(etiquetas[nome_et])


def inicio_seguro(conv):
    return conv.criada_em
