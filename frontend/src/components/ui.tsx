"use client";

import { CATEGORIES, CAMPS } from "@/lib/ui";
import {
  Radar,
  GraduationCap,
  Menu,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV = [
  { href: "/", label: "رصد", icon: Radar },
  { href: "/research", label: "دستیار", icon: GraduationCap },
];

export function TopNav() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 bg-navy text-white">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 bg-mblue flex items-center justify-center">
            <Radar size={18} strokeWidth={1.5} />
          </div>
          <span className="font-serif text-lg tracking-wide">AI Sentinel</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden sm:flex items-center gap-1">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-bold transition-all ${
                  active
                    ? "bg-mblue text-white"
                    : "text-white/70 hover:text-white hover:bg-white/10"
                }`}
              >
                <Icon size={17} strokeWidth={1.5} />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Mobile toggle */}
        <button className="sm:hidden p-2" onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="sm:hidden border-t border-white/10 bg-navy-soft">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setMenuOpen(false)}
              className="flex items-center gap-3 px-6 py-3 text-sm text-white/80 hover:text-white hover:bg-white/5 border-b border-white/5"
            >
              <Icon size={17} strokeWidth={1.5} />
              {label}
            </Link>
          ))}
        </div>
      )}
    </header>
  );
}

export function SectionHead({
  kicker,
  title,
  meta,
  icon: Icon,
}: {
  kicker?: string;
  title: string;
  meta?: string;
  icon?: React.ElementType;
}) {
  return (
    <div className="mb-6">
      {kicker && (
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-mblue mb-2">
          {kicker}
        </p>
      )}
      <div className="flex items-end justify-between border-b border-rule pb-4">
        <h2 className="font-serif text-2xl md:text-[28px] leading-tight text-navy flex items-center gap-3">
          {Icon && <Icon size={24} strokeWidth={1.5} className="text-mblue" />}
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
    <div className="flex flex-wrap gap-2">
      {CATEGORIES.map((c) => {
        const active = value === c.value;
        return (
          <button
            key={c.value || "all"}
            onClick={() => onChange(c.value)}
            className={`px-3 py-1.5 text-xs font-bold transition-all border ${
              active
                ? "bg-navy text-white border-navy"
                : "text-ink-dim border-rule hover:border-navy hover:text-navy"
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
    <div className="flex flex-wrap gap-2">
      {CAMPS.map((c) => {
        const active = value === c.value;
        return (
          <button
            key={c.value || "all"}
            onClick={() => onChange(c.value)}
            className={`px-3 py-1.5 text-xs font-bold transition-all border ${
              active
                ? "bg-mblue text-white border-mblue"
                : "text-ink-dim border-rule hover:border-mblue hover:text-mblue"
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
    <div className="flex flex-col items-center justify-center py-20 text-ink-faint">
      <p className="text-sm">{text}</p>
    </div>
  );
}

export function ErrorBox({ text }: { text: string }) {
  return (
    <div className="border-r-2 border-mred bg-red-50 px-4 py-3 text-sm text-[#8f1f1f]">
      {text}
    </div>
  );
}

export function SkeletonList({ n = 5 }: { n?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: n }).map((_, i) => (
        <div key={i} className="py-5 border-b border-rule">
          <div className="skeleton h-5 w-3/4 mb-3" />
          <div className="skeleton h-3 w-full mb-2" />
          <div className="skeleton h-3 w-2/3" />
        </div>
      ))}
    </div>
  );
}
