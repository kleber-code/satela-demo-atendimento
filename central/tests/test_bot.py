import json

from django.test import override_settings
from django.urls import reverse

from central.models import Agendamento, Artigo, Chamado, Conversa, Mensagem
from central.servicos import atendimento, bot, ia

from .base import CHAVE, BaseTest, com_chave, resposta_chat, tool_call


class BotTest(BaseTest):
    def conversa(self):
        return atendimento.nova_conversa("Teste", sessao_chave="s1")

    def fale(self, conv, texto):
        atendimento.registrar_mensagem_cliente(conv, texto)
        return bot.responder(conv, texto)

    # --- fallback sem chave de IA
    def test_sem_chave_responde_pela_base_com_fonte(self):
        conv = self.conversa()
        m = self.fale(conv, "Qual o prazo de entrega para o interior?")
        self.assertTrue(m.fallback)
        self.assertEqual(m.fontes[0]["titulo"], "Prazos e frete de entrega")
        self.assertIn("5 a 10", m.texto)
        self.assertEqual(conv.status, "bot")

    def test_sem_chave_consulta_pedido_e_mostra_acao(self):
        conv = self.conversa()
        m = self.fale(conv, "onde está o pedido AUR-10421?")
        self.assertIn("Em rota de entrega", m.texto)
        acao = conv.mensagens.get(tipo="acao")
        self.assertEqual(acao.acao["nome"], "consultar_pedido")
        self.assertTrue(acao.acao["ok"])

    def test_sem_chave_e_sem_resposta_transfere_para_humano(self):
        conv = self.conversa()
        self.fale(conv, "vocês fazem tatuagem?")
        conv.refresh_from_db()
        self.assertEqual(conv.status, "aguardando")
        self.assertTrue(conv.bot_falhou)
        self.assertTrue(conv.resumo_ia)
        self.assertTrue(conv.mensagens.filter(tipo="nota", texto__startswith="Resumo da IA").exists())

    # --- transferência para humano
    def test_pedido_de_humano_transfere_sem_gastar_ia(self):
        conv = self.conversa()
        self.fale(conv, "quero falar com um atendente")
        conv.refresh_from_db()
        self.assertEqual((conv.status, conv.motivo_falha), ("aguardando", "pediu_humano"))
        self.assertIsNotNone(conv.aguardando_desde)
        self.assertEqual(self.chamadas, [])

    def test_bot_nao_responde_quando_humano_assumiu(self):
        conv = self.conversa()
        conv.status = "atendimento"; conv.save()
        self.assertIsNone(self.fale(conv, "oi, tudo bem? preciso de ajuda"))
        self.assertFalse(conv.mensagens.filter(tipo="bot").exists())

    @com_chave
    def test_ia_pede_transferencia_e_resumo_vem_da_ia(self):
        self.mock_ia(
            resposta_chat("Vou chamar alguém.", [tool_call("transferir_humano", {"motivo": "Cliente irritado"})]),
            resposta_chat("Cliente irritado com atraso; quer solução hoje."),
        )
        conv = self.conversa()
        self.fale(conv, "isso é um absurdo, ninguém resolve nada")
        conv.refresh_from_db()
        self.assertEqual(conv.status, "aguardando")
        self.assertEqual(conv.resumo_ia, "Cliente irritado com atraso; quer solução hoje.")
        self.assertEqual(len(self.chamadas), 2)

    def test_resumo_heuristico_sem_ia(self):
        conv = self.conversa()
        atendimento.registrar_mensagem_cliente(conv, "meu pedido não chegou")
        atendimento.transferir_para_humano(conv, "teste")
        self.assertIn("meu pedido não chegou", conv.resumo_ia)

    def test_fora_do_expediente_avisa_na_transferencia(self):
        from unittest import mock

        conv = self.conversa()
        with mock.patch("central.servicos.horario.dentro_do_expediente", return_value=False):
            atendimento.transferir_para_humano(conv, "x")
        self.assertIn("fora do expediente", conv.mensagens.filter(tipo="sistema").last().texto)

    # --- IA mockada
    @com_chave
    def test_resposta_da_ia_cita_fonte_e_remove_marcador(self):
        self.mock_ia(resposta_chat(f"Interior: 5 a 10 dias úteis. [[fonte:{self.artigo.pk}]]"))
        conv = self.conversa()
        m = self.fale(conv, "prazo para o interior?")
        self.assertFalse(m.fallback)
        self.assertNotIn("[[fonte", m.texto)
        self.assertEqual(m.fontes, [{"id": self.artigo.pk, "titulo": self.artigo.titulo}])
        enviado = self.chamadas[0]
        self.assertEqual(enviado["model"], "AC310")
        self.assertIn("Prazos e frete de entrega", enviado["messages"][0]["content"])  # contexto da base no prompt

    @com_chave
    def test_ia_usa_ferramenta_de_pedido(self):
        self.mock_ia(
            resposta_chat("", [tool_call("consultar_pedido", {"numero": "AUR-10421"})]),
            resposta_chat("Seu pedido está em rota de entrega."),
        )
        conv = self.conversa()
        m = self.fale(conv, "cadê meu pedido AUR-10421")
        self.assertEqual(m.texto, "Seu pedido está em rota de entrega.")
        self.assertEqual(conv.mensagens.get(tipo="acao").acao["resultado"]["status"], "Em rota de entrega")
        # o resultado da função foi devolvido à IA como mensagem de role=tool
        self.assertEqual(self.chamadas[1]["messages"][-1]["role"], "tool")

    @com_chave
    def test_ia_agenda_e_abre_chamado(self):
        from datetime import timedelta
        from django.utils import timezone

        d = timezone.localdate() + timedelta(days=3)
        while d.weekday() == 6:
            d += timedelta(days=1)
        self.mock_ia(
            resposta_chat("", [
                tool_call("agendar", {"tipo": "retirada", "data": d.isoformat(), "periodo": "tarde"}, "a"),
                tool_call("abrir_chamado", {"assunto": "Defeito", "descricao": "não liga", "prioridade": "alta"}, "b"),
            ]),
            resposta_chat("Feito!"),
        )
        conv = self.conversa()
        self.fale(conv, "agenda e abre chamado")
        self.assertEqual(Agendamento.objects.count(), 1)
        self.assertEqual(Chamado.objects.get().prioridade, "alta")
        self.assertEqual(conv.mensagens.filter(tipo="acao").count(), 2)

    def test_agendamento_invalido_e_recusado(self):
        from central.servicos import acoes

        self.assertFalse(acoes.agendar(tipo="retirada", data="2001-01-01", periodo="manha")["ok"])
        self.assertFalse(acoes.agendar(tipo="x", data="2030-01-01")["ok"])

    @com_chave
    def test_erro_http_da_ia_cai_no_fallback_sem_excecao(self):
        self.mock_ia(resposta_chat("x"), status=503)
        conv = self.conversa()
        m = self.fale(conv, "prazo de entrega para o interior")
        self.assertTrue(m.fallback)
        self.assertIn("5 a 10", m.texto)

    @com_chave
    def test_timeout_da_ia_cai_no_fallback(self):
        import httpx

        def estoura(request):
            raise httpx.ConnectTimeout("lento", request=request)

        ia._transport = httpx.MockTransport(estoura)
        conv = self.conversa()
        m = self.fale(conv, "prazo de entrega para o interior")
        self.assertTrue(m.fallback)

    @com_chave
    @override_settings(IA_STREAM=True)
    def test_modo_stream_acumula_os_pedacos(self):
        import httpx

        corpo = (
            'data: {"choices":[{"delta":{"content":"Olá "}}]}\n\n'
            'data: {"choices":[{"delta":{"content":"mundo"}}]}\n\ndata: [DONE]\n\n'
        )
        ia._transport = httpx.MockTransport(lambda r: httpx.Response(200, content=corpo.encode()))
        self.assertEqual(ia.chat([{"role": "user", "content": "x"}])["content"], "Olá mundo")

    @com_chave
    def test_historico_enviado_e_limitado(self):
        self.mock_ia(resposta_chat("ok"))
        conv = self.conversa()
        for i in range(30):
            atendimento.adicionar_mensagem(conv, "cliente" if i % 2 == 0 else "bot", f"msg {i}")
        with override_settings(HISTORICO_MAX_MENSAGENS=5):
            self.fale(conv, "qual o prazo de entrega?")
        msgs = self.chamadas[0]["messages"]
        self.assertEqual(len([m for m in msgs if m["role"] != "system"]), 5)

    @com_chave
    def test_chave_e_prompt_nunca_vao_para_o_navegador(self):
        self.mock_ia(resposta_chat("Resposta qualquer"))
        r = self.client.post(reverse("api_enviar"), json.dumps({"texto": "qual o prazo de entrega?"}), content_type="application/json")
        corpo = r.content.decode()
        self.assertNotIn(CHAVE, corpo)
        self.assertNotIn("REGRAS", corpo)
        self.assertNotIn("Persona e estilo", corpo)
        pagina = self.client.get(reverse("demo")).content.decode()
        self.assertNotIn(CHAVE, pagina)
        self.assertNotIn("REGRAS", pagina)

    def test_notas_internas_nao_vazam_para_o_cliente(self):
        self.client.post(reverse("api_enviar"), json.dumps({"texto": "quero falar com um atendente"}), content_type="application/json")
        r = self.client.get(reverse("api_mensagens") + "?depois=0")
        tipos = {m["tipo"] for m in r.json()["mensagens"]}
        self.assertNotIn("nota", tipos)
        self.assertNotIn("Resumo da IA", r.content.decode())

    def test_agradecimento_resolve_pelo_bot_sem_ia(self):
        conv = self.conversa()
        self.fale(conv, "obrigado, valeu!")
        conv.refresh_from_db()
        self.assertEqual(conv.status, "resolvida")
        self.assertTrue(conv.resolvida_pelo_bot)

    def test_cliente_que_volta_reabre_conversa(self):
        conv = self.conversa()
        self.fale(conv, "obrigado, valeu!")
        self.fale(conv, "qual o prazo de entrega?")
        conv.refresh_from_db()
        self.assertEqual(conv.status, "bot")

    def test_avaliacao_csat(self):
        self.client.post(reverse("api_enviar"), json.dumps({"texto": "oi"}), content_type="application/json")
        r = self.client.post(reverse("api_avaliar"), json.dumps({"nota": 5}), content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Conversa.objects.get().csat, 5)
        r = self.client.post(reverse("api_avaliar"), json.dumps({"nota": 9}), content_type="application/json")
        self.assertEqual(r.status_code, 400)
