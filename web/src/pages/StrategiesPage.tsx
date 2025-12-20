import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Play, TrendingUp, Zap, Shield, Activity, RefreshCw, Power } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface Persona {
    id: string;
    name: string;
    symbol: string;
    timeframe: string;
    description: string;
    risk_level: string;
    expected_roi: string;
    win_rate: string;
    frequency: string;
    color: string;
    is_active: boolean;
}

export const StrategiesPage: React.FC = () => {
    const navigate = useNavigate();
    const [personas, setPersonas] = useState<Persona[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchPersonas = async () => {
        setLoading(true);
        try {
            const data = await api.fetchMarketplace();
            setPersonas(data);
        } catch (error) {
            console.error(error);
            toast.error("Failed to load marketplace");
        } finally {
            setLoading(false);
        }
    };

    const handleToggle = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await api.togglePersona(id);
            toast.success("Strategy status updated");
            fetchPersonas(); // Refresh UI
        } catch (error) {
            console.error(error);
            toast.error("Failed to toggle strategy");
        }
    };

    useEffect(() => {
        fetchPersonas();
    }, []);

    const getColorClass = (color: string) => {
        const map: any = {
            'amber': 'from-amber-500/20 to-orange-600/20 border-amber-500/50 text-amber-500',
            'cyan': 'from-cyan-500/20 to-blue-600/20 border-cyan-500/50 text-cyan-500',
            'slate': 'from-slate-500/20 to-gray-600/20 border-slate-500/50 text-slate-400',
            'indigo': 'from-indigo-500/20 to-violet-600/20 border-indigo-500/50 text-indigo-500',
        };
        return map[color] || map['slate'];
    };

    return (
        <div className="space-y-8 animate-fade-in relative min-h-screen">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-4xl font-black bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400 tracking-tight">
                        Quant Strategies
                    </h1>
                    <p className="text-slate-400 mt-2 text-lg">
                        Deploy autonomous trading agents. Each model runs independently with distinct alpha profiles.
                    </p>
                </div>
                <button
                    onClick={fetchPersonas}
                    className="p-3 bg-slate-800/50 hover:bg-slate-700 rounded-xl transition-all border border-slate-700/50 hover:border-indigo-500/50 group"
                >
                    <RefreshCw className={`w-5 h-5 text-slate-400 group-hover:text-white transition-colors ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-6">
                {personas.map((persona) => {
                    const theme = getColorClass(persona.color);
                    const activeClass = persona.is_active ? '' : 'opacity-60 grayscale-[0.5]';

                    return (
                        <div
                            key={persona.id}
                            className={`group relative bg-slate-900/40 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 hover:border-slate-600 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1 overflow-hidden cursor-pointer ${activeClass}`}
                            onClick={() => navigate(`/strategies/${persona.id}`)}
                        >
                            {/* Background Glow */}
                            <div className={`absolute -inset-0.5 bg-gradient-to-br ${theme.split(' ')[0]} opacity-0 group-hover:opacity-20 transition-opacity blur-2xl`} />

                            {/* Header */}
                            <div className="flex justify-between items-start mb-4 relative z-10">
                                <div>
                                    <h3 className={`text-xl font-black text-white tracking-wide flex items-center gap-2`}>
                                        {persona.name}
                                        {!persona.is_active && (
                                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-500 border border-slate-700">PAUSED</span>
                                        )}
                                    </h3>
                                    <div className="flex items-center gap-2 mt-1">
                                        <span className={`px-2 py-0.5 rounded text-xs font-bold bg-slate-800 border ${theme.split(' ')[2]} ${theme.split(' ')[3]}`}>
                                            {persona.symbol}
                                        </span>
                                        <span className="text-xs text-slate-500 font-mono uppercase">
                                            {persona.timeframe}
                                        </span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={(e) => handleToggle(persona.id, e)}
                                        className={`p-2 rounded-lg transition-all ${persona.is_active ? 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20' : 'bg-slate-800 text-slate-500 hover:text-slate-300'}`}
                                        title={persona.is_active ? "Pause Strategy" : "Resume Strategy"}
                                    >
                                        <Power className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>

                            {/* Description */}
                            <p className="text-slate-400 text-sm mb-6 h-10 line-clamp-2 relative z-10">
                                {persona.description}
                            </p>

                            {/* Stats Grid */}
                            <div className="grid grid-cols-2 gap-3 mb-6 relative z-10">
                                <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800">
                                    <span className="text-xs text-slate-500 block mb-1">Expected ROI</span>
                                    <span className={`text-xl font-bold ${theme.split(' ')[3]}`}>{persona.expected_roi}</span>
                                </div>
                                <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800">
                                    <span className="text-xs text-slate-500 block mb-1">Win Rate</span>
                                    <span className="text-xl font-bold text-white">{persona.win_rate}</span>
                                </div>
                            </div>

                            {/* Action Button */}
                            <button
                                className={`w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-slate-800 to-slate-900 border border-slate-700 hover:border-${persona.color}-500 group-hover:from-${persona.color}-900/50 group-hover:to-${persona.color}-800/50 transition-all flex items-center justify-center gap-2 relative z-10`}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    navigate(`/strategies/${persona.id}`);
                                }}
                            >
                                <span className={persona.is_active ? 'text-emerald-400' : 'text-slate-500'}>
                                    VIEW MODEL LOGIC
                                </span>
                            </button>
                        </div>
                    );
                })}
            </div>

            {/* Disclaimer */}
            <div className="mt-12 p-6 bg-slate-900/30 border border-slate-800/50 rounded-xl text-center max-w-2xl mx-auto">
                <p className="text-xs text-slate-500">
                    Past performance is not indicative of future results. All strategies run autonomously based on technical validation.
                    Scalping strategies may be affected by market volatility and spread costs.
                </p>
            </div>
        </div>
    );
};
