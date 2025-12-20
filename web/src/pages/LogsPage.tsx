import React, { useEffect, useState } from "react";
import { fetchLogs, getSignalEvaluation, triggerBatchEvaluation } from "../services/api";
import type { LogRow, SignalEvaluation } from "../types";
import { formatPrice, formatRelativeTime } from "../utils/format";

type Mode = "LITE" | "PRO" | "ADVISOR";

const TOKENS = ["ETH", "BTC", "SOL", "DOT", "ADA", "XRP", "AVAX", "LINK", "DOGE"] as const;

type RowWithEval = {
  row: LogRow;
  evaluation?: SignalEvaluation | null;
  evaluationLoading?: boolean;
  evaluationError?: string | null;
};

export const LogsPage: React.FC = () => {
  const [mode, setMode] = useState<Mode>("LITE");
  const [token, setToken] = useState<string>("ETH");

  const [rows, setRows] = useState<RowWithEval[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Carga inicial
  useEffect(() => {
    loadLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, token]);

  async function loadLogs() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchLogs(mode, token);
      // Ordenamos por timestamp descendente si existe
      const sorted = [...data].sort((a, b) => {
        const ta = getField(a, "timestamp") || getField(a, "signal_ts") || "";
        const tb = getField(b, "timestamp") || getField(b, "signal_ts") || "";
        return ta < tb ? 1 : ta > tb ? -1 : 0;
      });
      setRows(sorted.map((row) => ({ row })));
    } catch (err: any) {
      console.error("Error loading logs", err);
      setError(err?.message ?? "Error loading logs");
      setRows([]);
    } finally {
      setIsLoading(false);
    }
  }

  function getField(row: LogRow, key: string, fallback: string = ""): string {
    const v = row[key];
    if (v === undefined || v === null) return fallback;
    return String(v);
  }

  function getTimestamp(row: LogRow): string {
    return (
      (row["signal_ts"] as string) ||
      (row["timestamp"] as string) ||
      (row["time"] as string) ||
      ""
    );
  }

  function evaluationBadge(evalObj?: SignalEvaluation | null) {
    if (!evalObj) return <span className="text-xs text-slate-500">Pending</span>;

    let color = "bg-slate-800 text-slate-100 border-slate-700";
    let label = "BE";
    if (evalObj.status === "WIN") {
      color = "bg-emerald-500/10 text-emerald-300 border-emerald-500/40";
      label = "WIN";
    } else if (evalObj.status === "LOSS") {
      color = "bg-rose-500/10 text-rose-300 border-rose-500/40";
      label = "LOSS";
    }

    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${color}`}
      >
        {label} · {(evalObj.pnl_r * 100).toFixed(1)}%
      </span>
    );
  }

  async function handleCheckEvaluation(index: number) {
    setRows((prev) =>
      prev.map((item, i) =>
        i === index ? { ...item, evaluationLoading: true, evaluationError: null } : item
      )
    );

    try {
      const target = rows[index];
      const rawTs = getTimestamp(target.row);
      const ts = rawTs && !rawTs.endsWith("Z") ? `${rawTs}Z` : rawTs;
      if (!ts) throw new Error("No timestamp for this signal");

      // Trigger Evaluation
      await triggerBatchEvaluation();
      await new Promise((r) => setTimeout(r, 800));

      const evalRes = await getSignalEvaluation(token, ts);

      if (!evalRes) {
        // No hay evaluación para esta señal
        setRows((prev) =>
          prev.map((item, i) =>
            i === index
              ? {
                ...item,
                evaluation: null,
                evaluationLoading: false,
                evaluationError: "Signal is Active. Result pending...",
              }
              : item
          )
        );
      } else {
        setRows((prev) =>
          prev.map((item, i) =>
            i === index
              ? {
                ...item,
                evaluation: evalRes,
                evaluationLoading: false,
                evaluationError: null,
              }
              : item
          )
        );
      }
    } catch (err: any) {
      console.error("Error getting evaluation", err);
      setRows((prev) =>
        prev.map((item, i) =>
          i === index
            ? {
              ...item,
              evaluationLoading: false,
              evaluationError: err?.message ?? "Error getting evaluation",
            }
            : item
        )
      );
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold text-slate-50">Signals History</h1>
        <p className="text-slate-400 text-sm">
          Review generated signals by mode and token. For LITE signals you can also check
          automatic evaluation (WIN / LOSS / BE) when available.
        </p>
      </div>

      {/* Controls */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 flex flex-col gap-4">
        <div className="flex flex-wrap gap-3">
          {/* Token select */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 uppercase tracking-wide">Token</span>
            <select
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {TOKENS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Reload */}
          <div className="flex items-center ml-auto">
            <button
              type="button"
              onClick={loadLogs}
              disabled={isLoading}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-100 border border-slate-600 hover:bg-slate-700 disabled:opacity-60"
            >
              {isLoading ? "Loading..." : "Reload"}
            </button>
          </div>
        </div>

        {error && (
          <div className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
      </div>

      {/* Table / list */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4">
        {isLoading && rows.length === 0 && (
          <p className="text-sm text-slate-400">Loading logs...</p>
        )}

        {!isLoading && rows.length === 0 && !error && (
          <p className="text-sm text-slate-500">No logs found for this mode/token.</p>
        )}

        {rows.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm text-slate-100">
              <thead>
                <tr className="border-b border-slate-800 text-xs text-slate-400 uppercase">
                  <th className="text-left py-2 pr-3">Time</th>
                  <th className="text-left py-2 pr-3">Mode</th>
                  <th className="text-left py-2 pr-3">Source</th>
                  <th className="text-left py-2 pr-3">Direction</th>
                  <th className="text-left py-2 pr-3">TF</th>
                  <th className="text-left py-2 pr-3">Entry</th>
                  <th className="text-left py-2 pr-3">TP</th>
                  <th className="text-left py-2 pr-3">SL</th>
                  {mode === "LITE" && <th className="text-left py-2 pr-3">Eval</th>}
                  <th className="text-left py-2 pr-3">Notes</th>
                  {mode === "LITE" && <th className="py-2 pr-3" />}
                </tr>
              </thead>
              <tbody>
                {rows.map((item, index) => {
                  const { row, evaluation, evaluationLoading, evaluationError } = item;
                  const rawTs = getTimestamp(row);
                  // Fix Timezone: Ensure timestamp is treated as UTC if missing 'Z'
                  const ts = rawTs && !rawTs.endsWith("Z") ? `${rawTs}Z` : rawTs;
                  const tf =
                    getField(row, "timeframe") ||
                    getField(row, "tf") ||
                    getField(row, "frame");
                  const dir =
                    getField(row, "direction") ||
                    getField(row, "side") ||
                    getField(row, "signal_direction");
                  const entry = getField(row, "entry");
                  const tp = getField(row, "tp");
                  const sl = getField(row, "sl");
                  const note =
                    getField(row, "reason") ||
                    getField(row, "rationale") ||
                    getField(row, "comment");

                  return (
                    <tr key={index} className="border-b border-slate-800/60 last:border-none">
                      <td className="py-2 pr-3 align-top text-xs text-slate-300 whitespace-nowrap">
                        <div className="flex flex-col">
                          <span className="font-medium text-slate-200">
                            {formatRelativeTime(ts)}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {ts ? new Date(ts).toLocaleTimeString() : "-"}
                          </span>
                        </div>
                      </td>
                      <td className="py-2 pr-3 align-top text-xs text-slate-400 whitespace-nowrap">{mode}</td>
                      <td className="py-2 pr-3 align-top text-xs text-slate-500 font-mono whitespace-nowrap">
                        {getField(row, "source") === "lite_v2_router" ? (
                          <span className="text-indigo-400 font-bold">ME</span>
                        ) : (
                          getField(row, "source").replace("Marketplace:", "") || "System"
                        )}
                      </td>
                      <td className="py-2 pr-3 align-top text-xs whitespace-nowrap">
                        {dir ? (
                          <span
                            className={`px-2 py-0.5 rounded-full border text-[11px] font-semibold ${dir.toLowerCase() === "long"
                              ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/40"
                              : dir.toLowerCase() === "short"
                                ? "bg-rose-500/10 text-rose-300 border-rose-500/40"
                                : "bg-slate-800 text-slate-100 border-slate-700"
                              }`}
                          >
                            {dir.toUpperCase()}
                          </span>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td className="py-2 pr-3 align-top text-xs text-slate-300 whitespace-nowrap">
                        {tf || "-"}
                      </td>
                      <td className="py-2 pr-3 align-top text-xs text-slate-100 whitespace-nowrap">
                        {formatPrice(entry)}
                      </td>
                      <td className="py-2 pr-3 align-top text-xs text-emerald-300 whitespace-nowrap">
                        {formatPrice(tp)}
                      </td>
                      <td className="py-2 pr-3 align-top text-xs text-rose-300 whitespace-nowrap">
                        {formatPrice(sl)}
                      </td>

                      {mode === "LITE" && (
                        <td className="py-2 pr-3 align-top text-xs">
                          {evaluationError ? (
                            <span className="text-amber-400 text-[10px]">{evaluationError}</span>
                          ) : evaluationLoading ? (
                            <span className="text-slate-400">Checking...</span>
                          ) : (
                            evaluationBadge(evaluation)
                          )}
                        </td>
                      )}

                      <td className="py-2 pr-3 align-top text-xs text-slate-300 max-w-xs">
                        <div className="line-clamp-2">{note || "-"}</div>
                      </td>

                      {mode === "LITE" && (
                        <td className="py-2 pr-3 align-top text-xs text-right">
                          <button
                            type="button"
                            onClick={() => handleCheckEvaluation(index)}
                            disabled={evaluationLoading}
                            className="px-2 py-1 rounded-md border border-slate-600 bg-slate-800 text-[11px] text-slate-100 hover:bg-slate-700 disabled:opacity-60"
                          >
                            Check
                          </button>
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
