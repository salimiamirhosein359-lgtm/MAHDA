"use client";

import { CATEGORIES, CAMPS } from "@/lib/ui";
import { LayoutGrid, Swords, Search, Home } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "رصد", icon: Home },
  { href: "/rivalry", label: "چین vs آمریکا", icon: Swords },
  { href: "/research", label: "دستیار پژوهشی", icon: Search },
];

export function TopNav() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-0 z-10 border-b border-base-600 bg-base-900/90 backdrop-blur">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-500 to-cyan-500 flex items-center justify-center text-white font-black text-sm">
            AI
          </div>
          <span className="font-black text-lg">سِنتینل</span>
        </div>
        <div className="flex items-center gap-1">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-sm font-bold transition-colors ${
                  active ? "bg-accent-500 text-white" : "text-slate-400 hover:text-white hover:bg-base-700"
                }`}
              >
                <Icon size={16} />
                {label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
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
    <div className="flex flex-wrap gap-1.5">
      {CATEGORIES.map((c) => (
        <button
          key={c.value || "all"}
          onClick={() => onChange(c.value)}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all ${
            value === c.value
              ? "bg-accent-500 border-accent-500 text-white"
              : "border-base-600 text-slate-400 hover:border-accent-500/50 hover:text-white"
          }`}
        >
          {c.label}
        </button>
      ))}
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
    <div className="flex flex-wrap gap-1.5">
      {CAMPS.map((c) => (
        <button
          key={c.value || "all"}
          onClick={() => onChange(c.value)}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all ${
            value === c.value
              ? "bg-cyan-500 border-cyan-500 text-white"
              : "border-base-600 text-slate-400 hover:border-cyan-500/50 hover:text-white"
          }`}
        >
          {c.flag && <span className="ml-1">{c.flag}</span>}
          {c.label}
        </button>
      ))}
    </div>
  );
}

export function Empty({ text = "هنوز داده‌ای نیست" }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-slate-500">
      <LayoutGrid size={40} className="mb-3 opacity-30" />
      <p className="text-sm">{text}</p>
    </div>
  );
}

export function ErrorBox({ text }: { text: string }) {
  return (
    <div className="p-4 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-sm">
      {text}
    </div>
  );
}

export function SkeletonList({ n = 5 }: { n?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: n }).map((_, i) => (
        <div key={i} className="p-4 rounded-xl border border-base-600 bg-base-800">
          <div className="skeleton h-5 w-3/4 mb-3" />
          <div className="skeleton h-3 w-full mb-2" />
          <div className="skeleton h-3 w-2/3" />
        </div>
      ))}
    </div>
  );
}
