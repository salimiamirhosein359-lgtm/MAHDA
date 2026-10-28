"""AI Sentinel — rule-based classification (no LLM required).

Keyword-weighted classification of monitored items into:
- category: infrastructure|models|algorithms|tools|evals|applications|policy_economy|discourse|other
- camp:     US|CN|EU|other
- actor:    main person/org mentioned

Also provides ``strip_html`` to clean HTML leakage out of RSS summaries.
"""
import re

# ---------------------------------------------------------------------------
# Rule tables: category / camp / actor — weighted keyword phrases
# ---------------------------------------------------------------------------

CATEGORY_RULES: dict[str, list[str]] = {
    "infrastructure": [
        "gpu", "chip", "semiconductor", "nvidia", "tsmc", "datacenter", "data center",
        "h100", "b200", "blackwell", "wafer", "foundry", "export control", "asml",
        "cuda", "tpu", "accelerator", "compute cluster", "supercomputer",
        "power grid", "nuclear plant",
    ],
    "models": [
        "model", "gpt-", "chatgpt", "claude", "gemini", "llama", "qwen", "deepseek",
        "ernie", "hunyuan", "doubao", "kimi", "glm-", "mistral", "grok", "release",
        "weights", "open-weights", "multimodal", "foundation model", "llm",
        "frontier model", "openai", "anthropic", "xai", "o1", "o3", "o4",
    ],
    "algorithms": [
        "attention", "transformer", "quantization", "distillation", "rlhf", "dpo",
        "fine-tun", "sparse", "mixture of experts", "moe", "scaling law",
        "inference optimization", "algorithm", "neural network", "diffusion model",
        "gan", "autoregressive", "beam search", "tokenization",
    ],
    "tools": [
        "framework", "library", "sdk", "langchain", "vllm", "pytorch", "tensorflow",
        "jax", "open-source", "github", "agent", "copilot", "tool",
        "benchmark harness", "mcp", "server", "api", "extension", "plugin",
    ],
    "evals": [
        "benchmark", "mmlu", "swe-bench", "leaderboard", "eval", "score",
        "test set", "arena", "elo", "human eval", "math-bench", "gpqa", "humaneval",
    ],
    "applications": [
        "healthcare", "medical", "legal", "finance", "education", "robot",
        "autonomous", "enterprise", "customer service", "assistant", "coding",
        "developer", "search", "translation", "drug", "protein", "folding",
        "diagnosis", "copilot for",
    ],
    "policy_economy": [
        "regulation", "policy", "government", "eu ai act", "ban", "law", "senate",
        "congress", "ministry", "investment", "funding", "ipo", "acquisition",
        "billion", "market", "tariff", "sanction", "export curb", "beijing",
        "washington", "white house", "state department", "national security",
    ],
    "discourse": [
        "says", "claims", "criticiz", "debate", "controvers", "interview", "opinion",
        "essay", "memo", "open letter", "warning", "ai doom", "agi timeline",
        "predict", "forecast",
    ],
}

CAMP_RULES: dict[str, list[str]] = {
    "CN": [
        "china", "chinese", "beijing", "huawei", "alibaba", "baidu", "bytedance",
        "tencent", "deepseek", "qwen", "zhipu", "moonshot", "kimi", "ernie",
        "hunyuan", "doubao", "sensecore", "minimax", "01.ai", "scmp", "technode",
        "shanghai", "shenzhen", "hangzhou", "china's",
    ],
    "US": [
        "openai", "anthropic", "google", "microsoft", "meta", "nvidia", "amazon",
        "apple", "xai", "tesla", "musk", "altman", "pdd", "usa", "u.s.",
        "american", "white house", "washington", "san francisco", "seattle",
        "starline", "palo alto", "wall street", "silicon valley",
    ],
    "EU": [
        "eu ", "europe", "european", "brussels", "germany", "france", "uk ",
        "britain", "mistral", "deepmind london", "london", "paris", "berlin",
        "european union", "ai act",
    ],
}

ACTOR_RULES: dict[str, list[str]] = {
    "OpenAI": ["openai", "chatgpt", "gpt-", "sam altman", "altman"],
    "Anthropic": ["anthropic", "claude", "dario amodei"],
    "Google DeepMind": ["google", "deepmind", "gemini", "demis hassabis"],
    "Meta AI": ["meta", "llama", "yann lecun"],
    "Nvidia": ["nvidia", "jensen huang", "blackwell", "h100"],
    "Microsoft": ["microsoft", "copilot", "satya nadella"],
    "xAI": ["xai", "grok", "elon musk"],
    "DeepSeek": ["deepseek"],
    "Alibaba/Qwen": ["qwen", "alibaba"],
    "ByteDance": ["bytedance", "doubao"],
    "Moonshot/Kimi": ["kimi", "moonshot"],
    "Zhipu/GLM": ["zhipu", "glm-"],
    "Huawei": ["huawei", "ascend"],
    "China govt": ["beijing", "china's government", "chinese government"],
    "US govt": ["white house", "u.s. government", "washington"],
}

