"""Uma execução do fluxo: ideia -> diretor -> IAs em paralelo -> galeria.
O estado de cada etapa fica em estado.json na pasta da execução, e é isso
que o site lê para mostrar o andamento."""

import json
import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from . import config, diretor, galeria
from .providers import PROVEDORES

# status de cada nó: aguardando, rodando, ok, erro, pulado
CHAVE_PROMPT = {"chatgpt": "prompt_chatgpt", "gemini": "prompt_gemini", "flow": "prompt_flow"}


def _slug(texto: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower())[:40].strip("-") or "criativo"


def _no(status: str = "aguardando") -> dict:
    return {"status": status, "inicio": None, "fim": None, "erro": None, "arquivo": None}


class Execucao:
    def __init__(self, pasta: Path, estado: dict):
        self.pasta = pasta
        self.estado = estado
        self._lock = threading.Lock()

    @property
    def id(self) -> str:
        return self.pasta.name

    @classmethod
    def nova(cls, raiz: Path, ideia: str, formato: str = "1:1", contexto: str = "",
             ias: list[str] | None = None, usar_diretor: bool = True) -> "Execucao":
        ias = ias or list(PROVEDORES)
        desconhecidas = [n for n in ias if n not in PROVEDORES]
        if desconhecidas:
            raise ValueError(f"IA desconhecida: {', '.join(desconhecidas)}")
        if formato not in config.FORMATOS:
            raise ValueError(f"Formato inválido: {formato}")

        pasta = raiz / f"{datetime.now():%Y%m%d-%H%M%S}-{_slug(ideia)}"
        pasta.mkdir(parents=True, exist_ok=True)
        estado = {
            "ideia": ideia,
            "formato": formato,
            "contexto": contexto,
            "ias": ias,
            "criado_em": datetime.now().isoformat(timespec="seconds"),
            "briefing": None,
            "nos": {"ideia": _no("ok"), "diretor": _no(), **{n: _no() for n in ias}, "galeria": _no()},
        }
        if not usar_diretor or not config.tem_chave("ANTHROPIC_API_KEY"):
            motivo = "Desligado" if not usar_diretor else "Sem ANTHROPIC_API_KEY: ideia vai crua"
            estado["nos"]["diretor"] = {**_no("pulado"), "erro": motivo}
        execucao = cls(pasta, estado)
        execucao._salvar()
        return execucao

    @classmethod
    def carregar(cls, pasta: Path) -> "Execucao":
        return cls(pasta, json.loads((pasta / "estado.json").read_text(encoding="utf-8")))

    def _salvar(self) -> None:
        temp = self.pasta / "estado.json.tmp"
        temp.write_text(json.dumps(self.estado, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.pasta / "estado.json")

    def _atualizar(self, no: str, **campos) -> None:
        with self._lock:
            self.estado["nos"][no].update(campos)
            self._salvar()

    def _etapa(self, no: str, funcao, *args):
        self._atualizar(no, status="rodando", inicio=time.time(), fim=None, erro=None)
        try:
            resultado = funcao(*args)
        except Exception as erro:  # uma etapa falhar não derruba as outras
            self._atualizar(no, status="erro", fim=time.time(), erro=str(erro))
            return None
        arquivo = resultado.name if isinstance(resultado, Path) else None
        self._atualizar(no, status="ok", fim=time.time(), arquivo=arquivo)
        return resultado

    def rodar(self) -> None:
        e = self.estado
        if e["nos"]["diretor"]["status"] == "pulado":
            briefing = diretor.briefing_basico(e["ideia"])
        else:
            briefing = self._etapa("diretor", diretor.criar_briefing, e["ideia"], e["formato"], e["contexto"])
            if briefing is None:
                briefing = diretor.briefing_basico(e["ideia"])
        with self._lock:
            e["briefing"] = briefing
            self._salvar()
        (self.pasta / "briefing.json").write_text(json.dumps(briefing, ensure_ascii=False, indent=2), encoding="utf-8")

        with ThreadPoolExecutor(max_workers=len(e["ias"])) as pool:
            for nome in e["ias"]:
                pool.submit(self.rodar_ia, nome, montar_galeria=False)
        self._montar_galeria()

    def rodar_ia(self, nome: str, montar_galeria: bool = True) -> None:
        modulo, chave = PROVEDORES[nome]
        if not config.tem_chave(chave):
            self._atualizar(nome, status="pulado", erro=f"Defina {chave} no .env")
        else:
            self._etapa(nome, modulo.gerar, self.estado["briefing"], self.estado["formato"], self.pasta)
        if montar_galeria:
            self._montar_galeria()

    def _montar_galeria(self) -> None:
        def montar():
            resultados = {}
            for nome in self.estado["ias"]:
                no = self.estado["nos"][nome]
                resultados[nome] = self.pasta / no["arquivo"] if no["arquivo"] else (no["erro"] or no["status"])
            return galeria.montar(self.pasta, self.estado["ideia"], self.estado["formato"],
                                  self.estado["briefing"], resultados)

        self._etapa("galeria", montar)


def listar(raiz: Path) -> list[Execucao]:
    if not raiz.exists():
        return []
    pastas = sorted((p for p in raiz.iterdir() if (p / "estado.json").exists()), reverse=True)
    return [Execucao.carregar(p) for p in pastas]
