import { ExternalLink, TrendingUp } from "lucide-react";
import type { ItemOut } from "@/lib/api";
import { timeAgo, toFa, CATEGORIES, CAMPS } from "@/lib/ui";

/* McKinsey-style flat news card: hairline separators, no big radii,
   navy title that turns bright-blue on hover, generous whitespace. */
export default function ItemCard({ item }: { item: ItemOut }) {
  const cat = CATEGORIES.find((c) => c.value === item.category);
  const camp = CAMPS.find((c) => c.value === item.camp);
  const score = item.score ?? 0;
  const hot = score >= 0.8;

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group block py-6 border-b border-rule first:border-t transition-colors hover:bg-cgray-soft/60"
    >
      <div className="flex items-start gap-5 px-1">
        <div className="flex-1 min-w-0">
          {/* Kicker row */}
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mb-2 text-[11px]">
            {camp && camp.value && camp.value !== "other" && (
              <span className="text-ink-faint">
                {camp.flag} {camp.label}
              </span>
            )}
            {cat && cat.value && (
              <>
                <span className="text-rule">|</span>
                <span className="font-bold text-mblue-500 uppercase tracking-wide">
                  {cat.label}
                </span>
              </>
            )}
            {item.actor && (
              <>
                <span className="text-rule">|</span>
                <span className="text-ink-faint truncate max-w-40">{item.actor}</span>
              </>
            )}
          </div>

          {/* Title — serif, navy, blue on hover */}
          <h3 className="font-serif text-lg md:text-xl leading-8 text-navy group-hover:text-mblue-500 transition-colors line-clamp-2">
            {item.title}
          </h3>

          {/* Summary */}
          {item.summary && (
            <p className="mt-2 text-sm text-ink-dim leading-editorial line-clamp-3">
              {item.summary}
            </p>
          )}

          {/* Meta row */}
          <div className="mt-3 flex items-center gap-4 text-xs text-ink-faint">
            <span>{timeAgo(item.published_at)}</span>
            {item.author && <span className="truncate max-w-32">{item.author}</span>}
            <span className="mr-auto flex items-center gap-1.5 text-mblue-500 opacity-0 group-hover:opacity-100 transition-opacity">
              <ExternalLink size={13} strokeWidth={1.5} />
              مشاهده منبع
            </span>
          </div>
        </div>

        {/* Significance index — flat stat, red reserved for critical */}
        <div className="shrink-0 flex flex-col items-center justify-center w-16 h-16 border border-rule">
          <span className="text-[9px] uppercase tracking-widest text-ink-faint">
            اهمیت
          </span>
          <span
            className={`text-xl font-bold leading-none mt-1 ${hot ? "text-mred" : "text-navy"}`}
          >
            {toFa(Math.round(score * 100))}
          </span>
        </div>
      </div>
    </a>
  );
}

/* Trending keyword chip — outlined, quiet */
export function TrendChip({ keyword, count }: { keyword: string; count: number }) {
  return (
    <span className="inline-flex items-baseline gap-1.5 border border-rule px-3 py-1.5 text-xs text-navy hover:border-mblue-500 hover:text-mblue-500 transition-colors">
      <TrendingUp size={12} strokeWidth={1.5} className="translate-y-[1px]" />
      {keyword}
      <span className="text-ink-faint">{toFa(count)}</span>
    </span>
  );
}
