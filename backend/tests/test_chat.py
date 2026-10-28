"""AI Sentinel — chatbot (app.research.chat) unit tests.

No real DB or network required: archive search is tested against a mocked
session, web search against a mocked web_search, and the LLM path against a
mocked llm_complete. Pure-Python pieces (keyword extraction, merging/ranking,
answer composition) are tested directly.
"""
from types import SimpleNamespace

import app.research.chat as chat_mod
from app.research.chat import (
    _compose_answer,
    _merge_rank,
    chat_retrieve,
    extract_keywords,
)


# ---------------------------------------------------------------------------
# keyword extraction
# ---------------------------------------------------------------------------

def test_keyword_extraction_english():
    kws = extract_keywords("What are the latest AI models released by OpenAI?")
    assert "latest" not in kws  # question word / filler removed
    assert "models" in kws
    assert "openai" in kws
    assert "what" not in kws and "are" not in kws and "the" not in kws
    assert len(kws) >= 2


def test_keyword_extraction_persian():
    kws = extract_keywords("جدیدترین مدل‌های هوش مصنوعی دیپ‌سیک چی هستند؟")
    # stopwords (جدیدترین/چی/هستند/را) dropped; content words kept
    assert "دیپ‌سیک" in kws or "دیپ" in kws
    assert "چی" not in kws
    assert "هستند" not in kws
    assert len(kws) >= 1


def test_keyword_extraction_dedup_and_empty():
    assert extract_keywords("") == []
    assert extract_keywords("   ") == []
    kws = extract_keywords("Nvidia Nvidia GPU gpu models models")
    assert kws.count("nvidia") == 1  # deduplicated
    assert kws.count("gpu") == 1
    assert kws.count("models") == 1


def test_keyword_extraction_arabic_chars_normalized():
    # arabic ي should normalize to persian ی so the token is uniform
    kws = extract_keywords("هوش مصنوعي چگونه کار می‌کند")
    assert "مصنوعی" in kws  # normalized form present
    assert "چگونه" not in kws  # stopword


def test_keyword_extraction_fa_alias_to_english():
    """Persian transliterations also yield the English keyword."""
    kws = extract_keywords("اخبار جدید دیپ‌سیک چیست؟")
    assert "دیپ‌سیک" in kws
    assert "deepseek" in kws  # alias injected
    kws2 = extract_keywords("مدل‌های اوپن‌ای‌آی")
    assert "openai" in kws2
    kws3 = extract_keywords("وضعیت تراشه‌های انویدیا")
    assert "nvidia" in kws3 and "chip" in kws3


# ---------------------------------------------------------------------------
# merge + rank
# ---------------------------------------------------------------------------

def test_merge_rank_orders_and_numbers():
    archive = [
        {"title": "arc-low", "url": "u1", "snippet": "s", "kind": "archive", "_score": 0.3},
        {"title": "arc-high", "url": "u2", "snippet": "s", "kind": "archive", "_score": 0.9},
    ]
    web = [
        {"title": "web-mid", "url": "u3", "snippet": "s", "kind": "web", "_score": 0.7},
    ]
    out = _merge_rank(archive, web, limit=5)
    assert [s["title"] for s in out] == ["arc-high", "web-mid", "arc-low"]
    assert [s["ref_no"] for s in out] == [1, 2, 3]
    assert len(out) == 3


def test_merge_rank_respects_limit():
    archive = [{"title": f"a{i}", "url": f"u{i}", "kind": "archive", "_score": 0.5} for i in range(10)]
    out = _merge_rank(archive, [], limit=4)
    assert len(out) == 4


# ---------------------------------------------------------------------------
# answer composition
# ---------------------------------------------------------------------------

def test_compose_answer_empty():
    ans = _compose_answer("anything", [])
    assert "پیدا نشد" in ans


