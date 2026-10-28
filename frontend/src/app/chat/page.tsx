"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { api, type AskOut } from "@/lib/api";
import { TopNav } from "@/components/ui";
import { Send, Globe, Loader2, FileText, MessageSquare, ExternalLink, Sparkles } from "lucide-react";
import { toFa } from "@/lib/ui";

/* ---------- Minimal markdown renderer (regex-based, no packages) ---------- */

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  // Tokenize: **bold**, [label](url), [۱] style bare refs left to links
  const re = /(\*\*[^*]+\*\*)|(\[[^\]]+\]\([^)\s]+\))/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) nodes.push(text.slice(last, m.index));
    const tok = m[0];
    if (m[1]) {
      // bold
      nodes.push(
        <strong key={`${keyPrefix}-b-${i++}`} className="font-bold text-navy">
          {tok.slice(2, -2)}
        </strong>
      );
    } else if (m[2]) {
      // link
      const lm = /\[([^\]]+)\]\(([^)\s]+)\)/.exec(tok);
      if (lm) {
        nodes.push(
          <a
            key={`${keyPrefix}-l-${i++}`}
            href={lm[2]}
            target="_blank"
            rel="noopener noreferrer"
            className="text-mblue-500 hover:text-mblue-400 underline decoration-mblue-300 underline-offset-4"
          >
            {lm[1]}
          </a>
        );
      }
    }
    last = m.index + tok.length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

