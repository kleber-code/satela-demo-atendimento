import json

from django.test import RequestFactory, override_settings
from django.urls import reverse

from central.models import Conversa, EventoUso
from central.servicos import limites

from .base import BaseTest, com_chave


class LimitesTest(BaseTest):
    def post(self, texto="oi", ip="1.2.3.4", client=None):
        c = client or self.client
        return c.post(reverse("api_enviar"), json.dumps({"texto": texto}), content_type="application/json", REMOTE_ADDR=ip)

    @override_settings(LIMITE_SESSAO_POR_MINUTO=3, LIMITE_IP_POR_MINUTO=100)
    def test_limite_por_sessao_por_minuto(self):
        for _ in range(3):
            self.assertEqual(self.post().status_code, 200)
        r = self.post()
        self.assertEqual(r.status_code, 429)
        self.assertIn("rápido demais", r.json()["erro"])

    @override_settings(LIMITE_IP_POR_MINUTO=2, LIMITE_SESSAO_POR_MINUTO=100)
    def test_limite_por_ip_vale_entre_sessoes(self):
        from django.test import Client

        for _ in range(2):
            self.assertEqual(self.post(client=Client()).status_code, 200)
        self.assertEqual(self.post(client=Client()).status_code, 429)
        # outro IP continua liberado
        self.assertEqual(self.post(ip="9.9.9.9", client=Client()).status_code, 200)

    @override_settings(LIMITE_SESSAO_POR_DIA=2, LIMITE_SESSAO_POR_MINUTO=100, LIMITE_IP_POR_MINUTO=100)
    def test_limite_diario_por_sessao(self):
        self.post(); self.post()
        r = self.post()
        self.assertEqual(r.status_code, 429)
        self.assertIn("limite diário", r.json()["erro"])

    @override_settings(MENSAGEM_MAX_CHARS=1000)
    def test_mensagem_longa_e_vazia_sao_rejeitadas(self):
        self.assertEqual(self.post("x" * 1001).status_code, 400)
        self.assertEqual(self.post("   ").status_code, 400)
        self.assertEqual(Conversa.objects.count(), 0)

    @override_settings(TETO_IA_DIARIO=2)
    def test_teto_global_diario_de_ia(self):
        self.assertTrue(limites.consumir_ia())
        self.assertTrue(limites.consumir_ia())
        self.assertFalse(limites.consumir_ia())
        self.assertEqual(limites.ia_restante(), 0)
        self.assertEqual(EventoUso.objects.filter(tipo="ia").count(), 2)

    @com_chave
    @override_settings(TETO_IA_DIARIO=0)
    def test_acima_do_teto_nao_chama_a_ia_e_usa_fallback(self):
        r = self.post("Qual o prazo de entrega para o interior?")
        self.assertEqual(r.status_code, 200)
        bot = [m for m in r.json()["mensagens"] if m["tipo"] == "bot"][-1]
        self.assertTrue(bot["fallback"])
        self.assertEqual(self.chamadas, [])  # nenhuma chamada foi feita (transport guarda bloquearia)

    @override_settings(PROXY_HOPS=1)
    def test_ip_considera_apenas_proxy_confiavel(self):
        req = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="6.6.6.6, 10.0.0.9", REMOTE_ADDR="127.0.0.1")
        self.assertEqual(limites.ip_cliente(req), "10.0.0.9")  # o IP forjado pelo cliente é ignorado

    def test_ip_e_guardado_apenas_como_hash(self):
        self.post(ip="203.0.113.7")
        self.assertFalse(EventoUso.objects.filter(chave__contains="203.0.113.7").exists())
