// AI Sentinel — API client layer

export interface ItemOut {
  id: number;
  title: string;
  url: string;
  summary: string | null;
  author: string | null;
  published_at: string | null;
  item_type: string;
  category: string | null;
  camp: string;
  actor: string | null;
  score: number | null;
  source_id: number;
}

export interface ItemListOut {
  total: number;
  items: ItemOut[];
}

export interface RivalryOut {
  since: string;
  us: { camp: string; count: number; top_items: ItemOut[] };
  cn: { camp: string; count: number; top_items: ItemOut[] };
}

export interface TrendOut {
  category: string | null;
  keyword: string;
  count: number;
  momentum: number;
}

export interface ResearchJobOut {
  id: number;
  question: string;
  mode: string;
  status: string;
  breadth: number;
  depth: number;
  result_markdown: string | null;
  error: string | null;
  steps: { id: number; step_no: number; step_type: string; query: string | null; finding: string | null }[];
}

export interface AskOut {
  answer: string;
  sources: { ref_no: number; title: string; url: string; snippet: string | null }[];
  online: boolean;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  items(params: {
    category?: string;
    camp?: string;
    item_type?: string;
    min_score?: number;
    days?: number;
    limit?: number;
    offset?: number;
  }): Promise<ItemListOut> {
    const qs = new URLSearchParams();
    if (params.category) qs.set("category", params.category);
    if (params.camp) qs.set("camp", params.camp);
    if (params.item_type) qs.set("item_type", params.item_type);
    if (params.min_score !== undefined) qs.set("min_score", String(params.min_score));
    qs.set("days", String(params.days ?? 7));
    qs.set("limit", String(params.limit ?? 50));
    if (params.offset) qs.set("offset", String(params.offset));
    return get(`/api/v1/items?${qs.toString()}`);
  },

  rivalry(days = 7, top = 5): Promise<RivalryOut> {
    return get(`/api/v1/rivalry?days=${days}&top=${top}`);
  },

  trends(days = 7, limit = 20): Promise<TrendOut[]> {
    return get(`/api/v1/trends?days=${days}&limit=${limit}`);
  },

  startResearch(question: string, mode = "deep", breadth = 3, depth = 2): Promise<{ job_id: number }> {
    return post("/api/v1/research", { question, mode, breadth, depth });
  },

  research(id: number): Promise<ResearchJobOut> {
    return get(`/api/v1/research/${id}`);
  },

  ask(question: string, online = false): Promise<AskOut> {
    return post("/api/v1/ask", { question, online });
  },
};
