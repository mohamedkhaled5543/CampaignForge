---
title: CampaignForge AI
emoji: 🚀
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
---

# CampaignForge AI

Product brief to full campaign: product understanding, strategy (grounded in a marketing knowledge base),
three strategic directions, and Instagram and TikTok content.

## How it is built
```
Routes (app/api) -> Services (app/services) -> Chains (app/ai) -> LLM
                                  \-> RAG (app/rag: PDF -> MiniLM -> FAISS)
```
- **Two engines.** `PROVIDER=auto` uses your own Mistral-Nemo notebook (Colab + ngrok) when it is online and
  Gemini otherwise. `colab` or `gemini` force one engine. The page shows which one is answering.
- **Schema-checked output** (`with_structured_output`) with automatic retries.
- **Guardrails** (`app/ai/guardrails.py`) check for invented promo codes, deadlines and percentages, and regenerate once.
- Schemas, prompts and `static/index.html` come from the notebook.

## Deploy on Hugging Face Spaces (free)
1. Create a Space: **SDK = Docker**, blank template.
2. Put your PDF at `knowledge_base/CampaignForge_Marketing_Knowledge_Base.pdf`.
3. Upload this folder to the Space (web upload or `git push`).
4. Space **Settings > Variables and secrets**:
   - Secret `GOOGLE_API_KEY` (free key from Google AI Studio)
   - Variable `PROVIDER` = `auto`
   - Variable `COLAB_API_URL` = the ngrok address from your notebook (optional)
5. Wait for the build, then open `https://<user>-<space>.hf.space`.

Free Spaces sleep after 48 hours without visitors and wake when opened. Always-on needs paid hardware.

## Run locally
```
pip install -r requirements-dev.txt
export GOOGLE_API_KEY=...        # and optionally COLAB_API_URL=...
uvicorn app.main:app --port 7860
pytest
```
