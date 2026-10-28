"""AI Sentinel — embedding layer (local sentence-transformers or API)."""
import logging
import threading

from app.config import settings

log = logging.getLogger("ai_sentinel.embed")

_local_model = None
_local_lock = threading.Lock()


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(settings.embedding_model.split("/", 1)[1])
    return _local_model


def embed(text: str) -> list[float]:
    """Embed a text into a vector. Returns [] on failure (caller stores NULL)."""
    if not text or not text.strip():
        return []
    try:
        if settings.embedding_provider == "openai":
            import litellm

            resp = litellm.embedding(model=settings.openai_embedding_model, input=[text])
            return resp.data[0]["embedding"]
        with _local_lock:
            model = _get_local_model()
        return model.encode(text[:4000]).tolist()
    except Exception as e:
        log.warning("embedding failed: %s", e)
        return []
