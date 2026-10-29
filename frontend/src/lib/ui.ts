// Persian UI constants

export const CATEGORIES: { value: string; label: string; color: string }[] = [
  { value: "", label: "همه", color: "" },
  { value: "infrastructure", label: "زیرساخت", color: "bg-orange-500/15 text-orange-300 border-orange-500/30" },
  { value: "models", label: "مدل‌ها", color: "bg-violet-500/15 text-violet-300 border-violet-500/30" },
  { value: "algorithms", label: "الگوریتم‌ها", color: "bg-blue-500/15 text-blue-300 border-blue-500/30" },
  { value: "tools", label: "ابزارها", color: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  { value: "evals", label: "ارزیابی", color: "bg-yellow-500/15 text-yellow-300 border-yellow-500/30" },
  { value: "applications", label: "کاربردها", color: "bg-pink-500/15 text-pink-300 border-pink-500/30" },
  { value: "policy_economy", label: "سیاست و اقتصاد", color: "bg-red-500/15 text-red-300 border-red-500/30" },
  { value: "discourse", label: "گفتمان", color: "bg-teal-500/15 text-teal-300 border-teal-500/30" },
];

/* Per-category look: gradient icon tile + soft badge, all in the green→blue spectrum */
export const CAT_STYLE: Record<string, { grad: string; badge: string; bar: string }> = {
  infrastructure: { grad: "from-emerald-400 to-teal-600", badge: "bg-emerald-50 text-emerald-700", bar: "bg-emerald-500" },
  models: { grad: "from-teal-400 to-cyan-600", badge: "bg-teal-50 text-teal-700", bar: "bg-teal-500" },
  algorithms: { grad: "from-cyan-400 to-sky-600", badge: "bg-cyan-50 text-cyan-700", bar: "bg-cyan-500" },
  tools: { grad: "from-sky-400 to-blue-600", badge: "bg-sky-50 text-sky-700", bar: "bg-sky-500" },
  evals: { grad: "from-green-400 to-emerald-600", badge: "bg-green-50 text-green-700", bar: "bg-green-500" },
  applications: { grad: "from-lime-400 to-teal-500", badge: "bg-lime-50 text-lime-700", bar: "bg-lime-500" },
  policy_economy: { grad: "from-blue-400 to-indigo-600", badge: "bg-blue-50 text-blue-700", bar: "bg-blue-500" },
  discourse: { grad: "from-teal-500 to-blue-500", badge: "bg-slate-100 text-slate-700", bar: "bg-slate-500" },
  _default: { grad: "from-slate-400 to-slate-600", badge: "bg-slate-100 text-slate-600", bar: "bg-slate-400" },
};

export const CAMPS: { value: string; label: string; color: string; flag: string }[] = [
  { value: "", label: "همه کشورها", color: "", flag: "" },
  { value: "US", label: "آمریکا", color: "bg-blue-500/15 text-blue-300 border-blue-500/30", flag: "🇺🇸" },
  { value: "CN", label: "چین", color: "bg-red-500/15 text-red-300 border-red-500/30", flag: "🇨🇳" },
  { value: "EU", label: "اروپا", color: "bg-amber-500/15 text-amber-300 border-amber-500/30", flag: "🇪🇺" },
  { value: "other", label: "سایر", color: "bg-gray-500/15 text-gray-300 border-gray-500/30", flag: "🌍" },
];

export function timeAgo(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "همین حالا";
  if (mins < 60) return `${toFa(mins)} دقیقه پیش`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${toFa(hours)} ساعت پیش`;
  const days = Math.floor(hours / 24);
  return `${toFa(days)} روز پیش`;
}

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  const day = toFa(d.getDate());
  const months = ["ژانویه","فوریه","مارس","آوریل","مه","ژوئن","ژوئیه","اوت","سپتامبر","اکتبر","نوامبر","دسامبر"];
  const month = months[d.getMonth()];
  const year = toFa(d.getFullYear());
  return `${day} ${month} ${year}`;
}

export function formatTime(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const h = toFa(String(d.getHours()).padStart(2, "0"));
  const m = toFa(String(d.getMinutes()).padStart(2, "0"));
  return `${h}:${m}`;
}

export function extractSource(url: string): string {
  try {
    const host = new URL(url).hostname.replace("www.", "");
    return host;
  } catch {
    return "";
  }
}

export function toFa(n: number | string): string {
  return String(n).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[Number(d)]);
}

export function faCategory(cat: string | null): string {
  return CATEGORIES.find((c) => c.value === cat)?.label ?? "سایر";
}

export function faCamp(camp: string): string {
  return CAMPS.find((c) => c.value === camp)?.label ?? "سایر";
}
