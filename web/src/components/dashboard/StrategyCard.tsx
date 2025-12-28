import React from 'react';
import { Activity, TrendingUp, TrendingDown, Clock, BarChart2 } from 'lucide-react';

interface StrategyCardProps {
    name: string;
    timeframe: string;
    type: string;
    winRate: number;
    pnl: number;
    status: 'active' | 'standby';
    description: string;
    isCustom?: boolean;
}

export const StrategyCard: React.FC<StrategyCardProps> = ({
    name,
    timeframe,
    type,
    winRate,
    pnl,
    status,
    description,
    isCustom
}) => {
    const isProfitable = pnl > 0;
    const isActive = status === 'active';

    // Clean up text format (remove [" "] brackets and quotes if present)
    const cleanText = (text: string) => text ? text.replace(/[\[\]"']/g, '') : '';

    return (
    return (
        <div className={`
            relative overflow-hidden rounded-2xl p-5 transition-all duration-300 group
            bg-gradient-to-b from-slate-800/40 to-slate-900/40 backdrop-blur-md
            border border-slate-800/60 hover:border-indigo-500/30
            hover:shadow-[0_0_20px_-5px_rgba(99,102,241,0.2)]
            hover:-translate-y-1
        `}>
            {/* Background Glow Effect */}
            <div className={`absolute top-0 right-0 w-24 h-24 bg-${isCustom ? 'indigo' : 'emerald'}-500/10 blur-2xl rounded-full -mr-12 -mt-12 transition-opacity opacity-50 group-hover:opacity-100`} />

            {/* Custom Badge (Corner Position) */}
            {isCustom && (
                <div className="absolute top-0 right-0 mt-3 mr-3 px-1.5 py-0.5 bg-indigo-500 text-white text-[9px] font-bold uppercase tracking-wider rounded shadow-lg z-20">
                    CUSTOM
                </div>
            )}

            <div className="flex justify-between items-start mb-4 relative z-10">
                <div className="space-y-2">
                    {/* Status Pill */}
                    <div className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[9px] font-bold border uppercase tracking-wider shadow-sm
                        ${isActive
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-emerald-500/10'
                            : 'bg-slate-800 text-slate-400 border-slate-700'
                        }
                    `}>
                        <div className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
                        {status}
                    </div>

                    {/* Title & Meta */}
                    <div>
                        <h3 className="text-lg font-black text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-indigo-300 transition-all leading-tight">
                            {name}
                        </h3>
                        <div className="flex items-center gap-2 text-slate-500 text-[10px] mt-1.5 font-medium">
                            <span className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-300 border border-slate-700">{cleanText(timeframe)}</span>
                            <span className="text-slate-600">•</span>
                            <span className="text-slate-400">{cleanText(type)}</span>
                        </div>
                    </div>
                </div>

                {/* Type Icon */}
                <div className="flex flex-col items-end gap-2">
                    <div className={`p-2 rounded-xl border transition-colors ${type === 'Trend'
                        ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400 group-hover:bg-indigo-500/20'
                        : (type && type.includes('SOL') ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400' : 'bg-slate-800/50 border-slate-700 text-slate-400')
                        }`}>
                        {type === 'Trend' || name.includes('Trend') ? <TrendingUp size={16} /> : <Activity size={16} />}
                    </div>
                </div>
            </div>

            <p className="text-slate-400/80 text-[11px] mb-5 line-clamp-2 min-h-[2.4em] leading-relaxed font-medium">
                {description}
            </p>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-2 relative z-10">
                <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800/80 group-hover:border-slate-700 transition-colors relative overflow-hidden">
                    <div className="relative z-10">
                        <div className="text-slate-500 text-[9px] font-bold uppercase tracking-wider mb-0.5 flex items-center gap-1">
                            <BarChart2 className="w-2.5 h-2.5" /> Win Rate
                        </div>
                        <div className={`text-xl font-black font-mono tracking-tight ${winRate >= 50 ? 'text-emerald-400' : 'text-slate-200'}`}>
                            {winRate}%
                        </div>
                    </div>
                </div>

                <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800/80 group-hover:border-slate-700 transition-colors relative overflow-hidden">
                    <div className="relative z-10">
                        <div className="text-slate-500 text-[9px] font-bold uppercase tracking-wider mb-0.5 flex items-center gap-1">
                            <TrendingUp className="w-2.5 h-2.5" /> Total PnL
                        </div>
                        <div className={`text-xl font-black font-mono tracking-tight ${isProfitable ? 'text-emerald-400' : (pnl < 0 ? 'text-rose-400' : 'text-slate-200')}`}>
                            {pnl > 0 ? '+' : ''}{pnl}R
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
