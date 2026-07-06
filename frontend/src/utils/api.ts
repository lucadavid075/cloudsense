const BASE_URL = import.meta.env.VITE_API_URL || "";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

// Cost endpoints
export const api = {
  getDailyCosts: (days = 30) =>
    fetchJSON<{ data: DailyCost[]; total: number; days: number }>(
      `/api/costs/daily?days=${days}`
    ),

  getCostsByService: (days = 30) =>
    fetchJSON<{ raw: ServiceCostRow[]; by_service: ServiceTotal[]; days: number }>(
      `/api/costs/by-service?days=${days}`
    ),

  getForecast: (daysAhead = 30) =>
    fetchJSON<ForecastResult>(`/api/costs/forecast?days_ahead=${daysAhead}`),

  getAnomalies: (days = 30) =>
    fetchJSON<{ anomalies: Anomaly[]; count: number }>(
      `/api/costs/anomalies?days=${days}`
    ),

  getIdleResources: () =>
    fetchJSON<IdleResourceResult>("/api/resources/idle"),

  chat: (messages: ChatMessage[], sessionId?: string) =>
    postJSON<{ reply: string; session_id: string }>("/api/chat/", {
      messages,
      session_id: sessionId,
    }),

  getStarters: () =>
    fetchJSON<{ starters: string[] }>("/api/chat/starters"),

  triggerDigest: () =>
    postJSON<{ status: string }>("/api/alerts/digest/trigger", {}),
};

// Types
export interface DailyCost {
  date: string;
  amount: number;
}

export interface ServiceCostRow {
  date: string;
  service: string;
  amount: number;
  currency: string;
}

export interface ServiceTotal {
  service: string;
  total: number;
}

export interface ForecastResult {
  mean_value: number;
  currency: string;
  period_start: string;
  period_end: string;
  error?: string;
}

export interface Anomaly {
  date: string;
  amount: number;
  average: number;
  multiplier: number;
}

export interface IdleResource {
  resource_type: string;
  resource_id: string;
  region: string;
  estimated_monthly_cost: number;
  details: Record<string, unknown>;
}

export interface IdleResourceResult {
  resources: IdleResource[];
  summary: {
    total_idle_resources: number;
    unattached_ebs_volumes: number;
    unattached_elastic_ips: number;
    stopped_ec2_instances: number;
    estimated_monthly_waste_usd: number;
  };
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
