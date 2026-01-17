"use client"

import type React from "react"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "../services/api"
import { useAuth } from "../context/AuthContext"
import { RefreshCw, Zap, Radar, TrendingUp, TrendingDown, Clock, ChevronRight } from "lucide-react"
import toast from "react-hot-toast"
import { TacticalAnalysisDrawer } from "../components/scanner/TacticalAnalysisDrawer"
import { cn } from "../lib/utils"

export const ScannerPage: React.FC = () => {
    const navigate = useNavigate()
    const [signals, setSignals] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [isDrawerOpen, setIsDrawerOpen] = useState(false)
    const [selectedSignal, setSelectedSignal] = useState<any>(null)
    const { userProfile } = useAuth()

    const fetchSignals = async () => {
        try {
            const rawSignals = await api.get("/logs/recent?limit=200")

            const uniqueMap = new Map()
            const now = Date.now()

            const filtered = rawSignals.filter((s: any) => {
                const age = now - new Date(s.timestamp || s.evaluated_at).getTime()
                if (age > 24 * 60 * 60 * 1000) return false
                return true
            })

            filtered.forEach((sig: any) => {
                const key = `${sig.token}-${sig.timeframe}`
                if (!uniqueMap.has(key)) uniqueMap.set(key, sig)
            })

            setSignals(Array.from(uniqueMap.values()))
        } catch (error) {
            console.error("Error fetching signals", error)
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }

    useEffect(() => {
        fetchSignals()
        const interval = setInterval(fetchSignals, 15000)
        return () => clearInterval(interval)
    }, [])

    const handleRefresh = async () => {
        setRefreshing(true)
        const toastId = toast.loading("Scanning markets...")
        setTimeout(() => {
            fetchSignals()
            toast.success("Scan complete", { id: toastId })
        }, 1500)
    }

    const handleAnalyze = (signal: any) => {
        setSelectedSignal(signal)
        setIsDrawerOpen(true)
    }

    return (
        <div className="min-h-screen bg-[#020617] text-white selection:bg-brand-500/30 overflow-x-hidden font-sans relative pb-20">
            {/* Background Effects */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:64px_64px] opacity-30" />
                <div className="absolute top-[-10%] left-[-10%] w-[700px] h-[700px] bg-brand-500/8 rounded-full blur-[150px] mix-blend-screen"></div>
                <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-indigo-600/5 blur-[120px] rounded-full mix-blend-screen"></div>
            </div>

            {/* Content */}
            <div className="relative z-10 max-w-7xl mx-auto px-6 py-8 lg:py-12">
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-10">
                    <div className="relative">
                        <div className="absolute left-0 top-2 bottom-2 w-1 bg-gradient-to-b from-gold-400 to-orange-500 rounded-full shadow-[0_0_15px_rgba(251,191,36,0.5)]"></div>
                        <div className="pl-6">
                            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-gold-500/20 text-xs font-bold text-gold-400 mb-4 shadow-[0_0_15px_rgba(251,191,36,0.15)]">
                                <div className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gold-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-gold-500"></span>
                                </div>
                                System Live
                            </div>
                            <h1 className="text-4xl lg:text-5xl font-bold tracking-tight leading-tight mb-3">
                                Market{" "}
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-400 via-orange-400 to-gold-500 drop-shadow-sm">
                                    Radar
                                </span>
                            </h1>
                            <p className="text-slate-400 text-base font-light flex items-center gap-2">
                                Real-time anomaly detection stream
                                <span className="w-1 h-1 rounded-full bg-slate-600"></span>
                                <span className="text-xs text-slate-500 font-mono">Live Feed</span>
                            </p>
                        </div>
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={handleRefresh}
                            disabled={refreshing}
                            className={cn(
                                "p-3.5 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 hover:border-brand-500/30 transition-all active:scale-95 shadow-lg group disabled:opacity-50 disabled:cursor-not-allowed",
                            )}
                        >
                            <RefreshCw
                                size={20}
                                className={cn(
                                    "group-hover:text-brand-400 transition-colors",
                                    refreshing && "animate-spin text-brand-400",
                                )}
                            />
                        </button>
                        <button
                            onClick={() => navigate("/analysis")}
                            className="group/btn relative px-6 py-3.5 bg-gradient-to-r from-gold-500 to-orange-600 hover:from-gold-400 hover:to-orange-500 text-white rounded-xl font-bold text-sm shadow-lg shadow-gold-500/20 hover:shadow-gold-500/40 transition-all flex items-center gap-2 active:scale-95 overflow-hidden"
                        >
                            <div className="absolute inset-0 -translate-x-full group-hover/btn:animate-shine bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                            <Zap size={18} className="fill-white/20 relative" />
                            <span className="relative">Smart Analysis</span>
                        </button>
                    </div>
                </div>

                {/* Signals Grid */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                            <div key={i} className="h-64 bg-white/5 rounded-2xl animate-pulse"></div>
                        ))}
                    </div>
                ) : signals.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-in slide-in-from-bottom-5 duration-700">
                        {signals.map((signal, idx) => {
                            const isLong = signal.direction?.toLowerCase() === "long"
                            const isPending =
                                String(signal.result || "")
                                    .toUpperCase()
                                    .includes("OPEN") ||
                                String(signal.result || "")
                                    .toUpperCase()
                                    .includes("PENDING")
                            const isWin =
                                String(signal.result || "")
                                    .toUpperCase()
                                    .includes("WIN") ||
                                String(signal.result || "")
                                    .toUpperCase()
                                    .includes("TP")
                            const isLoss =
                                String(signal.result || "")
                                    .toUpperCase()
                                    .includes("LOSS") ||
                                String(signal.result || "")
                                    .toUpperCase()
                                    .includes("SL")

                            return (
                                <div key={idx} onClick={() => handleAnalyze(signal)} className="group relative cursor-pointer">
                                    <div
                                        className={cn(
                                            "absolute -inset-0.5 rounded-2xl blur-xl opacity-0 group-hover:opacity-60 transition-opacity duration-700",
                                            isLong
                                                ? "bg-gradient-to-br from-emerald-500/30 to-emerald-600/20"
                                                : "bg-gradient-to-br from-rose-500/30 to-rose-600/20",
                                        )}
                                    />

                                    <div className="relative glass-card rounded-2xl p-6 border border-white/10 bg-[#0f172a]/70 backdrop-blur-xl shadow-2xl overflow-hidden hover:border-white/20 transition-all duration-300">
                                        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                                        {/* Header */}
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center gap-3">
                                                <div
                                                    className={cn(
                                                        "p-2 rounded-xl border",
                                                        isLong ? "bg-emerald-500/10 border-emerald-500/20" : "bg-rose-500/10 border-rose-500/20",
                                                    )}
                                                >
                                                    {isLong ? (
                                                        <TrendingUp className="text-emerald-400" size={20} />
                                                    ) : (
                                                        <TrendingDown className="text-rose-400" size={20} />
                                                    )}
                                                </div>
                                                <div>
                                                    <h3 className="text-lg font-bold text-white">{signal.token?.toUpperCase()}</h3>
                                                    <p className="text-xs text-slate-500 font-mono">{signal.timeframe || "4h"}</p>
                                                </div>
                                            </div>
                                            <span
                                                className={cn(
                                                    "px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider border",
                                                    isLong
                                                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                                        : "bg-rose-500/10 text-rose-400 border-rose-500/20",
                                                )}
                                            >
                                                {signal.direction || "LONG"}
                                            </span>
                                        </div>

                                        {/* Metrics */}
                                        {/* Metrics */}
                                        <div className="space-y-3 mb-4">
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="text-slate-400 shrink-0">Entry</span>
                                                <span className="text-white font-mono font-bold truncate ml-4" title={`$${signal.entry?.toFixed(2)}`}>${signal.entry?.toFixed(2) || "—"}</span>
                                            </div>
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="text-slate-400 shrink-0">Target</span>
                                                <span className="text-emerald-400 font-mono font-bold truncate ml-4" title={`$${signal.tp?.toFixed(2)}`}>${signal.tp?.toFixed(2) || "—"}</span>
                                            </div>
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="text-slate-400 shrink-0">Stop Loss</span>
                                                <span className="text-rose-400 font-mono font-bold truncate ml-4" title={`$${signal.sl?.toFixed(2)}`}>${signal.sl?.toFixed(2) || "—"}</span>
                                            </div>
                                        </div>

                                        {/* Footer */}
                                        <div className="flex items-center justify-between pt-4 border-t border-white/5">
                                            <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                                                <Clock size={12} />
                                                <span>{new Date(signal.timestamp || signal.evaluated_at).toLocaleTimeString()}</span>
                                            </div>
                                            <div
                                                className={cn(
                                                    "px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border",
                                                    isPending && "bg-slate-500/10 text-slate-400 border-slate-500/20",
                                                    isWin && "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                                                    isLoss && "bg-rose-500/10 text-rose-400 border-rose-500/20",
                                                )}
                                            >
                                                {signal.result || "PENDING"}
                                            </div>
                                        </div>

                                        {/* View Details Arrow - Removed per user request */}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                ) : (
                    <div className="text-center py-20">
                        <div className="inline-flex p-6 rounded-2xl bg-white/5 border border-white/10 mb-6">
                            <Radar className="text-slate-500" size={48} />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">No Active Signals</h3>
                        <p className="text-slate-400 text-sm max-w-md mx-auto mb-6">
                            No signals detected in the last 24 hours. Run a manual analysis or wait for the system to detect new
                            opportunities.
                        </p>
                        <button
                            onClick={() => navigate("/analysis")}
                            className="px-6 py-3 bg-gradient-to-r from-gold-500 to-orange-600 hover:from-gold-400 hover:to-orange-500 text-white font-bold rounded-xl shadow-lg shadow-gold-500/30 transition-all flex items-center gap-2 mx-auto"
                        >
                            <Zap size={18} />
                            Run Analysis
                        </button>
                    </div>
                )}
            </div>

            {/* Tactical Analysis Drawer */}
            <TacticalAnalysisDrawer isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} signal={selectedSignal} />
        </div>
    )
}
