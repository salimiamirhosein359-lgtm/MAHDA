"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, type ItemListOut, type AskOut } from "@/lib/api";
import { CategoryFilter, CampFilter, TopNav, SectionHead, Empty, ErrorBox, SkeletonList } from "@/components/ui";
import ItemCard, { TrendChip } from "@/components/ItemCard";
import {
  RefreshCw, TrendingUp, FileText, Globe, BarChart3,
  Swords, Cpu, Brain, Wrench, FlaskConical, AppWindow, Landmark, MessageCircle,
  Send, Loader2, ExternalLink, Sparkles, Search,
} from "lucide-react";
import { toFa } from "@/lib/ui";
import type { TrendOut, RivalryOut } from "@/lib/api";

/* ---- Category icons ---- */
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

/* ---- Stat Card ---- */
function StatCard({ icon: Icon, label, value, color = "text-navy" }: {
  icon: React.ElementType; label: string; value: string; color?: string;
}) {
  return (
    <div className="flex items-center gap-4 p-5 bg-white border border-rule">
      <div className={`w-12 h-12 flex items-center justify-center bg-cgray-soft ${color}`}>
        <Icon size={22} strokeWidth={1.5} />
      </div>
      <div>
        <p className="text-[11px] font-bold uppercase tracking-wider text-ink-faint">{label}</p>
        <p className="font-serif text-2xl text-navy mt-0.5">{value}</p>
      </div>
    </div>
  );
}

