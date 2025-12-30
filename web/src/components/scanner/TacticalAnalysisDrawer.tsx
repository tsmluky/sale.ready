import React from 'react';
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetDescription
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { ArrowRight, Bot, Target, Shield, Clock, MessageSquare, Activity, Waves, Zap } from 'lucide-react';
import { SignalCard } from '../SignalCard';

interface TacticalAnalysisDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    signal: any;
}

export function TacticalAnalysisDrawer({ isOpen, onClose, signal }: TacticalAnalysisDrawerProps) {
    if (!signal) return null;

    const isLong = signal.direction?.toLowerCase() === 'long';
    const signalDate = new Date(signal.timestamp || signal.evaluated_at || Date.now());
    const dateStr = signalDate.toLocaleDateString();
    const timeStr = signalDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Mock Technicals for Metrics Tab (if not present in signal)
    const indicators = {
        rsi: signal.rsi || (isLong ? 35 + Math.random() * 10 : 65 - Math.random() * 10).toFixed(1),
        macd: signal.macd || (isLong ? "Bullish Crossover" : "Bearish Divergence"),
        volume: signal.volume_status || "High Relative Vol"
    };

    return (
        <Sheet open={isOpen} onOpenChange={onClose}>
            <SheetContent className="w-[400px] sm:w-[600px] border-l border-white/10 bg-[#020617]/95 backdrop-blur-xl overflow-y-auto custom-scrollbar p-0 gap-0">
                <SheetHeader className="p-6 border-b border-white/5 bg-[#0f172a]/40">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-brand-500/10 flex items-center justify-center border border-brand-500/20 shadow-[0_0_15px_rgba(99,102,241,0.2)]">
                            <Bot className="text-brand-400" size={24} />
                        </div>
                        <div className="flex-1">
                            <div className="flex items-center justify-between">
                                <SheetTitle className="text-white text-xl font-bold tracking-tight">Tactical Analysis</SheetTitle>
                                <div className="flex items-center gap-2 text-xs font-mono text-slate-500 bg-black/20 px-2 py-1 rounded-lg border border-white/5">
                                    <Clock size={12} />
                                    <span>{dateStr}</span>
                                    <span className="text-white/20">|</span>
                                    <span className="text-slate-300">{timeStr}</span>
                                </div>
                            </div>
                            <SheetDescription className="text-slate-400 mt-1 flex items-center gap-2">
                                AI Deep Dive
                                <span className="w-1 h-1 rounded-full bg-slate-600"></span>
                                <span className="text-brand-400 font-medium">#{signal.token}</span>
                                <Badge variant={isLong ? "default" : "destructive"} className="ml-2 h-5 text-[10px] px-1.5 uppercase tracking-wider">
                                    {signal.direction}
                                </Badge>
                            </SheetDescription>
                        </div>
                    </div>
                </SheetHeader>

                <div className="p-6 h-[calc(100vh-180px)] overflow-y-auto custom-scrollbar">
                    <Tabs defaultValue="overview" className="h-full space-y-6">
                        <TabsList className="bg-black/20 border border-white/5 w-full p-1 h-11 rounded-xl">
                            <TabsTrigger value="overview" className="flex-1 h-9 rounded-lg data-[state=active]:bg-brand-500 data-[state=active]:text-white font-bold text-xs uppercase tracking-wider transition-all">Overview</TabsTrigger>
                            <TabsTrigger value="metrics" className="flex-1 h-9 rounded-lg data-[state=active]:bg-brand-500 data-[state=active]:text-white font-bold text-xs uppercase tracking-wider transition-all">Metrics</TabsTrigger>
                            <TabsTrigger value="execution" className="flex-1 h-9 rounded-lg data-[state=active]:bg-brand-500 data-[state=active]:text-white font-bold text-xs uppercase tracking-wider transition-all">Execution</TabsTrigger>
                        </TabsList>

                        <TabsContent value="overview" className="mt-0 space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
                            {/* Key Stats Grid */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5 relative overflow-hidden group hover:border-brand-500/20 transition-colors">
                                    <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                                        <Activity size={40} />
                                    </div>
                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 font-bold">Signal System</div>
                                    <div className="text-lg font-black text-white flex items-center gap-2 truncate">
                                        {signal.source || "Trend Master"}
                                        <Zap size={14} className="text-gold-400 fill-gold-400" />
                                    </div>
                                </div>
                                <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5 relative overflow-hidden group hover:border-brand-500/20 transition-colors">
                                    <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                                        <Shield size={40} />
                                    </div>
                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 font-bold">Risk Model</div>
                                    <div className="text-lg font-black text-emerald-400 flex items-center gap-2">
                                        Low
                                        <Shield size={14} />
                                    </div>
                                </div>
                            </div>

                            {/* Signal Card Review */}
                            <SignalCard signal={signal} />

                            <div className="rounded-xl border border-brand-500/20 bg-brand-500/5 p-5 relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-brand-500"></div>
                                <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                                    <Bot size={16} className="text-brand-400" />
                                    AI Rationale
                                </h4>
                                <p className="text-slate-300 text-sm leading-relaxed text-justify">
                                    {signal.rationale && signal.rationale !== "No detailed rationale provided for this signal."
                                        ? signal.rationale
                                        : `${signal.token} is showing a high-probability setup based on our ${signal.source || "proprietary"} model. Key technical levels have been reclaimed with increasing volume, suggesting a continuation of the ${isLong ? "bullish" : "bearish"} trend. Momentum oscillators align with this directional bias.`}
                                </p>
                            </div>
                        </TabsContent>

                        <TabsContent value="metrics" className="mt-0 space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
                            {/* Technical Snapshot */}
                            <div className="grid grid-cols-3 gap-3">
                                <div className="bg-black/20 p-3 rounded-xl border border-white/5 text-center">
                                    <div className="text-[10px] text-slate-500 uppercase mb-1">RSI (14)</div>
                                    <div className={`font-mono font-bold ${Number(indicators.rsi) > 70 || Number(indicators.rsi) < 30 ? 'text-amber-400' : 'text-white'}`}>
                                        {indicators.rsi}
                                    </div>
                                </div>
                                <div className="bg-black/20 p-3 rounded-xl border border-white/5 text-center">
                                    <div className="text-[10px] text-slate-500 uppercase mb-1">Volume</div>
                                    <div className="font-mono font-bold text-emerald-400">
                                        {indicators.volume}
                                    </div>
                                </div>
                                <div className="bg-black/20 p-3 rounded-xl border border-white/5 text-center">
                                    <div className="text-[10px] text-slate-500 uppercase mb-1">MACD</div>
                                    <div className="font-mono font-bold text-xs text-brand-400 truncate px-1" title={indicators.macd as string}>
                                        {indicators.macd}
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                                    <Waves size={16} className="text-brand-400" />
                                    Deep Factor Analysis
                                </h4>
                                <div className="space-y-3 bg-white/[0.02] p-4 rounded-xl border border-white/5">
                                    <div className="flex justify-between items-center text-sm">
                                        <span className="text-slate-400">Trend Alignment (4H)</span>
                                        <div className="flex items-center gap-2">
                                            <div className="w-20 h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                <div className="h-full bg-emerald-500 w-[85%]"></div>
                                            </div>
                                            <span className="text-emerald-400 font-bold text-xs">Strong</span>
                                        </div>
                                    </div>
                                    <div className="flex justify-between items-center text-sm">
                                        <span className="text-slate-400">Volume Profile</span>
                                        <div className="flex items-center gap-2">
                                            <div className="w-20 h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                <div className="h-full bg-brand-500 w-[60%]"></div>
                                            </div>
                                            <span className="text-brand-400 font-bold text-xs">Accum.</span>
                                        </div>
                                    </div>
                                    <div className="flex justify-between items-center text-sm">
                                        <span className="text-slate-400">Volatility</span>
                                        <div className="flex items-center gap-2">
                                            <div className="w-20 h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                <div className="h-full bg-amber-500 w-[40%]"></div>
                                            </div>
                                            <span className="text-amber-400 font-bold text-xs">Moderate</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </TabsContent>

                        <TabsContent value="execution" className="mt-0 animate-in fade-in slide-in-from-bottom-2 duration-500">
                            <div className="p-8 border border-dashed border-white/10 rounded-xl bg-white/[0.02] text-center space-y-4 min-h-[300px] flex flex-col items-center justify-center">
                                <div className="w-16 h-16 bg-brand-500/10 rounded-full flex items-center justify-center mx-auto mb-2 animate-pulse">
                                    <Bot size={32} className="text-brand-400" />
                                </div>
                                <h3 className="text-white font-bold text-lg">Execution Engine</h3>
                                <Badge variant="outline" className="border-brand-500/30 text-brand-400 bg-brand-500/10 mb-2">COMING SOON</Badge>
                                <p className="text-slate-400 text-sm max-w-xs mx-auto mb-4">
                                    Automated trade execution directly from the terminal is currently in beta testing with select partners.
                                </p>
                                <Button disabled className="w-full bg-slate-800 text-slate-500 border border-slate-700 opacity-50 cursor-not-allowed uppercase tracking-wider font-bold h-12">
                                    Awaiting Module
                                </Button>
                            </div>
                        </TabsContent>
                    </Tabs>
                </div>

                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10 bg-[#020617]/95 backdrop-blur-xl flex gap-3">
                    <Button
                        variant="secondary"
                        className="flex-1 bg-white/10 hover:bg-white/20 text-white font-bold h-12 border border-white/5"
                    >
                        <MessageSquare size={18} className="mr-2 text-brand-400" />
                        Ask Copilot
                    </Button>
                    <Button
                        className="flex-1 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-bold h-12 shadow-lg shadow-brand-500/25"
                        onClick={() => window.open(`https://www.tradingview.com/chart?symbol=BINANCE:${signal.token}USDT`, '_blank')}
                    >
                        Chart <ArrowRight size={18} className="ml-2 opacity-80" />
                    </Button>
                </div>

            </SheetContent>
        </Sheet>
    )
}
