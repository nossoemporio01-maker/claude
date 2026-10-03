"""Flow: o Google Flow não tem API pública; o motor dele é o Veo.
Aqui chamamos o Veo direto pela Gemini API — mesmo resultado, automatizável."""

import time
from pathlib import Path

from google import genai
from google.genai import types

from .. import config

# Veo só gera horizontal ou vertical
PROPORCAO = {"1:1": "9:16", "4:5": "9:16", "9:16": "9:16", "16:9": "16:9"}
TIMEOUT_S = 15 * 60


def gerar(briefing: dict, formato: str, pasta: Path) -> Path:
    client = genai.Client(api_key=config.gemini_api_key())
    operacao = client.models.generate_videos(
        model=config.VEO_MODEL,
        prompt=briefing["prompt_flow"],
        config=types.GenerateVideosConfig(aspect_ratio=PROPORCAO[formato], number_of_videos=1),
    )

    inicio = time.monotonic()
    while not operacao.done:
        if time.monotonic() - inicio > TIMEOUT_S:
            raise TimeoutError("Veo demorou mais de 15 min")
        time.sleep(10)
        operacao = client.operations.get(operacao)

    if operacao.error:
        raise RuntimeError(f"Veo falhou: {operacao.error}")
    if not operacao.response or not operacao.response.generated_videos:
        raise RuntimeError("Veo não devolveu vídeo (possível bloqueio de segurança)")

    video = operacao.response.generated_videos[0].video
    client.files.download(file=video)
    arquivo = pasta / "flow.mp4"
    video.save(str(arquivo))
    return arquivo
