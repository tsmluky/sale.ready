import { API_BASE_URL, MOCK_LITE_SIGNAL, MOCK_PRO_RESPONSE, MOCK_ADVISOR_RESPONSE } from "../constants";
import {
  SignalLite,
  ProResponse,
  AdvisorResponse,
  SignalEvaluation,
  LogRow,

  ChatMessage,
  AnalysisMode,
  UserProfile,
} from "../types";

// =========================
// Helpers HTTP básicos
// =========================

const DEFAULT_TIMEOUT_MS = 60000; // Increased to 60s for robustness


async function fetchWithTimeout(
  url: string,
  init: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  // Inject Token if available
  const token = localStorage.getItem('auth_token');
  const headers = { ...init.headers } as Record<string, string>;

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(url, { ...init, headers, signal: controller.signal });
    return res;
  } catch (err: any) {
    console.error(`[API] 💥 Error ${url}`, err);
    throw err;
  } finally {
    clearTimeout(id);
  }
}

// ... existing isJsonContent ...

function isJsonContent(res: Response): boolean {
  const ct = res.headers.get("content-type") || "";
  return ct.toLowerCase().includes("application/json");
}

// CSV -> LogRow[]
const parseCSV = (csvText: string): LogRow[] => {
  if (!csvText) return [];
  const lines = csvText.trim().split(/\r?\n/);
  if (lines.length < 2) return [];

  const headers = lines[0].split(",").map((h) => h.trim());
  const result: LogRow[] = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const cols = line.split(",");
    const row: LogRow = {};
    for (let j = 0; j < headers.length; j++) {
      row[headers[j]] = (cols[j] ?? "").trim();
    }
    result.push(row);
  }
  return result;
}

// =========================
// Health (para DevPanel y checks)
// =========================

export async function getHealth(): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/health`, { method: "GET" });
  if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
  return res.json();
}

// =========================
// Análisis LITE / PRO / ADVISOR
// =========================

export async function analyzeLite(token: string, timeframe: string): Promise<SignalLite> {
  const body = { token, timeframe };

  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/analyze/lite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }

    return (await res.json()) as SignalLite;
  } catch (err) {
    console.error("analyzeLite failed", err);
    throw err; // Propagate error, do not mock
  }
}

export async function analyzePro(
  token: string,
  timeframe: string,
  rag: boolean
): Promise<ProResponse> {
  const body = { token, timeframe, context: { rag } };

  try {
    // Increased timeout for PRO analysis (AI generation can take time)
    const res = await fetchWithTimeout(`${API_BASE_URL}/analyze/pro`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }, 120000); // 120s timeout for DeepSeek/Gemini

    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }

    const data: any = isJsonContent(res) ? await res.json() : await res.text();
    const raw =
      typeof data === "string"
        ? data
        : data.analysis ?? data.raw ?? JSON.stringify(data, null, 2);

    // Return the full data object merged with the normalized 'raw' field
    // This preserves confidence, entry, tp, sl, etc.
    return { ...data, raw } as ProResponse;
  } catch (err) {
    console.error("analyzePro failed", err);
    throw err; // Propagate error, do not mock
  }
}

type AdvisorPayload = {
  token: string;
  direction: "long" | "short";
  entry: number;
  tp: number;
  sl: number;
  size_quote: number;
};

export async function analyzeAdvisor(payload: AdvisorPayload): Promise<AdvisorResponse> {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/analyze/advisor`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }

    return (await res.json()) as AdvisorResponse;
  } catch (err) {
    console.error("analyzeAdvisor failed", err);
    throw err;
  }
}

// =========================
// Logs genéricos /logs/{mode}/{token}
// Devuelve siempre LogRow[]
// =========================

export async function fetchLogs(mode: string, token: string): Promise<LogRow[]> {
  const modeUp = mode.toUpperCase();
  const tokenLower = token.toLowerCase();
  const url = `${API_BASE_URL}/logs/${modeUp}/${tokenLower}`;

  try {
    const res = await fetchWithTimeout(url, { method: "GET" });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }

    if (isJsonContent(res)) {
      const data: any = await res.json();
      if (Array.isArray(data)) return data as LogRow[];
      if (Array.isArray(data.logs)) return data.logs as LogRow[];
      return [];
    } else {
      const text = await res.text();
      return parseCSV(text);
    }
  } catch (err) {
    console.error("fetchLogs failed, returning []", err);
    return [];
  }
}

