"use client";

import { useEffect, useState } from "react";
import { api, type RivalryOut } from "@/lib/api";
import { TopNav, SectionHead, Empty, ErrorBox, SkeletonList } from "@/components/ui";
import { Globe } from "lucide-react";
import { toFa, timeAgo } from "@/lib/ui";

function CampColumn({
  title,
  flag,
  count,
  items,
  accent,
}: {
  title: string;
  flag: string;
  count: number;
  items: RivalryOut["us"]["top_items"];
  accent: "blue" | "red";
}) {
  const bar = accent === "blue" ? "bg-mblue-500" : "bg-mred";
  return (
    <div className="flex-1">
      <div className="mb-5">
        <div className={`inline-block w-10 h-1.5 ${bar} mb-4`} />
        <div className="flex items-baseline justify-between">
          <h3 className="font-serif text-2xl text-navy flex items-center gap-3">
            <span className="text-3xl leading-none">{flag}</span>
            {title}
          </h3>
          <span className="font-serif text-4xl text-navy">{toFa(count)}</span>
        </div>
        <p className="text-xs text-ink-faint mt-1">آیتم در ۷ روز اخیر</p>
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-ink-faint py-10 text-center border-t border-rule">
          آیتمی ثبت نشده است
        </p>
      ) : (
        <ul className="divide-y divide-rule border-t border-rule">
          {items.map((it) => (
            <li key={it.id}>
              <a
                href={it.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block py-4 hover:bg-cgray-soft/60 transition-colors group"
              >
                <p className="text-sm font-bold text-navy leading-6 line-clamp-2 group-hover:text-mblue-500 transition-colors">
                  {it.title}
                </p>
                <p className="text-xs text-ink-faint mt-1.5">{timeAgo(it.published_at)}</p>
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function RivalryPage() {
  const [data, setData] = useState<RivalryOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setData(await api.rivalry(7, 10));
      } catch (e) {
        setError(e instanceof Error ? e.message : "خطا");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const total = data ? data.us.count + data.cn.count : 0;
  const usPct = data && total > 0 ? Math.round((data.us.count / total) * 100) : 50;

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <TopNav />
      <main className="max-w-6xl mx-auto px-4 py-12 w-full flex-1">
        {/* Editorial header */}
        <div className="mb-10">
          <p className="text-[11px] font-bold uppercase tracking-[0.25em] text-mblue-500 mb-4">
            تحلیل رقابتی
          </p>
          <h1 className="font-serif text-3xl md:text-5xl leading-[1.3] text-navy max-w-3xl">
            رقابت چین و آمریکا بر سر هوش مصنوعی
          </h1>
          <p className="mt-5 max-w-2xl text-ink-dim leading-editorial">
            مقایسه حجم پوشش خبری و محورهای اصلی دو اکوسیستم در هفت روز گذشته.
          </p>
        </div>

        {loading ? (
          <SkeletonList n={4} />
        ) : error ? (
          <ErrorBox text={`خطا: ${error}`} />
        ) : data ? (
          <>
            {/* Balance bar — flat, corporate */}
            <div className="mb-12">
              <div className="flex items-center justify-between text-xs text-ink-faint mb-2">
                <span className="flex items-center gap-1.5">
                  <Globe size={13} strokeWidth={1.5} />
                  سهم پوشش خبری
                </span>
                <span>
                  {toFa(data.us.count)} : {toFa(data.cn.count)}
                </span>
              </div>
              <div className="flex h-2 w-full bg-cgray overflow-hidden">
                <div className="bg-mblue-500" style={{ width: `${usPct}%` }} />
                <div className="bg-mred" style={{ width: `${100 - usPct}%` }} />
              </div>
            </div>

            <div className="flex flex-col md:flex-row gap-10 md:gap-14">
              <CampColumn
                title="ایالات متحده"
                flag="🇺🇸"
                count={data.us.count}
                items={data.us.top_items}
                accent="blue"
              />
              <div className="hidden md:block w-px bg-rule shrink-0" />
              <div className="md:hidden h-px bg-rule w-full" />
              <CampColumn
                title="چین"
                flag="🇨🇳"
                count={data.cn.count}
                items={data.cn.top_items}
                accent="red"
              />
            </div>
          </>
        ) : (
          <Empty />
        )}
      </main>
    </div>
  );
}
