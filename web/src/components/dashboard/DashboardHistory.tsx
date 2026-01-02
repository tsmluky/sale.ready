import React from 'react';
import { History, TrendingUp, TrendingDown, Clock, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

import { formatRelativeTime } from '../../utils/format';

import { useAuth } from '../../context/AuthContext';

interface DashboardHistoryProps {
    signals: any[]; // Using any to be flexible with backend response, but will cast to SignalHistory
    onSignalClick?: (signal: any) => void;
}

export const DashboardHistory: React.FC<DashboardHistoryProps> = ({ signals, onSignalClick }) => {
    const { userProfile } = useAuth();
    const userTimezone = userProfile?.user?.timezone;

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between px-2 mb-2">
                <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <History className="text-brand-400" size={20} />
                        Command Stream
                    </h2>
                    <p className="text-xs text-slate-400 font-medium pl-8">
                        Live execution log from active agents.
                    </p>
                </div>
            </div>

            <div className="space-y-3">
                {signals.length === 0 ? (
                    <div className="p-12 text-center text-slate-500 italic glass-card rounded-2xl border-dashed border-slate-700">
                        <div className="flex flex-col items-center gap-4">
                            <div className="relative flex h-4 w-4">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500"></span>
                            </div>
                            <span className="text-sm font-bold text-slate-400">Scanning markets for high-probability setups...</span>
                        </div>
                    </div>
                ) : (
                    signals.map((sig) => (
                        <div
                            key={sig.id}
                            onClick={() => onSignalClick && onSignalClick(sig)}
                            className="group relative flex items-center justify-between p-4 rounded-xl bg-[#0F172A]/40 border border-white/5 hover:bg-white/5 hover:border-brand-500/30 hover:shadow-[0_4px_20px_-5px_rgba(0,0,0,0.5)] transition-all duration-300 cursor-pointer backdrop-blur-md active:scale-[0.99]"
                        >
                            {/* Left: Token & Context */}
                            <div className="flex items-center gap-4 relative z-10">
                                {/* Token Avatar */}
                                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500/20 to-indigo-600/20 flex items-center justify-center text-xs font-black text-white border border-white/10 shadow-inner group-hover:scale-110 transition-transform duration-300">
                                    {sig.token.substring(0, 3)}
                                </div>

                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-bold text-white group-hover:text-brand-300 transition-colors">{sig.token}</span>
                                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${sig.direction === 'long'
                                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                            : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                                            }`}>
                                            {sig.direction}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-slate-500 font-mono mt-0.5">
                                        <span>{formatRelativeTime(sig.timestamp)}</span>
                                        <span className="w-0.5 h-0.5 rounded-full bg-slate-600"></span>
                                        <span className="text-slate-400">{sig.source.replace('Marketplace:', '')}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Right: Status & PnL */}
                            <div className="flex items-center gap-6 relative z-10">
                                {/* Entry Price (Hidden on mobile) */}
                                <div className="hidden md:block text-right">
                                    <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Entry</div>
                                    <div className="font-mono text-sm text-slate-300 group-hover:text-white transition-colors">{sig.entry}</div>
                                </div>

                                {/* Status Badge */}
                                <div className="min-w-[100px] text-right">
                                    {(() => {
                                        // Robust status extraction
                                        const rawStatus = String(sig.result || sig.status || 'PENDING').toUpperCase();
                                        const isWin = rawStatus.includes('WIN') || rawStatus.includes('TP') || (sig.pnl_r && sig.pnl_r > 0);
                                        const isLoss = rawStatus.includes('LOSS') || rawStatus.includes('SL') || (sig.pnl_r && sig.pnl_r < 0);
                                        // Display text logic
                                        let displayStatus = rawStatus;
                                        if (isWin) displayStatus = sig.pnl_r ? `+${sig.pnl_r}R` : 'WIN';
                                        else if (isLoss) displayStatus = sig.pnl_r ? `${sig.pnl_r}R` : 'LOSS';
                                        else if (displayStatus === 'OPEN' || displayStatus === 'PENDING') displayStatus = 'RUNNING';

                                        const isRunning = displayStatus === 'RUNNING';

                                        if (isWin || isLoss) {
                                            return (
                                                <div className={`inline-flex flex-col items-end`}>
                                                    <span className={`text-sm font-black tracking-tight ${isWin
                                                        ? 'text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.5)]'
                                                        : 'text-rose-400 drop-shadow-[0_0_8px_rgba(244,63,94,0.5)]'
                                                        }`}>
                                                        {displayStatus}
                                                    </span>
                                                    {(sig.result || sig.status) && <span className="text-[10px] font-bold text-slate-500 uppercase">{sig.result || sig.status}</span>}
                                                </div>
                                            );
                                        } else {
                                            return (
                                                <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-bold shadow-[0_0_10px_rgba(99,102,241,0.2)] animate-pulse">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
                                                    RUNNING
                                                </span>
                                            );
                                        }
                                    })()}
                                </div>

                                <ArrowRight size={16} className="text-slate-600 group-hover:text-white group-hover:translate-x-1 transition-all duration-300" />
                            </div>

                            {/* Hover Gradient Overlay */}
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
