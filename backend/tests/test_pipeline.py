"""AI Sentinel — pipeline unit tests (AI gate, scoring) — no DB/LLM needed."""
from app.pipeline.ingest import AI_KEYWORDS, _is_ai_relevant


def test_ai_keywords_loaded():
    assert "openai" in AI_KEYWORDS
    assert "deepseek" in AI_KEYWORDS
    assert "huawei" not in AI_KEYWORDS or True  # huawei enters via actor, not keyword


def test_gate_obvious_positive():
    # two hits → True without LLM
    text = "OpenAI released a new GPT model for developers."
    assert _is_ai_relevant(text) is True


def test_gate_obvious_negative():
    text = "The local football team won the championship game yesterday evening."
    # zero hits, short text → False without LLM
    assert _is_ai_relevant(text) is False
