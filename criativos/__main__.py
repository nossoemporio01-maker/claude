"""Uso:
    python -m criativos "ideia do criativo" [--formato 9:16] [--so chatgpt,gemini] [--contexto "..."]
    python -m criativos.web            # abre o painel visual no navegador
"""

import argparse
import sys
from pathlib import Path

from . import config
from .pipeline import Execucao
from .providers import PROVEDORES

ICONES = {"ok": "✅", "erro": "❌", "pulado": "⏭️ ", "aguardando": "…", "rodando": "…"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera um criativo em várias IAs ao mesmo tempo.")
    parser.add_argument("ideia", help="A ideia do criativo, em texto livre")
    parser.add_argument("--formato", choices=config.FORMATOS, default="1:1")
    parser.add_argument("--so", help=f"Só estas IAs, separadas por vírgula ({', '.join(PROVEDORES)})")
    parser.add_argument("--contexto", default="", help="Marca, produto, público, tom de voz...")
    parser.add_argument("--sem-diretor", action="store_true", help="Manda a ideia crua, sem o Opus otimizar os prompts")
    parser.add_argument("--saida", default="saida", help="Pasta onde salvar os resultados")
    args = parser.parse_args()

    try:
        execucao = Execucao.nova(
            Path(args.saida), args.ideia, args.formato, args.contexto,
            args.so.split(",") if args.so else None, not args.sem_diretor,
        )
    except ValueError as erro:
        parser.error(str(erro))

    print(f"🚀 Gerando em: {', '.join(execucao.estado['ias'])} (o vídeo pode levar alguns minutos)")
    execucao.rodar()

    for nome, no in execucao.estado["nos"].items():
        if nome == "ideia":
            continue
        detalhe = no["arquivo"] or no["erro"] or ""
        tempo = f" ({no['fim'] - no['inicio']:.0f}s)" if no["inicio"] and no["fim"] else ""
        print(f"{ICONES[no['status']]} {nome}: {detalhe}{tempo}")
    print(f"\n📂 Resultados em {execucao.pasta}\n🖼️  Abra {execucao.pasta / 'index.html'} para comparar")
    return 0 if any(execucao.estado["nos"][n]["status"] == "ok" for n in execucao.estado["ias"]) else 1


if __name__ == "__main__":
    sys.exit(main())
