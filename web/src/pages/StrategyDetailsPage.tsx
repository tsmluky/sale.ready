import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { ArrowLeft, Activity, Shield, Zap, TrendingUp, History, Hash } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { TacticalAnalysisDrawer } from '../components/scanner/TacticalAnalysisDrawer';
import { SignalHistory } from '../components/SignalDetailsModal'; // Keep type if needed, or replace with 'any' if generic
import { formatRelativeTime } from '../utils/format';

export const StrategyDetailsPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [persona, setPersona] = useState<any>(null);
    const [history, setHistory] = useState<SignalHistory[]>([]);
    const [selectedSignal, setSelectedSignal] = useState<SignalHistory | null>(null);
    const [showInsights, setShowInsights] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!id) return;
        loadData(id);
    }, [id]);

    const loadData = async (personaId: string) => {
        setLoading(true);
        try {
            // 1. Get Metadata from Marketplace list
            const marketData = await api.fetchMarketplace();
            const found = marketData.find((p: any) => p.id === personaId);
            setPersona(found);

            // 2. Get History
            const historyData = await api.fetchPersonaHistory(personaId);
            setHistory(historyData);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    if (!persona) {
        return (
            <div className="p-8 text-center text-slate-500">
                Persona not found. <button onClick={() => navigate('/strategies')} className="text-indigo-400">Go Back</button>
            </div>
        );
    }

    // Helper: Calculate frequency dynamically from history
    const getFrequencyLabel = () => {
        // 1. Static/Configured Frequency (Priority)
        if (persona.frequency && persona.frequency.includes('/')) {
            return persona.frequency;
        }

        // 2. Dynamic Calculation (Fallback)
        if (!history || history.length < 2) return "Estimating...";

        // Sort history just in case
        const sorted = [...history].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        const first = new Date(sorted[0].timestamp);
        const last = new Date(sorted[sorted.length - 1].timestamp);

        const daysDiff = (last.getTime() - first.getTime()) / (1000 * 3600 * 24);

        if (daysDiff < 1) return "~" + history.length + " / day"; // Very high freq (all in 1 day)

        const perDay = history.length / daysDiff;
        if (perDay >= 1) return "~" + perDay.toFixed(1) + " / day";

        const perWeek = perDay * 7;
        return "~" + perWeek.toFixed(1) + " / week";
    };

    // Helper to determine strategy type tags based on ID/Name
    const getStrategyTags = () => {
        const tags = [];
        const lowerId = persona.id.toLowerCase();

        if (lowerId.includes('rsi') || lowerId.includes('divergence')) {
            tags.push('Mean Reversion', 'RSI', 'Momentum');
        } else if (lowerId.includes('trend') || lowerId.includes('ma') || lowerId.includes('cross')) {
            tags.push('Trend Following', 'EMA', 'Breakout');
        } else {
            tags.push('Proprietary Logic', 'Multi-Factor');
        }
        return tags;
    };

    // Helper for Risk Badge
    const RiskBadge = ({ level }: { level: string }) => {
        const colors: any = {
            Low: 'bg-emerald-500',
            Medium: 'bg-yellow-500',
            High: 'bg-rose-500'
        };
        // Unused color var removed or just use className logic
        return (
            <div className="flex flex-col gap-2">
                <div className="flex gap-1 h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div className={`h-full ${level === 'Low' ? 'w-1/3 bg-emerald-500' : 'w-full bg-slate-800 opacity-20'}`} />
                    <div className={`h-full ${level === 'Medium' ? 'w-2/3 bg-yellow-500' : 'w-full bg-slate-800 opacity-20'}`} />
                    <div className={`h-full ${level === 'High' ? 'w-full bg-rose-500' : 'w-full bg-slate-800 opacity-20'}`} />
                </div>
                <span className={`text-sm font-bold ${level === 'Low' ? 'text-emerald-400' : level === 'Medium' ? 'text-yellow-400' : 'text-rose-400'}`}>
                    {level.toUpperCase()}
                </span>
            </div>
        );
    };

    const themeColor = persona.color || 'indigo';

    return (
        <div className="space-y-8 animate-fade-in pb-12 relative">
            {/* SIGNAL DETAILS DRAWER */}
            {selectedSignal && (
                <TacticalAnalysisDrawer
                    isOpen={!!selectedSignal}
                    onClose={() => setSelectedSignal(null)}
                    signal={selectedSignal}
                />
            )}

            {/* INSIGHTS MODAL */}
            {showInsights && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-fade-in"
                    onClick={(e) => {
                        if (e.target === e.currentTarget) {
                            setShowInsights(false);
                        }
                    }}
                >
                    <div className="bg-slate-900 border border-slate-700/50 rounded-3xl max-w-4xl w-full shadow-2xl relative overflow-hidden flex flex-col md:flex-row">

                        {/* LEFT COLUMN: VISUAL HEADER */}
                        <div className={`relative w-full md:w-1/3 bg-gradient-to-br from-${themeColor}-600 to-indigo-900 p-8 flex flex-col justify-between overflow-hidden`}>
                            <div className="absolute top-0 left-0 w-full h-full bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20" />
                            <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-white/10 rounded-full blur-3xl" />

                            <div className="relative z-10">
                                <div className="flex items-center gap-2 text-white/80 mb-6">
                                    <Zap className="w-5 h-5 text-yellow-300" />
                                    <span className="font-bold tracking-widest text-xs uppercase">Strategy Profile</span>
                                </div>
                                <h2 className="text-3xl font-black text-white mb-2 leading-tight">
                                    {persona.name}
                                </h2>
                                <p className="text-white/60 text-sm font-medium">
                                    {getStrategyTags()[0]} Specialist
                                </p>
                            </div>

                            <div className="relative z-10 space-y-4 mt-12">
                                <div className="bg-black/20 backdrop-blur-sm p-4 rounded-xl border border-white/10">
                                    <div className="flex items-center gap-2 mb-1">
                                        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                                        <span className="text-xs font-bold text-emerald-300">SYSTEM STATUS</span>
                                    </div>
                                    <p className="text-white text-xs font-mono">
                                        Logic Engine v2.4.1 Online<br />
                                        Latency: 45ms
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* RIGHT COLUMN: CONTENT */}
                        <div className="flex-1 p-8 md:p-10 bg-slate-900">
                            <div className="flex justify-between items-start mb-8">
                                <div>
                                    <h3 className="text-lg font-bold text-white mb-1">Technical Architecture</h3>
                                    <p className="text-slate-500 text-sm">Component breakdown & behavior analysis</p>
                                </div>
                                <button
                                    onClick={() => setShowInsights(false)}
                                    className="p-2 hover:bg-slate-800 rounded-full text-slate-400 hover:text-white transition-colors"
                                >
                                    ✕
                                </button>
                            </div>

                            <div className="space-y-8">
                                {/* TAGS */}
                                <div>
                                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Core Components</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {getStrategyTags().map(tag => (
                                            <span key={tag} className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 text-xs font-bold hover:border-indigo-500 hover:text-white transition-colors cursor-default">
                                                {tag}
                                            </span>
                                        ))}
                                        <span className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-500 border border-slate-700 text-xs font-bold border-dashed">
                                            +2 Proprietary
                                        </span>
                                    </div>
                                </div>

                                {/* DESCRIPTION */}
                                <div>
                                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Logic Overview</h4>
                                    <p className="text-slate-300 text-sm leading-relaxed border-l-2 border-indigo-500 pl-4 py-1">
                                        {persona.description || "This agent targets high-probability setups using a composite momentum framework. It adapts to volatility conditions to optimize entry timing."}
                                    </p>
                                </div>

                                {/* CONFIG GRID */}
                                <div>
                                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Parameters</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-800">
                                            <span className="text-xs text-slate-500 block">Timeframe</span>
                                            <span className="text-white font-mono font-bold">1H (Hourly)</span>
                                        </div>
                                        <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-800">
                                            <span className="text-xs text-slate-500 block">Market Focus</span>
                                            <span className="text-white font-mono font-bold">{persona.symbol || "SOL"}</span>
                                        </div>
                                        <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-800">
                                            <span className="text-xs text-slate-500 block">Risk Model</span>
                                            <span className="text-white font-mono font-bold">Dynamic (ATR)</span>
                                        </div>
                                        <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-800">
                                            <span className="text-xs text-slate-500 block">Exit Strategy</span>
                                            <span className="text-white font-mono font-bold">Scalable TP</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-6 mt-8 border-t border-slate-800 text-center md:text-left flex flex-col md:flex-row justify-between items-center gap-4">
                                    <p className="text-xs text-slate-500">
                                        Protected by TraderCopilot Engine License.
                                    </p>
                                    {/* View Full Documentation removed */}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Header / Nav */}
            <div className="flex justify-between items-center">
                <button
                    onClick={() => navigate('/strategies')}
                    className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors group"
                >
                    <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Back to Marketplace
                </button>

                <div className="flex gap-3">
                    {/* INSIGHTS BUTTON */}
                    <button
                        onClick={() => setShowInsights(true)}
                        className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white px-4 py-2 rounded-lg font-semibold shadow-lg shadow-indigo-500/20 transition-all hover:scale-105"
                    >
                        <Zap className="w-4 h-4 text-yellow-300" />
                        Strategy Profile
                    </button>

                    {persona.is_custom && (
                        <button
                            onClick={async () => {
                                try {
                                    const toastId = toast.loading('Deleting agent...');
                                    await api.deletePersona(persona.id);
                                    toast.success('Agent deleted successfully', { id: toastId });
                                    navigate('/strategies');
                                } catch (e: any) {
                                    toast.error(e.message);
                                }
                            }}
                            className="text-xs font-bold text-rose-500 hover:text-white hover:bg-rose-600 px-4 py-2 rounded-lg transition-all border border-rose-500/20 hover:border-transparent flex items-center gap-2"
                        >
                            <span className="hidden md:inline">DELETE AGENT</span>
                            <span className="md:hidden">DEL</span>
                        </button>
                    )}
                </div>
            </div>

            {/* HERO SECTION */}
            <div className={`relative overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/50 p-8 md:p-12 backdrop-blur-sm`}>
                <div className={`absolute -top-32 -right-32 h-96 w-96 rounded-full bg-${themeColor}-500/20 blur-3xl`} />

                {/* Content */}
                <div className="relative z-10 grid lg:grid-cols-2 gap-12 items-center">
                    <div className="space-y-6">
                        <div className="flex items-center gap-3">
                            <span className={`px-3 py-1 rounded-full text-xs font-bold bg-${themeColor}-500/10 text-${themeColor}-400 border border-${themeColor}-500/20 tracking-wider uppercase`}>
                                {persona.id}
                            </span>
                            {persona.is_active && (
                                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                                    <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                    ACTIVE
                                </span>
                            )}
                        </div>

                        <div>
                            <h1 className="text-5xl md:text-6xl font-black text-white tracking-tighter mb-4 shadow-black drop-shadow-xl">
                                {persona.name}
                            </h1>
                            <p className="text-lg text-slate-400 leading-relaxed max-w-xl border-l-2 border-slate-700 pl-4">
                                {persona.description}
                            </p>
                        </div>
                    </div>

                    {/* ENHANCED STATS GRID */}
                    <div className="grid grid-cols-2 gap-4">
                        {/* Win Rate Card */}
                        <div className="p-5 bg-slate-950/80 rounded-2xl border border-slate-800/60 backdrop-blur-md shadow-xl hover:border-indigo-500/30 transition-colors group">
                            <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase tracking-wider mb-2 group-hover:text-indigo-400 transition-colors">
                                <Activity className="w-4 h-4" /> Win Rate
                            </div>
                            <div className="flex items-end gap-2">
                                {persona.win_rate && persona.win_rate !== "N/A" ? (
                                    <span className="text-4xl font-black text-white">{persona.win_rate}</span>
                                ) : (
                                    <span className="text-4xl font-black text-slate-600">--%</span>
                                )}
                            </div>
                            <div className="w-full h-1.5 bg-slate-800 rounded-full mt-3 overflow-hidden">
                                {persona.win_rate && persona.win_rate !== "N/A" ? (
                                    <div
                                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                                        style={{ width: `${persona.win_rate}` }}
                                    />
                                ) : (
                                    <div className="h-full w-full bg-slate-800" />
                                )}
                            </div>
                        </div>

                        {/* Expected ROI Card */}
                        <div className="p-5 bg-slate-950/80 rounded-2xl border border-slate-800/60 backdrop-blur-md shadow-xl hover:border-emerald-500/30 transition-colors group">
                            <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase tracking-wider mb-2 group-hover:text-emerald-400 transition-colors">
                                <TrendingUp className="w-4 h-4" /> Expected ROI
                            </div>
                            <div className={`text-3xl font-black ${persona.expected_roi && persona.expected_roi.includes('+') ? 'text-emerald-400' : 'text-slate-200'}`}>
                                {persona.expected_roi || '0.00 R'}
                            </div>
                            <span className="text-xs text-slate-500 mt-1 block">Return On Investment</span>
                        </div>

                        <div className="p-5 bg-slate-950/80 rounded-2xl border border-slate-800/60 backdrop-blur-md shadow-xl">
                            <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">
                                <Zap className="w-4 h-4" /> Activity
                            </div>
                            <div className="flex flex-col h-full justify-between">
                                <span className="text-2xl font-bold text-white">{getFrequencyLabel()}</span>
                                <div className="flex gap-1 items-end h-1.5 mt-2">
                                    <div className="w-full bg-cyan-500/20 rounded-full h-full overflow-hidden">
                                        <div className="bg-cyan-400 h-full w-2/3 animate-pulse" />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Risk Card */}
                        <div className="p-5 bg-slate-950/80 rounded-2xl border border-slate-800/60 backdrop-blur-md shadow-xl">
                            <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">
                                <Shield className="w-4 h-4" /> Risk Level
                            </div>
                            <RiskBadge level={persona.risk_level || 'Medium'} />
                        </div>
                    </div>
                </div>
            </div>

            {/* SIGNAL HISTORY */}
            <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
                <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-950/30">
                    <h3 className="text-lg font-bold text-white flex items-center gap-3">
                        <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
                            <History className="w-5 h-5" />
                        </div>
                        Signal History
                    </h3>
                    <div className="text-xs font-medium px-3 py-1 bg-slate-800 rounded-full text-slate-400 border border-slate-700">
                        Full History
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-950/50 text-slate-500 text-xs font-bold uppercase tracking-wider">
                                <th className="p-5 font-bold hover:text-white transition-colors cursor-pointer">Time</th>
                                <th className="p-5 font-bold hover:text-white transition-colors cursor-pointer">Token</th>
                                <th className="p-5 font-bold hover:text-white transition-colors cursor-pointer">Direction</th>
                                <th className="p-5 font-bold text-right hover:text-white transition-colors cursor-pointer">Entry</th>
                                <th className="p-5 font-bold text-right hover:text-white transition-colors cursor-pointer">TP / SL</th>
                                <th className="p-5 font-bold text-center hover:text-white transition-colors cursor-pointer">Result</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {history.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="p-12 text-center">
                                        <div className="flex flex-col items-center justify-center gap-3 opacity-50">
                                            <Hash className="w-8 h-8 text-slate-600" />
                                            <span className="text-slate-500 italic">No signals generated yet.</span>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                history.map((sig) => (
                                    <tr
                                        key={sig.id}
                                        onClick={() => setSelectedSignal(sig)}
                                        className="hover:bg-indigo-500/5 transition-all duration-200 group border-l-2 border-transparent hover:border-indigo-500 cursor-pointer"
                                    >
                                        <td className="p-5 text-slate-400 font-mono text-xs whitespace-nowrap group-hover:text-slate-300" title={new Date(sig.timestamp).toLocaleString()}>
                                            {formatRelativeTime(sig.timestamp)}
                                        </td>
                                        <td className="p-5 text-white font-bold text-sm flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-indigo-500" />
                                            {sig.token}
                                            {sig.mode === 'BACKTEST' && (
                                                <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-500 border border-slate-700">
                                                    BACKTEST
                                                </span>
                                            )}
                                        </td>
                                        <td className="p-5">
                                            <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-black uppercase tracking-wide border ${sig.direction.toLowerCase() === 'long'
                                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_8px_rgba(16,185,129,0.1)]'
                                                : 'bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-[0_0_8px_rgba(244,63,94,0.1)]'
                                                }`}>
                                                {sig.direction.toUpperCase() === 'LONG' ? '↑ LONG' : '↓ SHORT'}
                                            </span>
                                        </td>
                                        <td className="p-5 text-right font-mono text-slate-300 text-sm">
                                            {sig.entry}
                                        </td>
                                        <td className="p-5 text-right font-mono text-slate-500 text-xs space-y-1">
                                            <div className="flex justify-end items-center gap-2">
                                                <span className="text-emerald-500/80 font-bold">TP</span>
                                                <span>{sig.tp}</span>
                                            </div>
                                            <div className="flex justify-end items-center gap-2">
                                                <span className="text-rose-500/80 font-bold">SL</span>
                                                <span>{sig.sl}</span>
                                            </div>
                                        </td>
                                        <td className="p-5 text-center">
                                            {sig.result ? (
                                                <span className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${sig.result.result.includes('tp') || sig.result.pnl_r > 0
                                                    ? 'text-emerald-300 bg-emerald-500/20 border-emerald-500/30'
                                                    : sig.result.result.includes('sl') || sig.result.pnl_r < 0
                                                        ? 'text-rose-300 bg-rose-500/20 border-rose-500/30'
                                                        : 'text-slate-400 bg-slate-800 border-slate-700'
                                                    }`}>
                                                    {sig.result.result.toUpperCase()} ({sig.result.pnl_r > 0 ? '+' : ''}{sig.result.pnl_r}R)
                                                </span>
                                            ) : (
                                                <span className="text-[10px] font-bold text-slate-400 bg-slate-800 px-2.5 py-1 rounded-full border border-slate-700 inline-flex items-center gap-1.5">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
                                                    Running
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
