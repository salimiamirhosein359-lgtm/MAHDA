"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type ItemListOut, type AskOut } from "@/lib/api";
import { TopNav, ErrorBox } from "@/components/ui";
import ItemCard from "@/components/ItemCard";
import {
  Search, ArrowUp, Loader2, ExternalLink, Sparkles, Radar,
  Cpu, Brain, Wrench, FlaskConical, BarChart3, AppWindow, Landmark, MessageCircle,
} from "lucide-react";
import { toFa, CATEGORIES, CAT_STYLE } from "@/lib/ui";

const CAT_ICONS: Record<string, React.ElementType> = {
  infrastructure: Cpu,
  models: Brain,
  algorithms: FlaskConical,
  tools: Wrench,
  evals: BarChart3,
  applications: AppWindow,
  policy_economy: Landmark,
  discourse: MessageCircle,
};

/* ---- Chat / search (Perplexity-style floating bar) ---- */
function InlineChat() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskOut | null>(null);
  const [error, setError] = useState("");

  const send = async () => {
    if (question.trim().length < 2 || loading) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await api.ask(question.trim(), true));
    } catch (e) {
      setError(`خطا: ${e instanceof Error ? e.message : "نامشخص"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center bg-white rounded-2xl shadow-search ring-1 ring-black/5 focus-within:ring-2 focus-within:ring-mblue transition-all p-2">
        <Search size={20} strokeWidth={1.8} className="mx-3 text-ink-faint shrink-0" />
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") send(); }}
          placeholder="هر سؤالی دارید بپرسید…"
          className="flex-1 py-3 text-[15px] outline-none bg-transparent placeholder:text-ink-faint"
        />
        <button
          onClick={send}
          disabled={loading || question.trim().length < 2}
          aria-label="ارسال"
          className="w-11 h-11 rounded-xl bg-gradient-to-br from-emerald-500 to-sky-600 text-white disabled:opacity-40 hover:brightness-110 transition flex items-center justify-center shrink-0"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <ArrowUp size={19} strokeWidth={2.2} />}
        </button>
      </div>

      {error && <div className="mt-3"><ErrorBox text={error} /></div>}

      {result && (
        <div className="mt-5 space-y-4 fade-up text-right">
          <div className="p-6 bg-white rounded-2xl shadow-card">
            <div className="flex items-center gap-2 mb-3 text-mblue">
              <Sparkles size={16} />
              <span className="text-xs font-bold">پاسخ</span>
            </div>
            <div className="text-sm leading-[1.95] text-ink whitespace-pre-wrap">{result.answer}</div>
          </div>
          {result.sources.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {result.sources.slice(0, 8).map((s) => (
                <a
                  key={s.ref_no}
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex items-start gap-3 p-4 rounded-xl bg-white shadow-card hover:shadow-lift transition-all"
                >
                  <span className="shrink-0 w-7 h-7 rounded-lg bg-lblue-soft text-mblue-dark flex items-center justify-center text-xs font-bold">
                    {toFa(s.ref_no)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-navy group-hover:text-mblue transition-colors line-clamp-2" dir="auto">{s.title}</p>
                    {s.snippet && <p className="text-xs text-ink-faint mt-1 line-clamp-2" dir="auto">{s.snippet}</p>}
                  </div>
                  <ExternalLink size={14} className="text-ink-faint group-hover:text-mblue shrink-0 mt-1" />
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ---- Category tile: gradient icon, soft card, lift on hover ---- */
function CategoryTile({
  value, label, active, onClick,
}: { value: string; label: string; active: boolean; onClick: () => void }) {
  const Icon = CAT_ICONS[value] || Brain;
  const st = CAT_STYLE[value] ?? CAT_STYLE._default;
  return (
    <button
      onClick={onClick}
      className={`group flex flex-col items-center gap-3 px-3 py-5 rounded-2xl transition-all duration-200 ${
        active
          ? "bg-white shadow-lift ring-2 ring-mblue -translate-y-0.5"
          : "bg-white shadow-card hover:shadow-lift hover:-translate-y-0.5"
      }`}
    >
      <span className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${st.grad} text-white flex items-center justify-center shadow-md group-hover:scale-105 transition-transform`}>
        <Icon size={22} strokeWidth={1.8} />
      </span>
      <span className={`text-[13px] font-bold ${active ? "text-mblue" : "text-navy"}`}>{label}</span>
    </button>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<ItemListOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [category, setCategory] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await api.items({ category: category || undefined, days: 30, limit: 10 }));
    } catch (e) {
      setError(`خطا: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => { load(); }, [load]);

  const cats = CATEGORIES.filter((c) => c.value !== "");
  const activeLabel = cats.find((c) => c.value === category)?.label;

  return (
    <div className="min-h-screen bg-cgray-soft flex flex-col">
      <TopNav />

      {/* Hero */}
      <section className="hero-bg text-white">
        <div className="hero-grid" />
        <div className="relative max-w-3xl mx-auto px-4 pt-16 pb-28 text-center">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 ring-1 ring-white/20 text-xs mb-6 backdrop-blur">
            <Radar size={14} />
            <span>پایش لحظه‌ای</span>
          </div>
          <h1 className="text-3xl md:text-5xl font-extrabold leading-[1.4]">رصد تحولات هوش مصنوعی</h1>
        </div>
      </section>

      <main className="max-w-5xl mx-auto px-4 w-full flex-1 pb-16">
        {/* Floating search overlapping the hero */}
        <section className="-mt-14 relative z-10 max-w-3xl mx-auto">
          <InlineChat />
        </section>

        {/* Categories */}
        <section className="mt-12">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 md:gap-4">
            {cats.map((c) => (
              <CategoryTile
                key={c.value}
                value={c.value}
                label={c.label}
                active={category === c.value}
                onClick={() => setCategory(category === c.value ? "" : c.value)}
              />
            ))}
          </div>
        </section>

        {/* Latest news */}
        <section className="mt-12">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl md:text-2xl font-extrabold text-navy flex items-center gap-3">
              <span className="w-1.5 h-7 rounded-full bg-gradient-to-b from-emerald-400 to-sky-500" />
              {activeLabel ? `آخرین خبرهای ${activeLabel}` : "آخرین اخبار"}
            </h2>
            {category && (
              <button onClick={() => setCategory("")} className="text-xs font-bold text-mblue hover:underline">
                نمایش همه
              </button>
            )}
          </div>

          {loading && !data ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="bg-white rounded-2xl shadow-card p-5">
                  <div className="skeleton h-4 w-20 rounded-full mb-4" />
                  <div className="skeleton h-5 w-5/6 rounded mb-2" />
                  <div className="skeleton h-5 w-2/3 rounded mb-5" />
                  <div className="skeleton h-3 w-full rounded" />
                </div>
              ))}
            </div>
          ) : error ? (
            <ErrorBox text={error} />
          ) : data && data.items.length === 0 ? (
            <div className="py-16 text-center text-ink-faint text-sm bg-white rounded-2xl shadow-card">
              هیچ خبری در این دسته پیدا نشد
            </div>
          ) : data ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {data.items.map((item) => <ItemCard key={item.id} item={item} />)}
            </div>
          ) : null}
        </section>
      </main>

      <footer className="bg-navy text-white/60">
        <div className="max-w-5xl mx-auto px-4 py-6 text-xs text-center">© AI Sentinel — رصد تحولات هوش مصنوعی</div>
      </footer>
    </div>
  );
}
