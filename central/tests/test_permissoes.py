from io import StringIO
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from central.models import Artigo, Configuracao, Conversa, Perfil
from central.servicos import atendimento, demo

from .base import BaseTest

ROTAS_PROTEGIDAS = ["caixa", "caixa_lista", "metricas", "conhecimento", "treinar", "respostas", "configuracoes", "operacoes"]


class PermissoesTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.sup = demo.usuario_demo("supervisor")
        self.ate = demo.usuario_demo("atendente")
        self.outra = demo.garantir_usuario("camila", "Camila", "atendente", "#000000")
        self.conv = atendimento.nova_conversa("Cliente")
        atendimento.registrar_mensagem_cliente(self.conv, "oi")

    def test_rotas_do_painel_exigem_login(self):
        for nome in ROTAS_PROTEGIDAS:
            r = self.client.get(reverse(nome))
            self.assertEqual(r.status_code, 302, nome)
            self.assertIn("/entrar/", r["Location"])
        self.assertEqual(self.client.get(reverse("conversa", args=[self.conv.pk])).status_code, 302)
        self.assertEqual(self.client.post(reverse("conversa_enviar", args=[self.conv.pk]), {"texto": "x"}).status_code, 302)

    def test_rotas_publicas_abrem_sem_login(self):
        for nome in ["landing", "demo", "entrar", "saude"]:
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200, nome)

    def test_saude_retorna_ok(self):
        r = self.client.get("/saude/")
        self.assertEqual((r.status_code, r.content), (200, b"ok"))

    def test_painel_abre_logado(self):
        self.client.force_login(self.ate)
        for nome in ROTAS_PROTEGIDAS:
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200, nome)
        self.assertEqual(self.client.get(reverse("caixa") + f"?c={self.conv.pk}").status_code, 200)

    def test_atendente_nao_edita_base_nem_persona_nem_config(self):
        self.client.force_login(self.ate)
        self.assertEqual(self.client.get(reverse("artigo_novo")).status_code, 403)
        self.assertEqual(self.client.post(reverse("artigo_excluir", args=[self.artigo.pk])).status_code, 403)
        self.assertTrue(Artigo.objects.filter(pk=self.artigo.pk).exists())
        r = self.client.post(reverse("treinar"), {"nome_bot": "Hack", "instrucoes": "x", "msg_boas_vindas": "x"})
        self.assertEqual(r.status_code, 403)
        self.assertNotEqual(Configuracao.carregar().nome_bot, "Hack")
        self.assertEqual(self.client.post(reverse("configuracoes"), {}).status_code, 403)

    def test_supervisor_edita_artigo_e_persona(self):
        self.client.force_login(self.sup)
        r = self.client.post(reverse("artigo_editar", args=[self.artigo.pk]), {
            "titulo": "Prazos", "categoria": "Entrega", "palavras_chave": "prazo", "conteudo": "Novo texto", "ativo": "on"})
        self.assertEqual(r.status_code, 302)
        self.artigo.refresh_from_db()
        self.assertEqual(self.artigo.conteudo, "Novo texto")
        r = self.client.post(reverse("treinar"), {"nome_bot": "Luz", "instrucoes": "Seja breve.", "msg_boas_vindas": "Oi!", "bot_ativo": "on"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Configuracao.carregar().nome_bot, "Luz")

    def test_atendente_nao_age_em_conversa_de_outro(self):
        self.conv.atribuido = self.outra; self.conv.status = "atendimento"; self.conv.save()
        self.client.force_login(self.ate)
        r = self.client.post(reverse("conversa_enviar", args=[self.conv.pk]), {"texto": "intrometido"})
        self.assertEqual(r.status_code, 403)
        r = self.client.post(reverse("conversa_acao", args=[self.conv.pk]), {"acao": "resolver"})
        self.assertEqual(r.status_code, 403)
        self.assertFalse(self.conv.mensagens.filter(tipo="atendente").exists())
        # supervisor pode
        self.client.force_login(self.sup)
        self.assertEqual(self.client.post(reverse("conversa_enviar", args=[self.conv.pk]), {"texto": "ok"}).status_code, 200)

    def test_atendente_assume_responde_nota_e_resolve(self):
        self.client.force_login(self.ate)
        url = reverse("conversa_acao", args=[self.conv.pk])
        self.assertTrue(self.client.post(url, {"acao": "assumir"}).json()["ok"])
        self.conv.refresh_from_db()
        self.assertEqual((self.conv.status, self.conv.atribuido), ("atendimento", self.ate))
        self.client.post(reverse("conversa_enviar", args=[self.conv.pk]), {"texto": "Olá! Posso ajudar?"})
        self.client.post(reverse("conversa_enviar", args=[self.conv.pk]), {"texto": "cliente VIP", "tipo": "nota"})
        self.assertEqual(self.conv.mensagens.filter(tipo="atendente").count(), 1)
        self.assertEqual(self.conv.mensagens.filter(tipo="nota").count(), 1)
        self.conv.refresh_from_db()
        self.assertIsNotNone(self.conv.primeira_resposta_humana_em)
        # o cliente (widget) vê a resposta mas não a nota
        self.client.post(url, {"acao": "resolver"})
        self.conv.refresh_from_db()
        self.assertEqual(self.conv.status, "resolvida")

    def test_busca_e_filtros_da_caixa(self):
        self.client.force_login(self.ate)
        r = self.client.get(reverse("caixa_lista"), {"q": self.conv.protocolo})
        self.assertContains(r, "Cliente")
        r = self.client.get(reverse("caixa_lista"), {"status": "resolvida"})
        self.assertNotContains(r, self.conv.protocolo if False else 'data-id="%d"' % self.conv.pk)

    @override_settings(DEMO_MODE=True)
    def test_entrada_demo_com_um_clique(self):
        r = self.client.post(reverse("entrar_demo", args=["atendente"]))
        self.assertRedirects(r, reverse("caixa"))
        self.assertEqual(self.client.get(reverse("caixa")).status_code, 200)
        self.assertContains(self.client.get(reverse("caixa")), "Ambiente de demonstração")
        self.assertEqual(self.client.post(reverse("entrar_demo", args=["root"])).status_code, 404)

    @override_settings(DEMO_MODE=False)
    def test_sem_modo_demo_nao_ha_entrada_com_um_clique(self):
        self.assertEqual(self.client.post(reverse("entrar_demo", args=["atendente"])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("landing")), "Ambiente de demonstração")

    def test_usuarios_demo_nao_tem_senha(self):
        self.assertFalse(self.sup.has_usable_password())

    @override_settings(DEMO_ADMIN_PASSWORD="")
    def test_superusuario_so_existe_com_senha_definida(self):
        call_command("seed_demo", "--reset", stdout=StringIO())
        self.assertFalse(User.objects.filter(is_superuser=True).exists())

    @override_settings(DEMO_ADMIN_PASSWORD="uma-senha-forte-123")
    def test_superusuario_criado_com_senha(self):
        call_command("seed_demo", "--reset", stdout=StringIO())
        admin = User.objects.get(username="admin")
        self.assertTrue(admin.is_superuser and admin.check_password("uma-senha-forte-123"))
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("treinar")).status_code, 200)

    def test_widget_so_enxerga_a_propria_conversa(self):
        outra = atendimento.nova_conversa("Outro", sessao_chave="alheia")
        atendimento.registrar_mensagem_cliente(outra, "segredo alheio")
        r = self.client.get(reverse("api_mensagens") + "?depois=0")
        self.assertEqual(r.json()["mensagens"], [])


