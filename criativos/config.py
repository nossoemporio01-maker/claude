import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview")
VEO_MODEL = os.getenv("VEO_MODEL", "veo-3.1-generate-preview")

FORMATOS = ("1:1", "4:5", "9:16", "16:9")


def tem_chave(nome: str) -> bool:
    if nome == "GEMINI_API_KEY":
        return bool(gemini_api_key())
    return bool(os.getenv(nome))


def gemini_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