// =========================
// Market Data (Charts)
// =========================
export async function getOHLCV(token: string, timeframe: string): Promise<any[]> {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/market/ohlcv/${token}?timeframe=${timeframe}&limit=100`, { method: "GET" });
    if (!res.ok) throw new Error("Failed to fetch OHLCV");
    const data = await res.json();
    // Normalize for lightweight-charts: time (seconds), open, high, low, close
    return data.map((d: any) => ({
      time: d.timestamp / 1000, // MS to Seconds
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
      value: d.close, // fallback
    }));
  } catch (err) {
    console.warn("getOHLCV failed", err);
    return [];
  }
}

// =========================
// Trigger Evaluation (On-Demand)
// =========================

export async function triggerBatchEvaluation(): Promise<any> {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/analyze/evaluate`, {
      method: "POST",
    }, 60000); // 60s timeout for batch evaluation
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } catch (err) {
    console.warn("triggerBatchEvaluation failed", err);
    return { status: "error", message: "Failed to trigger evaluation" };
  }
}

// =========================
// getSignalEvaluation: /logs/EVALUATED/{token}
// =========================

export async function getSignalEvaluation(
  token: string,
  signalTimestamp: string
): Promise<SignalEvaluation | null> {
  const tokenLower = token.toLowerCase();
  const url = `${API_BASE_URL}/logs/EVALUATED/${tokenLower}`;

  try {
    const res = await fetchWithTimeout(url, { method: "GET" });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }

    let rows: LogRow[] = [];
    if (isJsonContent(res)) {
      const data: any = await res.json();
      if (Array.isArray(data)) rows = data as LogRow[];
      else if (Array.isArray(data.logs)) rows = data.logs as LogRow[];
    } else {
      const text = await res.text();
      rows = parseCSV(text);
    }

    const match = rows.find((r) => {
      const ts = (r["signal_ts"] as string) || (r["timestamp"] as string);
      return ts === signalTimestamp;
    });

    if (!match) return null;

    const rawResult = String(match["result"] ?? match["status"] ?? "").toUpperCase();

    let status: SignalEvaluation["status"] = "BE";
    if (rawResult.includes("WIN") || rawResult.includes("TP")) status = "WIN";
    else if (rawResult.includes("LOSS") || rawResult.includes("SL")) status = "LOSS";

    const exitPriceStr =
      (match["exit_price"] as string) ||
      (match["price_at_eval"] as string) ||
      (match["tp"] as string) ||
      (match["sl"] as string) ||
      "";
    const exit_price = exitPriceStr ? Number(exitPriceStr) : NaN;

    const closed_at =
      (match["evaluated_at"] as string) ||
      (match["closed_at"] as string) ||
      (match["timestamp"] as string) ||
      new Date().toISOString();

    let pnl_r = 0;
    if (match["pnl_r"] != null) {
      pnl_r = Number(match["pnl_r"]);
    } else if (match["move_pct"] != null) {
      const mv = Number(match["move_pct"]);
      if (!Number.isNaN(mv)) pnl_r = mv / 100;
    }

    return {
      status,
      pnl_r,
      exit_price,
      closed_at,
    };
  } catch (err) {
    console.error("getSignalEvaluation failed, returning null", err);
    return null;
  }
}

// =========================
// Telegram / Leaderboard / AdvisorChat
// =========================

