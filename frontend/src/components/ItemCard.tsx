import { ExternalLink, Flame } from "lucide-react";
import type { ItemOut } from "@/lib/api";
import { timeAgo, toFa, faCategory, faCamp, CATEGORIES, CAMPS } from "@/lib/ui";

export default function ItemCard({ item }: { item: ItemOut }) {
  const cat = CATEGORIES.find((c) => c.value === item.category);
  const camp = CAMPS.find((c) => c.value === item.camp);
  const score = item.score ?? 0;

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-4 rounded-xl border border-base-600 bg-base-800 hover:bg-base-700 transition-colors group"
    >
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          {/* Title */}
          <h3 className="font-bold text-base leading-7 line-clamp-2 group-hover:text-accent-400 transition-colors">
            {item.title}
          </h3>

          {/* Summary */}
          {item.summary && (
            <p className="mt-2 text-sm text-slate-400 line-clamp-3 leading-6">
              {item.summary}
            </p>
          )}

          {/* Badges */}
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            {cat && cat.value && (
              <span className={`px-2.5 py-0.5 rounded-full border ${cat.color}`}>
                {cat.label}
              </span>
            )}
            {camp && camp.value && camp.value !== "other" && (
              <span className={`px-2.5 py-0.5 rounded-full border ${camp.color}`}>
                {camp.flag} {camp.label}
              </span>
            )}
            {item.actor && (
              <span className="px-2.5 py-0.5 rounded-full border bg-cyan-500/10 text-cyan-300 border-cyan-500/30">
                {item.actor}
              </span>
            )}
          </div>

          {/* Meta row */}
          <div className="mt-3 flex items-center gap-4 text-xs text-slate-500">
            <span>{timeAgo(item.published_at)}</span>
            {item.author && <span className="truncate max-w-32">{item.author}</span>}
          </div>
        </div>

        {/* Score + open link */}
        <div className="flex flex-col items-center gap-2 shrink-0">
          <div
            className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold"
            style={{
              background: score >= 0.8 ? "rgba(239,68,68,.15)" : score >= 0.6 ? "rgba(124,92,255,.15)" : "rgba(148,163,184,.1)",
              color: score >= 0.8 ? "#f87171" : score >= 0.6 ? "#9b82ff" : "#94a3b8",
            }}
          >
            <Flame size={13} />
            {toFa(Math.round(score * 100))}
          </div>
          <ExternalLink
            size={16}
            className="text-slate-600 group-hover:text-accent-400 transition-colors"
          />
        </div>
      </div>
    </a>
  );
}
