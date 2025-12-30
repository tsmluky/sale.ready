import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Activity,
    TrendingUp,
    BarChart2,
    Terminal,
    Zap,
    Bot,
    ShieldCheck,
    Sparkles,
    Target,
    Clock,
    ArrowUpRight,
    ArrowDownRight,
    Layers,
    Cpu,
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { cn } from '../../lib/utils'; // Assuming this exists now

// KPI Card Component (Internal for now, matching redesign)
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
        <div className="relative group">
            <div
                className={`absolute -inset-0.5 bg-gradient-to-br ${color} rounded-xl blur-lg opacity-0 group-hover:opacity-40 transition-opacity duration-700`}
            ></div>

            <div className="relative glass-card rounded-xl p-5 lg:p-6 border border-white/10 bg-[#0f172a]/60 backdrop-blur-xl shadow-xl overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                <div
                    className={`absolute top-3 right-3 ${iconColor} opacity-10 group-hover:opacity-20 transition-opacity duration-500`}
                >
                    {icon}
                </div>

                <h3 className="text-slate-500 text-[10px] font-black uppercase tracking-widest mb-2">{title}</h3>

                {loading ? (
                    <div className="h-9 w-24 bg-white/5 rounded animate-pulse"></div>
                ) : (
                    <div className="flex items-baseline gap-2">
                        <div className="text-3xl lg:text-4xl font-black text-white tracking-tight drop-shadow-sm">{value}</div>
                        {trend && (
                            <div className={`${trend === "up" ? "text-emerald-400" : "text-rose-400"}`}>
                                {trend === "up" ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                            </div>
                        )}
                    </div>
                )}

                <div className="text-[10px] text-slate-500 mt-2 font-mono uppercase tracking-wider">{sub}</div>
            </div>
        </div>
    )
}

import { TacticalAnalysisDrawer } from '../scanner/TacticalAnalysisDrawer';

// ... (KPICard definition remains same)

