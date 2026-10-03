"""Opus 5.5 como diretor criativo: transforma a ideia crua num briefing
e num prompt otimizado para cada ferramenta."""

import json

import anthropic

from . import config

SCHEMA = {
    "type": "object",
    "properties": {
        "conceito": {"type": "string", "description": "Big idea do criativo em 1-2 frases"},
        "headline": {"type": "string"},
        "texto_apoio": {"type": "string"},
        "cta": {"type": "string"},
        "legenda": {"type": "string", "description": "Legenda pronta para o post, com hashtags"},
        "prompt_chatgpt": {"type": "string", "description": "Prompt em inglês para gerar a imagem no GPT Image"},
        "prompt_gemini": {"type": "string", "description": "Prompt em inglês para gerar a imagem no Gemini"},
        "prompt_flow": {
            "type": "string",
            "description": "Prompt em inglês para vídeo de ~8s no Veo/Flow: cena, câmera, luz, áudio",
        },
    },
    "required": [
        "conceito",
        "headline",
        "texto_apoio",
        "cta",
        "legenda",
        "prompt_chatgpt",
        "prompt_gemini",
        "prompt_flow",
    ],
    "additionalProperties": False,
}

SYSTEM = """Você é um diretor criativo sênior de performance (anúncios para Instagram, TikTok e Meta Ads).
Recebe uma ideia crua de criativo e devolve um briefing enxuto e prompts prontos para cada IA geradora.

Regras:
- Copy (headline, texto_apoio, cta, legenda) em português do Brasil, direta e persuasiva.
- Prompts de geração em inglês, ricos em detalhes visuais: sujeito, composição, enquadramento, luz, paleta, estilo, lente.
- Se o criativo tiver texto na arte, coloque o texto exato entre aspas no prompt da imagem.
- prompt_chatgpt e prompt_gemini devem explorar ângulos visuais DIFERENTES do mesmo conceito, para dar variedade ao teste A/B.
- prompt_flow descreve um vídeo curto (~8s) com movimento de câmera, ação e som ambiente/trilha."""


def criar_briefing(ideia: str, formato: str, contexto: str = "") -> dict:
    client = anthropic.Anthropic()
    pedido = f"Ideia do criativo: {ideia}\nFormato: {formato}"
    if contexto:
        pedido += f"\nContexto da marca/produto: {contexto}"

    resposta = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4000,
        system=SYSTEM,
        messages=[{"role": "user", "content": pedido}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )
    texto = next(b.text for b in resposta.content if b.type == "text")
    return json.loads(texto)


def briefing_basico(ideia: str) -> dict:
    """Usado quando não há ANTHROPIC_API_KEY ou com --sem-diretor:
    a mesma ideia vai crua para todas as IAs."""
    return {
        "conceito": ideia,
        "headline": "",
        "texto_apoio": "",
        "cta": "",
        "legenda": "",
        "prompt_chatgpt": ideia,
        "prompt_gemini": ideia,
        "prompt_flow": ideia,
    }