# Generic AI keywords — used to fall back to "models" when nothing else matched
GENERIC_AI_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "gpt", "chatgpt", "machine learning",
    "neural network", "deep learning", "inference", "training", "model",
]

# Strong gate keywords — a single hit is enough to pass the AI gate
STRONG_GATE_KEYWORDS = ["openai", "nvidia", "deepseek", "anthropic", "gemini",
                         "claude", "chatgpt", "llm", "gpt"]

# ---------------------------------------------------------------------------
# HTML cleaning
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

# Common HTML entities (named + numeric) leaked from RSS summaries
_HTML_ENTITIES = {
    "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
    "&#39;": "'", "&apos;": "'", "&hellip;": "…", "&mdash;": "—", "&ndash;": "–",
    "&#8216;": "'", "&#8217;": "'", "&#8220;": '"', "&#8221;": '"',
    "&#8230;": "…", "&#8212;": "—", "&#8211;": "–",
    "&#160;": " ", "&nbsp": " ", "&laquo;": "«", "&raquo;": "»",
    "&#171;": "«", "&#187;": "»", "&copy;": "©", "&reg;": "®",
    "&trade;": "™", "&pound;": "£", "&euro;": "€", "&bull;": "•",
}
_ENTITY_RE = re.compile(r"&#(\d+);?")
_MULTISPACE_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    """Remove HTML tags, comments, and common entities; collapse whitespace.

    Handles the typical leakage seen in RSS summaries (``<figure><img ...>`` etc.)
    and numeric entities such as ``&#8230;`` (rendered as ``8230`` after naive
    stripping). Returns ``""`` for falsy input.
    """
    if not text:
        return ""
    out = _HTML_COMMENT_RE.sub(" ", text)
    out = _HTML_TAG_RE.sub(" ", out)
    # named + fixed numeric entities
    for ent, rep in _HTML_ENTITIES.items():
        out = out.replace(ent, rep)
    # any remaining numeric entities → their character (or dropped when unknown)
    out = _ENTITY_RE.sub(
        lambda m: chr(int(m.group(1))) if int(m.group(1)) < 0x110000 else " ", out
    )
    out = _MULTISPACE_RE.sub(" ", out)
    return out.strip()


# ---------------------------------------------------------------------------
# Rule-based classification
# ---------------------------------------------------------------------------

# Valid values (used to clamp LLM output too)
VALID_CATEGORIES = set(CATEGORY_RULES.keys()) | {"other"}
VALID_CAMPS = {"US", "CN", "EU", "other"}


def _count_matches(low_text: str, phrases: list[str]) -> int:
    """Count how many keyword phrases occur (case-insensitive, whole phrase)."""
    return sum(1 for p in phrases if p in low_text)


def _best_rule(low_text: str, rules: dict[str, list[str]]) -> tuple[str, int, int]:
    """Return (best_key, best_match_count, second_best_count) for a rule table."""
    best_key, best_n, second_n = "other", 0, 0
    for key, phrases in rules.items():
        n = _count_matches(low_text, phrases)
        if n > best_n:
            second_n = best_n
            best_n = n
            best_key = key
        elif n > second_n:
            second_n = n
    return best_key, best_n, second_n


def classify_by_rules(text: str) -> dict:
    """Classify text with weighted keywords. No LLM calls.

    Returns ``{"category": str, "camp": str, "actor": str|None, "confidence": float}``.
    - category: most keyword matches wins; "models" if generic AI keywords are
      present but nothing matched; otherwise "other".
    - camp: same winner-takes-most logic over CAMP_RULES.
    - confidence: matches / max(matches) between top-1 and top-2 categories.
    """
    if not text:
        return {"category": "other", "camp": "other", "actor": None, "confidence": 0.0}

    low = strip_html(text).lower()

    # --- category ---
    cat, cat_n, cat_second = _best_rule(low, CATEGORY_RULES)
    if cat_n == 0:
        if any(kw in low for kw in GENERIC_AI_KEYWORDS):
            cat = "models"
        else:
            cat = "other"

    # --- camp ---
    camp, camp_n, _ = _best_rule(low, CAMP_RULES)
    if camp_n == 0:
        camp = "other"

    # --- actor: first actor whose keywords all-or-any match; prefer more matches ---
    actor, actor_n = None, 0
    for name, phrases in ACTOR_RULES.items():
        n = _count_matches(low, phrases)
        if n > actor_n:
            actor, actor_n = name, n

    # --- confidence ---
    denom = max(cat_n, cat_second)
    confidence = round(cat_n / denom, 2) if denom else (0.6 if cat == "models" else 0.0)

    return {
        "category": cat,
        "camp": camp,
        "actor": actor,
        "confidence": confidence,
    }
