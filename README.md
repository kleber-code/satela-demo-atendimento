# Aurora Atendimento IA

Central de atendimento omnichannel **simulada**, com IA, para demonstração comercial. A loja é fictícia (Aurora Casa & Tech) e todos os dados são inventados. Feita em Django 5 para rodar na plataforma Satela.

O que o visitante e o atendente enxergam:

- **Chat do cliente** em `/demo/`: o visitante conversa como se fosse um cliente; a mensagem chega na caixa de entrada do atendente em segundos.
- **Caixa de entrada** em `/caixa/` (estilo WhatsApp): status (bot, aguardando humano, em atendimento, resolvida), etiquetas, atribuição a atendentes, notas internas, busca, filtros, respostas rápidas (`/atalho`), SLA e não lidas.
- **Bot com IA** (API da Satela AI, compatível com OpenAI) que responde com base na **base de conhecimento**, cita a fonte e usa **ações**: consultar pedido, agendar retirada/visita e abrir chamado. As ações aparecem na conversa ("IA usou uma ação"). Se não sabe ou o cliente pede, **transfere para um humano com resumo gerado pela IA** (nota interna).
- **Métricas** em `/metricas/`: 1ª resposta (bot e humano), % resolvido pelo bot, contenção, volume por hora e por dia, status, CSAT, SLA, ações da IA. Gráficos em SVG/CSS próprios, sem CDN.
- **Treinar o bot** em `/treinar/`: persona/instruções e lista das conversas em que o bot falhou, com atalho para criar o artigo que faltava.
- Base de conhecimento, respostas rápidas, pedidos/agendamentos/chamados, horário de atendimento e configurações.

## Como rodar localmente

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export DEBUG=1
python manage.py migrate
python manage.py seed_demo          # ~40 conversas, equipe, base de conhecimento (idempotente)
python manage.py runserver
```

Abra `http://127.0.0.1:8000/`. No painel, use **Entrar como supervisora** ou **Entrar como atendente** (um clique, sem senha, só com `DEMO_MODE=1`).

Sem `SATELA_API_KEY` tudo funciona: o bot cai em respostas pré-definidas (busca na base, consulta de pedido por número e transferência para humano). Para usar a IA de verdade:

```bash
export SATELA_API_KEY=...   # em produção a plataforma injeta SATELA_API_URL e SATELA_API_KEY
```

Testes (nunca chamam a API real; o httpx é mockado e qualquer chamada não prevista derruba o teste):

```bash
python manage.py test
python manage.py check --deploy
```

Comandos úteis: `seed_demo --reset` (recria tudo), `seed_demo --se-vazio` (usado no release), `indexar_kb` (gera embeddings dos artigos; opcional).

## Variáveis de ambiente

| Variável | Padrão | Para quê |
|---|---|---|
| `DJANGO_SECRET_KEY` | derivada de forma estável | Chave do Django (defina em produção) |
| `DEBUG` | `0` | Modo debug |
| `DJANGO_ALLOWED_HOSTS` | `.satela.com.br,localhost,127.0.0.1,[::1]` | Hosts aceitos (CSV) |
| `CSRF_TRUSTED_ORIGINS` | derivado dos hosts | Origens extras (CSV) |
| `DATABASE_URL` | sqlite local (`/data` se existir) | Postgres em produção |
| `DEMO_MODE` | `1` | Login com um clique e faixa "Ambiente de demonstração" |
| `DEMO_ADMIN_PASSWORD` | vazio | Cria o superusuário `admin` só se definida |
| `SATELA_API_URL` | `https://api.satela.com.br` | Base da API de IA |
| `SATELA_API_KEY` | vazio | Chave da IA (vazio = fallback) |
| `SATELA_MODEL` | `AC310` | Modelo de chat |
| `SATELA_EMBED_MODEL` / `KB_EMBEDDINGS` | `EMB100` / `0` | Embeddings opcionais na busca |
| `IA_STREAM` | `0` | Usa `stream` na API (acumula os pedaços) |
| `IA_TIMEOUT` / `IA_MAX_TOKENS` | `25` / `500` | Timeout e tamanho da resposta |
| `LIMITE_IP_POR_MINUTO` / `LIMITE_IP_POR_DIA` | `12` / `150` | Mensagens por IP |
| `LIMITE_SESSAO_POR_MINUTO` / `LIMITE_SESSAO_POR_DIA` | `6` / `60` | Mensagens por sessão |
| `TETO_IA_DIARIO` | `300` | Teto global de chamadas à IA por dia |
| `MENSAGEM_MAX_CHARS` | `1000` | Tamanho máximo da mensagem do cliente |
| `HISTORICO_MAX_MENSAGENS` | `12` | Mensagens de histórico enviadas à IA |
| `PROXY_HOPS` | `1` | Proxies confiáveis à frente do app (para o IP real) |
| `COOKIES_SEGUROS`, `FORCAR_HTTPS`, `HSTS_SEGUNDOS` | seguro fora do debug / `0` / `3600` | Endurecimento de cookies e HTTPS |

O proxy da plataforma é reconhecido por `SECURE_PROXY_SSL_HEADER` (`X-Forwarded-Proto`). Mídia fica em `/data/media` se `/data` existir.

## Custo e limites

A demonstração é pública e a IA custa dinheiro, então há várias camadas (tabela `EventoUso`, compartilhada entre workers):