class SeedTest(BaseTest):
    def test_seed_e_idempotente_e_rico(self):
        call_command("seed_demo", stdout=StringIO())
        n = Conversa.objects.count()
        self.assertEqual(n, 40)
        call_command("seed_demo", stdout=StringIO())
        call_command("seed_demo", "--se-vazio", stdout=StringIO())
        self.assertEqual(Conversa.objects.count(), n)
        self.assertEqual(Artigo.objects.filter(titulo="Troca e devolução").count(), 1)
        statuses = set(Conversa.objects.values_list("status", flat=True))
        self.assertEqual(statuses, {"bot", "aguardando", "atendimento", "resolvida"})
        call_command("seed_demo", "--reset", stdout=StringIO())
        self.assertEqual(Conversa.objects.count(), 40)

    def test_metricas_e_telas_com_dados_do_seed(self):
        call_command("seed_demo", stdout=StringIO())
        self.client.force_login(demo.usuario_demo("supervisor"))
        r = self.client.get(reverse("metricas"))
        self.assertContains(r, "<svg")
        self.assertContains(r, "Resolvido pelo bot")
        for c in Conversa.objects.all()[:10]:
            self.assertEqual(self.client.get(reverse("caixa") + f"?c={c.pk}").status_code, 200)
        self.assertContains(self.client.get(reverse("treinar")), "Conversas em que o bot falhou")
