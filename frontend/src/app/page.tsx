"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type ItemListOut, type AskOut } from "@/lib/api";
import { TopNav, ErrorBox, SkeletonList } from "@/components/ui";
import ItemCard from "@/components/ItemCard";
import {
  Search, Send, Loader2, ExternalLink, Sparkles,
  Cpu, Brain, Wrench, FlaskConical, BarChart3, AppWindow, Landmark, MessageCircle,
} from "lucide-react";
import { toFa, CATEGORIES } from "@/lib/ui";

/* ---- Category icons for grid ---- */
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

/* ---- Inline Chat ---- */
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
      const answer = await api.ask(question.trim(), true);
      setResult(answer);
    } catch (e) {
      setError(`خطا: ${e instanceof Error ? e.message : "نامشخص"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center border border-rule bg-white focus-within:border-mblue transition-colors">
        <div className="pr-4 pl-2 text-ink-faint">
          <Search size={18} strokeWidth={1.5} />
        </div>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") send(); }}
          placeholder="هر سؤالی دارید بپرسید…"
          className="flex-1 py-3.5 text-sm outline-none bg-transparent placeholder:text-ink-faint/60"
        />
        <button
          onClick={send}
          disabled={loading || question.trim().length < 2}
          className="h-full px-5 py-3 bg-mblue text-white hover:bg-mblue-dark disabled:opacity-40 transition-colors flex items-center gap-2 text-sm font-bold"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} className="-scale-x-100" />}
          ارسال
        </button>
      </div>

      {error && <div className="mt-3"><ErrorBox text={error} /></div>}

      {result && (
        <div className="mt-4 space-y-4 fade-up">
          <div className="p-5 bg-white border border-rule">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles size={15} className="text-mblue" />
              <span className="text-[11px] font-bold uppercase tracking-wider text-ink-faint">
                نتایج
              </span>
            </div>
            <div className="text-sm leading-[1.85] text-ink whitespace-pre-wrap">
              {result.answer}
            </div>
          </div>
          {result.sources.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {result.sources.slice(0, 8).map((s) => (
                <a
                  key={s.ref_no}
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex items-start gap-3 p-4 border border-rule bg-white hover:border-mblue transition-colors"
                >
                  <span className="shrink-0 w-7 h-7 border border-rule flex items-center justify-center font-serif text-navy text-sm">
                    {toFa(s.ref_no)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-navy group-hover:text-mblue transition-colors line-clamp-2">{s.title}</p>
                    {s.snippet && <p className="text-xs text-ink-faint mt-1 line-clamp-2">{s.snippet}</p>}
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

/* ---- Category Card ---- */
function CategoryCard({
  cat,
  icon: Icon,
  active,
  onClick,
}: {
  cat: { value: string; label: string };
  icon: React.ElementType;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center justify-center gap-2 p-4 border transition-all ${
        active
          ? "bg-navy text-white border-navy"
          : "bg-white text-navy border-rule hover:border-mblue hover:text-mblue"
      }`}
    >
      <Icon size={24} strokeWidth={1.5} />
      <span className="text-xs font-bold">{cat.label}</span>
    </button>
  );
}

/* ---- Main ---- */
export default function Dashboard() {
  const [data, setData] = useState<ItemListOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [category, setCategory] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const items = await api.items({
        category: category || undefined,
        days: 30,
        limit: 10,
      });
      setData(items);
    } catch (e) {
      setError(`خطا: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => { load(); }, [load]);

  const cats = CATEGORIES.filter((c) => c.value !== "");

  return (
    <div className="min-h-screen bg-cgray-soft flex flex-col">
      <TopNav />

      {/* Hero */}
      <section className="bg-navy text-white">
        <div className="max-w-4xl mx-auto px-4 py-16 md:py-20 text-center">
          <h1 className="font-serif text-3xl md:text-5xl leading-[1.3]">
            رصد تحولات هوش مصنوعی
          </h1>
        </div>
      </section>

      <main className="max-w-5xl mx-auto px-4 py-8 w-full flex-1 space-y-10">

        {/* Chat */}
        <section className="-mt-8 relative z-10">
          <InlineChat />
        </section>

        {/* Category grid */}
        <section>
          <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
            {cats.map((c) => {
              const Icon = CAT_ICONS[c.value] || Brain;
              return (
                <CategoryCard
                  key={c.value}
                  cat={c}
                  icon={Icon}
                  active={category === c.value}
                  onClick={() => setCategory(category === c.value ? "" : c.value)}
                />
              );
            })}
          </div>
          {category && (
            <button
              onClick={() => setCategory("")}
              className="mt-3 text-xs text-mblue hover:underline"
            >
              ← نمایش همه دسته‌ها
            </button>
          )}
        </section>

        {/* Latest 10 news */}
        <section>
          <div className="flex items-end justify-between mb-5 border-b border-rule pb-4">
            <h2 className="font-serif text-xl md:text-2xl text-navy">
              {category ? CATEGORIES.find((c) => c.value === category)?.label ?? "اخبار" : "آخرین اخبار"}
            </h2>
            <span className="text-xs text-ink-faint">
              {data ? `${toFa(data.total)} مورد` : ""}
            </span>
          </div>

          {loading && !data ? (
            <SkeletonList n={5} />
          ) : error ? (
            <ErrorBox text={error} />
          ) : data && data.items.length === 0 ? (
            <div className="py-16 text-center text-ink-faint text-sm">
              هیچ خبری در این دسته پیدا نشد
            </div>
          ) : data ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.items.map((item) => (
                <ItemCard key={item.id} item={item} />
              ))}
            </div>
          ) : null}
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-navy text-white/50">
        <div className="max-w-5xl mx-auto px-4 py-6 text-xs text-center">
          © AI Sentinel — رصد تحولات هوش مصنوعی
        </div>
      </footer>
    </div>
  );
}
