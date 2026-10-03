"""Painel visual do fluxo, estilo n8n.

    python -m criativos.web [--porta 8000] [--saida saida]

Abre em http://localhost:8000
"""

import argparse
import json
import mimetypes
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import config
from .pipeline import Execucao, listar
from .providers import PROVEDORES

ESTATICOS = Path(__file__).parent / "static"
RAIZ = Path("saida")
ATIVAS: set[str] = set()  # execuções com thread rodando agora
_lock = threading.Lock()


def _em_background(execucao: Execucao, alvo, *args) -> None:
    def rodar():
        try:
            alvo(*args)
        finally:
            with _lock:
                ATIVAS.discard(execucao.id)

    with _lock:
        ATIVAS.add(execucao.id)
    threading.Thread(target=rodar, daemon=True).start()


def _resumo(execucao: Execucao) -> dict:
    estado = execucao.estado
    nos = estado["nos"]
    ativa = execucao.id in ATIVAS
    if not ativa:
        # execução que estava rodando quando o servidor caiu
        for no in nos.values():
            if no["status"] in ("rodando", "aguardando"):
                no.update(status="erro", erro="Interrompido (o servidor foi reiniciado)")
    return {"id": execucao.id, **estado, "ativa": ativa, "agora": time.time()}


def _carregar(id_: str) -> Execucao | None:
    pasta = (RAIZ / id_).resolve()
    if pasta.parent != RAIZ.resolve() or not (pasta / "estado.json").exists():
        return None
    return Execucao.carregar(pasta)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _json(self, dados, status=200):
        corpo = json.dumps(dados, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _arquivo(self, caminho: Path):
        if not caminho.is_file():
            return self._json({"erro": "não encontrado"}, 404)
        tipo = mimetypes.guess_type(caminho.name)[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo == "application/json":
            tipo += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(caminho.stat().st_size))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        with caminho.open("rb") as f:
            while bloco := f.read(1 << 16):
                self.wfile.write(bloco)

    def do_GET(self):
        partes = [unquote(p) for p in urlparse(self.path).path.strip("/").split("/") if p]
        if not partes:
            return self._arquivo(ESTATICOS / "index.html")
        if partes == ["api", "config"]:
            return self._json({
                "formatos": config.FORMATOS,
                "ias": {n: config.tem_chave(chave) for n, (_, chave) in PROVEDORES.items()},
                "diretor": config.tem_chave("ANTHROPIC_API_KEY"),
            })
        if partes == ["api", "execucoes"]:
            return self._json([_resumo(e) for e in listar(RAIZ)[:50]])
        if len(partes) == 3 and partes[:2] == ["api", "execucoes"]:
            execucao = _carregar(partes[2])
            return self._json(_resumo(execucao)) if execucao else self._json({"erro": "não encontrada"}, 404)
        if len(partes) == 3 and partes[0] == "arquivos":
            execucao = _carregar(partes[1])
            if execucao and "/" not in partes[2] and not partes[2].startswith("."):
                return self._arquivo(execucao.pasta / partes[2])
        return self._json({"erro": "não encontrado"}, 404)

    def do_POST(self):
        partes = [unquote(p) for p in urlparse(self.path).path.strip("/").split("/") if p]
        tamanho = int(self.headers.get("Content-Length") or 0)
        try:
            corpo = json.loads(self.rfile.read(tamanho) or b"{}")
        except json.JSONDecodeError:
            return self._json({"erro": "JSON inválido"}, 400)

        if partes == ["api", "execucoes"]:
            ideia = (corpo.get("ideia") or "").strip()
            if not ideia:
                return self._json({"erro": "Escreva a ideia do criativo"}, 400)
            try:
                execucao = Execucao.nova(
                    RAIZ, ideia, corpo.get("formato", "1:1"), (corpo.get("contexto") or "").strip(),
                    corpo.get("ias") or None, bool(corpo.get("diretor", True)),
                )
            except ValueError as erro:
                return self._json({"erro": str(erro)}, 400)
            _em_background(execucao, execucao.rodar)
            return self._json(_resumo(execucao), 201)

        # POST /api/execucoes/<id>/repetir/<ia>: roda de novo só uma IA
        if len(partes) == 5 and partes[:2] == ["api", "execucoes"] and partes[3] == "repetir":
            execucao = _carregar(partes[2])
            nome = partes[4]
            if not execucao or nome not in execucao.estado["ias"]:
                return self._json({"erro": "não encontrada"}, 404)
            if execucao.id in ATIVAS:
                return self._json({"erro": "Essa execução ainda está rodando"}, 409)
            if not execucao.estado["briefing"]:
                return self._json({"erro": "Essa execução não chegou a ter briefing"}, 409)
            _em_background(execucao, execucao.rodar_ia, nome)
            return self._json(_resumo(execucao), 202)

        return self._json({"erro": "não encontrado"}, 404)


def main() -> None:
    global RAIZ
    parser = argparse.ArgumentParser(description="Painel visual do fluxo de criativos")
    parser.add_argument("--porta", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--saida", default="saida")
    parser.add_argument("--sem-navegador", action="store_true")
    args = parser.parse_args()

    RAIZ = Path(args.saida)
    RAIZ.mkdir(parents=True, exist_ok=True)
    url = f"http://localhost:{args.porta}"
    servidor = ThreadingHTTPServer((args.host, args.porta), Handler)
    print(f"🎛️  Painel rodando em {url}  (Ctrl+C para parar)")
    if not args.sem_navegador:
        threading.Timer(0.5, webbrowser.open, [url]).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