1. Limite de mensagens por **IP** e por **sessão**, por minuto e por dia (IP guardado só como hash).
2. **Teto global diário** de chamadas à IA (`TETO_IA_DIARIO`, padrão 300). Cada rodada com a IA, resumo de transferência e embedding conta 1.
3. Mensagem com no máximo 1000 caracteres e histórico limitado a 12 mensagens enviado à IA.
4. Atalhos que **não gastam IA**: saudação, agradecimento (encerra e conta como resolvido pelo bot) e pedido explícito de humano.
5. **Fallback educado** quando a IA está sem chave, fora do ar, lenta ou acima do teto: busca na base e cita a fonte, consulta pedido por número, ou transfere para humano. Essas mensagens ganham o selo "pré-definida" na caixa de entrada.
6. A chave e o prompt interno nunca vão ao navegador; notas internas e resumos não são expostos ao widget (há teste para isso).

Em `/configuracoes/` o supervisor vê o consumo do dia e os limites ativos.

## Roteiro de demonstração de 2 minutos

1. (0:00) Abra `/` e clique em **Conversar como cliente**. Pergunte: "Qual o prazo de entrega para o interior?" e mostre a resposta com a **fonte** citada.
2. (0:20) Pergunte "Onde está meu pedido AUR-10421?": aparece o chip **"IA usou uma ação · Consultou pedido"**.
3. (0:40) Diga "Quero agendar a retirada do pedido na loja" e combine data e período; o bot agenda sozinho.
4. (0:55) Escreva "Tem cupom de primeira compra?" (o bot não sabe) ou "Quero falar com um atendente": ele **transfere para humano**.
5. (1:05) Em outra aba, **Abrir caixa de entrada** > supervisora. Mostre sua conversa em "Aguardando humano" com o **resumo da IA**; clique em Assumir e responda usando `/prazo`. No chat do cliente, a resposta chega em tempo real.
6. (1:25) Adicione uma **nota interna** e uma etiqueta; mostre busca e filtros.
7. (1:40) Abra **Métricas**: % resolvido pelo bot, 1ª resposta, volume por hora, CSAT.
8. (1:50) Abra **Treinar o bot**: as conversas em que ele falhou viram artigo com um clique. Feche mostrando a proteção de custo em Configurações.

## Arquitetura

```
config/                 settings, urls, wsgi
central/
  models.py             Conversa, Mensagem, Artigo, Pedido, Configuracao...
  servicos/
    ia.py               cliente httpx da Satela AI (chat, tools, stream, embeddings)
    bot.py              prompt, laço de tools, fallback, transferência
    kb.py               busca por palavras (+ embeddings opcionais)
    acoes.py            tools: consultar_pedido, agendar, abrir_chamado, transferir_humano
    limites.py          limites por IP/sessão e teto diário de IA
    atendimento.py      ciclo de vida da conversa (independe do canal)
    metricas.py, graficos.py
  canais/               interface de canais (web funciona; WhatsApp é um esqueleto)
  views_publico.py      landing, login, widget /demo/ e sua API
  views_painel.py       caixa de entrada, métricas, base, treino, config
```

Tempo real: **polling curto** (2 s no widget e na conversa aberta, 5 s na lista). Foi escolhido por ser o mais robusto atrás de gunicorn com `gthread`: sem conexão longa presa a um worker. A resposta do bot é gerada na própria requisição do POST (timeout de 25 s, uma thread).

## Plugando o WhatsApp (Hub da Satela)

Não está implementado, mas o encaixe é pequeno porque todo o núcleo trabalha com a interface de `central/canais/base.py`:

```python
class Canal:
    def receber(self, payload) -> EntradaMensagem   # webhook do Hub -> mensagem normalizada
    def enviar(self, conversa, mensagem) -> None    # entrega bot/atendente ao cliente
    def verificar_assinatura(self, request) -> bool # autenticidade do webhook
```

Passos:

1. Implementar `CanalWhatsApp` (`canais/whatsapp.py`): `receber` converte o evento do Hub em `EntradaMensagem(canal="whatsapp", identificador=<telefone>, texto=..., nome=...)`; `enviar` chama a API de envio do Hub com o texto (e, se quiser, as fontes).
2. Criar uma view `POST /canais/whatsapp/webhook/` (csrf_exempt) que chama `verificar_assinatura`, depois `receber`, e então `servicos.atendimento.processar_entrada(entrada)`. Ela localiza (ou cria) a conversa pelo `identificador` e aciona o mesmo bot, a mesma base, os mesmos limites e a mesma caixa de entrada.
3. `atendimento.adicionar_mensagem` já chama `canais.obter(conversa.canal).enviar(...)` para toda mensagem do bot ou do atendente, então as respostas voltam pelo WhatsApp sem mudar o painel.
4. Guardar o token do Hub em variável de ambiente (nunca no código) e aplicar os mesmos limites por contato.

No seed, algumas conversas aparecem com o selo `WA` apenas para ilustrar o painel omnichannel.

## Deploy na Satela

`Dockerfile` (python:3.12-slim, usuário não root, `collectstatic` no build, escuta `$PORT`), `Procfile` (release: migrate + `seed_demo --se-vazio`; web: gunicorn com 2 workers gthread) e arquivo `ENV` com `HEALTHCHECK_PATH=/saude/`. `GET /saude/` responde `200 ok` sem login.

## Limitações honestas

- É uma simulação: não há integração real com WhatsApp, e-mail ou ERP. Pedidos, agendamentos e chamados são tabelas fictícias; a consulta de pedido não valida identidade (um sistema real deveria).
- A qualidade das respostas depende do modelo e dos artigos. Sem chave de IA o bot é bem mais limitado (busca por palavras).
- O teto de IA e os limites usam contagem no banco; sob concorrência altíssima pode haver pequeno excesso.
- Polling gera requisições frequentes; para milhares de atendentes simultâneos seria melhor SSE/WebSocket.
- O CSAT da demo mistura dados de exemplo e avaliações dos visitantes.
