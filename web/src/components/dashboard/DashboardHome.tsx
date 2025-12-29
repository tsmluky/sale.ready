import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { StrategyCard } from './StrategyCard';
import { DashboardHistory } from './DashboardHistory';
import { Activity, DollarSign, Zap, RefreshCw, Target, Bot } from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { API_BASE_URL } from '../../constants';

import { MetricCard } from './MetricCard';
import { SignalDetailsModal, SignalHistory } from '../SignalDetailsModal';

export const DashboardHome: React.FC = () => {
    const [globalStats, setStats] = useState<any>({
        win_rate: 0,
        win_rate_change: 0,
        pnl_7d: 0,
        pnl_7d_change: 0,
        active_fleet: 6
    });
    const [strategies, setStrategies] = useState<any[]>([]);
    const [recentSignals, setRecentSignals] = useState<any[]>([]);
    const [selectedSignal, setSelectedSignal] = useState<SignalHistory | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const { userProfile } = useAuth();

    const fetchData = async () => {
        try {
            // 1. Fetch Stats
            const statsData = await api.get('/stats/summary');
            setStats(statsData);

            // 2. Fetch Active Strategies (Personas from Marketplace)
            const stratData = await api.get('/strategies/marketplace');
            setStrategies(stratData);

            // 3. Fetch Recent Signals (Now "Market Radar")
            const logsData = await api.get('/logs/recent?limit=20');
            setRecentSignals(logsData);
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleRefresh = () => {
        setRefreshing(true);
        fetchData();
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
            </div>
        );
    }



    const activeStrategies = strategies.filter(s => s.is_active);

    // Filter Feed: Show only Active Agents OR Followed Signals
    const filteredSignals = recentSignals.filter(sig => {
        // 1. Check if followed
        const isFollowed = userProfile?.portfolio?.followed_signals?.some(
            (f: any) => f.token === sig.token && f.timestamp === sig.timestamp
        );
        if (isFollowed) return true;

        // 2. Check if from Active Agent
        // sig.source should match strategy.strategy_id (e.g. "trend_king_v1")
        const isAgent = activeStrategies.some(strat =>
            strat.strategy_id === sig.source || strat.id === sig.source || strat.name === sig.source
        );
        if (isAgent) return true;

        // 3. Explicitly hide 'lite-rule' or 'manual' unless matched above
        if (sig.source === 'lite-rule' || sig.source?.includes('lite')) return false;

        // Default: Show others (System messages, etc)
        return true;
    });


    return (
        <div className="min-h-screen bg-[#020617] text-white selection:bg-gold-500/30 font-sans relative pb-16 animate-fade-in">
            {/* Background Texture & Lighting */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute inset-0 bg-grid opacity-20" />
                <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-brand-900/20 rounded-full blur-[120px] mix-blend-screen opacity-40"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-gold-500/5 blur-[120px] rounded-full mix-blend-screen opacity-30"></div>
            </div>

            {/* 1. Header & Global Metrics */}
            <div className="flex flex-col xl:flex-row gap-8 xl:items-center justify-between relative z-10 px-2">
                <div className="relative pl-6">
                    {/* Vertical Accent Line */}
                    <div className="absolute left-0 top-1 bottom-1 w-1.5 bg-gradient-to-b from-brand-400 to-indigo-600 rounded-full shadow-[0_0_15px_rgba(99,102,241,0.5)]"></div>

                    <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight mb-2 drop-shadow-md flex items-center gap-2">
                        Command <span className="text-brand-400">Center</span>
                    </h1>
                    <p className="text-slate-400 font-medium text-base max-w-lg leading-relaxed">
                        Real-time overview of your algorithmic fleet and market performance.
                    </p>
                </div>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 w-full xl:w-auto">
                    {/* Metric: PnL */}
                    <MetricCard
                        label="7d Net PnL"
                        value={`${globalStats?.pnl_7d > 0 ? '+' : ''}${globalStats?.pnl_7d || 0} R`}
                        trend={globalStats?.pnl_7d_change || 0}
                        icon={DollarSign}
                    />

                    {/* Metric: Active Agents */}
                    <MetricCard
                        label="Active Agents"
                        value={activeStrategies.length.toString()}
                        trend={0}
                        icon={Activity}
                    />

                    {/* Metric: Win Rate */}
                    <MetricCard
                        label="Win Rate (24h)"
                        value={`${globalStats?.win_rate || 0}%`}
                        trend={globalStats?.win_rate_change || 0}
                        icon={Target}
                    />

                    <button
                        onClick={handleRefresh}
                        className={`p-4 rounded-2xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 hover:border-brand-500/30 transition-all active:scale-95 flex items-center justify-center group shadow-lg`}
                    >
                        <RefreshCw size={24} className={refreshing ? 'animate-spin' : ''} />
                    </button>
                </div>
            </div>

            {/* Active Strategies Grid */}
            <div className="mb-8">
                <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                    <Activity className="text-gold-400" size={24} />
                    Active Agents
                </h2>
                {activeStrategies.length === 0 ? (
                    <div className="p-8 border border-dashed border-slate-800 rounded-xl bg-slate-900/50 text-center">
                        <p className="text-slate-500 mb-4">No agents are currently running.</p>
                        <a href="/strategies" className="text-indigo-400 hover:text-indigo-300 font-bold text-sm">Deploy an Agent from Marketplace &rarr;</a>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        {activeStrategies.map((strat, idx) => (
                            <Link to={`/strategies/${strat.id}`} key={strat.id || idx} className="block group">
                                <StrategyCard
                                    name={strat.name}
                                    timeframe={strat.timeframe}
                                    type={strat.symbol}
                                    winRate={parseInt(strat.win_rate) || 0}
                                    pnl={0} // TODO: Add per-strategy PnL in future
                                    status={'active'}
                                    description={strat.description}
                                    isCustom={strat.is_custom}
                                />
                            </Link>
                        ))}
                    </div>
                )}
            </div>

            {/* 3. Global History (Fleet Activity) */}
            {/* 3. Global History (Fleet Activity) */}
            <DashboardHistory
                signals={filteredSignals}
                onSignalClick={(sig) => setSelectedSignal(sig as SignalHistory)}
            />

            {/* Signal Details Modal */}
            {selectedSignal && (
                <SignalDetailsModal
                    signal={selectedSignal}
                    onClose={() => setSelectedSignal(null)}
                />
            )}
        </div>
    );
};
