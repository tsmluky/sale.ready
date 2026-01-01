import React from 'react';
import {
    ResponsiveContainer,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ReferenceLine,
    Label
} from 'recharts';

interface SignalChartProps {
    data: any[];
    entry: number;
    tp: number;
    sl: number;
    direction: 'long' | 'short';
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        // Format timestamp label
        const dateStr = new Date(Number(label) * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        return (
            <div className="bg-[#0f172a]/90 backdrop-blur-md border border-white/10 p-3 rounded-xl shadow-2xl min-w-[120px]">
                <p className="text-slate-400 text-[10px] mb-1 font-mono uppercase tracking-wider">{dateStr}</p>
                <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-brand-400 shadow-[0_0_10px_rgba(99,102,241,0.5)]"></span>
                    <p className="text-white font-mono font-bold text-lg">
                        {payload[0].value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </p>
                </div>
            </div>
        );
    }
    return null;
};

export const SignalChart = ({ data, entry, tp, sl, direction }: SignalChartProps) => {
    const validData = data.filter(d => d.value !== undefined);
    const prices = validData.map(d => d.value);

    if (prices.length === 0) return (
        <div className="flex items-center justify-center h-full text-slate-500 text-xs font-mono tracking-wider">
            AWAITING TELEMENTRY DATA...
        </div>
    );

    // Calculate domain with 15% padding to ensure SL/TP are well within view
    const levels = [entry, tp, sl].filter(v => typeof v === 'number' && v > 0);
    const validPrices = prices.filter(p => typeof p === 'number' && p > 0);
    const allValues = [...validPrices, ...levels];

    // Default fallbacks preventing -Infinity
    const minVal = allValues.length ? Math.min(...allValues) : 0;
    const maxVal = allValues.length ? Math.max(...allValues) : 100;

    // Use percentage padding relative to price range
    const range = maxVal - minVal;
    const padding = range === 0 ? maxVal * 0.1 : range * 0.15;

    const domainMin = minVal - padding;
    const domainMax = maxVal + padding;

    // Determine Trend Color
    const isLong = direction === 'long';
    // const mainColor = isLong ? "#10b981" : "#f43f5e"; // Emerald / Rose
    const mainColor = "#6366f1"; // Use Indigo for neutral/brand chart, Entry/TP/SL frame the trade context

    return (
        <div className="w-full h-full min-h-[300px] select-none bg-black/20 rounded-xl overflow-hidden relative p-2">

            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 30 }}>
                    <defs>
                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={mainColor} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={mainColor} stopOpacity={0} />
                        </linearGradient>
                    </defs>

                    <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="rgba(255,255,255,0.05)"
                        vertical={false}
                    />

                    <XAxis
                        dataKey="time"
                        stroke="#64748b"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                        minTickGap={40}
                        tickFormatter={(t) => {
                            try {
                                return new Date(t * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                            } catch { return ''; }
                        }}
                        dy={10}
                        height={20}
                    />

                    <YAxis
                        domain={[domainMin, domainMax]}
                        stroke="#64748b"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                        width={50}
                        tickFormatter={(val) =>
                            val.toLocaleString(undefined, { notation: "compact", maximumFractionDigits: 1 })
                        }
                        orientation="right"
                        dx={5}
                    />

                    <Tooltip
                        content={<CustomTooltip />}
                        cursor={{ stroke: 'rgba(255,255,255,0.2)', strokeWidth: 1, strokeDasharray: '4 4' }}
                    />

                    <Area
                        type="monotone"
                        dataKey="value"
                        stroke={mainColor}
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorPrice)"
                        isAnimationActive={true}
                        animationDuration={1500}
                    />

                    {/* Entry Line */}
                    {entry > 0 && (
                        <ReferenceLine y={entry} stroke="#fbbf24" strokeDasharray="3 3">
                            <Label value="ENTRY" position="right" fill="#fbbf24" fontSize={10} fontWeight="bold" />
                        </ReferenceLine>
                    )}

                    {/* TP Line */}
                    {tp > 0 && (
                        <ReferenceLine y={tp} stroke="#10b981">
                            <Label value="TP" position="right" fill="#10b981" fontSize={10} fontWeight="bold" />
                        </ReferenceLine>
                    )}

                    {/* SL Line */}
                    {sl > 0 && (
                        <ReferenceLine y={sl} stroke="#f43f5e">
                            <Label value="SL" position="right" fill="#f43f5e" fontSize={10} fontWeight="bold" />
                        </ReferenceLine>
                    )}
                </AreaChart>
            </ResponsiveContainer>

            <div className="absolute left-4 top-4 text-[9px] font-mono text-slate-500 pointer-events-none">
                Price Action (1H)
            </div>
        </div>
    );
};
