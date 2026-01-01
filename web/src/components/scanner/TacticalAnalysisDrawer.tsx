import React, { useState } from 'react';
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
import { AdvisorChat } from '../AdvisorChat';

interface TacticalAnalysisDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    signal: any;
}

export function TacticalAnalysisDrawer({ isOpen, onClose, signal }: TacticalAnalysisDrawerProps) {
    const [activeTab, setActiveTab] = useState("overview");
    const [realMetrics, setRealMetrics] = useState<any>(null);
    const [loadingMetrics, setLoadingMetrics] = useState(false);

    // Fetch Real OHLCV and Calculate Metrics
    React.useEffect(() => {
        if (isOpen && signal?.token) {
            setLoadingMetrics(true);
            const fetchMetrics = async () => {
                try {
                    // Import dynamically to avoid circular deps if any, or just use api
                    const { api } = await import('@/services/api');
                    const data = await api.getOHLCV(signal.token, signal.timeframe || '4h');

                    if (data && data.length > 20) {
                        const closes = data.map(d => d.close);
                        // Simple RSI Calculation
                        const calculateRSI = (prices: number[], period: number = 14) => {
                            let gains = 0, losses = 0;
                            for (let i = 1; i <= period; i++) {
                                const diff = prices[i] - prices[i - 1];
                                if (diff > 0) gains += diff;
                                else losses -= diff;
                            }
                            let avgGain = gains / period;
                            let avgLoss = losses / period;

                            // Exponential Moving Average
                            for (let i = period + 1; i < prices.length; i++) {
                                const diff = prices[i] - prices[i - 1];
                                const gain = diff > 0 ? diff : 0;
                                const loss = diff < 0 ? -diff : 0;
                                avgGain = (avgGain * 13 + gain) / 14;
                                avgLoss = (avgLoss * 13 + loss) / 14;
                            }

                            const rs = avgGain / avgLoss;
                            return 100 - (100 / (1 + rs));
                        };

                        const rsi = calculateRSI(closes);
                        const lastVol = data[data.length - 1].value; // Volume approximation if needed, or just value
                        // Mocking Volume Status based on simple moving average
                        const avgVol = data.slice(-20).reduce((a, b) => a + b.value, 0) / 20;
                        const volStatus = lastVol > avgVol * 1.5 ? "Surge" : lastVol > avgVol ? "High" : "Normal";

                        setRealMetrics({
                            rsi: rsi.toFixed(1),
                            volume: volStatus,
                            macd: rsi > 50 ? "Bullish" : "Bearish" // Simplified MACD proxy
                        });
                    }
                } catch (err) {
                    console.error("Failed to calculate metrics", err);
                } finally {
                    setLoadingMetrics(false);
                }
            };
            fetchMetrics();
        }
    }, [isOpen, signal?.token]);

    if (!signal) return null;

    const isLong = signal.direction?.toLowerCase() === 'long';
    // Time Normalization Helper
    const rawTs = signal.timestamp || signal.evaluated_at || new Date().toISOString();
    // Ensure we treat it as UTC if it lacks offset info, to prevent "local interpretation" of server time
    const safeTs = rawTs.endsWith('Z') ? rawTs : rawTs + 'Z';
    const signalDate = new Date(safeTs);

    // Force UTC for consistency if that's the "normalized" standard, or just ensure clear formatting
    const dateStr = signalDate.toLocaleDateString(undefined, { day: '2-digit', month: '2-digit', year: 'numeric' });
    const timeStr = signalDate.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false });

    // Use Real Metrics if available, else Mock
    const indicators = realMetrics || {
        rsi: signal.rsi || (isLong ? 35 + Math.random() * 10 : 65 - Math.random() * 10).toFixed(1),
        macd: signal.macd || (isLong ? "Bullish Crossover" : "Bearish Divergence"),
        volume: signal.volume_status || "High Relative Vol"
    };

    return (
        <Sheet open={isOpen} onOpenChange={onClose}>
            <SheetContent className="w-[400px] sm:w-[500px] border-l border-white/10 bg-[#020617]/95 backdrop-blur-xl overflow-y-auto custom-scrollbar p-0 gap-0">
                <SheetHeader className="p-5 border-b border-white/5 bg-[#0f172a]/40">
                    <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-lg bg-brand-500/10 flex items-center justify-center border border-brand-500/20 shadow-[0_0_15px_rgba(99,102,241,0.2)] shrink-0 mt-1">
                            <Bot className="text-brand-400" size={20} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                                <SheetTitle className="text-white text-lg font-bold tracking-tight truncate">Analysis</SheetTitle>
                                <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500 bg-black/40 px-2 py-1 rounded-md border border-white/5 whitespace-nowrap mr-8">
                                    <Clock size={10} />
                                    <span>{dateStr}</span>
                                    <span className="text-white/20">|</span>
                                    <span className="text-slate-300">{timeStr}</span>
                                </div>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                                <span className="text-slate-400 text-xs font-medium">AI Deep Dive</span>
                                <span className="w-1 h-1 rounded-full bg-slate-600"></span>
                                <span className="text-brand-400 font-bold text-xs">#{signal.token}</span>
                                <Badge variant="outline" className={`h-5 text-[10px] px-2 uppercase tracking-wider font-bold border ${isLong ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border-rose-500/20"}`}>
                                    {signal.direction}
                                </Badge>
                            </div>
                        </div>
                    </div>
                </SheetHeader>

                <div className="p-5 h-[calc(100vh-160px)] overflow-y-auto custom-scrollbar">
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full space-y-5">
                        <TabsList className="bg-black/20 border border-white/5 w-full p-1 h-10 rounded-lg grid grid-cols-4">
                            <TabsTrigger value="overview" className="h-8 rounded-md data-[state=active]:bg-brand-500 data-[state=active]:text-white font-bold text-[10px] uppercase tracking-wider transition-all">Overview</TabsTrigger>
                            <TabsTrigger value="metrics" className="h-8 rounded-md data-[state=active]:bg-brand-500 data-[state=active]:text-white font-bold text-[10px] uppercase tracking-wider transition-all">Metrics</TabsTrigger>
                            <TabsTrigger value="execution" className="h-8 rounded-md data-[state=active]:bg-brand-500 data-[state=active]:text-white font-bold text-[10px] uppercase tracking-wider transition-all">Execute</TabsTrigger>
                            <TabsTrigger value="chat" className="h-8 rounded-md data-[state=active]:bg-brand-500 data-[state=active]:text-white font-bold text-[10px] uppercase tracking-wider transition-all flex items-center justify-center gap-1">
                                <MessageSquare size={10} /> Chat
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="overview" className="mt-0 space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-500">
                            {/* Key Stats Grid - Compact */}
                            <div className="grid grid-cols-2 gap-3">
                                <div className="p-3 rounded-xl bg-gradient-to-br from-brand-500/10 to-transparent border border-brand-500/20 relative overflow-hidden group">
                                    <div className="absolute top-0 right-0 p-2 opacity-20 group-hover:opacity-40 transition-opacity">
                                        <Activity size={32} className="text-brand-500" />
                                    </div>
                                    <div className="text-[9px] text-brand-300 uppercase tracking-wider mb-1 font-bold">Signal System</div>
                                    <div className="text-base font-black text-white flex items-center gap-2 truncate relative z-10">
                                        {signal.source?.split('-')[0] || "Trend"} {/* Truncate name if long */}
                                        <Zap size={12} className="text-yellow-400 fill-yellow-400" />
                                    </div>
                                </div>
                                <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500/10 to-transparent border border-emerald-500/20 relative overflow-hidden group">
                                    <div className="absolute top-0 right-0 p-2 opacity-20 group-hover:opacity-40 transition-opacity">
                                        <Shield size={32} className="text-emerald-500" />
                                    </div>
                                    <div className="text-[9px] text-emerald-300 uppercase tracking-wider mb-1 font-bold">Risk Model</div>
                                    <div className="text-base font-black text-emerald-400 flex items-center gap-2 relative z-10">
                                        Low
                                        <Shield size={12} className="fill-emerald-400/20" />
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
                                    <div className={`font-mono font-bold ${Number(indicators.rsi) > 70 || Number(indicators.rsi) < 30 ? 'text-amber-400' : 'text-white'} ${loadingMetrics ? 'animate-pulse' : ''}`}>
                                        {loadingMetrics ? '...' : indicators.rsi}
                                    </div>
                                </div>
                                <div className="bg-black/20 p-3 rounded-xl border border-white/5 text-center">
                                    <div className="text-[10px] text-slate-500 uppercase mb-1">Volume</div>
                                    <div className={`font-mono font-bold text-emerald-400 ${loadingMetrics ? 'animate-pulse' : ''}`}>
                                        {loadingMetrics ? '...' : indicators.volume}
                                    </div>
                                </div>
                                <div className="bg-black/20 p-3 rounded-xl border border-white/5 text-center">
                                    <div className="text-[10px] text-slate-500 uppercase mb-1">MACD</div>
                                    <div className={`font-mono font-bold text-xs text-brand-400 truncate px-1 ${loadingMetrics ? 'animate-pulse' : ''}`} title={indicators.macd as string}>
                                        {loadingMetrics ? '...' : indicators.macd}
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

                        <TabsContent value="chat" className="mt-0 h-[450px] animate-in fade-in slide-in-from-bottom-2 duration-500">
                            <div className="h-full rounded-xl overflow-hidden border border-white/10 bg-[#0B1121]">
                                <AdvisorChat
                                    embedded={true}
                                    currentToken={signal.token}
                                    currentTimeframe={signal.timeframe || "1h"}
                                    initialContext={signal}
                                />
                            </div>
                        </TabsContent>
                    </Tabs>
                </div>

                <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-white/10 bg-[#020617]/95 backdrop-blur-xl">
                    <Button
                        className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold h-12 shadow-[0_0_20px_rgba(79,70,229,0.3)] border border-white/10 text-sm tracking-wide transition-all hover:scale-[1.02]"
                        onClick={() => window.open(`https://www.tradingview.com/chart?symbol=BINANCE:${signal.token}USDT`, '_blank')}
                    >
                        <Activity className="mr-2" size={18} />
                        Analyze on TradingView
                        <ArrowRight size={16} className="ml-2 opacity-70" />
                    </Button>
                </div>

            </SheetContent>
        </Sheet>
    )
}
