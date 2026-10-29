import { ArrowUpLeft, Clock, User, Calendar } from "lucide-react";
import type { ItemOut } from "@/lib/api";
import { formatDate, formatTime, extractSource, timeAgo, CATEGORIES, CAT_STYLE } from "@/lib/ui";

export default function ItemCard({ item }: { item: ItemOut }) {
  const cat = CATEGORIES.find((c) => c.value === item.category);
  const catLabel = cat && cat.value ? cat.label : "عمومی";
  const st = CAT_STYLE[item.category ?? ""] ?? CAT_STYLE._default;
  const source = extractSource(item.url);
  const initial = (source[0] ?? "?").toUpperCase();

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group relative flex flex-col bg-white rounded-2xl shadow-card hover:shadow-lift hover:-translate-y-0.5 transition-all duration-200 overflow-hidden"
    >
      {/* colored accent bar */}
      <span className={`absolute top-0 right-0 h-full w-1 ${st.bar}`} />

      <div className="p-5 pr-6 flex-1 flex flex-col">
        {/* top row: badge + relative time */}
        <div className="flex items-center justify-between mb-3">
          <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold ${st.badge}`}>
            {catLabel}
          </span>
          <span className="text-[11px] text-ink-faint">{timeAgo(item.published_at)}</span>
        </div>

        <h3 className="text-[15px] font-bold leading-7 text-navy group-hover:text-mblue transition-colors line-clamp-3" dir="auto">
          {item.title}
        </h3>

        {item.summary && (
          <p className="mt-2 text-[13px] text-ink-dim leading-[1.8] line-clamp-2" dir="auto">
            {item.summary}
          </p>
        )}

        <div className="flex-1" />

        {/* source + author */}
        <div className="mt-4 pt-4 border-t border-rule flex items-center gap-3">
          <span className={`w-8 h-8 rounded-lg bg-gradient-to-br ${st.grad} text-white text-sm font-bold flex items-center justify-center shrink-0`}>
            {initial}
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-bold text-navy truncate" dir="ltr" style={{ textAlign: "right" }}>
              {source || "منبع نامشخص"}
            </p>
            <p className="text-[11px] text-ink-faint flex items-center gap-1 truncate">
              <User size={11} strokeWidth={1.6} />
              {item.author || "نویسنده نامشخص"}
            </p>
          </div>
          <ArrowUpLeft size={18} className="text-ink-faint group-hover:text-mblue transition-colors shrink-0" />
        </div>

        {/* date + time */}
        <div className="mt-3 flex items-center gap-4 text-[11px] text-ink-faint">
          <span className="flex items-center gap-1.5">
            <Calendar size={12} strokeWidth={1.6} />
            {formatDate(item.published_at)}
          </span>
          {formatTime(item.published_at) && (
            <span className="flex items-center gap-1.5">
              <Clock size={12} strokeWidth={1.6} />
              {formatTime(item.published_at)}
            </span>
          )}
        </div>
      </div>
    </a>
  );
}
