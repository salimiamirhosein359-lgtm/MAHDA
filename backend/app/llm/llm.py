"""AI Sentinel — unified LLM layer via LiteLLM (cloud API + Ollama)."""
import logging

from app.config import settings

log = logging.getLogger("ai_sentinel.llm")


def llm_complete(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.3,
) -> str:
    """Call the configured LLM. Falls back to the fallback model on error."""
    try:
        import litellm

        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})

        try:
            resp = litellm.completion(
                model=model or settings.llm_model,
                messages=msgs,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:  # try fallback model
            log.warning("primary model failed (%s); trying fallback %s", e, settings.llm_model_fallback)
            resp = litellm.completion(
                model=settings.llm_model_fallback,
                messages=msgs,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content or ""
    except Exception as e:
        log.error("LLM unavailable: %s", e)
        return ""


# ---------- Prompts (Persian-aware) ----------

CLASSIFY_SYSTEM = """You are a classifier for AI-related news items.
Return ONLY a JSON object, no prose, in this exact shape:
{"category": "<one of: infrastructure|models|algorithms|tools|evals|applications|policy_economy|discourse|other>",
 "camp": "<one of: US|CN|EU|other>",
 "actor": "<main person/org or null>",
 "ai_relevant": <true|false>}"""

RELEVANCE_SYSTEM = """Does this text concern artificial intelligence (models, chips, algorithms,
policy, companies, research, applications of AI)? Answer ONLY true or false."""

SUMMARY_SYSTEM = """You write concise summaries. If the content is in Persian/English, reply in
Persian. Keep it under 120 words, factual, no fluff."""
