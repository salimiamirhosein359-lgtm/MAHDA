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

export function toFa(n: number | string): string {
  return String(n).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[Number(d)]);
}

export function faCategory(cat: string | null): string {
  return CATEGORIES.find((c) => c.value === cat)?.label ?? "سایر";
}

export function faCamp(camp: string): string {
  return CAMPS.find((c) => c.value === camp)?.label ?? "سایر";
}
