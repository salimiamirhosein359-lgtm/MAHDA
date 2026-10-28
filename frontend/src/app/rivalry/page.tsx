"use client";

import { useEffect, useState } from "react";
import { api, type RivalryOut } from "@/lib/api";
import { TopNav, Empty, ErrorBox, SkeletonList } from "@/components/ui";
import { Swords, Flag } from "lucide-react";
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
  const color = accent === "blue" ? "text-blue-300 border-blue-500/30 bg-blue-500/5" : "text-red-300 border-red-500/30 bg-red-500/5";
  return (
    <div className={`flex-1 rounded-xl border p-4 ${color}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-black text-lg flex items-center gap-2">
          <span className="text-2xl">{flag}</span>
          {title}
        </h2>
        <span className="text-2xl font-black">{toFa(count)}</span>
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-slate-500 py-6 text-center">آیتمی نیست</p>
      ) : (
        <ul className="space-y-2.5">
          {items.map((it) => (
            <li key={it.id}>
              <a
                href={it.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-3 rounded-lg bg-base-800 hover:bg-base-700 border border-base-600 transition-colors"
              >
                <p className="text-sm font-bold leading-6 line-clamp-2">{it.title}</p>
                <p className="text-xs text-slate-500 mt-1.5">{timeAgo(it.published_at)}</p>
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

  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex items-center gap-3 mb-6">
          <Swords className="text-accent-400" size={26} />
          <div>
            <h1 className="text-2xl font-black">رقابت چین و آمریکا</h1>
            <p className="text-sm text-slate-500 mt-0.5">۷ روز اخیر — مقایسه دو ستون</p>
          </div>
        </div>

        {loading ? (
          <SkeletonList n={4} />
        ) : error ? (
          <ErrorBox text={`خطا: ${error}`} />
        ) : data ? (
          <div className="flex flex-col md:flex-row gap-4">
            <CampColumn
              title="آمریکا"
              flag="🇺🇸"
              count={data.us.count}
              items={data.us.top_items}
              accent="blue"
            />
            <div className="flex items-center justify-center md:px-2">
              <Flag className="text-slate-600 rotate-90 md:rotate-0" size={22} />
            </div>
            <CampColumn
              title="چین"
              flag="🇨🇳"
              count={data.cn.count}
              items={data.cn.top_items}
              accent="red"
            />
          </div>
        ) : (
          <Empty />
        )}
      </main>
    </div>
  );
}
