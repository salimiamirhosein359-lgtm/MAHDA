"use client";

import { useEffect, useRef, useState } from "react";
import { api, type ResearchJobOut } from "@/lib/api";
import { TopNav } from "@/components/ui";
import { Search, Loader2, CheckCircle2, XCircle, ChevronDown, Globe, BookOpen } from "lucide-react";

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

  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="max-w-3xl mx-auto px-4 py-6">
        <div className="flex items-center gap-3 mb-6">
          <BookOpen className="text-accent-400" size={26} />
          <div>
            <h1 className="text-2xl font-black">دستیار پژوهشی</h1>
            <p className="text-sm text-slate-500 mt-0.5">پژوهش عمیق با جستجوی چندمرحله‌ای و منابع</p>
          </div>
        </div>

        {/* Question input */}
        <div className="p-4 rounded-xl border border-base-600 bg-base-800">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="مثلاً: وضعیت رقابت تراشه‌های AI بین چین و آمریکا در ۲۰۲۶ چیست؟"
            rows={3}
            className="w-full bg-base-900 rounded-lg p-3 text-sm border border-base-600 focus:border-accent-500 outline-none resize-none placeholder:text-slate-600"
          />
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => start("quick")}
              disabled={starting || polling}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-base-700 hover:bg-base-600 disabled:opacity-50 text-sm font-bold border border-base-600 transition-colors"
            >
              <Globe size={15} />
              جستجوی سریع
            </button>
            <button
              onClick={() => start("deep")}
              disabled={starting || polling}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-500 hover:bg-accent-400 disabled:opacity-50 text-sm font-bold text-white transition-colors"
            >
              {starting || polling ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />}
              پژوهش عمیق
            </button>
          </div>
          {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
        </div>

        {/* Job status */}
        {job && (
          <div className="mt-6 space-y-4">
            {/* Status */}
            <div
              className={`flex items-center gap-2 p-3 rounded-lg border text-sm font-bold ${
                job.status === "done"
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                  : job.status === "failed"
                    ? "border-red-500/30 bg-red-500/10 text-red-300"
                    : "border-accent-500/30 bg-accent-500/10 text-accent-300"
              }`}
            >
              {job.status === "done" ? (
                <CheckCircle2 size={18} />
              ) : job.status === "failed" ? (
                <XCircle size={18} />
              ) : (
                <Loader2 size={18} className="animate-spin" />
              )}
              {job.status === "done" ? "پژوهش کامل شد" : job.status === "failed" ? "خطا در پژوهش" : "در حال پژوهش..."}
              {job.error && <span className="text-xs font-normal">— {job.error}</span>}
            </div>

            {/* Steps */}
            {job.steps.length > 0 && (
              <div className="rounded-xl border border-base-600 bg-base-800">
                <details open className="p-4">
                  <summary className="flex items-center gap-2 cursor-pointer text-sm font-bold text-slate-300">
                    <ChevronDown size={15} />
                    مراحل ({job.steps.length})
                  </summary>
                  <ol className="mt-3 space-y-2">
                    {job.steps.map((s) => (
                      <li key={s.id} className="text-xs border-r-2 border-base-500 pr-3 py-1">
                        <span className="text-accent-400 font-bold">
                          {s.step_type === "search" ? "جستجو" : s.step_type === "read" ? "مطالعه" : s.step_type === "synthesize" ? "تجمیع" : s.step_type}
                        </span>
                        {s.query && <span className="text-slate-400"> — «{s.query}»</span>}
                        {s.finding && <p className="text-slate-500 mt-1 leading-5 line-clamp-2">{s.finding}</p>}
                      </li>
                    ))}
                  </ol>
                </details>
              </div>
            )}

            {/* Result */}
            {job.result_markdown && (
              <div className="p-5 rounded-xl border border-base-600 bg-base-800">
                <h3 className="font-black text-sm text-slate-300 mb-3">نتیجه</h3>
                <pre className="whitespace-pre-wrap text-sm leading-7 text-slate-200 font-sans">{job.result_markdown}</pre>
              </div>
            )}
          </div>
        )}

        {polling && !job && (
          <p className="mt-6 text-center text-sm text-slate-500 flex items-center justify-center gap-2">
            <Loader2 size={15} className="animate-spin" />
            در حال آماده‌سازی پژوهش...
          </p>
        )}
      </main>
    </div>
  );
}