export async function trackSignal(signalData: any): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/logs/track`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(signalData)
  });
  if (!res.ok) throw new Error("Failed to track signal");
  return res.json();
}

export async function notifyTelegram(message: string, chatId?: string): Promise<boolean> {
  try {
    const body: any = { text: message };
    if (chatId) body.chat_id = chatId;

    const res = await fetchWithTimeout(`${API_BASE_URL}/notify/telegram`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }

    const data = await res.json();
    if (data.status === 'skipped' || data.status === 'error') {
      console.warn('Telegram API skipped:', data.detail);
      throw new Error(data.detail || 'Telegram sending failed/skipped');
    }

    return true;
  } catch (err: any) {
    console.warn("notifyTelegram failed", err);
    throw err; // Propagate error so UI knows
  }
}

// Chat del Advisor (demo-friendly)
// - Primer mensaje: usa analyzeAdvisor y devuelve un ChatMessage tipo "analysis"
// - Mensajes siguientes: llama a /analyze/advisor/chat
export async function sendAdvisorChat(
  history: ChatMessage[],
  context: any
): Promise<ChatMessage> {
  // Mensaje inicial: hacemos un análisis completo
  if (!history.length) {
    const analysis = await analyzeAdvisor(context);
    return {
      id: Date.now().toString(),
      role: "assistant",
      content: `I've analyzed your proposed ${context.token} ${context.direction} position. Here is my risk assessment.`,
      type: "analysis",
      data: analysis,
      timestamp: new Date().toISOString(),
    };
  }

  // Mensajes siguientes: endpoint de chat real
  try {
    const body = {
      messages: history.map((m) => ({ role: m.role, content: m.content })),
      context,
    };

    const res = await fetchWithTimeout(
      `${API_BASE_URL}/analyze/advisor/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
      60000
    );

    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }

    const data: any = isJsonContent(res) ? await res.json() : await res.text();
    const content =
      typeof data === "string"
        ? data
        : data.content ?? data.message ?? data.reply ?? "Advisor reply received.";

    return {
      id: Date.now().toString(),
      role: "assistant",
      content,
      type: "text",
      timestamp: new Date().toISOString(),
    };
  } catch (err) {
    console.error("sendAdvisorChat failed", err);
    return {
      id: Date.now().toString(),
      role: "assistant",
      content:
        "I'm having trouble reaching the advisor backend right now. Please try again later.",
      type: "text",
      timestamp: new Date().toISOString(),
    };
  }
}

// =========================
// Auth API
// =========================

export async function login(email: string, password: string): Promise<any> {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const res = await fetchWithTimeout(`${API_BASE_URL}/auth/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });

  if (!res.ok) {
    throw new Error(`Login failed: ${res.statusText}`);
  }

  return res.json();
}

export async function register(email: string, password: string, name?: string): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name: name || 'Trader' })
  });

  // Handle 409 Conflict specifically
  if (res.status === 409) {
    throw new Error('Email already registered');
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));

    // Handle Validation Errors (422)
    if (res.status === 422 && Array.isArray(errorData.detail)) {
      const messages = errorData.detail.map((err: any) => matchValidationError(err)).join(', ');
      throw new Error(messages);
    }

    throw new Error(errorData.detail || 'Registration failed');
  }

  return res.json();
}

function matchValidationError(err: any): string {
  if (err.msg) return err.msg;
  return JSON.stringify(err);
}

export async function getMe(): Promise<UserProfile['user']> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/auth/users/me`, {
    method: 'GET'
  });

  if (!res.ok) throw new Error('Failed to fetch user profile');
  return res.json();
}


// =========================
// API pública agrupada
// =========================

export async function fetchMarketplace(): Promise<any[]> {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/strategies/marketplace`, {
      method: 'GET'
    });
    if (!res.ok) throw new Error('Failed to fetch marketplace');
    return res.json();
  } catch (err) {
    console.warn("fetchMarketplace failed", err);
    return [];
  }
}

export async function fetchPersonaHistory(personaId: string): Promise<any[]> {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/strategies/marketplace/${personaId}/history`, {
      method: "GET"
    });
    if (!res.ok) throw new Error("Failed to fetch history");
    return res.json();
  } catch (err) {
    console.error("fetchPersonaHistory failed", err);
    return [];
  }
}

// =========================
// Persona Creation
// =========================

export async function createPersona(payload: any): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/strategies/marketplace/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Failed to create persona: ${err}`);
  }

  return res.json();
}

export async function deletePersona(id: string): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/strategies/marketplace/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to delete persona");
  }

  return res.json();
}


export async function togglePersona(id: string): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/strategies/marketplace/${encodeURIComponent(id)}/toggle`, {
    method: "PATCH",
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to toggle persona");
  }

  return res.json();
}

// =========================
// M5: Admin Panel API
// =========================

export async function fetchAdminStats(): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/admin/stats`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to fetch admin stats");
  return res.json();
}

export async function fetchAdminUsers(page = 1, search = ""): Promise<any> {
  const query = new URLSearchParams({ page: page.toString(), size: "20" });
  if (search) query.append("q", search);

  const res = await fetchWithTimeout(`${API_BASE_URL}/admin/users?${query.toString()}`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to fetch users");
  return res.json();
}

export async function updateUserPlan(userId: number | string, plan: string): Promise<any> {
  // Use self-service endpoint for own plan update
  const res = await fetchWithTimeout(`${API_BASE_URL}/auth/users/me/plan?new_plan=${plan}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" }
  });
  if (!res.ok) throw new Error("Failed to update plan");
  return res.json();
}

export async function fetchAdminSignals(page = 1): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/admin/signals?page=${page}&size=50`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to fetch signals");
  return res.json();
}

export async function toggleSignalVisibility(signalId: number, isHidden: boolean): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/admin/signals/${signalId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_hidden: isHidden })
  });
  if (!res.ok) throw new Error("Failed to toggle signal visibility");
  return res.json();
}

