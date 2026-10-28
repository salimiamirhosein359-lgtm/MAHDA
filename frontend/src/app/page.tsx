"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type ItemListOut } from "@/lib/api";
import { CategoryFilter, CampFilter, TopNav, Empty, ErrorBox, SkeletonList } from "@/components/ui";
import ItemCard from "@/components/ItemCard";
import { RefreshCw, TrendingUp } from "lucide-react";
import { toFa } from "@/lib/ui";
import type { TrendOut } from "@/lib/api";

export default function Dashboard() {
  const [data, setData] = useState<ItemListOut | null>(null);
  const [trends, setTrends] = useState<TrendOut[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [category, setCategory] = useState("");
  const [camp, setCamp] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [items, t] = await Promise.all([
        api.items({ category: category || undefined, camp: camp || undefined, days: 7, limit: 50 }),
        api.trends(7, 12),
      ]);
      setData(items);
      setTrends(t);
    } catch (e) {
      setError(`خطا در دریافت داده‌ها: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  }, [category, camp]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-black">رصد هوش مصنوعی</h1>
            <p className="text-sm text-slate-500 mt-1">
              {data ? `${toFa(data.total)} آیتم در ۷ روز اخیر` : "در حال بارگذاری..."}
            </p>
          </div>
          <button
            onClick={load}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-base-700 hover:bg-base-600 text-sm font-bold border border-base-600 transition-colors"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
            به‌روزرسانی
          </button>
        </div>

        {/* Trends bar */}
        {trends && trends.length > 0 && (
          <div className="mb-6 p-3 rounded-xl border border-base-600 bg-base-800">
            <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
              <TrendingUp size={14} className="text-accent-400" />
              کلیدواژه‌های داغ
            </div>
            <div className="flex flex-wrap gap-1.5">
              {trends.slice(0, 12).map((t) => (
                <span
                  key={t.keyword}
                  className="px-2.5 py-1 rounded-md bg-base-700 text-xs text-slate-300 border border-base-600"
                  style={{ fontSize: `${11 + Math.min(t.count / 8, 6)}px` }}
                >
                  {t.keyword}
                  <span className="text-slate-600 mr-1">{toFa(t.count)}</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="space-y-3 mb-6">
          <CategoryFilter value={category} onChange={setCategory} />
          <CampFilter value={camp} onChange={setCamp} />
        </div>

        {/* Content */}
        {loading && !data ? (
          <SkeletonList n={5} />
        ) : error ? (
          <ErrorBox text={error} />
        ) : data && data.items.length === 0 ? (
          <Empty text="هیچ آیتمی با این فیلترها پیدا نشد" />
        ) : data ? (
          <div className="space-y-3">
            {data.items.map((item) => (
              <ItemCard key={item.id} item={item} />
            ))}
          </div>
        ) : null}
      </main>
    </div>
  );
}
