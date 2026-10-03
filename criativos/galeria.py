"""Monta um index.html comparando as versões lado a lado."""

import html
from pathlib import Path

from .providers.opus import DIMENSOES

TITULOS = {
    "chatgpt": "ChatGPT · imagem",
    "gemini": "Gemini · imagem",
    "flow": "Flow (Veo) · vídeo",
    "opus": "Opus 5.5 · peça em HTML",
}


def _midia(nome: str, arquivo: Path, formato: str) -> str:
    src = html.escape(arquivo.name)
    if arquivo.suffix == ".mp4":
        return f'<video src="{src}" controls loop playsinline></video>'
    if arquivo.suffix == ".html":
        largura, altura = DIMENSOES[formato]
        escala = 360 / largura
        return (
            f'<div class="moldura" style="height:{altura * escala:.0f}px">'
            f'<iframe src="{src}" style="width:{largura}px;height:{altura}px;transform:scale({escala})"></iframe>'
            f"</div>"
        )
    return f'<img src="{src}" alt="{html.escape(nome)}">'


def montar(pasta: Path, ideia: str, formato: str, briefing: dict, resultados: dict) -> Path:
    cards = []
    for nome, resultado in resultados.items():
        titulo = html.escape(TITULOS.get(nome, nome))
        if isinstance(resultado, Path):
            corpo = _midia(nome, resultado, formato)
            link = f'<a href="{html.escape(resultado.name)}" download>baixar</a>'
        else:
            corpo = f'<p class="erro">{html.escape(str(resultado))}</p>'
            link = ""
        cards.append(f'<article><h2>{titulo}</h2>{corpo}{link}</article>')

    copy = "".join(
        f"<dt>{rotulo}</dt><dd>{html.escape(briefing.get(chave, ''))}</dd>"
        for chave, rotulo in [
            ("conceito", "Conceito"),
            ("headline", "Headline"),
            ("texto_apoio", "Texto de apoio"),
            ("cta", "CTA"),
            ("legenda", "Legenda"),
        ]
        if briefing.get(chave)
    )

    pagina = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Criativos</title>
<style>
  :root {{ --bg:#f6f6f4; --card:#fff; --tx:#1b1b1b; --mut:#666; --err:#b3261e; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg:#141414; --card:#1f1f1f; --tx:#eee; --mut:#999; --err:#f2b8b5; }} }}
  body {{ margin:0; padding:24px 16px; background:var(--bg); color:var(--tx); font:15px/1.5 system-ui,sans-serif; }}
  header, main {{ max-width:1600px; margin:0 auto; }}
  h1 {{ font-size:22px; margin:0 0 4px; }}
  .ideia {{ color:var(--mut); margin:0 0 16px; }}
  dl {{ display:grid; grid-template-columns:max-content 1fr; gap:4px 16px; margin:0 0 24px; }}
  dt {{ font-weight:600; }} dd {{ margin:0; white-space:pre-wrap; }}
  main {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(360px,1fr)); gap:16px; }}
  article {{ background:var(--card); border-radius:12px; padding:16px; }}
  h2 {{ font-size:16px; margin:0 0 12px; }}
  img, video {{ width:100%; border-radius:8px; display:block; }}
  .moldura {{ width:360px; max-width:100%; overflow:hidden; border-radius:8px; }}
  iframe {{ border:0; transform-origin:0 0; }}
  .erro {{ color:var(--err); }}
  a {{ display:inline-block; margin-top:8px; color:inherit; }}
</style></head><body>
<header><h1>Criativos gerados</h1><p class="ideia">Ideia: {html.escape(ideia)} · formato {formato}</p><dl>{copy}</dl></header>
<main>{''.join(cards)}</main>
</body></html>"""
    arquivo = pasta / "index.html"
    arquivo.write_text(pagina, encoding="utf-8")
    return arquivo
