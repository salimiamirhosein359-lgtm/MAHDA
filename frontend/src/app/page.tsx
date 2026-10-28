"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type ItemListOut } from "@/lib/api";
import { CategoryFilter, CampFilter, TopNav, SectionHead, Empty, ErrorBox, SkeletonList } from "@/components/ui";
import ItemCard, { TrendChip } from "@/components/ItemCard";
import { RefreshCw, TrendingUp, FileText, Globe, BarChart3 } from "lucide-react";
import { toFa } from "@/lib/ui";
import type { TrendOut } from "@/lib/api";

function StatCard({
  icon: Icon,
  label,
  value,
  note,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="py-6 px-2 border-l border-rule first:border-l-0 last:border-l-0 md:border-l md:first:border-l-0 md:last:border-r-0 group">
      <div className="flex items-center gap-2 text-ink-faint mb-3">
        <Icon size={16} strokeWidth={1.5} />
        <span className="text-[11px] font-bold uppercase tracking-[0.15em]">{label}</span>
      </div>
      <p className="font-serif text-4xl text-navy leading-none mb-2">{value}</p>
      <p className="text-xs text-ink-dim leading-editorial">{note}</p>
    </div>
  );
}

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

  const usCount = data?.items.filter((i) => i.camp === "US").length ?? 0;
  const cnCount = data?.items.filter((i) => i.camp === "CN").length ?? 0;

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <TopNav />

      {/* HERO — editorial, serif, McKinsey style */}
      <section className="bg-navy text-white">
        <div className="max-w-6xl mx-auto px-4 py-16 md:py-24">
          <p className="text-[11px] font-bold uppercase tracking-[0.25em] text-mblue-400 mb-5">
            هوش مصنوعی · پایش هفتگی
          </p>
          <h1 className="font-serif text-4xl md:text-6xl leading-[1.25] max-w-3xl">
            رصد تحولات هوش مصنوعی،
            <br />
            <span className="text-white/70">با دید تحلیلی و داده‌محور</span>
          </h1>
          <p className="mt-6 max-w-2xl text-white/70 leading-editorial text-base md:text-lg">
            اخبار، مدل‌ها، ابزارها و سیاست‌گذاری هوش مصنوعی را از منابع معتبر
            دنبال کنید؛ روندهای کلیدی و رقابت چین و آمریکا را در یک نگاه ببینید.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-4">
            <a
              href="#feed"
              className="inline-flex items-center gap-2 bg-mblue-500 hover:bg-mblue-400 text-white px-6 py-3 text-sm font-bold transition-colors"
            >
              <FileText size={16} strokeWidth={1.5} />
              مشاهده اخبار هفته
            </a>
            <a
              href="/rivalry"
              className="inline-flex items-center gap-2 border border-white/30 hover:border-white text-white px-6 py-3 text-sm font-bold transition-colors"
            >
              <BarChart3 size={16} strokeWidth={1.5} />
              رقابت چین و آمریکا
            </a>
          </div>
        </div>
      </section>

      {/* Stat band — flat cards with hairline dividers */}
      <section className="border-b border-rule bg-cgray-soft">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4">
            <StatCard
              icon={FileText}
              label="آیتم‌های ۷ روز"
              value={data ? toFa(data.total) : "—"}
              note="مجموع مطالب رصدشده از منابع منتخب"
            />
            <StatCard
              icon={Globe}
              label="ایالات متحده"
              value={data ? toFa(usCount) : "—"}
              note="آیتم‌های مرتبط با اکوسیستم آمریکا"
            />
            <StatCard
              icon={Globe}
              label="چین"
              value={data ? toFa(cnCount) : "—"}
              note="آیتم‌های مرتبط با اکوسیستم چین"
            />
            <StatCard
              icon={TrendingUp}
              label="کلیدواژه‌های داغ"
              value={trends ? toFa(trends.length) : "—"}
              note="پرتکرارترین موضوعات این هفته"
            />
          </div>
        </div>
      </section>

      <main className="max-w-6xl mx-auto px-4 py-12 w-full flex-1">
        {/* Trends */}
        {trends && trends.length > 0 && (
          <section className="mb-12">
            <SectionHead
              kicker="روندها"
              title="کلیدواژه‌های پرتکرار"
              meta="۷ روز اخیر"
            />
            <div className="flex flex-wrap gap-2">
              {trends.slice(0, 12).map((t) => (
                <TrendChip key={t.keyword} keyword={t.keyword} count={t.count} />
              ))}
            </div>
          </section>
        )}

        {/* Feed */}
        <section id="feed">
          <div className="flex items-end justify-between mb-5 border-b border-rule pb-4">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-mblue-500 mb-2">
                پایش
              </p>
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

          {/* Filters */}
          <div className="space-y-3 mb-8 pt-2">
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

      {/* Footer — deep navy, McKinsey style */}
      <footer className="bg-navy text-white/60">
        <div className="max-w-6xl mx-auto px-4 py-10">
          <div className="flex flex-col md:flex-row items-start justify-between gap-6">
            <div>
              <p className="font-serif text-xl text-white mb-2">AI Sentinel</p>
              <p className="text-xs leading-editorial max-w-md">
                سامانه رصد و تحلیل تحولات هوش مصنوعی — اخبار، روندها و رقابت
                جهانی را با رویکردی داده‌محور دنبال می‌کند.
              </p>
            </div>
            <div className="text-xs space-y-2">
              <p className="uppercase tracking-[0.2em] text-white/40 mb-3">بخش‌ها</p>
              <p><a href="/" className="hover:text-white transition-colors">رصد</a></p>
              <p><a href="/rivalry" className="hover:text-white transition-colors">چین و آمریکا</a></p>
              <p><a href="/research" className="hover:text-white transition-colors">دستیار پژوهشی</a></p>
              <p><a href="/chat" className="hover:text-white transition-colors">گفت‌وگو</a></p>
            </div>
          </div>
          <div className="mt-8 pt-6 border-t border-white/10 text-[11px] text-white/40">
            © AI Sentinel — تمامی حقوق محفوظ است
          </div>
        </div>
      </footer>
    </div>
  );
}
