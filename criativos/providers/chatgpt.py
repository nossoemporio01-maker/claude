"""ChatGPT: imagem gerada pelo modelo de imagem da OpenAI (o mesmo do ChatGPT)."""

import base64
from pathlib import Path

from openai import OpenAI

from .. import config

TAMANHOS = {"1:1": "1024x1024", "4:5": "1024x1536", "9:16": "1024x1536", "16:9": "1536x1024"}


def gerar(briefing: dict, formato: str, pasta: Path) -> Path:
    client = OpenAI()
    resposta = client.images.generate(
        model=config.OPENAI_IMAGE_MODEL,
        prompt=briefing["prompt_chatgpt"],
        size=TAMANHOS[formato],
        quality="high",
        n=1,
    )
    arquivo = pasta / "chatgpt.png"
    arquivo.write_bytes(base64.b64decode(resposta.data[0].b64_json))
    return arquivo
