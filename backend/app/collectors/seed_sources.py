"""AI Sentinel — seed sources (groups A-D from ARCHITECTURE.md).

Groups:
  A = technical/research        (arxiv, github, hf...)
  B = reputable outlets         (Economist, McKinsey, MIT TR...)
  C = people/companies/policy   (lab blogs, execs, regulators...)
  D = geopolitics China-US      (rivalry sources...)
Camps: US | CN | EU | other — used by the Rivalry dashboard.
"""

SEED_SOURCES = [
    # ---------- Group A — technical (handled by dedicated collectors, rss fallbacks) ----------
    {"name": "arxiv", "kind": "arxiv", "group": "A", "camp": "other", "weight": 0.9, "config": {}},
    {"name": "github-ai", "kind": "github", "group": "A", "camp": "other", "weight": 0.7, "config": {}},

    # ---------- Group B — reputable analytical outlets ----------
    {"name": "mit-tech-review", "kind": "rss", "group": "B", "camp": "other", "weight": 0.8,
     "config": {"url": "https://www.technologyreview.com/feed/"}},
    {"name": "wired", "kind": "rss", "group": "B", "camp": "other", "weight": 0.7,
     "config": {"url": "https://www.wired.com/feed/rss"}},
    {"name": "the-verge-ai", "kind": "rss", "group": "B", "camp": "US", "weight": 0.7,
     "config": {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"}},
    {"name": "techcrunch-ai", "kind": "rss", "group": "B", "camp": "US", "weight": 0.8,
     "config": {"url": "https://techcrunch.com/category/artificial-intelligence/feed/"}},
    {"name": "venturebeat-ai", "kind": "rss", "group": "B", "camp": "US", "weight": 0.7,
     "config": {"url": "https://venturebeat.com/category/ai/feed/"}},
    {"name": "the-decoder", "kind": "rss", "group": "B", "camp": "other", "weight": 0.8,
     "config": {"url": "https://the-decoder.com/feed/"}},
    {"name": "marktechpost", "kind": "rss", "group": "B", "camp": "other", "weight": 0.6,
     "config": {"url": "https://www.marktechpost.com/feed/"}},
    {"name": "the-economist-tech", "kind": "rss", "group": "B", "camp": "EU", "weight": 0.9,
     "config": {"url": "https://www.economist.com/technology-quarterly/rss.xml"}},

    # ---------- Group C — labs, execs, policy ----------
    {"name": "openai-blog", "kind": "rss", "group": "C", "camp": "US", "weight": 1.0,
     "config": {"url": "https://openai.com/blog/rss.xml"}},
    {"name": "anthropic-news", "kind": "rss", "group": "C", "camp": "US", "weight": 1.0,
     "config": {"url": "https://www.anthropic.com/rss.xml"}},
    {"name": "google-deepmind-blog", "kind": "rss", "group": "C", "camp": "US", "weight": 0.9,
     "config": {"url": "https://deepmind.google/blog/rss.xml"}},
    {"name": "meta-ai-blog", "kind": "rss", "group": "C", "camp": "US", "weight": 0.8,
     "config": {"url": "https://ai.meta.com/blog/rss/"}},
    {"name": "huggingface-blog", "kind": "rss", "group": "C", "camp": "other", "weight": 0.8,
     "config": {"url": "https://huggingface.co/blog/feed.xml"}},
    {"name": "reddit-machinelearning", "kind": "rss", "group": "C", "camp": "other", "weight": 0.4,
     "config": {"url": "https://www.reddit.com/r/MachineLearning/.rss"}},
    {"name": "reddit-localllama", "kind": "rss", "group": "C", "camp": "other", "weight": 0.4,
     "config": {"url": "https://www.reddit.com/r/LocalLLaMA/.rss"}},

    # ---------- Group C — Chinese labs (via mirrors/aggregators where RSS exists) ----------
    {"name": "huggingface-papers", "kind": "rss", "group": "A", "camp": "other", "weight": 0.7,
     "config": {"url": "https://huggingface.co/papers/"}},

    # ---------- Group D — geopolitics: China-US rivalry ----------
    {"name": "scmp-tech", "kind": "rss", "group": "D", "camp": "CN", "weight": 0.8,
     "config": {"url": "https://www.scmp.com/rss/4/feed"}},
    {"name": "reuters-technology", "kind": "rss", "group": "D", "camp": "other", "weight": 0.9,
     "config": {"url": "https://feeds.reuters.com/reuters/technologyNews"}},
    {"name": "technode", "kind": "rss", "group": "D", "camp": "CN", "weight": 0.7,
     "config": {"url": "https://technode.com/feed/"}},
]