/* ---- Chat inline ---- */
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
      {/* Search bar */}
      <div className="flex items-center gap-0 border border-rule bg-white focus-within:border-mblue transition-colors">
        <div className="pr-4 pl-2 text-ink-faint">
          <Search size={18} strokeWidth={1.5} />
        </div>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") send(); }}
          placeholder="هر سؤالی دارید بپرسید… (مثلاً: ایلان ماسک، DeepSeek، تراشه AI)"
          className="flex-1 py-3.5 text-sm outline-none bg-transparent placeholder:text-ink-faint/60"
        />
        <button
          onClick={send}
          disabled={loading || question.trim().length < 2}
          className="h-full px-5 py-3 bg-mblue text-white hover:bg-mblue-dark disabled:opacity-40 transition-colors flex items-center gap-2 text-sm font-bold"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} className="-scale-x-100" />}
          جستجو
        </button>
      </div>

      {/* Results */}
      {error && <ErrorBox text={error} />}
      {result && (
        <div className="mt-4 space-y-4 fade-up">
          {/* Answer text */}
          <div className="p-5 bg-cgray-soft border border-rule">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles size={15} className="text-mblue" />
              <span className="text-[11px] font-bold uppercase tracking-wider text-ink-faint">
                نتایج جستجو
                {result.online && (
                  <span className="text-mblue mr-2">· آنلاین</span>
                )}
              </span>
            </div>
            <div className="text-sm leading-[1.85] text-ink whitespace-pre-wrap">
              {result.answer}
            </div>
          </div>

          {/* Sources as cards */}
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

/* ---- Main Dashboard ---- */
export default function Dashboard() {
  const [data, setData] = useState<ItemListOut | null>(null);
  const [trends, setTrends] = useState<TrendOut[] | null>(null);
  const [rivalry, setRivalry] = useState<RivalryOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [category, setCategory] = useState("");
  const [camp, setCamp] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [items, t, r] = await Promise.all([
        api.items({ category: category || undefined, camp: camp || undefined, days: 7, limit: 50 }),
        api.trends(7, 12),
        api.rivalry(7, 5),
      ]);
      setData(items);
      setTrends(t);
      setRivalry(r);
    } catch (e) {
      setError(`خطا در دریافت داده‌ها: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  }, [category, camp]);

  useEffect(() => { load(); }, [load]);

  const usCount = rivalry?.us.count ?? 0;
  const cnCount = rivalry?.cn.count ?? 0;

  return (
    <div className="min-h-screen bg-cgray-soft flex flex-col">
      <TopNav />

      {/* Hero */}
      <section className="bg-navy text-white">
        <div className="max-w-6xl mx-auto px-4 py-14 md:py-20">
          <p className="text-[11px] font-bold uppercase tracking-[0.25em] text-mblue-400 mb-4">
            پایش هوش مصنوعی
          </p>
          <h1 className="font-serif text-3xl md:text-5xl leading-[1.3] max-w-3xl">
            رصد تحولات هوش مصنوعی
            <br />
            <span className="text-white/60">با دید تحلیلی و داده‌محور</span>
          </h1>
        </div>
      </section>

      {/* Stats */}
      <section className="max-w-6xl mx-auto px-4 -mt-6 w-full relative z-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard icon={FileText} label="آیتم ۷ روز" value={data ? toFa(data.total) : "—"} />
          <StatCard icon={Globe} label="آمریکا 🇺🇸" value={toFa(usCount)} color="text-mblue" />
          <StatCard icon={Globe} label="چین 🇨🇳" value={toFa(cnCount)} color="text-mred" />
          <StatCard icon={TrendingUp} label="کلیدواژه داغ" value={trends ? toFa(trends.length) : "—"} />
        </div>
      </section>

      <main className="max-w-6xl mx-auto px-4 py-8 w-full flex-1 space-y-10">

        {/* Inline Chat / Search */}
        <section>
          <SectionHead
            icon={MessageCircle}
            kicker="گفت‌وگو"
            title="از آرشیو و اینترنت بپرسید"
          />
          <InlineChat />
        </section>

        {/* Rivalry mini */}
        {rivalry && (
          <section>
            <SectionHead icon={Swords} kicker="رقابت" title="چین و آمریکا" meta="۷ روز اخیر" />
            <div className="flex items-center gap-0 h-10 border border-rule overflow-hidden">
              <div
                className="h-full bg-mblue flex items-center justify-center text-white text-xs font-bold px-3 transition-all"
                style={{ width: `${Math.max(usCount / Math.max(usCount + cnCount, 1) * 100, 20)}%` }}
              >
                🇺🇸 {toFa(usCount)}
              </div>
              <div
                className="h-full bg-mred flex items-center justify-center text-white text-xs font-bold px-3 transition-all"
                style={{ width: `${Math.max(cnCount / Math.max(usCount + cnCount, 1) * 100, 20)}%` }}
              >
                🇨🇳 {toFa(cnCount)}
              </div>
            </div>
          </section>
        )}

        {/* Trends */}
        {trends && trends.length > 0 && (
          <section>
            <SectionHead icon={TrendingUp} kicker="روندها" title="کلیدواژه‌های پرتکرار" meta="۷ روز اخیر" />
            <div className="flex flex-wrap gap-2">
              {trends.slice(0, 12).map((t) => (
                <TrendChip key={t.keyword} keyword={t.keyword} count={t.count} />
              ))}
            </div>
          </section>
        )}

        {/* News Feed */}
        <section id="feed">
          <div className="flex items-end justify-between mb-5 border-b border-rule pb-4">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-mblue mb-2">پایش</p>
              <h2 className="font-serif text-2xl md:text-[28px] leading-tight text-navy">
                آخرین اخبار و تحلیل‌ها
              </h2>
            </div>
            <button
              onClick={load}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 border border-navy text-navy text-sm font-bold hover:bg-navy hover:text-white disabled:opacity-40 transition-colors"
            >
              <RefreshCw size={15} strokeWidth={1.5} className={loading ? "animate-spin" : ""} />
              به‌روزرسانی
            </button>
          </div>

          <div className="space-y-3 mb-6">
            <CategoryFilter value={category} onChange={setCategory} />
            <CampFilter value={camp} onChange={setCamp} />
          </div>

          {loading && !data ? (
            <SkeletonList n={5} />
          ) : error ? (
            <ErrorBox text={error} />
          ) : data && data.items.length === 0 ? (
            <Empty text="هیچ آیتمی با این فیلترها پیدا نشد" />
          ) : data ? (
            <div>
              {data.items.map((item) => (
                <ItemCard key={item.id} item={item} />
              ))}
            </div>
          ) : null}
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-navy text-white/50">
        <div className="max-w-6xl mx-auto px-4 py-8 text-xs text-center">
          © AI Sentinel — رصد و تحلیل تحولات هوش مصنوعی
        </div>
      </footer>
    </div>
  );
}
