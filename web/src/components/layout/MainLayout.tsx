import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    LineChart,
    Zap,
    Radar, // Added Radar
    Settings,
    Menu,
    Activity,
    Terminal,
    LogOut,
    FlaskConical,
    Crosshair
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { NotificationCenter } from '../NotificationCenter';
import { API_BASE_URL } from '../../constants';
import { AdvisorChat } from '../AdvisorChat';
import { TutorialOverlay } from '../tutorial/TutorialOverlay';


import { useTheme } from '../../context/ThemeContext';

interface MainLayoutProps {
    children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
    const { theme } = useTheme(); // Theme Hook
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [prices, setPrices] = useState<any[]>([]);
    const navigate = useNavigate();
    const location = useLocation();
    const { logout, userProfile } = useAuth();
    const user = userProfile?.user;

    // Fetch Market Summary
    useEffect(() => {
        const fetchPrices = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/market/summary`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.current_prices) {
                        setPrices(data.current_prices);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch market summary", error);
            }
        };

        fetchPrices();
        const interval = setInterval(fetchPrices, 30000); // Update every 30s
        return () => clearInterval(interval);

    }, []);

    const navItems = [
        { id: '/', label: 'Overview', icon: LayoutDashboard },
        { id: '/scanner', label: 'Radar', icon: Radar },
        { id: '/analysis', label: 'Analyst', icon: Crosshair },
        { id: '/strategies', label: 'Quant', icon: Activity },
        { id: '/backtest', label: 'Backtest', icon: FlaskConical },
        { id: '/pricing', label: 'Membership', icon: Zap },
        { id: '/settings', label: 'Settings', icon: Settings },
    ];

    // Add Admin Link if Owner/Admin
    if (user?.role === 'admin' || user?.plan === 'OWNER') {
        navItems.push({ id: '/admin', label: 'Admin Panel', icon: Terminal }); // Using Terminal icon or Shield if imported
    }

    const activeItem = navItems.find(item => location.pathname === item.id) || navItems[0];

    return (
        <div className="flex h-screen bg-[#020617] text-slate-200 overflow-hidden font-sans relative selection:bg-brand-500/30">
            {/* Global Background Ambience - Obsidian Theme */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute inset-0 bg-grid opacity-[0.03]" />
                <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-brand-500/5 rounded-full blur-[150px] animate-pulse-slow" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-gold-500/5 rounded-full blur-[150px] animate-pulse-slow delay-1000" />
            </div>
            <TutorialOverlay />

            {/* Mobile Sidebar Overlay */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden backdrop-blur-sm"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={`
        fixed lg:static inset-y-0 left-0 z-50 w-72 bg-[#020617]/80 backdrop-blur-xl border-r border-white/5
        transform transition-transform duration-300 ease-in-out
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
                <div className="h-full flex flex-col relative overflow-hidden">
                    {/* Sidebar Light Glow */}
                    <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-brand-500/5 to-transparent pointer-events-none" />

                    {/* Logo Area */}
                    <div className="h-20 flex items-center px-6 border-b border-white/5 relative z-10">
                        <div className="flex items-center gap-3 group cursor-pointer">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white shadow-lg shadow-brand-500/20 group-hover:shadow-brand-500/40 transition-all">
                                {/* Use Logo URL if available, else generic Icon */}
                                {theme.logoUrl && theme.logoUrl.startsWith('http') ? (
                                    <img src={theme.logoUrl} alt="Logo" className="w-6 h-6" />
                                ) : (
                                    <Zap className="w-5 h-5 fill-white" />
                                )}
                            </div>
                            <div className="flex flex-col">
                                <span className="font-black text-lg tracking-tight text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-brand-200 transition-all">
                                    {theme.appName}
                                </span>
                                <span className="text-[10px] text-brand-400 font-bold tracking-widest uppercase">Copilot Console</span>
                            </div>
                        </div>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-4 py-8 space-y-1.5 relative z-10 overflow-y-auto custom-scrollbar">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = location.pathname === item.id;

                            return (
                                <button
                                    key={item.id}
                                    id={`nav-${item.label.toLowerCase().replace(' ', '-')}`} // Added ID for Tutorial Highlight
                                    onClick={() => {
                                        console.log(`[NAV] Clicked: ${item.label} (${item.id})`);
                                        navigate(item.id);
                                        setIsSidebarOpen(false);
                                    }}
                                    className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all duration-300 group
                    ${isActive
                                            ? 'bg-gradient-to-r from-brand-500/20 to-brand-500/5 text-white border border-brand-500/20 shadow-[0_0_15px_-3px_rgba(99,102,241,0.2)]'
                                            : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'}
                  `}
                                >
                                    <Icon className={`w-5 h-5 transition-colors ${isActive ? 'text-brand-400' : 'text-slate-500 group-hover:text-brand-300'}`} />
                                    {item.label}
                                    {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-400 shadow-[0_0_8px_rgba(99,102,241,0.6)] animate-pulse" />}
                                </button>
                            );
                        })}
                    </nav>

                    {/* User Footer */}
                    <div className="p-4 border-t border-white/5 relative z-10">
                        <div className="flex items-center justify-between px-3 py-3 rounded-xl bg-white/5 border border-white/5 mb-3 hover:bg-white/10 transition-colors group">
                            <div
                                className="flex items-center gap-3 text-left cursor-default"
                            >
                                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-500 to-indigo-600 flex items-center justify-center text-white font-black text-xs border border-white/10 shadow-lg">
                                    {user?.name?.substring(0, 2).toUpperCase() || 'ME'}
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-sm font-bold text-white group-hover:text-brand-300 transition-colors">{user?.name || 'Trader'}</span>
                                    <span className="text-[10px] text-slate-400 font-medium bg-black/40 px-1.5 py-0.5 rounded inline-block w-fit mt-0.5 border border-white/5">
                                        {user?.plan ? `${user.plan}` : 'FREE'} PLAN
                                    </span>
                                </div>
                            </div>
                            <button onClick={logout} className="p-2 text-slate-500 hover:text-white hover:bg-rose-500/20 hover:border-rose-500/30 border border-transparent rounded-lg transition-all">
                                <LogOut className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="flex items-center gap-2 justify-center py-1">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                            <span className="text-[10px] text-emerald-400/80 font-bold tracking-widest font-mono">SYSTEM ONLINE</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
                {/* Background Gradient Mesh */}
                <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-indigo-900/10 to-transparent pointer-events-none" />


                {/* Header */}
                <header className="h-20 flex items-center justify-between px-8 border-b border-white/5 bg-[#020617]/50 backdrop-blur-md z-30 sticky top-0">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setIsSidebarOpen(true)}
                            className="lg:hidden p-2 -ml-2 text-slate-400 hover:text-white"
                        >
                            <Menu className="w-6 h-6" />
                        </button>

                        <h1 className="text-xl font-black text-white flex items-center gap-2 tracking-tight">
                            {activeItem.label}
                        </h1>
                    </div>

                    {/* Top Bar Stats */}
                    <div className="flex items-center gap-6">
                        {/* Market Ticker */}
                        <div className="hidden md:flex items-center gap-6 text-sm bg-white/5 px-5 py-2 rounded-full border border-white/5 max-w-xl overflow-hidden relative group hover:border-brand-500/20 transition-colors">
                            {/* FADE MASKS */}
                            <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-[#020617] to-transparent z-10 pointer-events-none"></div>
                            <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-[#020617] to-transparent z-10 pointer-events-none"></div>

                            <div className="flex items-center gap-6 animate-marquee whitespace-nowrap hover:pause">
                                {prices.length === 0 ? (
                                    <span className="text-slate-500 text-xs font-mono">Connecting to global markets...</span>
                                ) : (
                                    [...prices, ...prices].map((p, i) => (
                                        <div key={`${p.symbol}-${i}`} className="flex items-center gap-2 min-w-max">
                                            <span className="text-slate-400 font-bold text-xs">{p.symbol}</span>
                                            <span className="font-mono text-white font-bold text-xs">${p.price < 1 ? p.price.toFixed(4) : p.price.toFixed(2)}</span>
                                            <span className={`text-[10px] font-bold px-1 rounded ${p.change_24h >= 0 ? 'text-emerald-400 bg-emerald-400/10' : 'text-rose-400 bg-rose-400/10'}`}>
                                                {p.change_24h >= 0 ? '+' : ''}{p.change_24h.toFixed(2)}%
                                            </span>
                                            {/* Divider */}
                                            <div className="w-1 h-1 rounded-full bg-slate-800 mx-2"></div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Notification Center */}
                        <div className="pl-6 border-l border-white/5">
                            <NotificationCenter />
                        </div>
                    </div>
                </header>

                {/* Scrollable Content */}
                <main className="flex-1 overflow-y-auto overflow-x-hidden p-6 relative z-10 custom-scrollbar">
                    <div className="max-w-7xl mx-auto">
                        {children}
                    </div>
                </main>
            </div>

            {/* Global Advisor Chat - Hidden on Scanner Page to prevent overlap with Drawer */}
            {location.pathname !== '/scanner' && <AdvisorChat />}
        </div>
    );
};
