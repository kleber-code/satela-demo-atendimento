from central.models import Artigo
from central.servicos import kb

from .base import BaseTest


class BaseConhecimentoTest(BaseTest):
    def test_busca_ignora_acentos_e_caixa(self):
        r = kb.buscar("QUAL O PRAZO DE ENTREGA NO INTERIOR")
        self.assertEqual(r[0][0], self.artigo)
        self.assertGreaterEqual(r[0][1], kb.LIMIAR_CONFIANCA)

    def test_artigo_inativo_nao_aparece(self):
        self.artigo.ativo = False
        self.artigo.save()
        self.assertEqual(kb.buscar("prazo de entrega"), [])

    def test_pergunta_sem_relacao_nao_e_confiante(self):
        r = kb.buscar("vocês vendem tatuagem?")
        self.assertTrue(not r or r[0][1] < kb.LIMIAR_CONFIANCA)

    def test_cobertura_baixa_nunca_e_confiante(self):
        r = kb.buscar("tem cupom de entrega?")  # só 'entrega' casa; 'cupom' não existe na base
        self.assertTrue(all(s < kb.LIMIAR_CONFIANCA for _, s in r))

    def test_trecho_relevante_pega_o_paragrafo_certo(self):
        a = Artigo.objects.create(titulo="T", conteudo="Primeiro parágrafo sobre loja.\nSegundo sobre garantia de 12 meses.")
        self.assertIn("garantia", kb.trecho_relevante(a, "qual a garantia"))

    def test_embeddings_indisponiveis_voltam_para_texto(self):
        from django.test import override_settings

        with override_settings(KB_EMBEDDINGS=True, SATELA_API_KEY="k"):
            self.artigo.embedding = [0.1, 0.2]
            self.artigo.save()
            from central.servicos import ia
            import httpx

            ia._transport = httpx.MockTransport(lambda r: httpx.Response(500))
            r = kb.buscar("prazo de entrega interior")
            self.assertEqual(r[0][0], self.artigo)

    def test_embeddings_reordenam_quando_disponiveis(self):
        from django.test import override_settings
        import httpx
        from central.servicos import ia

        outro = Artigo.objects.create(titulo="Outro", conteudo="algo sem relação", embedding=[0.0, 1.0])
        self.artigo.embedding = [1.0, 0.0]
        self.artigo.save()
        ia._transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"data": [{"index": 0, "embedding": [1.0, 0.0]}]}))
        with override_settings(KB_EMBEDDINGS=True, SATELA_API_KEY="k"):
            r = kb.buscar("entrega rápida")
        self.assertEqual(r[0][0], self.artigo)
