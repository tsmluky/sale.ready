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
        <div className="flex h-screen bg-[#020617] text-slate-200 overflow-hidden font-sans relative selection:bg-indigo-500/30">
            {/* Aurora Background Effects - Global */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[120px] animate-pulse-slow"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 rounded-full blur-[120px] animate-pulse-slow delay-1000"></div>
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
        fixed lg:static inset-y-0 left-0 z-50 w-64 bg-[#020617] border-r border-slate-800/50
        transform transition-transform duration-300 ease-in-out
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
                <div className="h-full flex flex-col">
                    {/* Logo Area */}
                    <div className="h-16 flex items-center px-6 border-b border-slate-800/50">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                                {/* Use Logo URL if available, else generic Icon */}
                                {theme.logoUrl && theme.logoUrl.startsWith('http') ? (
                                    <img src={theme.logoUrl} alt="Logo" className="w-5 h-5" />
                                ) : (
                                    <Activity className="w-5 h-5 text-indigo-400" />
                                )}
                            </div>
                            <span className="font-bold text-lg tracking-tight text-slate-100">
                                {theme.appName}
                            </span>
                        </div>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-3 py-6 space-y-1">
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
                    w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
                    ${isActive
                                            ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/10'
                                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'}
                  `}
                                >
                                    <Icon className={`w-5 h-5 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                                    {item.label}
                                </button>
                            );
                        })}
                    </nav>

                    {/* User Footer */}
                    <div className="p-4 border-t border-slate-800/50">
                        <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-900/50 border border-slate-800/50 mb-3">
                            <div
                                className="flex items-center gap-3 text-left opacity-90 hover:opacity-100 transition-opacity cursor-default"
                            >
                                <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-xs border border-indigo-500/30">
                                    {user?.name?.substring(0, 2).toUpperCase() || 'ME'}
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-xs font-medium text-slate-300">{user?.name || 'Trader'}</span>
                                    <span className="text-[10px] text-slate-500">{user?.plan ? `${user.plan} Plan` : 'Free Plan'}</span>
                                </div>
                            </div>
                            <button onClick={logout} className="text-slate-500 hover:text-rose-400 transition-colors">
                                <LogOut className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="flex items-center gap-2 justify-center">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                            <span className="text-[10px] text-slate-500 font-mono">SYSTEM ONLINE</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
                {/* Background Gradient Mesh */}
                <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-indigo-900/10 to-transparent pointer-events-none" />


                {/* Header */}
                <header className="h-16 flex items-center justify-between px-6 border-b border-slate-800/50 bg-[#020617]/80 backdrop-blur-md z-30 sticky top-0">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setIsSidebarOpen(true)}
                            className="lg:hidden p-2 -ml-2 text-slate-400 hover:text-slate-200"
                        >
                            <Menu className="w-6 h-6" />
                        </button>

                        <h1 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                            {activeItem.label}
                        </h1>
                    </div>

                    {/* Top Bar Stats */}
                    <div className="flex items-center gap-4">
                        {/* Market Ticker */}
                        <div className="hidden md:flex items-center gap-6 text-sm bg-slate-900/50 px-4 py-1.5 rounded-full border border-slate-800/50 max-w-xl overflow-hidden relative group">
                            {/* FADE MASKS */}
                            <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-slate-900/90 to-transparent z-10 pointer-events-none"></div>
                            <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-slate-900/90 to-transparent z-10 pointer-events-none"></div>

                            <div className="flex items-center gap-6 animate-marquee whitespace-nowrap hover:pause">
                                {prices.length === 0 ? (
                                    <span className="text-slate-500 text-xs">Loading market data...</span>
                                ) : (
                                    [...prices, ...prices].map((p, i) => (
                                        <div key={`${p.symbol}-${i}`} className="flex items-center gap-2 min-w-max">
                                            <span className="text-slate-500 font-medium">{p.symbol}</span>
                                            <span className="font-mono text-slate-200">${p.price < 1 ? p.price.toFixed(4) : p.price.toFixed(2)}</span>
                                            <span className={`text-xs font-medium ${p.change_24h >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                {p.change_24h >= 0 ? '+' : ''}{p.change_24h.toFixed(2)}%
                                            </span>
                                            {/* Divider */}
                                            <div className="w-px h-3 bg-slate-700/50 mx-2"></div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Notification Center */}
                        <div className="pl-4 border-l border-slate-800/50">
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
