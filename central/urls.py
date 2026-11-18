from django.urls import path

from . import views_publico as pub
from . import views_painel as pn

urlpatterns = [
    path("", pub.landing, name="landing"),
    path("saude/", pub.saude, name="saude"),
    path("entrar/", pub.entrar, name="entrar"),
    path("entrar/demo/<str:papel>/", pub.entrar_demo, name="entrar_demo"),
    path("sair/", pub.sair, name="sair"),
    # widget de demonstração (cliente)
    path("demo/", pub.demo, name="demo"),
    path("demo/api/enviar/", pub.api_enviar, name="api_enviar"),
    path("demo/api/mensagens/", pub.api_mensagens, name="api_mensagens"),
    path("demo/api/avaliar/", pub.api_avaliar, name="api_avaliar"),
    path("demo/api/encerrar/", pub.api_encerrar, name="api_encerrar"),
    path("demo/api/nova/", pub.api_nova, name="api_nova"),
    # painel
    path("caixa/", pn.caixa, name="caixa"),
    path("caixa/lista/", pn.caixa_lista, name="caixa_lista"),
    path("caixa/<int:pk>/", pn.conversa_painel, name="conversa"),
    path("caixa/<int:pk>/mensagens/", pn.conversa_mensagens, name="conversa_mensagens"),
    path("caixa/<int:pk>/enviar/", pn.conversa_enviar, name="conversa_enviar"),
    path("caixa/<int:pk>/acao/", pn.conversa_acao, name="conversa_acao"),
    path("metricas/", pn.metricas, name="metricas"),
    path("conhecimento/", pn.conhecimento, name="conhecimento"),
    path("conhecimento/novo/", pn.artigo_form, name="artigo_novo"),
    path("conhecimento/<int:pk>/", pn.artigo_form, name="artigo_editar"),
    path("conhecimento/<int:pk>/excluir/", pn.artigo_excluir, name="artigo_excluir"),
    path("treinar/", pn.treinar, name="treinar"),
    path("respostas/", pn.respostas, name="respostas"),
    path("configuracoes/", pn.configuracoes, name="configuracoes"),
    path("operacoes/", pn.operacoes, name="operacoes"),
]
