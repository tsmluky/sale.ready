"use client"

import React, { useEffect, useState } from "react"
import { api } from "../../services/api"
import { ArrowLeft, ChevronLeft, ChevronRight, Filter, Search, Terminal } from "lucide-react"
import { Link } from "react-router-dom"
import { cn } from "../../lib/utils"

export const DashboardHistory: React.FC = () => {
    const [signals, setSignals] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [page, setPage] = useState(1)
    const [hasMore, setHasMore] = useState(true)
    const [filter, setFilter] = useState("ALL") // ALL, WIN, LOSS, PENDING

    const ITEMS_PER_PAGE = 50

    useEffect(() => {
        loadHistory()
    }, [page, filter])

    const loadHistory = async () => {
        setLoading(true)
        try {
            // Using existing endpoint mechanics, but likely need a specialized /history endpoint
            // For now reusing getRecentSignals with high limit or filtering
            // ideally: api.getHistory(page, limit, filter)
            // As a stopgap, we fetch 'recent' with a higher limit and filter client side or 
            // relying on existing paginated endpoints if available.

            // NOTE: Ideally we should add a dedicated paginated history endpoint in backend.
            // Using getRecentSignals as proxy for now.
            const res = await api.getRecentSignals(ITEMS_PER_PAGE, false, true) // Include system for history? Maybe.

            // Client side filtering for Phase 1 MVP if backend doesn't support specific filter params
            let filtered = res;
            if (filter !== "ALL") {
                filtered = res.filter(s => {
                    const status = (s.status || s.result || "PENDING").toUpperCase();
                    if (filter === "PENDING") return status === "OPEN" || status === "PENDING";
                    return status.includes(filter);
                });
            }

            setSignals(filtered)
            setHasMore(res.length >= ITEMS_PER_PAGE) // Rough check
        } catch (e) {
            console.error("History load failed", e)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-[#020617] text-white p-6 pb-20 font-sans">
            {/* Header */}
            <div className="max-w-7xl mx-auto flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                    <Link to="/" className="p-2 hover:bg-white/5 rounded-full text-slate-400 hover:text-white transition-colors">
                        <ArrowLeft size={20} />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            <Terminal className="text-brand-400" size={24} />
                            Signal History
                        </h1>
                        <p className="text-slate-500 text-sm">Full archive of all trading signals</p>
                    </div>
                </div>

                {/* Filters */}
                <div className="flex gap-2 bg-[#0f172a] p-1 rounded-lg border border-white/5">
                    {["ALL", "WIN", "LOSS", "PENDING"].map(f => (
                        <button
                            key={f}
                            onClick={() => { setFilter(f); setPage(1); }}
                            className={cn(
                                "px-3 py-1.5 rounded text-xs font-bold transition-all",
                                filter === f
                                    ? "bg-brand-500/10 text-brand-400 shadow-[0_0_10px_rgba(56,189,248,0.1)]"
                                    : "text-slate-500 hover:text-slate-300"
                            )}
                        >
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto">
                <div className="glass-card rounded-xl border border-white/5 bg-[#0f172a]/50 overflow-hidden">
                    {/* Table Header */}
                    <div className="grid grid-cols-12 gap-4 p-4 border-b border-white/5 text-[10px] font-bold text-slate-500 uppercase tracking-wider bg-[#0f172a]/80">
                        <div className="col-span-2">Time</div>
                        <div className="col-span-2">Token</div>
                        <div className="col-span-1">Side</div>
                        <div className="col-span-2 text-right">Entry</div>
                        <div className="col-span-3 text-right">Exit / Status</div>
                        <div className="col-span-2 text-right">PnL</div>
                    </div>

                    {loading ? (
                        <div className="p-8 text-center text-slate-500 flex flex-col items-center gap-2">
                            <div className="animate-spin text-brand-500"><Terminal size={24} /></div>
                            Loading history...
                        </div>
                    ) : signals.length === 0 ? (
                        <div className="p-12 text-center text-slate-500">
                            No signals found matching criteria.
                        </div>
                    ) : (
                        signals.map((sig, idx) => {
                            const rawStatus = String(sig.result || sig.status || 'PENDING').toUpperCase();
                            const isWin = rawStatus.includes('WIN') || rawStatus.includes('TP') || (sig.pnl_r && sig.pnl_r > 0);
                            const isLoss = rawStatus.includes('LOSS') || rawStatus.includes('SL') || (sig.pnl_r && sig.pnl_r < 0);

                            let displayStatus = rawStatus;
                            if (isWin) displayStatus = "WIN";
                            else if (isLoss) displayStatus = "LOSS";
                            else if (displayStatus === 'OPEN') displayStatus = 'RUNNING';

                            const isLong = sig.direction?.toLowerCase() === 'long';
                            const pnlVal = sig.pnl_r || sig.pnl; // adapt to schema

                            return (
                                <div key={idx} className="grid grid-cols-12 gap-4 p-4 border-b border-white/5 items-center hover:bg-white/[0.02] transition-colors text-sm">
                                    <div className="col-span-2 font-mono text-slate-400 text-xs">
                                        {new Date(sig.timestamp || sig.created_at).toLocaleString()}
                                    </div>
                                    <div className="col-span-2 font-bold flex items-center gap-2">
                                        <div className={cn(
                                            "w-6 h-6 rounded flex items-center justify-center border text-[9px] font-black",
                                            isLong ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-400" : "border-rose-500/20 bg-rose-500/5 text-rose-400"
                                        )}>
                                            {sig.token?.substring(0, 3)}
                                        </div>
                                        {sig.token}
                                    </div>
                                    <div className="col-span-1">
                                        <span className={cn(
                                            "text-[10px] px-1.5 py-0.5 rounded font-bold uppercase",
                                            isLong ? "text-emerald-400 bg-emerald-500/10" : "text-rose-400 bg-rose-500/10"
                                        )}>
                                            {sig.direction}
                                        </span>
                                    </div>
                                    <div className="col-span-2 text-right font-mono text-slate-300">
                                        {sig.entry}
                                    </div>
                                    <div className="col-span-3 text-right">
                                        <span className={cn(
                                            "text-[10px] px-2 py-1 rounded font-bold uppercase border",
                                            isWin && "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
                                            isLoss && "text-rose-400 bg-rose-500/10 border-rose-500/20",
                                            !isWin && !isLoss && "text-slate-400 bg-slate-500/10 border-slate-500/20"
                                        )}>
                                            {displayStatus}
                                        </span>
                                    </div>
                                    <div className="col-span-2 text-right font-mono font-bold">
                                        {pnlVal ? (
                                            <span className={pnlVal > 0 ? "text-emerald-400" : "text-rose-400"}>
                                                {pnlVal > 0 ? "+" : ""}{pnlVal}R
                                            </span>
                                        ) : <span className="text-slate-600">-</span>}
                                    </div>
                                </div>
                            )
                        })
                    )}
                </div>

                {/* Pagination Controls */}
                <div className="flex justify-between items-center mt-6">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1 || loading}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0f172a] border border-white/5 hover:bg-white/5 disabled:opacity-50 transition-colors text-sm"
                    >
                        <ChevronLeft size={16} /> Previous
                    </button>
                    <span className="text-slate-500 text-sm font-mono">Page {page}</span>
                    <button
                        onClick={() => setPage(p => p + 1)}
                        disabled={!hasMore || loading}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0f172a] border border-white/5 hover:bg-white/5 disabled:opacity-50 transition-colors text-sm"
                    >
                        Next <ChevronRight size={16} />
                    </button>
                </div>
            </div>
        </div>
    )
}
