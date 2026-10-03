from . import chatgpt, flow, gemini, opus

# nome -> (módulo, variável de ambiente exigida)
PROVEDORES = {
    "chatgpt": (chatgpt, "OPENAI_API_KEY"),
    "gemini": (gemini, "GEMINI_API_KEY"),
    "flow": (flow, "GEMINI_API_KEY"),
    "opus": (opus, "ANTHROPIC_API_KEY"),
}
