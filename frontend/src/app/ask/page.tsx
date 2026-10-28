"use client";

import { useState } from "react";
import { api, type AskOut } from "@/lib/api";
import { TopNav } from "@/components/ui";
import { Send, Globe, Loader2, FileText, MessageCircle } from "lucide-react";

interface QAPair {
  question: string;
  answer: AskOut;
}

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<QAPair[]>([]);
  const [online, setOnline] = useState(false);

  const send = async () => {
    if (question.trim().length < 2) return;
    setLoading(true);
    setError("");
    try {
      const answer = await api.ask(question.trim(), online);
      setHistory((h) => [{ question: question.trim(), answer }, ...h]);
      setQuestion("");
    } catch (e) {
      setError(`خطا: ${e instanceof Error ? e.message : "نامشخص"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="max-w-3xl mx-auto px-4 py-6 flex flex-col min-h-[calc(100vh-3.5rem)]">
        <div className="flex items-center gap-3 mb-6">
          <MessageCircle className="text-accent-400" size={24} />
          <div>
            <h1 className="text-xl font-black">پرسش و پاسخ</h1>
            <p className="text-xs text-slate-500 mt-0.5">با ارجاع به منابع [۱]، [۲]...</p>
          </div>
        </div>

        {/* History */}
        <div className="flex-1 space-y-4 mb-24">
          {history.length === 0 && (
            <div className="text-center py-16 text-slate-600">
              <MessageCircle size={36} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">اولین سؤال خود را بپرسید</p>
            </div>
          )}
          {history.map((qa, i) => (
            <div key={i} className="space-y-2">
              {/* Question bubble */}
              <div className="flex justify-start">
                <div className="max-w-2xl px-4 py-2.5 rounded-xl rounded-tr-sm bg-accent-500 text-white text-sm font-bold">
                  {qa.question}
                </div>
              </div>
              {/* Answer */}
              <div className="p-4 rounded-xl border border-base-600 bg-base-800">
                <p className="text-sm leading-7 text-slate-200 whitespace-pre-wrap">{qa.answer.answer}</p>
                {qa.answer.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-base-600 space-y-1.5">
                    {qa.answer.sources.map((s) => (
                      <a
                        key={s.ref_no}
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-xs text-cyan-300 hover:text-cyan-200"
                      >
                        <FileText size={12} />
                        <span className="text-slate-500">[{s.ref_no}]</span>
                        <span className="truncate">{s.title}</span>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Input bar (fixed) */}
        <div className="fixed bottom-0 left-0 right-0 border-t border-base-600 bg-base-900/95 backdrop-blur p-4">
          <div className="max-w-3xl mx-auto">
            {error && <p className="text-xs text-red-400 mb-2">{error}</p>}
            <div className="flex items-end gap-2">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                placeholder="سؤال خود را بنویسید... (Enter برای ارسال)"
                rows={1}
                className="flex-1 bg-base-800 rounded-xl p-3 text-sm border border-base-600 focus:border-accent-500 outline-none resize-none placeholder:text-slate-600"
              />
              <button
                onClick={() => setOnline((v) => !v)}
                title="جستجوی آنلاین"
                className={`p-3 rounded-xl border transition-colors ${
                  online ? "bg-cyan-500/15 border-cyan-500/50 text-cyan-300" : "border-base-600 text-slate-500 hover:text-slate-300"
                }`}
              >
                <Globe size={17} />
              </button>
              <button
                onClick={send}
                disabled={loading || question.trim().length < 2}
                className="p-3 rounded-xl bg-accent-500 hover:bg-accent-400 disabled:opacity-40 text-white transition-colors"
              >
                {loading ? <Loader2 size={17} className="animate-spin" /> : <Send size={17} className="-scale-x-100" />}
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
