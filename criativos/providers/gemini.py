"""Gemini: imagem gerada pelo modelo de imagem do Gemini (Nano Banana)."""

from pathlib import Path

from google import genai
from google.genai import types

from .. import config


def gerar(briefing: dict, formato: str, pasta: Path) -> Path:
    client = genai.Client(api_key=config.gemini_api_key())
    resposta = client.models.generate_content(
        model=config.GEMINI_IMAGE_MODEL,
        contents=briefing["prompt_gemini"],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=formato),
        ),
    )
    for parte in resposta.candidates[0].content.parts:
        if parte.inline_data and parte.inline_data.data:
            extensao = (parte.inline_data.mime_type or "image/png").split("/")[-1]
            arquivo = pasta / f"gemini.{extensao}"
            arquivo.write_bytes(parte.inline_data.data)
            return arquivo
    raise RuntimeError(f"Gemini não devolveu imagem. Resposta: {resposta.text!r}")
