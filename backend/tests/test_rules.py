"""AI Sentinel — rule-based classifier tests (no DB / no LLM needed)."""
from app.pipeline.rules import (
    CAMP_RULES,
    CATEGORY_RULES,
    classify_by_rules,
    strip_html,
)


# ------------------------------- strip_html --------------------------------

def test_strip_html_removes_figure_img():
    text = (
        "<figure><img src=\"https://example.com/pic.jpg\" alt=\"Nvidia chip\">"
        "<figcaption>Nvidia's new Blackwell GPU&#8230;</figcaption></figure>"
        " Nvidia announced the B200 chip today."
    )
    out = strip_html(text)
    assert "<" not in out
    assert ">" not in out
    assert "img" not in out
    assert "http" not in out
    assert "8230" not in out  # numeric entity decoded, not left as digits
    assert "B200" in out
    assert "announced" in out


def test_strip_html_entities_and_whitespace():
    text = "OpenAI&nbsp;&nbsp;released&nbsp;GPT-5 &amp; more&#8230;   today   "
    out = strip_html(text)
    assert out == "OpenAI released GPT-5 & more… today"


def test_strip_html_empty_and_plain():
    assert strip_html("") == ""
    assert strip_html(None) == ""
    assert strip_html("plain text") == "plain text"


# ------------------------------- category ---------------------------------

def test_category_infrastructure():
    text = "TSMC wafer foundry output hit by power grid issues; Nvidia GPU supply tight."
    assert classify_by_rules(text)["category"] == "infrastructure"


def test_category_models():
    text = "OpenAI released GPT-5 weights for chatgpt plus users, a new llm model."
    assert classify_by_rules(text)["category"] == "models"


def test_category_models_fallback_for_generic_ai():
    text = "A new study on artificial intelligence training methods."
    assert classify_by_rules(text)["category"] == "models"


def test_category_other_when_no_match():
    text = "The football team won the championship game yesterday evening."
    assert classify_by_rules(text)["category"] == "other"


def test_category_policy_economy():
    text = "The EU AI act regulation passed congress with new export control curbs."
    assert classify_by_rules(text)["category"] == "policy_economy"


# --------------------------------- camp ------------------------------------

def test_camp_cn():
    text = "Beijing pushes Huawei and Alibaba to speed up domestic chip making in China."
    assert classify_by_rules(text)["camp"] == "CN"


def test_camp_us():
    text = "OpenAI and Nvidia met the White House about the new Washington accord."
    assert classify_by_rules(text)["camp"] == "US"


def test_camp_eu():
    text = "Brussels and the European Union discuss the AI act with Mistral in Paris."
    assert classify_by_rules(text)["camp"] == "EU"


def test_camp_other_when_no_match():
    text = "A new research method for protein folding prediction."
    assert classify_by_rules(text)["camp"] == "other"


# --------------------------------- actor -----------------------------------

def test_actor_openai():
    text = "Sam Altman says OpenAI will release new models soon."
    res = classify_by_rules(text)
    assert res["actor"] == "OpenAI"


def test_actor_deepseek():
    res = classify_by_rules("DeepSeek publishes a cheap training recipe for reasoning models.")
    assert res["actor"] == "DeepSeek"


# ------------------------------- structure --------------------------------

def test_result_shape_and_confidence():
    res = classify_by_rules("Nvidia GPU and TSMC foundry news about chips and wafers.")
    assert set(res.keys()) == {"category", "camp", "actor", "confidence"}
    assert isinstance(res["confidence"], float)
    assert 0.0 <= res["confidence"] <= 1.0
    assert res["category"] == "infrastructure"


def test_rule_tables_nonempty():
    for cat, kws in CATEGORY_RULES.items():
        assert kws, f"empty keyword list for {cat}"
    for camp, kws in CAMP_RULES.items():
        assert kws, f"empty keyword list for {camp}"
