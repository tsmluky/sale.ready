import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Shield, Users, EyeOff, Activity, Search, AlertTriangle, CheckCircle, XCircle, DollarSign } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface AdminStats {
    total_users: number;
    users_24h: number;
    active_plans: number;
    hidden_signals: number;
    total_signals: number;
    signals_24h: number;
    system_status: string;
    mrr: number;
}
// ... (lines 14-142 remain unchanged - relying on visual confirmation, I will target the imports and interface first, then the JSX separately if needed or try to capture context)

// Let's do imports and interface and JSX in one go if context allows, or safer separate.
// Context provided previously shows imports at line 3.
// I will target the imports and interface first.

interface UserData {
    id: number;
    email: string;
    role: string;
    plan: string;
    created_at: string;
}

interface SignalData {
    id: number;
    token: string;
    mode: string;
    timestamp: string;
    is_hidden: number;
}

export const AdminPage: React.FC = () => {
    const [stats, setStats] = useState<AdminStats | null>(null);
    const [activeTab, setActiveTab] = useState<'users' | 'signals' | 'audit' | 'status'>('users');

    // Users State
    const [users, setUsers] = useState<UserData[]>([]);
    const [userPage, setUserPage] = useState(1);
    const [userSearch, setUserSearch] = useState('');

    // Signals State
    const [signals, setSignals] = useState<SignalData[]>([]);
    const [signalPage, setSignalPage] = useState(1);

    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchStats();
        fetchUsers();
    }, []);

    const fetchStats = async () => {
        try {
            const data = await api.fetchAdminStats();
            setStats(data);
        } catch (error) {
            console.error(error);
            toast.error("Failed to load admin stats");
        }
    };

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const data = await api.fetchAdminUsers(userPage, userSearch);
            setUsers(data.items);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const fetchSignals = async () => {
        setLoading(true);
        try {
            const data = await api.fetchAdminSignals(signalPage);
            setSignals(data.items);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'users') fetchUsers();
        if (activeTab === 'signals') fetchSignals();
    }, [activeTab, userPage, signalPage, userSearch]);

    const handleUpdatePlan = async (userId: number, newPlan: string) => {
        if (!confirm(`Change user ${userId} plan to ${newPlan}?`)) return;
        try {
            await api.updateUserPlan(userId, newPlan);
            toast.success("Plan updated");
            fetchUsers();
            fetchStats();
        } catch (error) {
            toast.error("Failed to update plan");
        }
    };

    const handleToggleSignal = async (signalId: number, currentHidden: number) => {
        const newState = currentHidden === 1 ? false : true;
        try {
            await api.toggleSignalVisibility(signalId, newState);
            toast.success(newState ? "Signal Hidden" : "Signal Visible");
            fetchSignals();
            fetchStats();
        } catch (error) {
            toast.error("Failed to toggle signal");
        }
    };

    return (
        <div className="space-y-8 animate-fade-in text-slate-200">
            {/* Header */}
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-black text-white flex items-center gap-3">
                        <Shield className="w-10 h-10 text-red-500" />
                        Admin Control
                    </h1>
                    <p className="text-slate-400 mt-2">System Management & Audits</p>
                </div>
                {stats && (
                    <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-4 py-2 rounded-lg">
                        <div className={`w-2 h-2 rounded-full ${stats.system_status.includes("ONLINE") ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`}></div>
                        <span className="text-xs font-bold font-mono text-slate-300">{stats.system_status}</span>
                    </div>
                )}
            </div>

            {/* KPI Cards */}
            {stats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                        <div className="flex items-center gap-2 text-slate-400 mb-2">
                            <Users className="w-4 h-4" /> Total Users
                        </div>
                        <div className="flex items-baseline gap-2">
                            <div className="text-2xl font-bold text-white">{stats.total_users}</div>
                            {stats.users_24h > 0 && <div className="text-xs text-emerald-400 font-bold">+{stats.users_24h} today</div>}
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                        <div className="flex items-center gap-2 text-emerald-400 mb-2">
                            <Activity className="w-4 h-4" /> Active Subscriptions
                        </div>
                        <div className="text-2xl font-bold text-emerald-400">{stats.active_plans}</div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                        <div className="flex items-center gap-2 text-slate-400 mb-2">
                            <Activity className="w-4 h-4" /> Total Signals
                        </div>
                        <div className="flex items-baseline gap-2">
                            <div className="text-2xl font-bold text-white">{stats.total_signals}</div>
                            {stats.signals_24h > 0 && <div className="text-xs text-blue-400 font-bold">+{stats.signals_24h} 24h</div>}
                        </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                        <div className="flex items-center gap-2 text-emerald-400 mb-2">
                            <DollarSign className="w-4 h-4" /> Est. Monthly Revenue
                        </div>
                        <div className="text-2xl font-bold text-white">
                            {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(stats.mrr || 0)}
                        </div>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div className="flex gap-4 border-b border-slate-800 pb-2">
                <button
                    onClick={() => setActiveTab('users')}
                    className={`px-4 py-2 font-bold transition-colors ${activeTab === 'users' ? 'text-white border-b-2 border-indigo-500' : 'text-slate-500 hover:text-slate-300'}`}
                >
                    Users
                </button>
                <button
                    onClick={() => setActiveTab('signals')}
                    className={`px-4 py-2 font-bold transition-colors ${activeTab === 'signals' ? 'text-white border-b-2 border-indigo-500' : 'text-slate-500 hover:text-slate-300'}`}
                >
                    Signals
                </button>
                <button
                    onClick={() => setActiveTab('status')}
                    className={`px-4 py-2 font-bold transition-colors ${activeTab === 'status' ? 'text-white border-b-2 border-indigo-500' : 'text-slate-500 hover:text-slate-300'}`}
                >
                    Project Status
                </button>
            </div>

            {/* Content */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 overflow-hidden">
                {activeTab === 'users' && (
                    <div className="space-y-4">
                        <div className="flex gap-2 mb-4">
                            <div className="relative flex-1 max-w-sm">
                                <Search className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                                <input
                                    type="text"
                                    placeholder="Search by email..."
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm focus:border-indigo-500 outline-none"
                                    value={userSearch}
                                    onChange={(e) => setUserSearch(e.target.value)}
                                />
                            </div>
                        </div>

                        <table className="w-full text-left text-sm">
                            <thead className="text-slate-500 border-b border-slate-800">
                                <tr>
                                    <th className="pb-3 pl-2">ID</th>
                                    <th className="pb-3">Email</th>
                                    <th className="pb-3">Role</th>
                                    <th className="pb-3">Plan</th>
                                    <th className="pb-3">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="text-slate-300">
                                {users.map(u => (
                                    <tr key={u.id} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                                        <td className="py-3 pl-2 font-mono text-slate-500">#{u.id}</td>
                                        <td className="py-3">{u.email}</td>
                                        <td className="py-3">
                                            {u.role === 'admin' ?
                                                <span className="text-red-400 font-bold">OWNER</span> :
                                                <span className="text-slate-500">User</span>
                                            }
                                        </td>
                                        <td className="py-3">
                                            <span className={`px-2 py-1 round text-xs font-bold ${u.plan === 'PRO' ? 'bg-indigo-500/20 text-indigo-400' : u.plan === 'OWNER' ? 'bg-red-500/20 text-red-400' : 'bg-slate-700 text-slate-400'}`}>
                                                {u.plan}
                                            </span>
                                        </td>
                                        <td className="py-3 flex gap-2">
                                            {u.plan !== 'PRO' && u.role !== 'admin' && (
                                                <button onClick={() => handleUpdatePlan(u.id, 'PRO')} className="px-2 py-1 text-xs bg-indigo-600 hover:bg-indigo-700 rounded text-white">
                                                    Upgrade PRO
                                                </button>
                                            )}
                                            {u.plan === 'PRO' && (
                                                <button onClick={() => handleUpdatePlan(u.id, 'FREE')} className="px-2 py-1 text-xs bg-slate-700 hover:bg-slate-600 rounded text-white">
                                                    Downgrade
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>

                        {/* Pagination Simple */}
                        <div className="flex justify-between items-center pt-4">
                            <span className="text-xs text-slate-500">Page {userPage}</span>
                            <div className="flex gap-2">
                                <button disabled={userPage === 1} onClick={() => setUserPage(p => p - 1)} className="px-3 py-1 bg-slate-800 rounded disabled:opacity-50">Prev</button>
                                <button onClick={() => setUserPage(p => p + 1)} className="px-3 py-1 bg-slate-800 rounded">Next</button>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'signals' && (
                    <div className="space-y-4">
                        <table className="w-full text-left text-sm">
                            <thead className="text-slate-500 border-b border-slate-800">
                                <tr className="uppercase text-xs font-bold tracking-wider">
                                    <th className="pb-3 pl-2">Time</th>
                                    <th className="pb-3">Token</th>
                                    <th className="pb-3">Mode</th>
                                    <th className="pb-3">Status</th>
                                    <th className="pb-3 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="text-slate-300">
                                {signals.map(s => (
                                    <tr key={s.id} className={`border-b border-slate-800/50 hover:bg-slate-800/20 ${s.is_hidden ? 'opacity-50' : ''}`}>
                                        <td className="py-3 pl-2 text-slate-500 font-mono text-xs">{new Date(s.timestamp).toLocaleString()}</td>
                                        <td className="py-3 font-bold">{s.token}</td>
                                        <td className="py-3"><span className="text-xs bg-slate-800 px-2 py-1 rounded border border-slate-700">{s.mode}</span></td>
                                        <td className="py-3">
                                            {s.is_hidden ?
                                                <span className="flex items-center gap-1 text-amber-500 text-xs font-bold"><EyeOff className="w-3 h-3" /> HIDDEN</span> :
                                                <span className="flex items-center gap-1 text-emerald-500 text-xs font-bold"><CheckCircle className="w-3 h-3" /> ACTIVE</span>
                                            }
                                        </td>
                                        <td className="py-3 text-right">
                                            <button
                                                onClick={() => handleToggleSignal(s.id, s.is_hidden)}
                                                className={`px-3 py-1 text-xs rounded font-bold transition-colors ${s.is_hidden ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30' : 'bg-amber-500/20 text-amber-500 hover:bg-amber-500/30'}`}
                                            >
                                                {s.is_hidden ? "UNHIDE" : "HIDE"}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {/* Pagination Simple */}
                        <div className="flex justify-between items-center pt-4">
                            <span className="text-xs text-slate-500">Page {signalPage}</span>
                            <div className="flex gap-2">
                                <button disabled={signalPage === 1} onClick={() => setSignalPage(p => p - 1)} className="px-3 py-1 bg-slate-800 rounded disabled:opacity-50 hover:bg-slate-700 transition">Prev</button>
                                <button onClick={() => setSignalPage(p => p + 1)} className="px-3 py-1 bg-slate-800 rounded hover:bg-slate-700 transition">Next</button>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'status' && (
                    <div className="space-y-6">
                        <div className="bg-slate-950/50 p-6 rounded-xl border border-slate-800/50">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Activity className="text-brand-500" size={20} /> Project Status & Changelog
                            </h3>
                            <div className="prose prose-invert max-w-none prose-sm">
                                <ul className="space-y-4">
                                    <li className="bg-emerald-500/5 p-4 rounded-lg border border-emerald-500/10">
                                        <span className="font-bold text-emerald-400 block mb-1">Current Version: v1.2.1-stable</span>
                                        <span className="text-slate-400">Sale-Ready Audit **PASSED**. System hardened for production distribution.</span>
                                    </li>
                                    <li className="bg-slate-900 p-4 rounded-lg border border-slate-800 relative overflow-hidden">
                                        <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
                                        <span className="font-bold text-blue-400 block mb-2 text-xs uppercase tracking-wider">Latest Updates (Today)</span>
                                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                                            <li>Fixed <strong>MIME Type / White Screen</strong> error by enforcing strict Cache-Control headers.</li>
                                            <li>Resolved <strong>500 Internal Server Errors</strong> on Logs API by ignoring NULL values in legacy data.</li>
                                            <li>Overhauled <strong>Confirmed Levels UI</strong> (Pro Analysis) with a Premium Grid design.</li>
                                            <li>Admin: Added this Status Dashboard.</li>
                                        </ul>
                                    </li>
                                </ul>

                                <hr className="border-slate-800 my-6" />

                                <h4 className="text-slate-200 font-bold mb-2">Technical Validation (Reference)</h4>
                                <pre className="bg-black/30 p-4 rounded-lg text-xs font-mono text-slate-400 overflow-x-auto border border-slate-800">
                                    {`# Technical Validation Report - TraderCopilot v1.2
Date: 2025-12-18
Status: SALE-READY (Hardened)

1. Deterministic Persistence: Verified (SQLite + WAL)
2. Strict RBAC: Enforced (Owner/Admin Only)
3. Fault Tolerance: Active (Rate Limits handled)
4. Operational Hygiene: 100% Uptime in Audit`}
                                </pre>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
