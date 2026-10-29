"use client";

import { useState } from "react";
import { api, type AskOut } from "@/lib/api";
import { TopNav, SectionHead, ErrorBox } from "@/components/ui";
import {
  GraduationCap, Search, Loader2, Globe, FileText,
  ExternalLink, Sparkles, Database, Wifi,
} from "lucide-react";
import { toFa } from "@/lib/ui";

export default function ResearchPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AskOut | null>(null);
  const [mode, setMode] = useState<"memory" | "online">("memory");

  const search = async () => {
    if (question.trim().length < 2 || loading) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      if (mode === "online") {
        const onlineResult = await api.ask(question.trim(), true);
        setResult(onlineResult);
      } else {
        const memoryResult = await api.ask(question.trim(), false);
        setResult(memoryResult);
      }
    } catch (e) {
      setError(`خطا: ${e instanceof Error ? e.message : "نامشخص"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cgray-soft flex flex-col">
      <TopNav />

      {/* Hero */}
      <section className="hero-bg text-white"><div className="hero-grid" />
        <div className="relative max-w-4xl mx-auto px-4 pt-14 pb-24 text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-400 to-sky-500 flex items-center justify-center mx-auto mb-5 shadow-lg">
            <GraduationCap size={28} strokeWidth={1.5} />
          </div>
          <h1 className="text-3xl md:text-4xl leading-[1.3]">
            دستیار پژوهشی
          </h1>
          <p className="mt-3 text-white/60 text-sm max-w-lg mx-auto leading-[1.85]">
            ابتدا در آرشیو ۱۷ هزار مقاله و خبر جمع‌آوری‌شده جستجو می‌کند، سپس در صورت نیاز به اینترنت مراجعه می‌کند.
          </p>
        </div>
      </section>

      <main className="max-w-4xl mx-auto px-4 py-8 w-full flex-1">
        {/* Search box */}
        <div className="bg-white rounded-2xl shadow-search p-6 -mt-14 relative z-10">
          <div className="flex items-center gap-3 mb-4">
            <button
              onClick={() => setMode("memory")}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-bold border transition-all ${
                mode === "memory"
                  ? "bg-navy text-white border-navy"
                  : "text-ink-dim border-rule hover:border-navy"
              }`}
            >
              <Database size={15} strokeWidth={1.5} />
              جستجو در حافظه
            </button>
            <button
              onClick={() => setMode("online")}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-bold border transition-all ${
                mode === "online"
                  ? "bg-mblue text-white border-mblue"
                  : "text-ink-dim border-rule hover:border-mblue"
              }`}
            >
              <Wifi size={15} strokeWidth={1.5} />
              حافظه + اینترنت
            </button>
          </div>

          <div className="flex items-center gap-0 border border-rule focus-within:border-mblue transition-colors">
            <div className="pr-4 pl-2 text-ink-faint">
              <Search size={18} strokeWidth={1.5} />
            </div>
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") search(); }}
              placeholder="موضوع یا عبارت مورد نظر را وارد کنید…"
              className="flex-1 py-3.5 text-sm outline-none bg-transparent placeholder:text-ink-faint/60"
            />
            <button
              onClick={search}
              disabled={loading || question.trim().length < 2}
              className="px-6 py-3.5 bg-navy text-white text-sm font-bold hover:bg-navy-soft disabled:opacity-40 transition-colors flex items-center gap-2"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
              جستجو
            </button>
          </div>

          <p className="mt-3 text-[11px] text-ink-faint">
            {mode === "memory"
              ? "🗄️ فقط در آرشیو داخلی (مقالات، اخبار و کتاب‌ها) جستجو می‌شود"
              : "🌐 ابتدا آرشیو، سپس منابع آنلاین (گوگل، بینگ، ویکی‌پدیا و...)"}
          </p>
        </div>

        {error && <div className="mt-4"><ErrorBox text={error} /></div>}

        {loading && (
          <div className="mt-8 text-center">
            <Loader2 size={28} className="animate-spin text-mblue mx-auto mb-3" />
            <p className="text-sm text-ink-faint">
              {mode === "memory" ? "در حال جستجوی آرشیو…" : "در حال جستجوی آرشیو و اینترنت…"}
            </p>
          </div>
        )}

        {result && !loading && (
          <div className="mt-6 space-y-6 fade-up">
            <div className="bg-white border border-rule p-6">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles size={16} className="text-mblue" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-ink-faint">
                  نتایج پژوهش
                  {result.online && <span className="text-mblue mr-2">· شامل منابع آنلاین</span>}
                </span>
              </div>
              <div className="text-sm leading-[1.85] text-ink whitespace-pre-wrap">
                {result.answer}
              </div>
            </div>

            {result.sources.length > 0 && (
              <div>
                <SectionHead
                  icon={FileText}
                  kicker="منابع"
                  title={`${toFa(result.sources.length)} منبع پیدا شد`}
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {result.sources.map((s) => (
                    <a
                      key={s.ref_no}
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group flex items-start gap-3 p-4 bg-white border border-rule hover:border-mblue transition-colors"
                    >
                      <span className="shrink-0 w-8 h-8 border border-rule flex items-center justify-center text-navy text-sm">
                        {toFa(s.ref_no)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-navy group-hover:text-mblue transition-colors line-clamp-2">
                          {s.title}
                        </p>
                        {s.snippet && (
                          <p className="text-xs text-ink-faint mt-1 line-clamp-2 leading-[1.7]">
                            {s.snippet}
                          </p>
                        )}
                      </div>
                      <ExternalLink size={14} className="text-ink-faint group-hover:text-mblue shrink-0 mt-1" />
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!result && !loading && !error && (
          <div className="mt-12 text-center text-ink-faint">
            <GraduationCap size={40} className="mx-auto mb-4 opacity-30" />
            <p className="text-sm">یک موضوع وارد کنید تا آرشیو و منابع آنلاین را بررسی کنیم</p>
          </div>
        )}
      </main>
    </div>
  );
}
