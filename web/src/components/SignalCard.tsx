import React from 'react';
import { Target } from 'lucide-react';

interface SignalCardProps {
  signal: any;
  chartNode?: React.ReactNode;
}

export function SignalCard({ signal, chartNode }: SignalCardProps) {
  if (!signal) return null;

  return (
    <div className="space-y-4">
      {/* Price Targets Grid */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-[#0b1121] rounded-xl p-3 text-center border border-white/5 relative overflow-hidden group hover:border-white/10 transition-colors">
          <div className="absolute top-0 right-0 w-8 h-8 bg-slate-500/10 rounded-bl-xl"></div>
          <div className="text-[9px] text-slate-500 uppercase font-black tracking-widest mb-1">Entry</div>
          <div className="text-base font-mono font-bold text-white tracking-tighter">
            {typeof signal.entry === 'number' ? signal.entry.toFixed(2) : signal.entry}
          </div>
        </div>

        <div className="bg-[#0b1121] rounded-xl p-3 text-center border border-emerald-500/20 relative overflow-hidden group hover:border-emerald-500/30 transition-colors">
          <div className="absolute top-0 right-0 w-8 h-8 bg-emerald-500/10 rounded-bl-xl"></div>
          <div className="text-[9px] text-emerald-500/70 uppercase font-black tracking-widest mb-1">Target</div>
          <div className="text-base font-mono font-bold text-emerald-400 tracking-tighter shadow-emerald-500/20 drop-shadow-sm">
            {typeof signal.tp === 'number' ? signal.tp.toFixed(2) : signal.tp}
          </div>
        </div>

        <div className="bg-[#0b1121] rounded-xl p-3 text-center border border-rose-500/20 relative overflow-hidden group hover:border-rose-500/30 transition-colors">
          <div className="absolute top-0 right-0 w-8 h-8 bg-rose-500/10 rounded-bl-xl"></div>
          <div className="text-[9px] text-rose-500/70 uppercase font-black tracking-widest mb-1">Stop</div>
          <div className="text-base font-mono font-bold text-rose-400 tracking-tighter">
            {typeof signal.sl === 'number' ? signal.sl.toFixed(2) : signal.sl}
          </div>
        </div>
      </div>

      {/* Optional Chart Node */}
      {chartNode && (
        <div className="bg-black/40 rounded-xl border border-white/5 p-4 h-[200px] relative z-10">
          {chartNode}
        </div>
      )}
    </div>
  );
}
