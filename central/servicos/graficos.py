"""Gráficos SVG próprios (sem bibliotecas). Cores via classes CSS/variáveis para claro/escuro."""
import math

from django.utils.html import escape
from django.utils.safestring import mark_safe


def barras(valores, rotulos, largura=720, altura=220, destaque=None, titulo="Gráfico de barras"):
    n = len(valores)
    mx = max(valores) if valores and max(valores) > 0 else 1
    esq, base, topo = 28, altura - 26, 14
    area_h = base - topo
    passo = (largura - esq - 8) / max(n, 1)
    larg = passo * 0.68
    partes = [f'<svg class="grafico" viewBox="0 0 {largura} {altura}" role="img" aria-label="{escape(titulo)}">']
    for frac in (0, 0.5, 1):
        y = base - area_h * frac
        partes.append(f'<line class="g-grade" x1="{esq}" x2="{largura-4}" y1="{y:.1f}" y2="{y:.1f}"/>')
        partes.append(f'<text class="g-eixo" x="{esq-6}" y="{y+4:.1f}" text-anchor="end">{round(mx*frac)}</text>')
    for i, v in enumerate(valores):
        h = area_h * v / mx
        x = esq + i * passo + (passo - larg) / 2
        cls = "g-barra destaque" if destaque is not None and i == destaque else "g-barra"
        partes.append(
            f'<rect class="{cls}" x="{x:.1f}" y="{base-h:.1f}" width="{larg:.1f}" height="{max(h,0):.1f}" rx="3">'
            f"<title>{escape(str(rotulos[i]))}: {v}</title></rect>"
        )
        if n <= 12 or i % 3 == 0:
            partes.append(f'<text class="g-eixo" x="{x+larg/2:.1f}" y="{altura-8}" text-anchor="middle">{escape(str(rotulos[i]))}</text>')
    partes.append("</svg>")
    return mark_safe("".join(partes))


def rosca(fatias, tamanho=180, titulo="Distribuição"):
    """fatias: [(rotulo, valor, classe_css)]"""
    total = sum(v for _, v, _ in fatias)
    r, c = 70, tamanho / 2
    circ = 2 * math.pi * r
    partes = [f'<svg class="grafico rosca" viewBox="0 0 {tamanho} {tamanho}" role="img" aria-label="{escape(titulo)}">']
    partes.append(f'<circle class="g-trilho" cx="{c}" cy="{c}" r="{r}" fill="none" stroke-width="22"/>')
    off = 0
    for rotulo, v, cls in fatias:
        if total and v:
            comp = circ * v / total
            partes.append(
                f'<circle class="{cls}" cx="{c}" cy="{c}" r="{r}" fill="none" stroke-width="22" '
                f'stroke-dasharray="{comp:.2f} {circ-comp:.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {c} {c})">'
                f"<title>{escape(rotulo)}: {v}</title></circle>"
            )
            off += comp
    partes.append(f'<text class="g-centro" x="{c}" y="{c+4}" text-anchor="middle">{total}</text>')
    partes.append(f'<text class="g-eixo" x="{c}" y="{c+22}" text-anchor="middle">conversas</text></svg>')
    return mark_safe("".join(partes))


def linha(valores, rotulos, largura=720, altura=200, titulo="Série"):
    n = len(valores)
    mx = max(valores) if valores and max(valores) > 0 else 1
    esq, base, topo = 28, altura - 26, 16
    area_h = base - topo
    passo = (largura - esq - 16) / max(n - 1, 1)
    pts = [(esq + i * passo + 4, base - area_h * v / mx) for i, v in enumerate(valores)]
    caminho = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{pts[0][0]:.1f},{base} " + caminho + f" {pts[-1][0]:.1f},{base}"
    p = [f'<svg class="grafico" viewBox="0 0 {largura} {altura}" role="img" aria-label="{escape(titulo)}">']
    for frac in (0, 0.5, 1):
        y = base - area_h * frac
        p.append(f'<line class="g-grade" x1="{esq}" x2="{largura-4}" y1="{y:.1f}" y2="{y:.1f}"/>')
        p.append(f'<text class="g-eixo" x="{esq-6}" y="{y+4:.1f}" text-anchor="end">{round(mx*frac)}</text>')
    p.append(f'<polygon class="g-area" points="{area}"/><polyline class="g-linha" points="{caminho}" fill="none"/>')
    for (x, y), v, rot in zip(pts, valores, rotulos):
        p.append(f'<circle class="g-ponto" cx="{x:.1f}" cy="{y:.1f}" r="4"><title>{escape(str(rot))}: {v}</title></circle>')
        p.append(f'<text class="g-eixo" x="{x:.1f}" y="{altura-8}" text-anchor="middle">{escape(str(rot))}</text>')
    p.append("</svg>")
    return mark_safe("".join(p))
