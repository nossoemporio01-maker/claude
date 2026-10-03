"""Opus 5.5: o Claude não gera imagem em pixels, então ele entrega a peça
como HTML/CSS/SVG autocontido, no tamanho do formato, pronto para print/screenshot."""

import re
from pathlib import Path

import anthropic

from .. import config

DIMENSOES = {"1:1": (1080, 1080), "4:5": (1080, 1350), "9:16": (1080, 1920), "16:9": (1920, 1080)}

SYSTEM = """Você é um designer de anúncios de alta conversão.
Crie a peça como UM arquivo HTML autocontido (CSS inline, ilustrações em SVG inline, sem imagens externas;
Google Fonts é permitido). O <body> deve ter exatamente o tamanho pedido, sem margem nem rolagem.
Hierarquia forte, contraste alto, CTA visível. Responda só com o HTML, sem explicações."""


def gerar(briefing: dict, formato: str, pasta: Path) -> Path:
    largura, altura = DIMENSOES[formato]
    pedido = (
        f"Tamanho: {largura}x{altura}px\n"
        f"Conceito: {briefing['conceito']}\n"
        f"Headline: {briefing['headline']}\n"
        f"Texto de apoio: {briefing['texto_apoio']}\n"
        f"CTA: {briefing['cta']}"
    )

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=config.CLAUDE_MODEL,
        max_tokens=32000,
        system=SYSTEM,
        messages=[{"role": "user", "content": pedido}],
    ) as stream:
        mensagem = stream.get_final_message()

    html = "".join(b.text for b in mensagem.content if b.type == "text")
    html = re.sub(r"^```(?:html)?\s*|\s*```$", "", html.strip())
    arquivo = pasta / "opus.html"
    arquivo.write_text(html, encoding="utf-8")
    return arquivo