def test_compose_answer_with_sources():
    sources = [
        {"ref_no": 1, "title": "DeepSeek R1 released", "snippet": "open-weights reasoning model", "kind": "archive"},
        {"ref_no": 2, "title": "OpenAI news", "snippet": "GPT-5 rumor", "kind": "web"},
    ]
    ans = _compose_answer("latest AI models", sources)
    assert ans.startswith("بر اساس 2 منبع")
    assert "(1 از آرشیو داخلی، 1 از وب)" in ans
    assert "•" in ans
    assert "منابع مرتبط:" in ans
    assert "[1] DeepSeek R1 released" in ans
    assert "[2] OpenAI news" in ans


# ---------------------------------------------------------------------------
# chat_retrieve with mocked dependencies (no DB / no network)
# ---------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows


class _FakeDB:
    """Minimal Session stand-in: db.execute(sql, params).fetchall()."""

    def __init__(self, rows):
        self.rows = rows
        self.calls = []
        self.closed = False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        return _FakeResult(self.rows)

    def close(self):
        self.closed = True


def test_chat_retrieve_english_mocked(monkeypatch):
    """'latest AI models' with mocked DB + web → sources returned, no crash."""
    fake_db = _FakeDB(
        rows=[
            (
                1,
                "DeepSeek R1: open-weights reasoning model",
                "https://example.com/r1",
                "New reasoning models from DeepSeek and OpenAI latest releases.",
                "models",
                "CN",
                "DeepSeek",
                None,
                0.9,
            ),
            (
                2,
                "OpenAI GPT-5 announcement",
                "https://example.com/gpt5",
                "Latest AI models from OpenAI: GPT-5 benchmarks.",
                "models",
                "US",
                "OpenAI",
                None,
                0.8,
            ),
        ]
    )
    monkeypatch.setattr(
        chat_mod, "web_search",
        lambda q, limit=8: [
            {"title": "Latest AI models 2026", "url": "https://web.example/ai",
             "snippet": "A roundup of the latest AI models."},
        ],
    )
    monkeypatch.setattr(chat_mod, "_llm_enhance", lambda q, s: "")  # no LLM key

    out = chat_retrieve("latest AI models", online=True, db=fake_db)

    assert isinstance(out, dict)
    assert set(out.keys()) >= {"answer", "sources", "online"}
    assert len(out["sources"]) >= 3  # 2 archive + 1 web
    assert out["online"] is True
    assert out["answer"].startswith("بر اساس 3 منبع")
    kinds = {s["kind"] for s in out["sources"]}
    assert "archive" in kinds and "web" in kinds
    refs = [s["ref_no"] for s in out["sources"]]
    assert refs == sorted(refs) == [1, 2, 3]
    # web search actually got called with extracted keywords
    assert fake_db.calls, "archive search should have run"


def test_chat_retrieve_offline_archive_only(monkeypatch):
    fake_db = _FakeDB(
        rows=[
            (1, "Qwen3 technical report", "https://example.com/qwen3",
             "Qwen3 family of models", "models", "CN", "Alibaba", None, 0.7),
        ]
    )
    called = {"web": 0}

    def _no_web(q, limit=8):
        called["web"] += 1
        return []

    monkeypatch.setattr(chat_mod, "web_search", _no_web)
    monkeypatch.setattr(chat_mod, "_llm_enhance", lambda q, s: "")

    out = chat_retrieve("qwen3 technical report", online=False, db=fake_db)
    assert called["web"] == 0  # offline → web never touched
    assert out["online"] is False
    assert len(out["sources"]) == 1
    assert out["sources"][0]["kind"] == "archive"
    assert "پیدا نشد" not in out["answer"]


