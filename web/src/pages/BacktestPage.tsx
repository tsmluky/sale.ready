import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, TrendingUp, TrendingDown, Clock, Info } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { API_BASE_URL } from '../constants';
import { api } from '../services/api';
import { toast } from 'react-hot-toast';

export const BacktestPage: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [params, setParams] = useState({
        token: 'SOL',
        timeframe: '1h',
        days: 30,
        strategy: 'rsi_divergence',
        capital: 1000
    });

    const [results, setResults] = useState<any>(null);
    const [error, setError] = useState('');

    // Persona Modal State
    const [isPersonaModalOpen, setIsPersonaModalOpen] = useState(false);
    const [personaName, setPersonaName] = useState('');
    const [personaDesc, setPersonaDesc] = useState('');
    const navigate = useNavigate();

    const runBacktest = async () => {
        setLoading(true);
        setError('');
        setResults(null);

        try {
            const res = await fetch(`${API_BASE_URL}/backtest/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    strategy_id: params.strategy,
                    token: params.token,
                    timeframe: params.timeframe,
                    days: Number(params.days),
                    initial_capital: Number(params.capital)
                })
            });

            if (!res.ok) {
                const text = await res.text();
                throw new Error(`Error ${res.status}: ${text}`);
            }

            const data = await res.json();
            setResults(data);
            toast.success("Backtest simulation complete!");
        } catch (err: any) {
            console.error(err);
            setError(err.message || "Error executing backtest");
            toast.error("Backtest failed");
        } finally {
            setLoading(false);
        }
    };

    const handleCreatePersona = async () => {
        if (!results) return;

        const toastId = toast.loading('Creating Agent...');
        try {
            await api.createPersona({
                name: personaName,
                description: personaDesc,
                symbol: params.token.toUpperCase(),
                timeframe: params.timeframe,
                strategy_id: params.strategy,
                risk_level: (results.metrics.max_drawdown || 0) < -10 ? "High" : "Medium",
                expected_roi: `${(results.metrics.roi_pct || 0).toFixed(0)}%`,
                win_rate: `${(results.metrics.win_rate || 0).toFixed(0)}%`,
                frequency: "Day Trader"
            });

            toast.success('Agent Launched!', { id: toastId });
            setIsPersonaModalOpen(false);
            navigate('/strategies');

        } catch (err: any) {
            toast.error('Failed to create agent: ' + err.message, { id: toastId });
        }
    };

    // ... (chartData logic remains same)
    const chartData = results?.curve || [];

    // ... (CustomTooltip remains same)
    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-[#1e293b] border border-slate-700 p-3 rounded shadow-xl">
                    <p className="text-slate-400 text-xs mb-1">{label}</p>
                    {payload.map((p: any, idx: number) => (
                        <p key={idx} style={{ color: p.color }} className="text-sm font-mono">
                            {p.name}: ${Number(p.value).toFixed(2)}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="p-6 space-y-8 min-h-screen bg-[#020617] text-slate-100 animate-fade-in">

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="px-2 py-0.5 rounded text-xs font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">BETA</span>
                    </div>
                    <h1 className="text-3xl font-black bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-fuchsia-400 tracking-tight">
                        Strategy Lab 🧪
                    </h1>
                    <p className="text-slate-400 mt-2 max-w-2xl">
                        Experiment with different strategies, tokens, and timeframes.
                        Validating a profitable configuration? Create a customized Persona from it.
                    </p>
                </div>
            </div>

            {/* Controls */}
            <div className="bg-[#0f172a] p-6 rounded-2xl border border-slate-800 shadow-xl backdrop-blur-sm">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
                    {/* ... (Selects remain same, just styling tweaks if needed) ... */}
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Strategy</label>
                        <select
                            className="w-full bg-[#1e293b] border border-slate-700 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                            value={params.strategy}
                            onChange={(e) => setParams({ ...params, strategy: e.target.value })}
                        >
                            <option value="rsi_divergence">RSI Divergence AI</option>
                            <option value="ma_cross">Trend MA Cross</option>
                            <option value="bb_mean_reversion">Bollinger Mean Rev</option>
                            <option value="donchian">Donchian Breakout</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Token</label>
                        <select
                            className="w-full bg-[#1e293b] border border-slate-700 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                            value={params.token}
                            onChange={(e) => setParams({ ...params, token: e.target.value })}
                        >
                            <option value="BTC">Bitcoin (BTC)</option>
                            <option value="ETH">Ethereum (ETH)</option>
                            <option value="SOL">Solana (SOL)</option>
                            <option value="XRP">XRP (XRP)</option>
                            <option value="BNB">Binance Coin (BNB)</option>
                            <option value="DOGE">Dogecoin (DOGE)</option>
                            <option value="ADA">Cardano (ADA)</option>
                            <option value="AVAX">Avalanche (AVAX)</option>
                            <option value="DOT">Polkadot (DOT)</option>
                            <option value="LINK">Chainlink (LINK)</option>
                            <option value="LTC">Litecoin (LTC)</option>
                            <option value="MATIC">Polygon (MATIC)</option>
                            <option value="UNI">Uniswap (UNI)</option>
                            <option value="ATOM">Cosmos (ATOM)</option>
                            <option value="NEAR">Near Protocol (NEAR)</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Timeframe</label>
                        <select
                            className="w-full bg-[#1e293b] border border-slate-700 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                            value={params.timeframe}
                            onChange={(e) => setParams({ ...params, timeframe: e.target.value })}
                        >
                            <option value="15m">15 Minutes (Scalp)</option>
                            <option value="1h">1 Hour (Intraday)</option>
                            <option value="4h">4 Hours (Swing)</option>
                            <option value="1d">1 Day (Position)</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">History Length</label>
                        <select
                            className="w-full bg-[#1e293b] border border-slate-700 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                            value={params.days}
                            onChange={(e) => setParams({ ...params, days: Number(e.target.value) })}
                        >
                            <option value={7}>7 Days (Fast)</option>
                            <option value={30}>30 Days (Standard)</option>
                            <option value={90}>90 Days (Deep)</option>
                        </select>
                    </div>

                    <button
                        onClick={runBacktest}
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold py-2.5 px-4 rounded-lg transition-all flex items-center justify-center gap-2 shadow-lg hover:shadow-indigo-500/25 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <Clock className="animate-spin h-5 w-5" />
                        ) : (
                            <Play className="h-5 w-5" />
                        )}
                        {loading ? 'Simulating...' : 'Run Experiment'}
                    </button>
                </div>
                {error && <p className="text-rose-400 mt-4 text-sm bg-rose-950/30 p-3 rounded-lg border border-rose-900 flex items-center gap-2"><Info className="w-4 h-4" />{error}</p>}
            </div>

            {/* Results View */}
            {results && results.metrics && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

                    {/* Performance Summary Banner */}
                    <div className={`p-4 rounded-xl border flex flex-col md:flex-row items-center justify-between gap-4 ${results.metrics.total_pnl > results.metrics.buy_hold_pnl
                        ? 'bg-green-900/10 border-green-900/50'
                        : 'bg-red-900/10 border-red-900/50'
                        }`}>
                        <div className="flex items-center gap-4">
                            <div className={`p-3 rounded-full ${results.metrics.total_pnl > results.metrics.buy_hold_pnl ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                                }`}>
                                {results.metrics.total_pnl > results.metrics.buy_hold_pnl ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
                            </div>
                            <div>
                                <h3 className="font-bold text-lg text-slate-200">
                                    {results.metrics.total_pnl > results.metrics.buy_hold_pnl ? 'Strategy Outperforms Market' : 'Strategy Underperforms Market'}
                                </h3>
                                <p className="text-slate-400 text-sm">
                                    Alpha: <span className="font-mono font-bold text-slate-200">
                                        ${(results.metrics.total_pnl - results.metrics.buy_hold_pnl).toFixed(2)}
                                    </span> vs Buy & Hold
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-6">
                            <div className="text-right">
                                <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Net Result</span>
                                <p className={`text-3xl font-bold ${results.metrics.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {results.metrics.total_pnl >= 0 ? '+' : ''}{results.metrics.total_pnl} USD
                                </p>
                            </div>

                            {/* Create Persona Intent */}
                            {results.metrics.total_pnl > 0 && (
                                <button
                                    onClick={() => setIsPersonaModalOpen(true)}
                                    className="bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold px-4 py-2 rounded-lg border border-slate-700 transition-all flex flex-col items-center gap-1 group"
                                >
                                    <span className="group-hover:text-indigo-400 transition-colors">SAVE AS AGENT</span>
                                    <span className="text-[10px] text-slate-500 font-normal">Add to Marketplace</span>
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Detailed Metrics Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800">
                            <p className="text-slate-500 text-xs uppercase mb-1">Buy & Hold PnL</p>
                            <p className="text-xl font-mono text-slate-300">
                                {results.metrics.buy_hold_pnl >= 0 ? '+' : ''}{results.metrics.buy_hold_pnl} USD
                            </p>
                            <p className="text-[10px] text-slate-500 mt-1">If you just held the token</p>
                        </div>
                        <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800">
                            <p className="text-slate-500 text-xs uppercase mb-1">Win Rate</p>
                            <p className="text-xl font-bold text-indigo-400">{results.metrics.win_rate}%</p>
                            <p className="text-[10px] text-slate-500 mt-1">{results.metrics.total_trades} Trades Executed</p>
                        </div>
                        <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800">
                            <p className="text-slate-500 text-xs uppercase mb-1">Best Trade</p>
                            <p className="text-xl font-bold text-green-400">+{results.metrics.best_trade} USD</p>
                        </div>
                        <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800">
                            <p className="text-slate-500 text-xs uppercase mb-1">Worst Trade</p>
                            <p className="text-xl font-bold text-red-400">{results.metrics.worst_trade} USD</p>
                        </div>
                    </div>

                    {/* Chart */}
                    <div className="bg-[#0f172a] p-6 rounded-xl border border-slate-800 h-[450px]">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold flex items-center gap-2">
                                <TrendingUp className="h-5 w-5 text-indigo-400" /> Comparativa de Equity
                            </h3>
                            <div className="flex gap-4 text-xs">
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full bg-[#818cf8]"></div>
                                    <span className="text-slate-300 font-bold">Tu Estrategia</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full bg-[#64748b]"></div>
                                    <span className="text-slate-400">Mercado (Buy & Hold)</span>
                                </div>
                            </div>
                        </div>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                <XAxis
                                    dataKey="time"
                                    stroke="#64748b"
                                    tick={{ fontSize: 12 }}
                                    minTickGap={50}
                                    tickFormatter={(val) => {
                                        // "time" is now "YYYY-MM-DD HH:mm"
                                        try {
                                            if (params.days > 2) {
                                                // Return MM-DD
                                                // Assuming val is "YYYY-MM-DD HH:mm"
                                                if (val.includes('-')) {
                                                    const datePart = val.split(' ')[0];
                                                    const parts = datePart.split('-');
                                                    if (parts.length === 3) {
                                                        return `${parts[2]}/${parts[1]}`; // DD/MM
                                                    }
                                                }
                                            }
                                            // Fallback or short duration: Show HH:mm
                                            if (val.includes(' ')) return val.split(' ')[1];
                                            return val;
                                        } catch (e) {
                                            return val;
                                        }
                                    }}
                                />
                                <YAxis stroke="#64748b" domain={['auto', 'auto']} />
                                <Tooltip content={<CustomTooltip />} />
                                <Line
                                    name="Strategy Equity"
                                    type="monotone"
                                    dataKey="strategy_equity"
                                    stroke="#818cf8"
                                    strokeWidth={3}
                                    dot={false}
                                    activeDot={{ r: 6, strokeWidth: 0 }}
                                />
                                <Line
                                    name="Buy & Hold"
                                    type="monotone"
                                    dataKey="buy_hold_equity"
                                    stroke="#64748b"
                                    strokeWidth={2}
                                    strokeDasharray="5 5"
                                    dot={false}
                                    opacity={0.6}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Trades Table */}
                    <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-hidden">
                        <div className="p-4 border-b border-slate-800 flex justify-between items-center">
                            <h3 className="text-lg font-semibold">Historial de Trades</h3>
                            <span className="text-xs text-slate-500 bg-slate-900 px-2 py-1 rounded">Last 50</span>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm text-slate-400">
                                <thead className="bg-[#1e293b] text-slate-200">
                                    <tr>
                                        <th className="p-3 w-16">#</th>
                                        <th className="p-3">In</th>
                                        <th className="p-3">Out</th>
                                        <th className="p-3">Type</th>
                                        <th className="p-3">Entry</th>
                                        <th className="p-3">Exit</th>
                                        <th className="p-3">Reason</th>
                                        <th className="p-3 text-right">PnL</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800">
                                    {[...results.trades].reverse().map((t: any) => (
                                        <tr key={t.id} className="hover:bg-[#1e293b]/50 transition-colors">
                                            <td className="p-3">#{t.id}</td>
                                            <td className="p-3 text-slate-300 font-mono text-xs">{t.entry_time}</td>
                                            <td className="p-3 text-slate-300 font-mono text-xs">{t.exit_time}</td>
                                            <td className="p-3">
                                                <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${t.type === 'LONG' ? 'bg-green-900/30 text-green-400 border border-green-900/50' : 'bg-red-900/30 text-red-400 border border-red-900/50'
                                                    }`}>
                                                    {t.type}
                                                </span>
                                            </td>
                                            <td className="p-3">${t.entry}</td>
                                            <td className="p-3">${t.exit}</td>
                                            <td className="p-3">
                                                <span className="text-xs bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
                                                    {t.reason}
                                                </span>
                                            </td>
                                            <td className={`p-3 text-right font-mono font-bold ${t.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                {t.pnl >= 0 ? '+' : ''}{t.pnl}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {/* Persona Creation Modal */}
                        {isPersonaModalOpen && (
                            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                                <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-md w-full p-6 shadow-2xl animate-in fade-in zoom-in duration-200">
                                    <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                                        <span className="text-2xl">🧬</span> Create New Agent
                                    </h2>

                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Agent Name</label>
                                            <input
                                                type="text"
                                                value={personaName}
                                                onChange={(e) => setPersonaName(e.target.value)}
                                                placeholder="e.g. Solana Trend Hunter"
                                                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Description</label>
                                            <textarea
                                                value={personaDesc}
                                                onChange={(e) => setPersonaDesc(e.target.value)}
                                                placeholder="What does this agent do? e.g. Aggressively trades breakouts on 1H timeframe."
                                                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500 transition-colors h-24 resize-none"
                                            />
                                        </div>

                                        <div className="p-3 bg-indigo-900/10 border border-indigo-900/30 rounded-lg">
                                            <h4 className="text-xs font-bold text-indigo-400 mb-2 uppercase">Stats to Publish</h4>
                                            <div className="grid grid-cols-2 gap-2 text-xs">
                                                <div className="flex justify-between">
                                                    <span className="text-slate-500">ROI:</span>
                                                    <span className="text-green-400 font-mono">+{results?.metrics?.roi_pct != null ? Number(results.metrics.roi_pct).toFixed(2) : '0.00'}%</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-slate-500">Win Rate:</span>
                                                    <span className="text-indigo-400 font-mono">{results?.metrics?.win_rate != null ? Number(results.metrics.win_rate).toFixed(1) : '0.0'}%</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-slate-500">Token:</span>
                                                    <span className="text-slate-300">{params.token.toUpperCase()}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-slate-500">Timeframe:</span>
                                                    <span className="text-slate-300">{params.timeframe}</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex gap-3 mt-6">
                                            <button
                                                onClick={() => setIsPersonaModalOpen(false)}
                                                className="flex-1 bg-slate-800 hover:bg-slate-700 text-white font-semibold py-2 rounded-lg transition-colors"
                                            >
                                                Cancel
                                            </button>
                                            <button
                                                onClick={handleCreatePersona}
                                                disabled={!personaName}
                                                className="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold py-2 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-900/20"
                                            >
                                                Launch Agent 🚀
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
