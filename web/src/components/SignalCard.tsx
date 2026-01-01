import React, { useState } from 'react';
import { Target, TrendingUp, TrendingDown, ShieldAlert, Zap, Bot, LineChart, Send, Copy, Check, Bookmark } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/services/api';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useCopilot } from '@/context/CopilotContext';

interface SignalCardProps {
  signal: any;
  chartNode?: React.ReactNode;
}

export function SignalCard({ signal, chartNode }: SignalCardProps) {
  const { setContext } = useCopilot();
  const [isSaved, setIsSaved] = useState(signal.is_saved === 1);
  const [sentiment, setSentiment] = useState<'bullish' | 'bearish' | 'neutral'>(
    signal.direction?.toLowerCase() === 'long' ? 'bullish' : 'bearish'
  );

  if (!signal) return null;

  const isLong = signal.direction?.toLowerCase() === 'long';

  // Format helper
  const fmt = (val: any) => typeof val === 'number' ? val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 }) : val;

  const handleDiscuss = () => {
    setContext({
      token: signal.token,
      timeframe: signal.timeframe,
      signal: signal,
      message: `I'm analyzing this ${signal.token} ${signal.direction} signal. What do you think?`
    });
  };

  const handleTrack = async () => {
    try {
      if (signal.id) {
        // Existing signal -> Toggle
        const res = await api.toggleSignalSave(signal.id);
        setIsSaved(res.is_saved === 1);
        toast.success(res.is_saved === 1 ? "Signal Saved to Dashboard" : "Signal Removed from Dashboard");
      } else {
        // Transient signal -> Create Track
        const newSig = await api.trackSignal(signal);
        if (newSig && newSig.id) {
          signal.id = newSig.id; // Update local ref
          setIsSaved(true);
          toast.success("Signal Tracked Successfully");
        }
      }
    } catch (e) {
      console.error(e);
      toast.error("Failed to update signal tracking");
    }
  };

  const handleShare = async () => {
    try {
      await api.notifyTelegram(`🚀 *TRADERCOPILOT SIGNAL*\n\nAsset: #${signal.token}\nDirection: ${signal.direction.toUpperCase()}\n\n🎯 Entry: ${fmt(signal.entry)}\n💰 TP: ${fmt(signal.tp)}\n🛡️ SL: ${fmt(signal.sl)}\n\n⚡ Confidence: ${(signal.confidence * 100).toFixed(0)}%`);
      toast.success("Sent to Telegram");
    } catch (e) {
      toast.error("Failed to share");
    }
  };

  return (
    <div className="w-full animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0f172a]/80 backdrop-blur-xl shadow-2xl">

        {/* Top Strip */}
        <div className={cn("absolute top-0 left-0 w-full h-1 bg-gradient-to-r", isLong ? "from-emerald-500 via-emerald-400 to-transparent" : "from-rose-500 via-rose-400 to-transparent")} />

        <div className="p-6">
          {/* Header: Token & Direction */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className={cn(
                "w-12 h-12 rounded-xl flex items-center justify-center shadow-lg border border-white/5",
                isLong ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
              )}>
                {isLong ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-2xl font-black text-white tracking-tight">{signal.token}</h2>
                  <Badge variant="outline" className={cn(
                    "text-[10px] px-2 py-0.5 h-5 border-white/10 uppercase tracking-wider font-bold",
                    isLong ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                  )}>
                    {signal.direction}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleTrack}
                    className={cn(
                      "w-6 h-6 ml-2 rounded-full transition-all",
                      isSaved
                        ? "bg-brand-500/20 text-brand-400 hover:bg-brand-500/30"
                        : "text-slate-500 hover:text-white hover:bg-white/10"
                    )}
                    title={isSaved ? "Stop Tracking" : "Track Signal"}
                  >
                    <Bookmark size={14} className={cn("transition-transform", isSaved && "fill-current")} />
                  </Button>
                </div>
                <div className="flex items-center gap-3 text-xs font-medium text-slate-400 mt-1">
                  <span>{signal.timeframe}</span>
                  <span className="w-1 h-1 rounded-full bg-slate-600" />
                  <span>{signal.timestamp ? new Date(signal.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}</span>
                </div>
              </div>
            </div>

            {/* Confidence Score - Top Right (Above Stop Loss) */}
            <div className="text-right">
              <div className="flex items-center gap-1.5 justify-end mb-1">
                <Zap size={14} className="text-brand-400 fill-brand-400 animate-pulse" />
                <span className="text-2xl font-black text-white tracking-tighter">
                  {(Number(signal.confidence || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <div className="text-[10px] uppercase font-bold text-brand-400/80 tracking-widest">
                Confidence
              </div>
            </div>
          </div>

          {/* Price Grid - Compact & Fixed Overflow */}
          <div className="grid grid-cols-3 gap-2">
            <div className="p-3 rounded-lg bg-[#020617]/50 border border-white/5">
              <div className="text-[9px] text-slate-500 uppercase tracking-wider mb-1 font-bold">Entry</div>
              <div className="text-sm font-mono font-bold text-white truncate" title={String(signal.entry)}>
                {fmt(signal.entry)}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-[#020617]/50 border border-white/5 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500/50" />
              <div className="text-[9px] text-emerald-500/70 uppercase tracking-wider mb-1 font-bold">Take Profit</div>
              <div className="text-sm font-mono font-bold text-emerald-400 truncate" title={String(signal.tp)}>
                {fmt(signal.tp)}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-[#020617]/50 border border-white/5 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-rose-500/50" />
              <div className="text-[9px] text-rose-500/70 uppercase tracking-wider mb-1 font-bold">Stop Loss</div>
              <div className="text-sm font-mono font-bold text-rose-400 truncate" title={String(signal.sl)}>
                {fmt(signal.sl)}
              </div>
            </div>
          </div>

          {/* Rationale Text - Prominent */}
          {signal.rationale && (
            <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/5">
              <div className="flex items-start gap-3">
                <Bot size={16} className="text-brand-400 mt-0.5 shrink-0" />
                <p className="text-sm text-slate-300 leading-relaxed italic">
                  "{signal.rationale}"
                </p>
              </div>
            </div>
          )}

          {/* Chart Injection Point (Fixed Height for Visibility) */}
          {chartNode && (
            <div className="mt-6 h-[250px] w-full relative">
              {chartNode}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