def test_chat_retrieve_web_timeout_falls_back(monkeypatch):
    """Web slower than the 10s budget → archive-only answer, online=False."""
    import time as _time

    fake_db = _FakeDB(
        rows=[(1, "Nvidia Blackwell", "https://example.com/b200",
               "Nvidia B200 GPU", "infrastructure", "US", "Nvidia", None, 0.8)],
    )

    def _slow_web(q, limit=8):
        _time.sleep(1)  # can't sleep 10s in a test; shrink the budget instead
        return []

    monkeypatch.setattr(chat_mod, "web_search", _slow_web)
    monkeypatch.setattr(chat_mod, "WEB_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(chat_mod, "_llm_enhance", lambda q, s: "")

    out = chat_retrieve("nvidia blackwell gpu", online=True, db=fake_db)
    assert len(out["sources"]) == 1
    assert out["sources"][0]["kind"] == "archive"
    assert out["online"] is False  # web unavailable → reported as archive-only


def test_chat_retrieve_no_results(monkeypatch):
    fake_db = _FakeDB(rows=[])
    monkeypatch.setattr(chat_mod, "web_search", lambda q, limit=8: [])
    monkeypatch.setattr(chat_mod, "_searxng_html_fallback", lambda q, limit=8: [])
    monkeypatch.setattr(chat_mod, "_llm_enhance", lambda q, s: "")

    out = chat_retrieve("zzz nonexistent topic", online=True, db=fake_db)
    assert out["sources"] == []
    assert "پیدا نشد" in out["answer"]


def test_chat_retrieve_llm_layered_when_available(monkeypatch):
    fake_db = _FakeDB(
        rows=[(1, "Claude 4 released", "https://example.com/c4",
               "Anthropic Claude 4 model", "models", "US", "Anthropic", None, 0.9)],
    )
    monkeypatch.setattr(chat_mod, "web_search", lambda q, limit=8: [])
    monkeypatch.setattr(chat_mod, "_llm_enhance", lambda q, s: "پاسخ LLM با ارجاع [1]")

    out = chat_retrieve("claude 4 release", online=False, db=fake_db)
    assert out["answer"].startswith("پاسخ LLM")
    assert "بر اساس 1 منبع" in out["answer"]  # composed part still appended


def test_chat_retrieve_empty_archive_web_only(monkeypatch):
    """Archive with no matches + web hits → web-only answer."""
    fake_db = _FakeDB(rows=[])  # archive finds nothing for these keywords
    monkeypatch.setattr(
        chat_mod, "web_search",
        lambda q, limit=8: [
            {"title": "Web result", "url": "https://w.example/1", "snippet": "snippet"},
        ],
    )
    monkeypatch.setattr(chat_mod, "_searxng_html_fallback", lambda q, limit=8: [])
    monkeypatch.setattr(chat_mod, "_llm_enhance", lambda q, s: "")
    out = chat_retrieve("qqqq zzzz unique topic", online=True, db=fake_db)
    assert len(out["sources"]) == 1
    assert out["sources"][0]["kind"] == "web"
    assert "بر اساس 1 منبع" in out["answer"]


def test_chat_retrieve_auto_session_finds_archive(monkeypatch):
    """No db passed → a session is opened automatically (best-effort).

    We monkeypatch _get_session to hand back a fake DB so no real PostgreSQL
    is needed, and web returns nothing → archive-only result must appear.
    """
    fake_db = _FakeDB(
        rows=[(1, "Llama 4 release", "https://example.com/llama4",
               "Meta Llama 4 models release", "models", "US", "Meta", None, 0.8)],
    )
    monkeypatch.setattr(chat_mod, "_get_session", lambda: fake_db)
    monkeypatch.setattr(chat_mod, "web_search", lambda q, limit=8: [])
    monkeypatch.setattr(chat_mod, "_searxng_html_fallback", lambda q, limit=8: [])
    monkeypatch.setattr(chat_mod, "_llm_enhance", lambda q, s: "")

    out = chat_retrieve("llama 4 release", online=False)
    assert len(out["sources"]) == 1
    assert out["sources"][0]["kind"] == "archive"
    assert out["online"] is False


def test_chat_retrieve_never_raises(monkeypatch):
    """Broken DB + broken web → graceful empty answer, not an exception."""
    class _BoomDB:
        def execute(self, *a, **k):
            raise RuntimeError("db down")

    def _boom_web(q, limit=8):
        raise RuntimeError("net down")

    monkeypatch.setattr(chat_mod, "web_search", _boom_web)
    monkeypatch.setattr(chat_mod, "_searxng_html_fallback", lambda q, limit=8: [])
    monkeypatch.setattr(chat_mod, "_llm_enhance", lambda q, s: "")
    out = chat_retrieve("anything at all", online=True, db=_BoomDB())
    assert out["sources"] == []
    assert "پیدا نشد" in out["answer"]


# ---------------------------------------------------------------------------
# SearXNG HTML fallback parser (offline, markup fixture)
# ---------------------------------------------------------------------------

_FAKE_HTML = """
<html><body>
<article class="result result-default category-general">
  <a href="https://example.com/r1" class="thumbnail_link"><img src="/x"></a>
  <h3><a href="https://example.com/r1" rel="noreferrer"><span class="highlight">AI</span> Release Tracker</a></h3>
  <p class="content">Tracks 269 models &amp; 11 companies.</p>
</article>
<article class="result result-default category-general">
  <a href="https://example.com/r2" class="thumbnail_link"></a>
  <h3><a href="https://example.com/r2" rel="noreferrer">Second Result</a></h3>
  <p class="content">Another snippet.</p>
</article>
<article class="result result-default category-general">
  <h3><a href="javascript:alert(1)" rel="noreferrer">Bad URL</a></h3>
  <p class="content">should be skipped</p>
</article>
</body></html>
"""


def test_searxng_html_fallback_parses(monkeypatch):
    class _FakeResp:
        status_code = 200
        text = _FAKE_HTML

        def raise_for_status(self):
            pass

    class _FakeHttpx:
        @staticmethod
        def get(url, params=None, timeout=None, headers=None, follow_redirects=True):
            assert "q" in params
            return _FakeResp()

    monkeypatch.setitem(__import__("sys").modules, "httpx", _FakeHttpx)
    out = chat_mod._searxng_html_fallback("ai release tracker", limit=5)
    assert len(out) == 2  # javascript: URL skipped
    assert out[0]["title"] == "AI Release Tracker"
    assert out[0]["url"] == "https://example.com/r1"
    assert "269 models & 11 companies" in out[0]["snippet"]
    assert out[1]["title"] == "Second Result"


def test_web_search_budgeted_falls_back_to_html(monkeypatch):
    """web_search returns nothing (JSON 403) → HTML fallback is consulted."""
    monkeypatch.setattr(chat_mod, "web_search", lambda q, limit=8: [])
    monkeypatch.setattr(
        chat_mod, "_searxng_html_fallback",
        lambda q, limit=8: [{"title": "HTML result", "url": "https://h.example/1", "snippet": "snip"}],
    )
    # provider must read as searxng for the fallback to engage
    from app.config import settings as real_settings

    monkeypatch.setattr(chat_mod, "WEB_TIMEOUT_SECONDS", 5.0)
    orig = real_settings.web_search_provider
    real_settings.web_search_provider = "searxng"
    try:
        out = chat_mod._web_search_budgeted(["some", "keywords"], 8)
    finally:
        real_settings.web_search_provider = orig
    assert len(out) == 1
    assert out[0]["kind"] == "web"
    assert out[0]["title"] == "HTML result"


# ---------------------------------------------------------------------------
# chat history API (RAM)
# ---------------------------------------------------------------------------

def test_chat_history_endpoints():
    from fastapi.testclient import TestClient

    from app.api.v1 import chat as chat_api
    from app.main import app

    client = TestClient(app)

    # clean slate
    r = client.delete("/api/v1/chat/history")
    assert r.status_code == 200
    assert r.json()["cleared"] >= 0

    # record a turn via the helper (what /ask uses internally)
    chat_api.record_turn("سؤال تستی", {"answer": "پاسخ", "online": True, "sources": [{"ref_no": 1}]})

    r = client.get("/api/v1/chat/history")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["turns"][0]["question"] == "سؤال تستی"
    assert data["turns"][0]["n_sources"] == 1

    # clear again
    r = client.delete("/api/v1/chat/history")
    assert r.status_code == 200
    assert r.json()["cleared"] == 1
    r = client.get("/api/v1/chat/history")
    assert r.json()["count"] == 0
