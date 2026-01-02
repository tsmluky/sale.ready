import React, { useEffect, useState } from 'react';
import { DashboardHistory } from '../components/dashboard/DashboardHistory';
import { api } from '../services/api';
import { Loader2 } from 'lucide-react';
import { TacticalAnalysisDrawer } from '../components/scanner/TacticalAnalysisDrawer';

export const HistoryPage: React.FC = () => {
    const [signals, setSignals] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedSignal, setSelectedSignal] = useState(null);

    useEffect(() => {
        const fetchHistory = async () => {
            setLoading(true);
            try {
                // Fetch more signals for history view, e.g., 50
                const data = await api.getRecentSignals(50, false, true);
                setSignals(data);
            } catch (error) {
                console.error("Failed to fetch history", error);
            } finally {
                setLoading(false);
            }
        };

        fetchHistory();
    }, []);

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white tracking-tight">Signal History</h1>
                <p className="text-slate-400 mt-2">Comprehensive log of all system activity and signal evaluations.</p>
            </div>

            {loading ? (
                <div className="flex justify-center items-center h-64">
                    <Loader2 className="animate-spin text-brand-500" size={32} />
                </div>
            ) : (
                <DashboardHistory
                    signals={signals}
                    onSignalClick={(sig) => setSelectedSignal(sig)}
                />
            )}

            {selectedSignal && (
                <TacticalAnalysisDrawer
                    isOpen={!!selectedSignal}
                    onClose={() => setSelectedSignal(null)}
                    signal={selectedSignal}
                />
            )}
        </div>
    );
};
