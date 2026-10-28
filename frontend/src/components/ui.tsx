"use client";

import { CATEGORIES, CAMPS } from "@/lib/ui";
import {
  LayoutGrid,
  Swords,
  Search,
  Home,
  MessageSquare,
  ChevronLeft,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "رصد", icon: Home },
  { href: "/rivalry", label: "چین و آمریکا", icon: Swords },
  { href: "/research", label: "دستیار پژوهشی", icon: Search },
  { href: "/chat", label: "گفت‌وگو", icon: MessageSquare },
];

export function TopNav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-20 bg-navy text-white">
      {/* Utility strip */}
      <div className="border-b border-white/10">
        <div className="max-w-6xl mx-auto px-4 h-8 flex items-center justify-between text-[11px] text-white/60">
          <span>تحلیل رقابتی هوش مصنوعی — نسخه پایش</span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-1.5 h-1.5 bg-mblue-400 rounded-full" />
            رصد خودکار فعال است
          </span>
        </div>
      </div>
      {/* Main bar */}
      <div className="border-b border-white/10">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          {/* Wordmark — serif logotype, McKinsey style */}
          <Link href="/" className="flex items-baseline gap-2 group">
            <span className="font-serif text-2xl leading-none tracking-wide text-white">
              AI&nbsp;Sentinel
            </span>
            <span className="hidden sm:inline-block text-[10px] uppercase tracking-[0.3em] text-white/50 group-hover:text-white/70 transition-colors">
              Insights
            </span>
          </Link>
          {/* Nav — thin-line icons, understated */}
          <nav className="flex items-center gap-0.5">
            {NAV.map(({ href, label, icon: Icon }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-1.5 px-3 py-2 text-sm transition-colors ${
                    active
                      ? "text-white border-b-2 border-mblue-500 -mb-[1px]"
                      : "text-white/70 hover:text-white border-b-2 border-transparent"
                  }`}
                >
                  <Icon size={16} strokeWidth={1.5} />
                  <span className="hidden sm:inline">{label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}

/* Thin rule section header, McKinsey editorial style */
export function SectionHead({
  kicker,
  title,
  meta,
}: {
  kicker?: string;
  title: string;
  meta?: string;
}) {
  return (
    <div className="mb-5">
      {kicker && (
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-mblue-500 mb-2">
          {kicker}
        </p>
      )}
      <div className="flex items-end justify-between border-b border-rule pb-4">
        <h2 className="font-serif text-2xl md:text-[28px] leading-tight text-navy">
          {title}
        </h2>
        {meta && <p className="text-xs text-ink-faint">{meta}</p>}
      </div>
    </div>
  );
}

export function CategoryFilter({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-2">
      {CATEGORIES.map((c) => {
        const active = value === c.value;
        return (
          <button
            key={c.value || "all"}
            onClick={() => onChange(c.value)}
            className={`relative pb-1 text-sm transition-colors ${
              active
                ? "text-navy font-bold border-b-2 border-mblue-500"
                : "text-ink-dim hover:text-navy border-b-2 border-transparent"
            }`}
          >
            {c.label}
          </button>
        );
      })}
    </div>
  );
}

export function CampFilter({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-2">
      {CAMPS.map((c) => {
        const active = value === c.value;
        return (
          <button
            key={c.value || "all"}
            onClick={() => onChange(c.value)}
            className={`relative pb-1 text-sm transition-colors ${
              active
                ? "text-navy font-bold border-b-2 border-mblue-500"
                : "text-ink-dim hover:text-navy border-b-2 border-transparent"
            }`}
          >
            {c.flag && <span className="ml-1">{c.flag}</span>}
            {c.label}
          </button>
        );
      })}
    </div>
  );
}

export function Empty({ text = "هنوز داده‌ای نیست" }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-ink-faint border-t border-rule">
      <LayoutGrid size={40} strokeWidth={1.5} className="mb-4 opacity-40" />
      <p className="text-sm leading-editorial">{text}</p>
    </div>
  );
}

export function ErrorBox({ text }: { text: string }) {
  /* McKinsey red reserved for alerts only */
  return (
    <div className="border-r-2 border-mred bg-red-50 px-4 py-3 text-sm text-[#8f1f1f] leading-editorial">
      {text}
    </div>
  );
}

export function SkeletonList({ n = 5 }: { n?: number }) {
  return (
    <div className="divide-y divide-rule border-y border-rule">
      {Array.from({ length: n }).map((_, i) => (
        <div key={i} className="py-6">
          <div className="skeleton h-5 w-3/4 mb-3" />
          <div className="skeleton h-3 w-full mb-2" />
          <div className="skeleton h-3 w-2/3" />
        </div>
      ))}
    </div>
  );
}

/* Breadcrumb — quiet, corporate */
export function Breadcrumb({ items }: { items: { label: string; href?: string }[] }) {
  return (
    <nav className="flex items-center gap-1 text-xs text-ink-faint mb-4">
      {items.map((it, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && <ChevronLeft size={12} strokeWidth={1.5} />}
          {it.href ? (
            <Link href={it.href} className="hover:text-mblue-500 transition-colors">
              {it.label}
            </Link>
          ) : (
            <span className="text-ink-dim">{it.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
