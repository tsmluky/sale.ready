import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
    label: string;
    value: string;
    trend: number;
    icon: LucideIcon;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, trend, icon: Icon }) => (
    <div className="group relative overflow-hidden rounded-2xl bg-[#020617]/60 backdrop-blur-xl border border-white/5 p-5 shadow-lg transition-all duration-300 hover:border-brand-500/30 hover:shadow-[0_0_20px_-5px_rgba(99,102,241,0.3)] hover:-translate-y-1">
        {/* Top Gradient Line (Similar to Sidebar Active) */}
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-brand-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

        {/* Glow Blob */}
        <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full blur-3xl opacity-10 transition-opacity duration-500 group-hover:opacity-20 ${trend >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`} />

        <div className="relative z-10 flex items-start justify-between mb-4">
            <div className={`p-2.5 rounded-xl ${trend >= 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'} transition-transform group-hover:scale-110 duration-300`}>
                <Icon size={20} strokeWidth={2.5} />
            </div>
            {trend !== 0 && (
                <div className={`flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full border ${trend > 0 ? 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5' : 'text-rose-400 border-rose-500/20 bg-rose-500/5'}`}>
                    {trend > 0 ? '↗' : '↘'} {Math.abs(trend)}%
                </div>
            )}
        </div>

        <div className="relative z-10">
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-widest mb-1 group-hover:text-brand-300 transition-colors">{label}</div>
            <div className="text-3xl font-black text-white tracking-tight flex items-baseline gap-1 shadow-black drop-shadow-sm">
                {value}
            </div>
        </div>
    </div>
);
