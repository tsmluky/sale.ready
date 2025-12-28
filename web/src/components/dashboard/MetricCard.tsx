import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
    label: string;
    value: string;
    trend: number;
    icon: LucideIcon;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, trend, icon: Icon }) => (
    <div className="bg-slate-900/40 border border-slate-800/60 p-3.5 px-5 rounded-2xl flex items-center gap-4 min-w-[160px] backdrop-blur-md hover:bg-slate-900/60 transition-all duration-300 hover:border-indigo-500/30 group relative overflow-hidden h-full">
        <div className={`absolute -right-4 -top-4 w-16 h-16 rounded-full blur-2xl opacity-10 ${trend >= 0 ? 'bg-emerald-500' : 'bg-rose-500'} group-hover:opacity-20 transition-opacity`} />

        <div className={`p-2.5 rounded-xl relative z-10 ${trend >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
            <Icon size={20} />
        </div>
        <div className="relative z-10 flex flex-col justify-center">
            <div className="text-[9px] text-slate-400 uppercase font-black tracking-widest leading-none mb-1">{label}</div>
            <div className="flex items-baseline gap-2">
                <div className="text-xl font-mono font-bold text-white tracking-tight leading-none">
                    {value}
                </div>
                {trend !== 0 && (
                    <div className={`text-[9px] font-bold inline-flex items-center ${trend > 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                        {trend > 0 ? '▲' : '▼'} {Math.abs(trend)}%
                    </div>
                )}
            </div>
        </div>
    </div>
);
