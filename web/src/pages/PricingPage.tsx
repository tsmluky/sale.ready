
import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Check, X, CreditCard, ShieldCheck, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

export const PricingPage: React.FC = () => {
    const { userProfile, upgradeSubscription } = useAuth();
    const normalizedPlan = (userProfile?.user.subscription_status || 'free').toLowerCase();
    const [processing, setProcessing] = useState<string | null>(null);

    const handleUpgrade = async (planId: string) => {
        if (normalizedPlan === planId) return;

        setProcessing(planId);
        const targetPlan = planId as 'free' | 'trader' | 'pro';

        try {
            await upgradeSubscription(targetPlan);
            toast.success(`Successfully switched to ${planId.toUpperCase()} plan`);
        } catch (error) {
            console.error("Upgrade failed:", error);
            toast.error("Failed to update subscription");
        } finally {
            setProcessing(null);
        }
    };

    const isPlanActive = (planId: string) => normalizedPlan === planId;

    return (
        <div className="relative z-10 max-w-7xl mx-auto px-4 md:px-6 py-8 lg:py-12 pb-20 min-h-screen">
            {/* Background Texture & Lighting */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute inset-0 bg-grid opacity-20" />
                <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-brand-500/10 rounded-full blur-[120px] mix-blend-screen opacity-50"></div>
                <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-gold-600/5 blur-[120px] rounded-full mix-blend-screen opacity-30"></div>
            </div>

            {/* Premium Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
                <div className="pl-6 relative">
                    <div className="absolute left-0 top-2 bottom-2 w-1 bg-gradient-to-b from-gold-400 to-orange-600 rounded-full shadow-[0_0_15px_rgba(251,191,36,0.5)]"></div>
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-gold-500/20 text-xs font-bold text-gold-400 mb-4 shadow-[0_0_15px_rgba(251,191,36,0.15)]">
                        <CreditCard size={12} />
                        Membership
                    </div>
                    <h1 className="text-4xl lg:text-5xl font-bold tracking-tight leading-tight mb-3">
                        Execution{" "}
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-400 via-orange-400 to-gold-500 drop-shadow-sm">
                            Plans
                        </span>
                    </h1>
                    <p className="text-slate-400 text-base font-light max-w-2xl">
                        Transparent pricing. Professional tooling. Cancel anytime.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 items-center relative z-10">

                {/* FREE PLAN */}
                <div className={cn(
                    "glass-card p-6 md:p-8 rounded-3xl border-t border-white/10 hover:border-white/20 transition-all group relative",
                    isPlanActive('free') ? "ring-2 ring-slate-600 bg-slate-900/80" : "bg-[#0B1121]/40"
                )}>
                    <h3 className="text-lg font-medium text-slate-400 mb-2">Explorer</h3>
                    <div className="text-4xl font-bold mb-6 text-white font-mono">$0<span className="text-base font-normal text-slate-500">/mo</span></div>

                    <ul className="space-y-4 mb-10">
                        <li className="flex items-center gap-3 text-sm text-slate-300"><Check className="w-4 h-4 text-emerald-500" /> Signals: BTC, ETH, SOL Only</li>
                        <li className="flex items-center gap-3 text-sm text-slate-300"><Check className="w-4 h-4 text-emerald-500" /> Analyst AI (Read-Only)</li>
                        <li className="flex items-center gap-3 text-sm text-slate-400"><div className="w-4 h-4 rounded-full bg-amber-500/10 flex items-center justify-center text-[10px] text-amber-500">!</div> 15-minute Delayed Data</li>
                        <li className="flex items-center gap-3 text-sm text-slate-500"><ShieldCheck className="w-4 h-4 text-slate-600" /> Basic Support</li>
                    </ul>

                    <Button
                        onClick={() => handleUpgrade('free')}
                        disabled={isPlanActive('free') || processing !== null}
                        variant="outline"
                        className={cn("w-full py-6 rounded-xl border-white/10 font-bold tracking-wide uppercase", isPlanActive('free') ? "text-slate-500" : "text-white hover:bg-white/5")}
                    >
                        {isPlanActive('free') ? "Current Plan" : "Downgrade"}
                    </Button>
                </div>

                {/* TRADER PLAN - Highlighted Gold/Premium */}
                <div className="relative transform md:-translate-y-4">
                    {/* Glow */}
                    <div className="absolute -inset-0.5 bg-gradient-to-b from-gold-500 to-orange-600 rounded-[26px] blur opacity-40 animate-pulse-slow"></div>

                    <div className={cn(
                        "relative glass-card bg-[#0f172a] p-6 md:p-10 rounded-3xl border border-gold-500/30 shadow-2xl shadow-gold-900/20",
                        isPlanActive('trader') && "ring-2 ring-gold-500"
                    )}>
                        <div className="absolute top-0 right-0 p-4">
                            <span className="bg-gold-500/10 text-gold-400 border border-gold-500/20 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide flex items-center gap-1">
                                <Zap size={10} fill="currentColor" /> Most Popular
                            </span>
                        </div>

                        <h3 className="text-lg font-medium text-gold-400 mb-2">Trader</h3>
                        <div className="text-4xl md:text-5xl font-bold mb-6 text-white font-mono tracking-tight">
                            <span className="line-through text-slate-600 text-3xl mr-3">$20</span>
                            $0<span className="text-sm font-normal text-gold-400 ml-2">(Beta)</span>
                        </div>
                        <p className="text-slate-400 text-sm mb-8 font-light">Free access while in Beta.</p>

                        <ul className="space-y-4 mb-10">
                            <li className="flex items-center gap-3 text-sm text-white font-medium"><Check className="w-4 h-4 text-gold-400" /> Real-Time Signals (Zero Latency)</li>
                            <li className="flex items-center gap-3 text-sm text-white font-medium"><Check className="w-4 h-4 text-gold-400" /> All 150+ Tokens (Alts & Memes)</li>
                            <li className="flex items-center gap-3 text-sm text-white font-medium"><Check className="w-4 h-4 text-gold-400" /> Instant Telegram Alerts</li>
                            <li className="flex items-center gap-3 text-sm text-white font-medium"><Check className="w-4 h-4 text-gold-400" /> Analyst AI (20 evals/day)</li>
                            <li className="flex items-center gap-3 text-sm text-white font-medium"><Check className="w-4 h-4 text-gold-400" /> Priority Support</li>
                        </ul>

                        <Button
                            onClick={() => handleUpgrade('trader')}
                            disabled={isPlanActive('trader') || processing !== null}
                            className={cn(
                                "w-full py-6 rounded-xl font-bold text-sm uppercase tracking-wide shadow-lg transition-all",
                                isPlanActive('trader')
                                    ? "bg-gold-900/20 text-gold-500 border border-gold-500/20"
                                    : "bg-gradient-to-r from-gold-500 to-orange-500 hover:to-orange-400 text-black border-none"
                            )}
                        >
                            {isPlanActive('trader') ? <span className="flex items-center gap-2"><Check size={16} /> Active Plan</span> : processing === 'trader' ? "Processing..." : "Start Free Beta Access"}
                        </Button>
                    </div>
                </div>

                {/* PRO PLAN */}
                <div className={cn(
                    "glass-card p-6 md:p-8 rounded-3xl border-t border-purple-500/30 hover:border-purple-500/50 transition-all group",
                    isPlanActive('pro') ? "ring-2 ring-purple-500 bg-slate-900/80" : "bg-[#0B1121]/40"
                )}>
                    <h3 className="text-lg font-medium text-purple-400 mb-2">Pro</h3>
                    <div className="text-3xl md:text-4xl font-bold mb-6 text-white font-mono">
                        <span className="line-through text-slate-600 text-2xl mr-3">$50</span>
                        $0<span className="text-sm font-normal text-purple-400 ml-2">(Beta)</span>
                    </div>

                    <ul className="space-y-4 mb-10">
                        <li className="flex items-center gap-3 text-sm text-slate-300"><Check className="w-4 h-4 text-purple-500" /> Everything in Trader</li>
                        <li className="flex items-center gap-3 text-sm text-slate-300"><Check className="w-4 h-4 text-purple-500" /> <span className="text-purple-300 font-bold">Unlimited AI Advisor Chat</span></li>
                        <li className="flex items-center gap-3 text-sm text-slate-300"><Check className="w-4 h-4 text-purple-500" /> Create Custom Strategies (Lab)</li>
                        <li className="flex items-center gap-3 text-sm text-slate-300"><Check className="w-4 h-4 text-purple-500" /> Hunter Mode (1m/5m Scalping)</li>
                        <li className="flex items-center gap-3 text-sm text-slate-300"><Check className="w-4 h-4 text-purple-500" /> Multi-Exchange Connection</li>
                    </ul>

                    <Button
                        onClick={() => handleUpgrade('pro')}
                        disabled={isPlanActive('pro') || processing !== null}
                        variant="outline"
                        className={cn(
                            "w-full py-6 rounded-xl border-white/10 font-bold tracking-wide uppercase",
                            isPlanActive('pro') ? "text-slate-500 bg-slate-900" : "text-white hover:bg-purple-500/20 hover:border-purple-500/50"
                        )}
                    >
                        {isPlanActive('pro') ? "Current Plan" : "Enable Pro Beta"}
                    </Button>
                </div>

            </div>
        </div>
    );
};

export default PricingPage;