// =========================
// M6: Dashboard Stats (Real Data)
// =========================

export async function getDashboardStats(): Promise<{ summary: any, chart: any[] }> {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/stats/dashboard`, { method: "GET" });
    if (!res.ok) throw new Error("Failed to fetch dashboard stats");
    return res.json();
  } catch (err) {
    console.error("getDashboardStats failed", err);
    // Return empty fail-safe to prevent UI crash
    return {
      summary: {
        win_rate_24h: 0,
        signals_evaluated_24h: 0,
        signals_total_evaluated: 0,
        signals_lite_24h: 0,
        open_signals: 0,
        pnl_7d: 0.0
      },
      chart: []
    };
  }
}

// Deprecated: getStats is now part of getDashboardStats
// Kept for compatibility if needed, but returning safe defaults
export async function getStats(): Promise<any> {
  const data = await getDashboardStats();
  return {
    win_rate: data.summary.win_rate_24h,
    active_fleet: data.summary.open_signals, // Mapping "Open Signals" to "Active Fleet" concept
    pnl_7d: data.summary.pnl_7d
  };
}

// Deprecated: Chart data is now part of getDashboardStats
export async function getChartData(): Promise<any[]> {
  const data = await getDashboardStats();
  return data.chart;
}

export async function getEvaluatedCount(): Promise<number> {
  const data = await getDashboardStats();
  return data.summary.signals_evaluated_24h; // Or total if preferred, but usually 24h count is what we want for "activity"
}


export async function getRecentSignals(limit: number = 20, savedOnly: boolean = false, includeSystem: boolean = false): Promise<any[]> {
  try {
    let url = `${API_BASE_URL}/logs/recent?limit=${limit}`;
    if (savedOnly) url += `&saved_only=true`;
    url += `&include_system=${includeSystem}`;

    const res = await fetchWithTimeout(url, { method: "GET" });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : (data.logs || []);
  } catch { return []; }
}

export async function toggleSignalSave(id: number): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/logs/${id}/toggle_save`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to toggle save");
  return res.json();
}

export async function getSystemConfig(): Promise<any> {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/system/config`, { method: "GET" }, 5000);
    if (!res.ok) return {};
    return res.json();
  } catch (err) {
    console.warn("getSystemConfig failed", err);
    return {};
  }
}

export const api = {
  analyzeLite,
  analyzePro,
  analyzeAdvisor,
  fetchLogs,
  triggerBatchEvaluation,
  getSignalEvaluation,
  notifyTelegram,
  trackSignal,

  sendAdvisorChat,
  login,
  register,
  getMe,
  fetchMarketplace,
  fetchPersonaHistory,
  createPersona,
  deletePersona,
  togglePersona,
  getOHLCV,
  getSystemConfig,
  getDashboardStats,
  getStats,
  getEvaluatedCount,
  getChartData,
  getRecentSignals,
  toggleSignalSave, // Export added to object

  // Admin
  fetchAdminStats,
  fetchAdminUsers,
  updateUserPlan,
  fetchAdminSignals,
  toggleSignalVisibility,
  get: async (endpoint: string) => {
    const res = await fetchWithTimeout(`${API_BASE_URL}${endpoint}`, { method: 'GET' });
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
    return res.json();
  },

  updateTelegramId: async (chatId: string) => {
    const res = await fetchWithTimeout(`${API_BASE_URL}/auth/users/me/telegram`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId }),
    });
    if (!res.ok) throw new Error("Failed to update Telegram ID");
    return res.json();
  },

  updateTimezone: async (timezone: string) => {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/auth/users/me/timezone`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ timezone }),
    });
    if (!response.ok) throw new Error('Failed to update timezone');
    return response.json();
  },

  changePassword: async (oldPassword: string, newPassword: string) => {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE_URL}/auth/users/me/password`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to update password');
    }
    return response.json();
  },

  getAdvisorProfile: async () => {
    const res = await fetchWithTimeout(`${API_BASE_URL}/advisor/profile`, { method: "GET" });
    if (!res.ok) throw new Error("Failed to fetch profile");
    return res.json();
  },

  updateAdvisorProfile: async (data: any) => {
    const res = await fetchWithTimeout(`${API_BASE_URL}/advisor/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update profile");
    return res.json();
  },
};