export const DashboardHome: React.FC = () => {
    const { userProfile } = useAuth();

    // State
    const [stats, setStats] = useState<any>({
        win_rate: 0,
        win_rate_change: 0,
        pnl_7d: 0,
        pnl_7d_change: 0,
        active_fleet: 0
    });
    const [recentSignals, setRecentSignals] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [evaluatedCount, setEvaluatedCount] = useState(0);
    const [chartData, setChartData] = useState<any[]>([]);

    // Selection state for Drawer
    const [selectedSignal, setSelectedSignal] = useState<any>(null);

    // Fetch Data
    const fetchData = async () => {
        try {
            const [statsData, logsData, strategiesData] = await Promise.all([
                api.get('/stats/summary'),
                api.get('/logs/recent?limit=20'),
                api.get('/strategies/marketplace')
            ]);

            setStats({
                ...statsData,
                active_fleet: strategiesData.filter((s: any) => s.is_active).length
            });
            setRecentSignals(logsData);
            setEvaluatedCount(logsData.length);

            // Mock chart data
            const mockChartData = [
                { date: "20/12", wins: 5, losses: 2 },
                { date: "21/12", wins: 7, losses: 1 },
                { date: "22/12", wins: 4, losses: 3 },
                { date: "23/12", wins: 8, losses: 2 },
                { date: "24/12", wins: 6, losses: 1 },
                { date: "25/12", wins: 9, losses: 3 },
                { date: "26/12", wins: 7, losses: 2 },
            ];
            setChartData(mockChartData);

        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const [isBannerDismissed, setIsBannerDismissed] = useState(() => {
        return localStorage.getItem('welcome_banner_dismissed') === 'true';
    });

    const dismissBanner = () => {
        setIsBannerDismissed(true);
        localStorage.setItem('welcome_banner_dismissed', 'true');
    };

    const showWelcome = !userProfile?.user?.onboarding_completed && !isBannerDismissed;

    return (
        <div className="min-h-screen bg-[#020617] text-white selection:bg-gold-500/30 overflow-x-hidden font-sans relative">
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] opacity-20" />
                <div className="absolute top-[-10%] right-[10%] w-[600px] h-[600px] bg-brand-500/10 rounded-full blur-[140px] mix-blend-screen opacity-30"></div>
                <div className="absolute bottom-[-15%] left-[-5%] w-[500px] h-[500px] bg-gold-500/10 blur-[120px] rounded-full mix-blend-screen opacity-40"></div>
                <div className="absolute top-[40%] left-[50%] w-[400px] h-[400px] bg-emerald-500/5 blur-[100px] rounded-full mix-blend-screen opacity-20"></div>
            </div>

            {/* Main Content */}
            <div className="relative z-10 max-w-7xl mx-auto px-6 py-8 lg:py-12">
                {/* Welcome Banner */}
                {showWelcome && (
                    <div className="mb-8 relative group animate-in slide-in-from-top-5 duration-700">
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-brand-500/30 to-gold-500/30 rounded-2xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity duration-1000"></div>

                        <div className="relative glass-card rounded-2xl p-6 lg:p-8 border border-white/10 bg-[#0f172a]/80 overflow-hidden shadow-2xl">
                            <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-brand-500/10 to-transparent pointer-events-none" />

                            {/* Close Button */}
                            <button
                                onClick={dismissBanner}
                                className="absolute top-4 right-4 p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors z-20"
                            >
                                <ArrowDownRight className="rotate-45" size={20} />
                            </button>

                            <div className="relative z-10">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="bg-brand-500 text-white p-2.5 rounded-xl shadow-[0_0_20px_rgba(99,102,241,0.4)]">
                                        <Zap size={20} fill="currentColor" />
                                    </div>
                                    <h2 className="text-xl lg:text-2xl font-bold text-white tracking-tight">Welcome, Commander.</h2>
                                </div>
                                <p className="text-slate-300 max-w-2xl mb-6 leading-relaxed font-light">
                                    Your terminal is ready. The AI is online and scanning the markets. Initialize your first scan to start
                                    building your portfolio.
                                </p>
                                <div className="flex flex-wrap gap-3">
                                    <Link
                                        to="/analysis"
                                        className="bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-400 hover:to-brand-500 text-white font-bold px-6 py-3 rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-brand-500/25 active:scale-95"
                                    >
                                        <Terminal size={18} /> Initialize Terminal
                                    </Link>
                                    <Link
                                        to="/settings"
                                        className="glass border border-white/10 text-slate-300 font-bold px-6 py-3 rounded-xl transition-all flex items-center gap-2 active:scale-95 hover:border-white/20 hover:bg-white/5"
                                    >
                                        <Sparkles size={18} /> Configure Alerts
                                    </Link>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                <div className="mb-8 animate-in slide-in-from-bottom-3 duration-500">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass border border-gold-500/20 text-xs font-medium text-gold-400 mb-3 shadow-[0_0_10px_rgba(251,191,36,0.1)]">
                        <Activity className="w-3 h-3" />
                        Live Dashboard
                    </div>
                    <h1 className="text-3xl lg:text-4xl font-bold tracking-tight leading-tight">
                        Performance{" "}
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-400 to-orange-500 drop-shadow-sm">
                            Command Center
                        </span>
                    </h1>
                    <p className="text-slate-400 mt-2 text-sm font-light">Real-time analytics and signal intelligence</p>
                </div>

                {/* KPI Grid */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8 animate-in slide-in-from-bottom-5 duration-700">
                    <KPICard
                        title="Win Rate"
                        value={loading ? "—" : `${stats.win_rate ?? 0}%`}
                        sub="Last 24h"
                        trend={(stats.win_rate ?? 0) >= 70 ? "up" : "down"}
                        icon={<Target size={32} />}
                        color="from-emerald-500/20 to-emerald-600/10"
                        iconColor="text-emerald-400"
                        loading={loading}
                    />

                    <KPICard
                        title="Active Signals"
                        value={loading ? "—" : (stats.active_fleet ?? 0)} // Using active_fleet as active signals count proxy
                        sub="Open Positions"
                        icon={<Layers size={32} />}
                        color="from-brand-500/20 to-brand-600/10"
                        iconColor="text-brand-400"
                        loading={loading}
                    />

                    <KPICard
                        title="Evaluated"
                        value={loading ? "—" : evaluatedCount} // Using total signals fetched
                        sub="Last 7 Days"
                        icon={<Cpu size={32} />}
                        color="from-slate-500/20 to-slate-600/10"
                        iconColor="text-slate-400"
                        loading={loading}
                    />

                    <KPICard
                        title="Est. PnL"
                        value={loading ? "—" : `${(stats.pnl_7d ?? 0) > 0 ? "+" : ""}${(stats.pnl_7d ?? 0)}R`}
                        sub="7-Day Return"
                        trend={(stats.pnl_7d ?? 0) >= 0 ? "up" : "down"}
                        icon={<TrendingUp size={32} />}
                        color={(stats.pnl_7d ?? 0) >= 0 ? "from-gold-500/20 to-orange-600/10" : "from-rose-500/20 to-rose-600/10"}
                        iconColor={(stats.pnl_7d ?? 0) >= 0 ? "text-gold-400" : "text-rose-400"}
                        loading={loading}
                    />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 animate-in slide-in-from-bottom-7 duration-900">
                    {/* Chart Section */}
                    <div className="lg:col-span-2 relative group">
                        <div className="absolute -inset-0.5 bg-gradient-to-br from-brand-500/20 to-gold-500/10 rounded-2xl blur-xl opacity-0 group-hover:opacity-50 transition-opacity duration-1000"></div>

                        <div className="relative glass-card rounded-2xl p-6 border border-white/10 bg-[#0f172a]/60 backdrop-blur-xl shadow-2xl">
                            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-30" />

                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                        <BarChart2 className="text-gold-400" size={20} />
                                        Signal Performance
                                    </h3>
                                    <p className="text-xs text-slate-500 mt-1 font-mono uppercase tracking-wider">Last 7 Days Analysis</p>
                                </div>

                                <div className="flex gap-4 text-xs font-bold uppercase tracking-wider">
                                    <div className="flex items-center gap-1.5">
                                        <div className="w-3 h-3 rounded bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]"></div>
                                        <span className="text-slate-400">Wins</span>
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        <div className="w-3 h-3 rounded bg-rose-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]"></div>
                                        <span className="text-slate-400">Losses</span>
                                    </div>
                                </div>
                            </div>

                            <div className="h-64 lg:h-80 w-full">
                                {loading ? (
                                    <div className="w-full h-full flex items-center justify-center bg-[#020617]/50 rounded-xl border border-white/5 animate-pulse">
                                        <div className="text-center">
                                            <Cpu className="w-8 h-8 text-slate-600 mx-auto mb-2 animate-spin" />
                                            <span className="text-slate-600 font-mono text-xs uppercase tracking-wider">Loading data...</span>
                                        </div>
                                    </div>
                                ) : chartData.length > 0 ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={chartData}>
                                            <XAxis
                                                dataKey="date"
                                                stroke="#64748b"
                                                fontSize={11}
                                                tickLine={false}
                                                axisLine={false}
                                                fontFamily="monospace"
                                            />
                                            <YAxis
                                                stroke="#64748b"
                                                fontSize={11}
                                                tickLine={false}
                                                axisLine={false}
                                                allowDecimals={false}
                                                fontFamily="monospace"
                                            />
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: "#0f172a",
                                                    borderColor: "#334155",
                                                    color: "#f8fafc",
                                                    borderRadius: "12px",
                                                    border: "1px solid rgba(255,255,255,0.1)",
                                                    fontFamily: "monospace",
                                                    fontSize: "12px",
                                                }}
                                                cursor={{ fill: "#1e293b", opacity: 0.3 }}
                                            />
                                            <Bar dataKey="wins" name="Wins" stackId="a" fill="#10b981" radius={[4, 4, 0, 0]} />
                                            <Bar dataKey="losses" name="Losses" stackId="a" fill="#ef4444" radius={[0, 0, 4, 4]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-slate-500 border border-dashed border-white/10 rounded-xl bg-[#020617]/30">
                                        <div className="text-center">
                                            <BarChart2 className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                                            <span className="text-xs font-mono uppercase tracking-wider">No data for this period</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Live Feed Section */}
                    <div className="relative group">
                        <div className="absolute -inset-0.5 bg-gradient-to-br from-gold-500/20 to-orange-500/10 rounded-2xl blur-xl opacity-0 group-hover:opacity-50 transition-opacity duration-1000"></div>

                        <div className="relative glass-card rounded-2xl p-6 border border-white/10 bg-[#0f172a]/60 backdrop-blur-xl flex flex-col h-full shadow-2xl">
                            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-30" />

                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                        <Activity className="text-gold-400" size={20} />
                                        Live Feed
                                    </h3>
                                    <p className="text-xs text-slate-500 mt-1 font-mono uppercase tracking-wider">Recent Signals</p>
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto pr-2 space-y-3 max-h-[400px] custom-scrollbar">
                                {loading ? (
                                    <div className="space-y-3">
                                        {[1, 2, 3, 4].map((i) => (
                                            <div key={i} className="h-20 bg-[#020617]/50 rounded-xl border border-white/5 animate-pulse" />
                                        ))}
                                    </div>
                                ) : recentSignals.length > 0 ? (
                                    recentSignals.slice(0, 10).map((log, idx) => {
                                        const token = (log.token || "ETH").toString().toUpperCase()
                                        const ts = (log.evaluated_at as string) || (log.timestamp as string) || new Date().toISOString()
                                        const time = new Date(ts).toLocaleTimeString([], {
                                            hour: "2-digit",
                                            minute: "2-digit",
                                        })

                                        const result = String(log.result || "").toUpperCase()
                                        const isWin = result.includes("WIN") || result.includes("TP")
                                        const isLoss = result.includes("LOSS") || result.includes("SL")

                                        const badgeClass = isWin
                                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                            : isLoss
                                                ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                                                : "bg-brand-500/10 text-brand-400 border-brand-500/20"

                                        const move = log.move_pct || log.timeframe || "—"

                                        return (
                                            <div
                                                key={idx}
                                                onClick={() => setSelectedSignal(log)}
                                                className="border border-white/5 rounded-xl p-4 cursor-pointer hover:bg-white/[0.02] hover:border-gold-500/30 transition-all duration-300 bg-[#020617]/30 backdrop-blur-sm group/signal"
                                            >
                                                <div className="flex justify-between items-start mb-2">
                                                    <div className="flex items-center gap-2">
                                                        <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center border border-white/10 font-bold text-xs">
                                                            {token.slice(0, 2)}
                                                        </div>
                                                        <span className="font-bold text-white text-sm">{token}</span>
                                                    </div>
                                                    <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono">
                                                        <Clock size={10} />
                                                        {time}
                                                    </div>
                                                </div>

                                                <div className="flex justify-between items-center">
                                                    <span
                                                        className={`text-xs font-bold px-2 py-1 rounded-lg border ${badgeClass} uppercase tracking-wide`}
                                                    >
                                                        {result || "SIGNAL"}
                                                    </span>
                                                    <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
                                                        {isWin && <ArrowUpRight size={12} className="text-emerald-400" />}
                                                        {isLoss && <ArrowDownRight size={12} className="text-rose-400" />}
                                                        {move}
                                                    </span>
                                                </div>
                                            </div>
                                        )
                                    })
                                ) : (
                                    <div className="text-center text-slate-500 py-12 text-sm border border-dashed border-white/10 rounded-xl bg-[#020617]/30">
                                        <Activity className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                                        <p className="font-mono text-xs uppercase tracking-wider">No recent activity</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="fixed bottom-0 w-full border-t border-white/5 bg-[#020617]/90 backdrop-blur-md py-2 px-6 flex justify-between items-center text-[10px] uppercase font-bold text-slate-600 tracking-wider z-20 shadow-[0_-4px_20px_rgba(0,0,0,0.3)]">
                <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1.5 hover:text-gold-400 transition-colors cursor-default">
                        <ShieldCheck size={12} /> Encrypted Connection
                    </span>
                    <span className="hidden sm:inline-block w-px h-3 bg-white/10"></span>
                    <span className="hidden sm:inline-block hover:text-brand-400 transition-colors cursor-default">
                        Latency: <span className="text-emerald-500 font-mono">24ms</span>
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <TrendingUp size={12} className="text-emerald-500" /> Market Data:{" "}
                    <span className="text-emerald-500 font-mono">Live</span>
                </div>
            </div>

            <TacticalAnalysisDrawer
                open={!!selectedSignal}
                onOpenChange={(open) => !open && setSelectedSignal(null)}
                signal={selectedSignal}
            />
        </div>
    );
};