function MarkdownAnswer({ text }: { text: string }) {
  const paragraphs = text.split(/\n{2,}/).filter((p) => p.trim().length > 0);
  return (
    <div className="space-y-4">
      {paragraphs.map((p, i) => {
        const t = p.trim();
        if (t.startsWith("### ") || t.startsWith("## ") || t.startsWith("# ")) {
          const level = t.match(/^#+/)![0].length;
          const inner = t.replace(/^#+\s+/, "");
          return (
            <h3
              key={i}
              className={
                level === 1
                  ? "font-serif text-xl text-navy mt-2"
                  : "font-serif text-lg text-navy mt-2"
              }
            >
              {renderInline(inner, `p${i}`)}
            </h3>
          );
        }
        if (t.startsWith("- ") || t.startsWith("* ")) {
          const items = t
            .split("\n")
            .map((l) => l.replace(/^[-*]\s+/, "").trim())
            .filter(Boolean);
          return (
            <ul key={i} className="space-y-2 pr-5 list-disc marker:text-mblue-500">
              {items.map((li, j) => (
                <li key={j} className="leading-editorial">
                  {renderInline(li, `p${i}-${j}`)}
                </li>
              ))}
            </ul>
          );
        }
        return (
          <p key={i} className="leading-editorial">
            {renderInline(t, `p${i}`)}
          </p>
        );
      })}
    </div>
  );
}

/* ---------- Chat page ---------- */

interface ChatTurn {
  role: "user" | "assistant";
  text?: string; // user
  answer?: AskOut; // assistant
}

const SUGGESTIONS = [
  "جدیدترین مدل‌های زبانی این هفته چه بوده‌اند؟",
  "وضعیت صادرات تراشه به چین چگونه است؟",
  "روندهای سرمایه‌گذاری هوش مصنوعی چیست؟",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [online, setOnline] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const send = async (q?: string) => {
    const question = (q ?? input).trim();
    if (question.length < 2 || loading) return;
    setLoading(true);
    setError("");
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    try {
      const answer = await api.ask(question, online);
      setMessages((m) => [...m, { role: "assistant", answer }]);
    } catch (e) {
      setError(`خطا: ${e instanceof Error ? e.message : "نامشخص"}`);
    } finally {
      setLoading(false);
      taRef.current?.focus();
    }
  };

  return (
    <div className="h-screen flex flex-col bg-white">
      <TopNav />

      <div className="flex-1 min-h-0 flex flex-col">
        {/* Conversation scroll area */}
        <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 w-full">
            {messages.length === 0 && !loading ? (
              /* Empty state — McKinsey hero style */
              <div className="py-20 md:py-28 text-center">
                <p className="text-[11px] font-bold uppercase tracking-[0.25em] text-mblue-500 mb-5">
                  دستیار گفت‌وگو
                </p>
                <h1 className="font-serif text-3xl md:text-5xl leading-[1.3] text-navy max-w-xl mx-auto">
                  چه خبر از دنیای هوش مصنوعی؟
                </h1>
                <p className="mt-5 text-ink-dim leading-editorial max-w-md mx-auto">
                  درباره اخبار، مدل‌ها، شرکت‌ها و سیاست‌گذاری هوش مصنوعی بپرسید؛
                  پاسخ‌ها با ارجاع به منابع شماره‌دار ارائه می‌شوند.
                </p>
                <div className="mt-10 flex flex-col gap-3 max-w-md mx-auto">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="group flex items-center gap-3 border border-rule px-5 py-4 text-sm text-navy hover:border-mblue-500 hover:bg-cgray-soft/60 transition-colors text-right"
                    >
                      <Sparkles size={15} strokeWidth={1.5} className="text-mblue-500 shrink-0" />
                      <span className="leading-editorial">{s}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="py-8 space-y-8">
                {messages.map((msg, i) =>
                  msg.role === "user" ? (
                    /* User message — right-aligned block (RTL natural), navy bubble */
                    <div key={i} className="flex justify-start">
                      <div className="max-w-[85%] md:max-w-[75%] bg-navy text-white px-5 py-3.5 text-sm leading-editorial">
                        {msg.text}
                      </div>
                    </div>
                  ) : (
                    /* Assistant answer — white card with hairline border + sources */
                    <div key={i} className="fade-up">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="w-6 h-6 flex items-center justify-center bg-mblue-500 text-white">
                          <MessageSquare size={13} strokeWidth={1.5} />
                        </span>
                        <span className="text-[11px] font-bold uppercase tracking-[0.15em] text-ink-faint">
                          پاسخ AI Sentinel
                        </span>
                        {msg.answer?.online && (
                          <span className="flex items-center gap-1 text-[10px] text-mblue-500 border border-lblue-soft px-2 py-0.5">
                            <Globe size={10} strokeWidth={1.5} />
                            جستجوی آنلاین
                          </span>
                        )}
                      </div>
                      <div className="border border-rule bg-white p-6 md:p-7">
                        <MarkdownAnswer text={msg.answer?.answer ?? ""} />
                        {msg.answer && msg.answer.sources.length > 0 && (
                          <div className="mt-6 pt-5 border-t border-rule space-y-3">
                            <p className="text-[11px] font-bold uppercase tracking-[0.15em] text-ink-faint">
                              منابع
                            </p>
                            {msg.answer.sources.map((s) => (
                              <a
                                key={s.ref_no}
                                href={s.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="group flex items-start gap-3 text-xs hover:bg-cgray-soft/60 -mx-2 px-2 py-2 transition-colors"
                              >
                                <span className="font-serif text-navy shrink-0 w-6 h-6 border border-rule flex items-center justify-center">
                                  {toFa(s.ref_no)}
                                </span>
                                <span className="flex-1 min-w-0">
                                  <span className="block text-navy font-bold group-hover:text-mblue-500 transition-colors truncate">
                                    {s.title}
                                  </span>
                                  {s.snippet && (
                                    <span className="block text-ink-faint leading-editorial mt-0.5 line-clamp-2">
                                      {s.snippet}
                                    </span>
                                  )}
                                </span>
                                <ExternalLink
                                  size={13}
                                  strokeWidth={1.5}
                                  className="text-ink-faint group-hover:text-mblue-500 transition-colors shrink-0 mt-0.5"
                                />
                              </a>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                )}

                {/* Thinking indicator */}
                {loading && (
                  <div className="fade-up">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 flex items-center justify-center bg-mblue-500 text-white">
                        <MessageSquare size={13} strokeWidth={1.5} />
                      </span>
                      <span className="text-[11px] font-bold uppercase tracking-[0.15em] text-ink-faint">
                        در حال پاسخ‌گویی
                      </span>
                    </div>
                    <div className="border border-rule bg-white p-6">
                      <div className="flex items-center gap-2">
                        <span className="typing-dot" />
                        <span className="typing-dot" />
                        <span className="typing-dot" />
                        <span className="text-xs text-ink-faint mr-2">
                          {online ? "در حال جستجوی منابع آنلاین…" : "در حال پردازش پرسش…"}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Input bar — sticky bottom, McKinsey framing */}
        <div className="border-t border-rule bg-white">
          <div className="max-w-3xl mx-auto px-4 py-4 w-full">
            {error && (
              <p className="text-xs text-mred mb-2">{error}</p>
            )}
            <div className="flex items-end gap-2 border border-rule focus-within:border-mblue-500 transition-colors bg-white">
              <textarea
                ref={taRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                placeholder="سؤال خود را بنویسید… (Enter برای ارسال، Shift+Enter برای خط جدید)"
                rows={1}
                className="flex-1 px-4 py-3.5 text-sm leading-editorial outline-none resize-none placeholder:text-ink-faint max-h-40"
              />
              <button
                onClick={() => setOnline((v) => !v)}
                title={online ? "جستجوی آنلاین فعال است" : "جستجوی آنلاین غیرفعال است"}
                className={`self-stretch w-11 flex items-center justify-center border-r border-rule transition-colors ${
                  online
                    ? "text-mblue-500 bg-lblue-soft/50"
                    : "text-ink-faint hover:text-navy hover:bg-cgray-soft"
                }`}
              >
                <Globe size={17} strokeWidth={1.5} />
              </button>
              <button
                onClick={() => send()}
                disabled={loading || input.trim().length < 2}
                className="self-stretch w-12 flex items-center justify-center bg-mblue-500 hover:bg-mblue-400 disabled:opacity-40 text-white transition-colors"
              >
                {loading ? (
                  <Loader2 size={17} className="animate-spin" strokeWidth={1.5} />
                ) : (
                  <Send size={17} strokeWidth={1.5} className="-scale-x-100" />
                )}
              </button>
            </div>
            <p className="mt-2.5 text-[11px] text-ink-faint text-center leading-editorial">
              AI Sentinel می‌تواند اشتباه کند؛ منابع را بررسی کنید.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
