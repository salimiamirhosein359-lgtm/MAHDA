import { ExternalLink, Clock, User, Globe, Calendar } from "lucide-react";
import type { ItemOut } from "@/lib/api";
import { formatDate, formatTime, extractSource, CATEGORIES } from "@/lib/ui";

export default function ItemCard({ item }: { item: ItemOut }) {
  const cat = CATEGORIES.find((c) => c.value === item.category);
  const catLabel = cat && cat.value ? cat.label : "عمومی";
  const source = extractSource(item.url);

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group block bg-white border border-rule hover:border-mblue transition-all"
    >
      {/* Category tag — always shown */}
      <div className="bg-cgray-soft px-4 py-1.5 border-b border-rule">
        <span className="text-[10px] font-bold uppercase tracking-wider text-mblue">
          {catLabel}
        </span>
      </div>

      <div className="p-5">
        {/* Title */}
        <h3 className="font-serif text-base md:text-lg leading-7 text-navy group-hover:text-mblue transition-colors line-clamp-2">
          {item.title}
        </h3>

        {/* Summary */}
        {item.summary && (
          <p className="mt-2 text-sm text-ink-dim leading-[1.7] line-clamp-2">
            {item.summary}
          </p>
        )}

        {/* Meta: source, author, date, time */}
        <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-ink-faint">
          {source && (
            <span className="flex items-center gap-1.5">
              <Globe size={12} strokeWidth={1.5} />
              {source}
            </span>
          )}
          {item.author && (
            <span className="flex items-center gap-1.5">
              <User size={12} strokeWidth={1.5} />
              {item.author}
            </span>
          )}
          <span className="flex items-center gap-1.5">
            <Calendar size={12} strokeWidth={1.5} />
            {formatDate(item.published_at)}
          </span>
          {formatTime(item.published_at) && (
            <span className="flex items-center gap-1.5">
              <Clock size={12} strokeWidth={1.5} />
              {formatTime(item.published_at)}
            </span>
          )}
          <span className="mr-auto flex items-center gap-1.5 text-mblue opacity-0 group-hover:opacity-100 transition-opacity">
            <ExternalLink size={12} strokeWidth={1.5} />
            مشاهده
          </span>
        </div>
      </div>
    </a>
  );
}
