"""Uso:
    python -m criativos "ideia do criativo" [--formato 9:16] [--so chatgpt,gemini] [--contexto "..."]
"""

import argparse
import json
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from . import config, diretor, galeria
from .providers import PROVEDORES


def _slug(texto: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower())[:40].strip("-") or "criativo"


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera um criativo em várias IAs ao mesmo tempo.")
    parser.add_argument("ideia", help="A ideia do criativo, em texto livre")
    parser.add_argument("--formato", choices=config.FORMATOS, default="1:1")
    parser.add_argument("--so", help=f"Só estas IAs, separadas por vírgula ({', '.join(PROVEDORES)})")
    parser.add_argument("--contexto", default="", help="Marca, produto, público, tom de voz...")
    parser.add_argument("--sem-diretor", action="store_true", help="Manda a ideia crua, sem o Opus otimizar os prompts")
    parser.add_argument("--saida", default="saida", help="Pasta onde salvar os resultados")
    args = parser.parse_args()

    escolhidos = args.so.split(",") if args.so else list(PROVEDORES)
    desconhecidos = [n for n in escolhidos if n not in PROVEDORES]
    if desconhecidos:
        parser.error(f"IA desconhecida: {', '.join(desconhecidos)}")

    pasta = Path(args.saida) / f"{datetime.now():%Y%m%d-%H%M%S}-{_slug(args.ideia)}"
    pasta.mkdir(parents=True, exist_ok=True)

    if args.sem_diretor or not config.tem_chave("ANTHROPIC_API_KEY"):
        briefing = diretor.briefing_basico(args.ideia)
    else:
        print("🎬 Opus 5.5 montando o briefing e os prompts...")
        briefing = diretor.criar_briefing(args.ideia, args.formato, args.contexto)
    (pasta / "briefing.json").write_text(json.dumps(briefing, ensure_ascii=False, indent=2), encoding="utf-8")

    resultados: dict = {}
    tarefas = {}
    with ThreadPoolExecutor(max_workers=len(escolhidos)) as pool:
        for nome in escolhidos:
            modulo, chave = PROVEDORES[nome]
            if not config.tem_chave(chave):
                resultados[nome] = f"Pulado: defina {chave} no .env"
                print(f"⏭️  {nome}: sem {chave}")
                continue
            print(f"🚀 {nome}: gerando...")
            tarefas[pool.submit(modulo.gerar, briefing, args.formato, pasta)] = (nome, time.monotonic())

        for futuro in as_completed(tarefas):
            nome, inicio = tarefas[futuro]
            try:
                resultados[nome] = futuro.result()
                print(f"✅ {nome}: {resultados[nome]} ({time.monotonic() - inicio:.0f}s)")
            except Exception as erro:  # um provedor falhar não derruba os outros
                resultados[nome] = f"Erro: {erro}"
                print(f"❌ {nome}: {erro}")

    ordenados = {n: resultados[n] for n in escolhidos if n in resultados}
    indice = galeria.montar(pasta, args.ideia, args.formato, briefing, ordenados)
    print(f"\n📂 Resultados em {pasta}\n🖼️  Abra {indice} para comparar")
    return 0 if any(isinstance(r, Path) for r in ordenados.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
