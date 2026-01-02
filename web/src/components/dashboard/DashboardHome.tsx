"use client"

import React, { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import {
    Activity,
    TrendingUp,
    BarChart2,
    Terminal,
    Zap,
    Target,
    ArrowUpRight,
    ArrowDownRight,
    Layers,
    Cpu,
    ChevronRight,
    TrendingDown,
} from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from "recharts"
import { api } from "../../services/api"
import { useAuth } from "../../context/AuthContext"
import { cn } from "../../lib/utils"
// Ensure this path matches your project structure
import { TacticalAnalysisDrawer } from "../scanner/TacticalAnalysisDrawer"

// --- Compact KPI Card ---
function KPICard({
    title,
    value,
    sub,
    icon,
    color,
    iconColor,
    loading,
    trend,
}: {
    title: string
    value: string | number
    sub: string
    icon: React.ReactNode
    color: string
    iconColor: string
    loading?: boolean
    trend?: "up" | "down"
}) {
    return (
        <div className="relative group h-full">
            <div
                className={`absolute -inset-0.5 bg-gradient-to-br ${color} rounded-2xl blur-xl opacity-0 group-hover:opacity-40 transition-all duration-700`}
            />

            <div className="relative glass-card rounded-2xl p-5 border border-white/5 bg-[#0f172a]/80 backdrop-blur-md shadow-xl overflow-hidden hover:border-white/10 transition-all duration-300 h-full flex flex-col justify-between">

                {/* Header */}
                <div className="flex justify-between items-start mb-2">
                    <h3 className="text-slate-500 text-[10px] font-black uppercase tracking-[0.2em]">{title}</h3>
                    <div className={`${iconColor} opacity-50 scale-75`}>
                        {icon}
                    </div>
                </div>

                {/* Main Value */}
                {loading ? (
                    <div className="h-8 w-24 bg-white/5 rounded animate-pulse my-1"></div>
                ) : (
                    <div className="flex items-center gap-2">
                        <div className="text-3xl font-black text-white tracking-tighter drop-shadow-sm">{value}</div>
                        {trend && (
                            <div className={cn("flex px-1.5 py-0.5 rounded text-[10px] font-bold", trend === "up" ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400")}>
                                {trend === "up" ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                            </div>
                        )}
                    </div>
                )}

                {/* Subtext */}
                <div className="text-[10px] text-slate-500 font-mono flex items-center gap-1.5 mt-2">
                    {/* Fixed Dot Logic */}
                    <span className={`w-1 h-1 rounded-full ${trend === 'up' ? 'bg-emerald-500' : 'bg-slate-600'}`}></span>
                    {sub}
                </div>
            </div>
        </div>
    )
}

export const DashboardHome: React.FC = () => {
    const { userProfile } = useAuth()
    const [showWelcome, setShowWelcome] = useState(false)
    const [loading, setLoading] = useState(true)
    const [currentTime, setCurrentTime] = useState(new Date())

    // Clock Timer
    useEffect(() => {
        const timer = setInterval(() => setCurrentTime(new Date()), 1000)
        return () => clearInterval(timer)
    }, [])

    // Stats State
    const [stats, setStats] = useState({ win_rate: 0, active_fleet: 0, pnl_7d: 0 })
    const [evaluatedCount, setEvaluatedCount] = useState(0)
    const [chartData, setChartData] = useState<any[]>([])
    const [recentSignals, setRecentSignals] = useState<any[]>([])
    const [selectedSignal, setSelectedSignal] = useState(null)

    // Check banner persistence
    useEffect(() => {
        const dismissed = localStorage.getItem('dashboard_welcome_dismissed')
        if (!dismissed) {
            setShowWelcome(true)
        }
    }, [])

    const dismissBanner = () => {
        setShowWelcome(false)
        localStorage.setItem('dashboard_welcome_dismissed', 'true')
    }

    useEffect(() => {
        // Parallel data fetching for speed
        const loadData = async () => {
            setLoading(true)
            try {
                const [statsData, countData, chartRes, signalsRes] = await Promise.all([
                    api.getStats(),
                    api.getEvaluatedCount(),
                    api.getChartData(),
                    api.getRecentSignals(5, false, false) // 5 items, savedOnly=false, includeSystem=false (Clean Feed)
                ])
                setStats(statsData)
                setEvaluatedCount(countData)
                setChartData(chartRes)
                setRecentSignals(signalsRes)
            } catch (e) {
                console.error("Dashboard data load failed", e)
            } finally {
                setLoading(false)
            }
        }
        loadData()
    }, [])

    return (
        <div className="min-h-screen bg-[#020617] text-white selection:bg-gold-500/30 font-sans relative pb-20">
            {/* Background Effects */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:64px_64px] opacity-30" />
                <div className="absolute top-[-10%] right-[10%] w-[500px] h-[500px] bg-brand-500/5 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] left-[-5%] w-[400px] h-[400px] bg-gold-500/5 blur-[100px] rounded-full" />
            </div>

            {/* Main Content Container */}
            <div className="relative z-10 max-w-7xl mx-auto px-6 py-8 lg:py-12 w-full space-y-8">

                {/* Welcome Banner */}
                {showWelcome && (
                    <div className="relative group animate-in slide-in-from-top-2 duration-500">
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-brand-500/20 to-brand-500/10 rounded-xl blur opacity-30"></div>
                        <div className="relative glass-card rounded-xl p-4 border border-white/10 bg-[#0f172a]/95 flex items-center justify-between gap-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-brand-500/10 rounded-lg text-brand-400">
                                    <Terminal size={18} />
                                </div>
                                <p className="text-sm text-slate-300">
                                    <span className="text-white font-bold">System Online.</span> AI engines are scanning.
                                </p>
                            </div>
                            <div className="flex items-center gap-3">
                                <Link to="/scanner" className="text-xs font-bold text-brand-400 hover:text-brand-300 uppercase tracking-wider">
                                    Initialize Scan
                                </Link>
                                <button onClick={dismissBanner} className="p-1 hover:bg-white/10 rounded text-slate-400 hover:text-white">
                                    <ArrowDownRight size={14} />
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Premium Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="pl-6 relative">
                        <div className="absolute left-0 top-2 bottom-2 w-1 bg-gradient-to-b from-gold-400 to-orange-500 rounded-full shadow-[0_0_15px_rgba(251,191,36,0.5)]"></div>
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-gold-500/20 text-xs font-bold text-gold-400 mb-4 shadow-[0_0_15px_rgba(251,191,36,0.15)]">
                            <Activity size={12} />
                            Command Center
                        </div>
                        <h1 className="text-4xl lg:text-5xl font-bold tracking-tight leading-tight mb-3">
                            Overview{" "}
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-400 via-orange-400 to-gold-500 drop-shadow-sm">
                                Dashboard
                            </span>
                        </h1>
                        <p className="text-slate-400 text-base font-light max-w-2xl flex items-center gap-2">
                            Real-time system metrics and anomaly detection stream.
                            <span className="w-1 h-1 rounded-full bg-slate-600"></span>
                            <span className="text-xs text-slate-500 font-mono tracking-wider">{currentTime.toLocaleTimeString('en-US', { hour12: false })}</span>
                        </p>
                    </div>
                </div>

                {/* KPI Grid */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 w-full">
                    <KPICard
                        title="WIN RATE"
                        value={loading ? "—" : `${stats.win_rate ?? 0}%`}
                        sub="Last 24h"
                        trend={(stats.win_rate ?? 0) >= 60 ? "up" : "down"}
                        icon={<Target size={20} />}
                        color="from-emerald-500/20 to-emerald-900/10"
                        iconColor="text-emerald-400"
                        loading={loading}
                    />
                    <KPICard
                        title="ACTIVE"
                        value={loading ? "—" : (stats.active_fleet ?? 0)}
                        sub="Open Signals"
                        icon={<Layers size={20} />}
                        color="from-brand-500/20 to-brand-900/10"
                        iconColor="text-brand-400"
                        loading={loading}
                    />
                    <KPICard
                        title="EVALUATED"
                        value={loading ? "—" : evaluatedCount}
                        sub="Past 24h"
                        icon={<Cpu size={20} />}
                        color="from-indigo-500/20 to-slate-900/10"
                        iconColor="text-indigo-400"
                        loading={loading}
                    />
                    <KPICard
                        title="NET PNL"
                        value={loading ? "—" : `${(stats.pnl_7d ?? 0) > 0 ? '+' : ''}${stats.pnl_7d ?? 0}R`}
                        sub="7-Day Return"
                        trend={(stats.pnl_7d ?? 0) >= 0 ? "up" : "down"}
                        icon={<TrendingUp size={20} />}
                        color={(stats.pnl_7d ?? 0) >= 0 ? "from-gold-500/20 to-orange-900/10" : "from-rose-500/20 to-rose-900/10"}
                        iconColor={(stats.pnl_7d ?? 0) >= 0 ? "text-gold-400" : "text-rose-400"}
                        loading={loading}
                    />
                </div>

                {/* 2. Charts & Activity (Fills remaining height) */}
                <div className="w-full grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Chart */}
                    <div className="lg:col-span-2 glass-card rounded-2xl p-5 border border-white/5 bg-[#0f172a]/70 flex flex-col relative group overflow-hidden h-[400px]">
                        <div className="flex justify-between items-center mb-4 shrink-0">
                            <div>
                                <h3 className="text-base font-bold text-white flex items-center gap-2">
                                    <BarChart2 size={16} className="text-brand-400" />
                                    Performance Analytics
                                </h3>
                            </div>
                            <div className="flex gap-3">
                                <span className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                                    <div className="w-1.5 h-1.5 rounded bg-emerald-500"></div> Wins
                                </span>
                                <span className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                                    <div className="w-1.5 h-1.5 rounded bg-rose-500"></div> Losses
                                </span>
                            </div>
                        </div>

                        <div className="flex-1 w-full min-h-0">
                            {loading ? (
                                <div className="w-full h-full flex items-center justify-center">
                                    <div className="animate-spin text-brand-500"><Cpu size={24} /></div>
                                </div>
                            ) : (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                                        <XAxis
                                            dataKey="date"
                                            stroke="#64748b"
                                            fontSize={10}
                                            tickLine={false}
                                            axisLine={false}
                                            dy={5}
                                        />
                                        <YAxis
                                            stroke="#64748b"
                                            fontSize={10}
                                            tickLine={false}
                                            axisLine={false}
                                        />
                                        <Tooltip
                                            cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                                            contentStyle={{
                                                backgroundColor: '#0f172a',
                                                borderColor: 'rgba(255,255,255,0.1)',
                                                borderRadius: '8px',
                                                fontSize: '11px',
                                            }}
                                            itemStyle={{ fontSize: '11px' }}
                                            labelStyle={{ color: '#94a3b8', marginBottom: '2px', fontSize: '11px' }}
                                        />
                                        <Bar dataKey="wins" name="Wins" stackId="a" maxBarSize={32} radius={[0, 0, 4, 4]}>
                                            {chartData.map((entry, index) => (
                                                <Cell key={`cell-win-${index}`} fill="#10b981" fillOpacity={0.8} />
                                            ))}
                                        </Bar>
                                        <Bar dataKey="losses" name="Losses" stackId="a" maxBarSize={32} radius={[4, 4, 0, 0]}>
                                            {chartData.map((entry, index) => (
                                                <Cell key={`cell-loss-${index}`} fill="#f43f5e" fillOpacity={0.8} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            )}
                        </div>
                    </div>

                    {/* Recent Activity List */}
                    <div className="glass-card rounded-2xl border border-white/5 bg-[#0f172a]/70 flex flex-col overflow-hidden relative">
                        <div className="absolute top-0 w-full h-10 bg-gradient-to-b from-[#0f172a] to-transparent z-10 pointer-events-none opacity-50" />

                        <div className="p-4 border-b border-white/5 flex justify-between items-center bg-white/[0.02] shrink-0">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <Activity size={16} className="text-slate-400" />
                                Recent Signals
                            </h3>
                            <Link to="/history" className="text-[10px] font-bold text-brand-400 hover:text-brand-300 uppercase tracking-wider flex items-center gap-1">
                                All <ChevronRight size={12} />
                            </Link>
                        </div>

                        <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
                            {loading ? (
                                Array(5).fill(0).map((_, i) => (
                                    <div key={i} className="h-12 bg-white/5 rounded-lg animate-pulse mx-2 my-1"></div>
                                ))
                            ) : recentSignals.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center text-slate-500">
                                    <span className="text-xs">No signals</span>
                                </div>
                            ) : (
                                recentSignals.slice(0, 10).map((sig, idx) => {
                                    return (
                                        <div
                                            key={idx}
                                            onClick={() => setSelectedSignal(sig)}
                                            className="flex items-center justify-between p-2.5 rounded-lg hover:bg-white/5 transition-colors cursor-pointer border border-transparent hover:border-white/5 group"
                                        >
                                            {(() => {
                                                // Robust status check: Check result (logs/recent usually), status (evaluations), and fallback
                                                const rawStatus = String(sig.result || sig.status || 'PENDING').toUpperCase();
                                                const isWin = rawStatus.includes('WIN') || rawStatus.includes('TP') || (sig.pnl_r && sig.pnl_r > 0);
                                                const isLoss = rawStatus.includes('LOSS') || rawStatus.includes('SL') || (sig.pnl_r && sig.pnl_r < 0);
                                                // If it says pending/open but has a pnl Result, trust the pnl/result.

                                                // Display text logic
                                                let displayStatus = rawStatus;
                                                if (isWin) displayStatus = sig.pnl_r ? `+${sig.pnl_r}R` : 'WIN';
                                                else if (isLoss) displayStatus = sig.pnl_r ? `${sig.pnl_r}R` : 'LOSS';
                                                else if (displayStatus === 'OPEN') displayStatus = 'RUNNING';

                                                const isLong = sig.direction?.toLowerCase() === 'long';

                                                return (
                                                    <>
                                                        <div className="flex items-center gap-3">
                                                            {/* Token Box */}
                                                            <div className={cn(
                                                                "w-7 h-7 rounded flex items-center justify-center border text-[9px] font-black",
                                                                isLong ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-400" : "border-rose-500/20 bg-rose-500/5 text-rose-400"
                                                            )}>
                                                                {sig.token?.substring(0, 3)}
                                                            </div>
                                                            <div className="flex flex-col">
                                                                <div className="text-[11px] font-bold text-slate-200 leading-tight">
                                                                    {sig.token}
                                                                </div>
                                                                <div className="text-[9px] text-slate-500 font-mono">
                                                                    {(() => {
                                                                        let ts = sig.timestamp || sig.evaluated_at;
                                                                        if (!ts) return "--:--";
                                                                        // Force UTC if naive string (common in SQL responses)
                                                                        if (typeof ts === 'string' && !ts.endsWith('Z') && !ts.includes('+')) {
                                                                            ts = ts.replace(' ', 'T') + 'Z';
                                                                        }
                                                                        return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                                                                    })()}
                                                                </div>
                                                            </div>
                                                        </div>

                                                        <div className={cn(
                                                            "text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider min-w-[50px] text-center",
                                                            isWin && "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                                                            isLoss && "bg-rose-500/10 text-rose-400 border-rose-500/20",
                                                            !isWin && !isLoss && "bg-slate-500/10 text-slate-400 border-slate-500/20"
                                                        )}>
                                                            {displayStatus}
                                                        </div>
                                                    </>
                                                );
                                            })()}
                                        </div>
                                    )
                                })
                            )}
                        </div>
                    </div>
                </div>

            </div>

            {/* Tactical Analysis Drawer Container */}
            {selectedSignal && (
                <TacticalAnalysisDrawer
                    isOpen={!!selectedSignal}
                    onClose={() => setSelectedSignal(null)}
                    signal={selectedSignal}
                />
            )}
        </div>
    )
}
