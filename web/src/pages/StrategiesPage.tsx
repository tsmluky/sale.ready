"use client"

import type React from "react"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "../services/api"
import { Activity, RefreshCw, Power, ChevronRight, Target } from "lucide-react"
import { toast } from "react-hot-toast"
import { cn } from "../lib/utils"

interface Persona {
    id: string
    name: string
    symbol: string
    timeframe: string
    description: string
    risk_level: string
    expected_roi: string
    win_rate: string
    frequency: string
    color: string
    is_active: boolean
}

export const StrategiesPage: React.FC = () => {
    const navigate = useNavigate()
    const [personas, setPersonas] = useState<Persona[]>([])
    const [loading, setLoading] = useState(true)

    const fetchPersonas = async () => {
        setLoading(true)
        try {
            const data = await api.fetchMarketplace()
            setPersonas(data)
        } catch (error) {
            console.error(error)
            toast.error("Failed to load marketplace")
        } finally {
            setLoading(false)
        }
    }

    const handleToggle = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation()
        try {
            await api.togglePersona(id)
            toast.success("Strategy status updated")
            fetchPersonas()
        } catch (error) {
            console.error(error)
            toast.error("Failed to toggle strategy")
        }
    }

    useEffect(() => {
        fetchPersonas()
    }, [])

    const getColorClasses = (color: string) => {
        const map: Record<string, { gradient: string; border: string; text: string; bg: string }> = {
            amber: {
                gradient: "from-amber-500/20 to-orange-600/20",
                border: "border-amber-500/30",
                text: "text-amber-400",
                bg: "bg-amber-500/10",
            },
            cyan: {
                gradient: "from-cyan-500/20 to-blue-600/20",
                border: "border-cyan-500/30",
                text: "text-cyan-400",
                bg: "bg-cyan-500/10",
            },
            slate: {
                gradient: "from-slate-500/20 to-gray-600/20",
                border: "border-slate-500/30",
                text: "text-slate-400",
                bg: "bg-slate-500/10",
            },
            indigo: {
                gradient: "from-indigo-500/20 to-violet-600/20",
                border: "border-indigo-500/30",
                text: "text-indigo-400",
                bg: "bg-indigo-500/10",
            },
            emerald: {
                gradient: "from-emerald-500/20 to-green-600/20",
                border: "border-emerald-500/30",
                text: "text-emerald-400",
                bg: "bg-emerald-500/10",
            },
        }
        return map[color] || map.slate
    }

    return (
        <div className="min-h-screen bg-[#020617] text-white selection:bg-brand-500/30 overflow-x-hidden font-sans relative pb-20">
            {/* Background Effects */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:64px_64px] opacity-30" />
                <div className="absolute top-[-10%] left-[-10%] w-[700px] h-[700px] bg-brand-500/8 rounded-full blur-[150px] mix-blend-screen"></div>
                <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-indigo-600/5 blur-[120px] rounded-full mix-blend-screen"></div>
            </div>

            {/* Content */}
            <div className="relative z-10 max-w-7xl mx-auto px-6 py-8 lg:py-12">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
                    <div className="pl-6 relative">
                        <div className="absolute left-0 top-2 bottom-2 w-1 bg-gradient-to-b from-gold-400 to-orange-500 rounded-full shadow-[0_0_15px_rgba(251,191,36,0.5)]"></div>
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-gold-500/20 text-xs font-bold text-gold-400 mb-4 shadow-[0_0_15px_rgba(251,191,36,0.15)]">
                            <Activity size={12} />
                            Autonomous Agents
                        </div>
                        <h1 className="text-4xl lg:text-5xl font-bold tracking-tight leading-tight mb-3">
                            Quant{" "}
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-400 via-orange-400 to-gold-500 drop-shadow-sm">
                                Strategies
                            </span>
                        </h1>
                        <p className="text-slate-400 text-base font-light max-w-2xl">
                            Deploy autonomous trading agents. Each model runs independently with distinct alpha profiles and risk
                            parameters.
                        </p>
                    </div>
                    <button
                        onClick={fetchPersonas}
                        className="p-3.5 bg-white/5 hover:bg-white/10 rounded-xl transition-all border border-white/10 hover:border-brand-500/30 group shadow-lg active:scale-95"
                    >
                        <RefreshCw
                            className={cn(
                                "w-5 h-5 text-slate-400 group-hover:text-brand-400 transition-colors",
                                loading && "animate-spin text-brand-400",
                            )}
                        />
                    </button>
                </div>

                {/* Stats Bar */}
                <div className="mb-10 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="glass-card rounded-2xl p-5 border border-white/10 bg-[#0f172a]/70 backdrop-blur-xl">
                        <div className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Total Strategies</div>
                        <div className="text-3xl font-black text-white">{personas.length}</div>
                    </div>
                    <div className="glass-card rounded-2xl p-5 border border-white/10 bg-[#0f172a]/70 backdrop-blur-xl">
                        <div className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Active</div>
                        <div className="text-3xl font-black text-emerald-400">{personas.filter((p) => p.is_active).length}</div>
                    </div>
                    <div className="glass-card rounded-2xl p-5 border border-white/10 bg-[#0f172a]/70 backdrop-blur-xl">
                        <div className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Avg Win Rate</div>
                        <div className="text-3xl font-black text-gold-400">
                            {personas.length > 0
                                ? Math.round(
                                    personas.reduce((sum, p) => sum + Number.parseFloat(p.win_rate || "0"), 0) / personas.length,
                                )
                                : 0}
                            %
                        </div>
                    </div>
                    <div className="glass-card rounded-2xl p-5 border border-white/10 bg-[#0f172a]/70 backdrop-blur-xl">
                        <div className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Status</div>
                        <div className="flex items-center gap-2">
                            <div className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </div>
                            <span className="text-sm font-bold text-emerald-400">Live</span>
                        </div>
                    </div>
                </div>

                {/* Strategies Grid */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-6">
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                            <div key={i} className="h-80 bg-white/5 rounded-2xl animate-pulse"></div>
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-6 animate-in slide-in-from-bottom-5 duration-700">
                        {personas.map((persona) => {
                            const theme = getColorClasses(persona.color)
                            const activeClass = persona.is_active ? "" : "opacity-60 grayscale-[0.5]"

                            return (
                                <div
                                    key={persona.id}
                                    onClick={() => navigate(`/strategies/${persona.id}`)}
                                    className={cn("group relative cursor-pointer", activeClass)}
                                >
                                    <div
                                        className={cn(
                                            "absolute -inset-0.5 rounded-2xl blur-xl opacity-0 group-hover:opacity-60 transition-opacity duration-700 bg-gradient-to-br",
                                            theme.gradient,
                                        )}
                                    />

                                    <div className="relative glass-card rounded-2xl p-6 border border-white/10 bg-[#0f172a]/70 backdrop-blur-xl shadow-2xl overflow-hidden hover:border-white/20 transition-all duration-300 h-full flex flex-col">
                                        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                                        {/* Background Glow */}
                                        <div
                                            className={cn(
                                                "absolute -right-20 -top-20 w-64 h-64 rounded-full blur-[80px] opacity-0 group-hover:opacity-20 transition-all duration-500 pointer-events-none bg-gradient-to-br",
                                                theme.gradient,
                                            )}
                                        />

                                        {/* Header */}
                                        <div className="flex justify-between items-start mb-6 relative z-10">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <h3 className="text-xl font-black text-white tracking-wide">{persona.name}</h3>
                                                    {!persona.is_active && (
                                                        <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-slate-800 text-slate-500 border border-slate-700 uppercase tracking-wider">
                                                            Paused
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <span
                                                        className={cn(
                                                            "px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider border",
                                                            theme.bg,
                                                            theme.border,
                                                            theme.text,
                                                        )}
                                                    >
                                                        {persona.symbol ? persona.symbol.replace(/[[\]"']/g, "") : ""}
                                                    </span>
                                                    <span className="text-[10px] text-slate-500 font-mono uppercase font-bold">
                                                        {persona.timeframe ? persona.timeframe.replace(/[[\]"']/g, "") : ""}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Toggle */}
                                            <button
                                                onClick={(e) => handleToggle(persona.id, e)}
                                                className={cn(
                                                    "p-2 rounded-lg transition-all border",
                                                    persona.is_active
                                                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                                                        : "bg-slate-500/10 border-slate-500/30 text-slate-400 hover:bg-slate-500/20",
                                                )}
                                            >
                                                <Power size={16} />
                                            </button>
                                        </div>

                                        {/* Description */}
                                        <p className="text-sm text-slate-400 mb-6 leading-relaxed line-clamp-2 relative z-10">
                                            {persona.description}
                                        </p>

                                        {/* Metrics Grid */}
                                        <div className="grid grid-cols-2 gap-3 mb-6 relative z-10">
                                            <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                                                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-bold mb-1">
                                                    Win Rate
                                                </div>
                                                <div className={cn("text-lg font-black", theme.text)}>{persona.win_rate}</div>
                                            </div>
                                            <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                                                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-bold mb-1">
                                                    Expected ROI
                                                </div>
                                                <div className="text-lg font-black text-gold-400">{persona.expected_roi}</div>
                                            </div>
                                            <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                                                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-bold mb-1">Risk</div>
                                                <div className="text-lg font-black text-white">{persona.risk_level}</div>
                                            </div>
                                            <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                                                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-bold mb-1">
                                                    Frequency
                                                </div>
                                                <div className="text-lg font-black text-white">{persona.frequency}</div>
                                            </div>
                                        </div>

                                        {/* Footer */}
                                        <div className="mt-auto pt-4 border-t border-white/5 relative z-10">
                                            <div className="flex items-center justify-between">
                                                <span className="text-xs text-slate-500 font-mono">View Details</span>
                                                <ChevronRight
                                                    size={16}
                                                    className="text-slate-600 group-hover:text-brand-400 group-hover:translate-x-1 transition-all"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                )}

                {/* Empty State */}
                {!loading && personas.length === 0 && (
                    <div className="text-center py-20">
                        <div className="inline-flex p-6 rounded-2xl bg-white/5 border border-white/10 mb-6">
                            <Target className="text-slate-500" size={48} />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">No Strategies Available</h3>
                        <p className="text-slate-400 text-sm max-w-md mx-auto">
                            Check back later or contact support to enable strategies for your account.
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
}
