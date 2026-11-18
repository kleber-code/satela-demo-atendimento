"""Base de conhecimento: busca por palavras (sempre disponível) + embeddings (opcional)."""
import math
import re
import unicodedata

from django.conf import settings

from ..models import Artigo
from . import ia, limites

STOP = set(
    "a o as os um uma uns umas de do da dos das em no na nos nas por para com sem sobre que e ou "
    "se eu voce vcs voces meu minha meus minhas seu sua quero queria gostaria preciso saber como "
    "qual quais quanto quando onde posso pode podem tem ter foi ser sao esta estou isso essa esse "
    "mais muito ja nao sim oi ola bom boa dia tarde noite favor obrigado obrigada mim me te".split()
)
LIMIAR_CONFIANCA = 3.0


def normalizar(txt):
    txt = unicodedata.normalize("NFD", txt.lower())
    return "".join(c for c in txt if unicodedata.category(c) != "Mn")


def _radical(p):
    return p[:5] if len(p) > 5 else p


def tokens(txt):
    return {_radical(t) for t in re.findall(r"[a-z0-9]+", normalizar(txt)) if len(t) >= 3 and t not in STOP}


def _pontuar(consulta_tokens, artigo):
    if not consulta_tokens:
        return 0.0
    t_titulo = tokens(artigo.titulo)
    t_chaves = tokens(artigo.palavras_chave.replace(",", " "))
    t_corpo = tokens(artigo.conteudo)
    s = 0.0
    for t in consulta_tokens:
        if t in t_titulo:
            s += 3
        if t in t_chaves:
            s += 3
        if t in t_corpo:
            s += 1
    return s


def _cobertura(consulta_tokens, artigo):
    """Fração dos termos da pergunta que aparecem em algum lugar do artigo."""
    if not consulta_tokens:
        return 0.0
    alvo = tokens(artigo.titulo) | tokens(artigo.palavras_chave.replace(",", " ")) | tokens(artigo.conteudo)
    return len(consulta_tokens & alvo) / len(consulta_tokens)


def buscar_texto(consulta, k=3):
    q = tokens(consulta)
    pontos = []
    for a in Artigo.objects.filter(ativo=True):
        s = _pontuar(q, a)
        if s > 0 and _cobertura(q, a) <= 0.5:
            s = min(s, LIMIAR_CONFIANCA - 0.5)  # cobre pouco da pergunta: nunca "confiante"
        pontos.append((a, s))
    pontos = [(a, s) for a, s in pontos if s > 0]
    pontos.sort(key=lambda x: -x[1])
    return pontos[:k]


def _cos(a, b):
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


def buscar_semantica(consulta, k=3):
    artigos = list(Artigo.objects.filter(ativo=True).exclude(embedding=None))
    if not artigos or not limites.consumir_ia():
        return None
    try:
        q = ia.embeddings([consulta])[0]
    except ia.IAIndisponivel:
        return None
    ranking = sorted(((a, _cos(q, a.embedding)) for a in artigos), key=lambda x: -x[1])
    return [(a, s) for a, s in ranking[:k] if s > 0.25]


def buscar(consulta, k=3):
    """Retorna [(artigo, pontuacao)]. Usa embeddings se habilitados e disponíveis; senão texto.

    A pontuação devolvida é sempre a textual (comparável ao LIMIAR_CONFIANCA); os embeddings
    apenas reordenam/complementam os candidatos.
    """
    texto = buscar_texto(consulta, k)
    if settings.KB_EMBEDDINGS and ia.configurada():
        sem = buscar_semantica(consulta, k)
        if sem:
            q = tokens(consulta)
            sem_ids = {a.pk for a, _ in sem}
            vistos, saida = set(), []
            for a, _ in sem + texto:
                if a.pk in vistos:
                    continue
                vistos.add(a.pk)
                pont = _pontuar(q, a)
                saida.append((a, max(pont, LIMIAR_CONFIANCA) if a.pk in sem_ids else pont))
            return saida[:k]
    return texto


def indexar_embeddings():
    artigos = list(Artigo.objects.filter(ativo=True))
    vetores = ia.embeddings([f"{a.titulo}\n{a.conteudo}" for a in artigos])
    for a, v in zip(artigos, vetores):
        a.embedding = v
        a.save(update_fields=["embedding"])
    return len(artigos)


def trecho_relevante(artigo, consulta, limite=520):
    """Os parágrafos do artigo que mais combinam com a consulta (usado no fallback sem IA)."""
    q = tokens(consulta)
    paragrafos = [p.strip() for p in re.split(r"\n+", artigo.conteudo) if p.strip()]
    if not paragrafos:
        return ""
    ranking = sorted(range(len(paragrafos)), key=lambda i: (-len(q & tokens(paragrafos[i])), i))
    escolhidos, total = [], 0
    for i in ranking:
        if len(q & tokens(paragrafos[i])) == 0 and escolhidos:
            break
        if escolhidos and total + len(paragrafos[i]) > limite:
            continue
        escolhidos.append(i)
        total += len(paragrafos[i])
        if len(escolhidos) == 2:
            break
    texto = "\n".join(paragrafos[i] for i in sorted(escolhidos))
    return texto if len(texto) <= limite + 80 else texto[:limite].rsplit(" ", 1)[0] + "…"
