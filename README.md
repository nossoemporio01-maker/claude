# Criativos multi-IA

Você escreve a ideia de um criativo, e ela é gerada **ao mesmo tempo** em quatro IAs:

| IA | O que gera | Como |
|---|---|---|
| **ChatGPT** | Imagem | API de imagem da OpenAI (`gpt-image-2`, o mesmo motor do ChatGPT) |
| **Gemini** | Imagem | Modelo de imagem do Gemini (Nano Banana) |
| **Flow** | Vídeo de ~8s | Veo pela Gemini API. O Google Flow não tem API pública, mas o motor dele é o Veo. |
| **Opus 5.5** | Peça em HTML/SVG + copy | Claude Opus 5.5 |

Antes de gerar, o **Opus 5.5 faz o papel de diretor criativo**: transforma a ideia crua em conceito,
headline, CTA e legenda, e escreve um prompt otimizado para cada ferramenta. Os prompts de ChatGPT e
Gemini exploram ângulos diferentes, para você ter variações para teste A/B.

No fim, um `index.html` mostra todas as versões lado a lado.

```
ideia ──► Opus 5.5 (diretor: briefing + prompts)
              │
              ├──► ChatGPT ─► chatgpt.png
              ├──► Gemini  ─► gemini.png
              ├──► Flow/Veo ─► flow.mp4
              └──► Opus 5.5 ─► opus.html
                                   └──► index.html (comparação)
```

## Instalação

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # e coloque suas chaves
```

Chaves:
- `ANTHROPIC_API_KEY`: https://console.anthropic.com
- `OPENAI_API_KEY`: https://platform.openai.com/api-keys
- `GEMINI_API_KEY` (serve para Gemini e Flow/Veo): https://aistudio.google.com/apikey

Se faltar uma chave, essa IA é pulada e as outras rodam normalmente. Sem a chave da Anthropic,
a ideia vai crua (sem passar pelo diretor) para as outras IAs.

## Uso

```bash
python -m criativos "Promoção de café gelado para o verão, clima de praia"

# Stories/Reels
python -m criativos "Lançamento do tênis X" --formato 9:16

# Com contexto da marca
python -m criativos "Black Friday" --contexto "Loja de produtos naturais, público 25-45, tom acolhedor"

# Só algumas IAs
python -m criativos "Dia das mães" --so chatgpt,gemini
```

| Opção | Descrição |
|---|---|
| `--formato` | `1:1` (padrão), `4:5`, `9:16`, `16:9`. O Veo só gera `9:16` ou `16:9`, então `1:1`/`4:5` viram vertical no vídeo. |
| `--so` | Lista de IAs: `chatgpt,gemini,flow,opus` |
| `--contexto` | Marca, produto, público, tom de voz |
| `--sem-diretor` | Pula o Opus e manda a ideia crua para todas |
| `--saida` | Pasta de saída (padrão `saida/`) |

Cada execução cria `saida/<data>-<ideia>/` com:
- `briefing.json`: conceito, copy, legenda e os prompts usados
- `chatgpt.png`, `gemini.png`, `flow.mp4`, `opus.html`
- `index.html`: galeria comparando tudo

## Trocar modelos

Os modelos ficam no `.env` (`CLAUDE_MODEL`, `OPENAI_IMAGE_MODEL`, `GEMINI_IMAGE_MODEL`, `VEO_MODEL`).
Quando sair uma versão nova, basta trocar ali.

## Observações

- O vídeo do Veo leva de 1 a 5 minutos; as imagens saem em segundos. Tudo roda em paralelo.
- Veo e imagens em qualidade alta são pagos por geração. Use `--so` para testar barato.
- O Claude não gera imagem em pixels, então a peça do Opus é um HTML no tamanho exato do formato.
  Abra no navegador e tire um print, ou use como base editável.
