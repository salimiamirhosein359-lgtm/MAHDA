"use client";

import { useEffect, useRef, useState } from "react";
import { api, type ResearchJobOut } from "@/lib/api";
import { TopNav, SectionHead, ErrorBox } from "@/components/ui";
import { Search, Loader2, CheckCircle2, XCircle, ChevronDown, Globe, BookOpen, FileText } from "lucide-react";
import { toFa } from "@/lib/ui";

function StepType({ t }: { t: string }) {
  if (t === "search") return "جستجو";
  if (t === "read") return "مطالعه";
  if (t === "synthesize") return "تجمیع";
  return t;
}

export default function ResearchPage() {
  const [question, setQuestion] = useState("");
  const [job, setJob] = useState<ResearchJobOut | null>(null);
  const [starting, setStarting] = useState(false);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => {
    if (pollRef.current) clearInterval(pollRef.current);
  }, []);

  const start = async (mode: "quick" | "deep") => {
    if (question.trim().length < 3) {
      setError("سؤال را کامل‌تر بنویسید (حداقل ۳ حرف)");
      return;
    }
    setStarting(true);
    setError("");
    setJob(null);
    try {
      const { job_id } = await api.startResearch(question.trim(), mode, 3, 2);
      setStarting(false);
      setPolling(true);
      pollRef.current = setInterval(async () => {
        try {
          const j = await api.research(job_id);
          setJob(j);
          if (j.status === "done" || j.status === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
            setPolling(false);
          }
        } catch {
          // keep polling
        }
      }, 3000);
    } catch (e) {
      setStarting(false);
      setError(`خطا در شروع پژوهش: ${e instanceof Error ? e.message : "نامشخص"}`);
    }
  };

  const busy = starting || polling;

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <TopNav />
      <main className="max-w-3xl mx-auto px-4 py-12 w-full flex-1">
        {/* Editorial header */}
        <div className="mb-10">
          <p className="text-[11px] font-bold uppercase tracking-[0.25em] text-mblue-500 mb-4">
            ابزار پژوهشی
          </p>
          <h1 className="font-serif text-3xl md:text-4xl leading-[1.3] text-navy">
            دستیار پژوهشی
          </h1>
          <p className="mt-4 text-ink-dim leading-editorial max-w-xl">
            پژوهش عمیق با جستجوی چندمرحله‌ای، مطالعه منابع و تجمیع یافته‌ها در
            یک گزارش ساختارمند.
          </p>
        </div>

        {/* Question input — flat card with hairline border */}
        <div className="border border-rule p-6">
          <label className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.15em] text-ink-faint mb-3">
            <BookOpen size={14} strokeWidth={1.5} />
            پرسش پژوهشی
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="مثلاً: وضعیت رقابت تراشه‌های هوش مصنوعی بین چین و آمریکا در ۲۰۲۶ چیست؟"
            rows={3}
            className="w-full bg-white p-4 text-sm leading-editorial border border-rule focus:border-mblue-500 outline-none resize-none placeholder:text-ink-faint transition-colors"
          />
          <div className="flex gap-3 mt-4">
            <button
              onClick={() => start("quick")}
              disabled={busy}
              className="flex items-center gap-2 px-5 py-2.5 border border-navy text-navy text-sm font-bold hover:bg-navy hover:text-white disabled:opacity-40 transition-colors"
            >
              <Globe size={15} strokeWidth={1.5} />
              جستجوی سریع
            </button>
            <button
              onClick={() => start("deep")}
              disabled={busy}
              className="flex items-center gap-2 px-5 py-2.5 bg-mblue-500 hover:bg-mblue-400 text-white text-sm font-bold disabled:opacity-40 transition-colors"
            >
              {busy ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} strokeWidth={1.5} />}
              پژوهش عمیق
            </button>
          </div>
          {error && <div className="mt-3"><ErrorBox text={error} /></div>}
        </div>

        {/* Job status */}
        {job && (
          <div className="mt-10 space-y-8">
            {/* Status line */}
            <div
              className={`flex items-center gap-2.5 py-3 px-4 border-r-2 text-sm font-bold ${
                job.status === "done"
                  ? "border-mblue-500 bg-cgray-soft text-navy"
                  : job.status === "failed"
                    ? "border-mred bg-red-50 text-[#8f1f1f]"
                    : "border-navy bg-cgray-soft text-navy"
              }`}
            >
              {job.status === "done" ? (
                <CheckCircle2 size={18} strokeWidth={1.5} />
              ) : job.status === "failed" ? (
                <XCircle size={18} strokeWidth={1.5} />
              ) : (
                <Loader2 size={18} className="animate-spin" strokeWidth={1.5} />
              )}
              {job.status === "done" ? "پژوهش کامل شد" : job.status === "failed" ? "خطا در پژوهش" : "در حال پژوهش…"}
              {job.error && <span className="text-xs font-normal">— {job.error}</span>}
            </div>

            {/* Steps — numbered editorial list */}
            {job.steps.length > 0 && (
              <section>
                <SectionHead
                  kicker="روند"
                  title="مراحل پژوهش"
                  meta={`${toFa(job.steps.length)} مرحله`}
                />
                <ol className="divide-y divide-rule border-y border-rule">
                  {job.steps.map((s, i) => (
                    <li key={s.id} className="py-4 flex gap-4 items-start">
                      <span className="font-serif text-lg text-ink-faint w-6 shrink-0 leading-7">
                        {toFa(i + 1)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-bold text-mblue-500 uppercase tracking-wide">
                            <StepType t={s.step_type} />
                          </span>
                          {s.query && (
                            <span className="text-sm text-navy font-bold">«{s.query}»</span>
                          )}
                        </div>
                        {s.finding && (
                          <p className="text-xs text-ink-dim mt-1.5 leading-editorial line-clamp-2">
                            {s.finding}
                          </p>
                        )}
                      </div>
                    </li>
                  ))}
                </ol>
              </section>
            )}

            {/* Result — report-style */}
            {job.result_markdown && (
              <section>
                <SectionHead kicker="خروجی" title="گزارش نهایی" />
                <div className="bg-cgray-soft border border-rule p-6">
                  <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.15em] text-ink-faint mb-4 pb-4 border-b border-rule">
                    <FileText size={14} strokeWidth={1.5} />
                    نتیجه پژوهش
                  </div>
                  <pre className="whitespace-pre-wrap text-sm leading-editorial text-ink font-sans">
                    {job.result_markdown}
                  </pre>
                </div>
              </section>
            )}
          </div>
        )}

        {polling && !job && (
          <p className="mt-10 text-center text-sm text-ink-faint flex items-center justify-center gap-2">
            <Loader2 size={15} className="animate-spin" strokeWidth={1.5} />
            در حال آماده‌سازی پژوهش…
          </p>
        )}
      </main>
    </div>
  );
}
