
import React from 'react';
import { useAuth } from '../context/AuthContext';
import {
    Check,
    X,
    Zap,
    Cpu,
    Globe,
    Clock,
    MessageSquare,
    ShieldCheck,
    CreditCard
} from 'lucide-react';

export const PricingPage: React.FC = () => {
    const { userProfile, upgradeSubscription } = useAuth();
    const normalizedPlan = (userProfile?.user.subscription_status || 'free').toLowerCase();
    const [processing, setProcessing] = React.useState<string | null>(null);

    const handleUpgrade = async (planId: string) => {
        setProcessing(planId);
        // Map keys if needed, currently they match roughly but careful with types
        const targetPlan = planId as 'free' | 'trader' | 'pro';

        try {
            await upgradeSubscription(targetPlan);
        } catch (error) {
            console.error("Upgrade failed:", error);
        } finally {
            setProcessing(null);
        }
    };

    // Logic to determine button state
    const getButtonText = (planId: string) => {
        if (normalizedPlan === planId) return "Current Plan";
        if (planId === 'free') return "Downgrade to Explorer";
        if (planId === 'trader') return normalizedPlan === 'pro' ? "Downgrade to Trader" : "Upgrade to Trader";
        if (planId === 'pro') return "Upgrade to Pro";
        return "Upgrade";
    };

    const isPlanActive = (planId: string) => normalizedPlan === planId;

    const plans = [
        {
            id: 'free',
            name: 'Explorer',
            price: '$0',
            period: 'forever',
            description: 'Perfect for checking the market occasionally.',
            features: [
                { text: 'Signals: BTC, ETH, SOL Only', included: true },
                { text: '15-minute Delayed Data', included: true, warning: true },
                { text: 'Analyst AI (Read-Only)', included: true },
                { text: 'Timeframes: 4h, Daily', included: true },
                { text: 'Real-time Alerts', included: false },
                { text: 'Advisor Chat', included: false },
                { text: 'Custom Strategies', included: false },
            ],
            cta: 'Downgrade',
            active: isPlanActive('free'),
            highlight: false
        },
        {
            id: 'trader',
            name: 'Trader',
            price: '$20',
            period: '/ month',
            description: 'For active traders who need speed and coverage.',
            features: [
                { text: 'Real-Time Signals (Zero Latency)', included: true, highlight: true },
                { text: 'All 150+ Tokens (Alts & Memes)', included: true },
                { text: 'Instant Telegram Alerts', included: true },
                { text: 'All Timeframes (15m+)', included: true },
                { text: 'Analyst AI (20 evals/day)', included: true },
                { text: 'Advisor Chat', included: false },
                { text: 'Custom Strategies', included: false },
            ],
            cta: 'Upgrade to Trader',
            active: isPlanActive('trader'),
            highlight: true
        },
        {
            id: 'pro',
            name: 'Pro',
            price: '$50',
            period: '/ month',
            description: 'For serious algorithmic traders and automation.',
            features: [
                { text: 'Everything in Trader', included: true },
                { text: 'Unlimited AI Advisor Chat', included: true, highlight: true },
                { text: 'Create Custom Strategies (Lab)', included: true },
                { text: 'Hunter Mode (1m/5m Scalping)', included: true },
                { text: 'Priority Dev Support', included: true },
                { text: 'Multi-Exchange Connection', included: true },
                { text: 'API Access', included: true },
            ],
            cta: 'Upgrade to Pro',
            active: isPlanActive('pro'),
            highlight: false
        }
    ];

    return (
        <div className="p-4 md:p-8 max-w-7xl mx-auto pb-24 md:pb-8 animate-fade-in">
            <div className="text-center max-w-3xl mx-auto mb-12">
                <h1 className="text-3xl md:text-5xl font-bold text-white mb-4 tracking-tight">
                    Upgrade your <span className="text-emerald-400">Trading Edge</span>
                </h1>
                <p className="text-slate-400 text-lg">
                    Select the plan that fits your trading style. Unlock real-time data, AI insights, and automation tools.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
                {/* Glow Effect for Highlighted Card */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full md:w-1/3 h-full bg-emerald-500/10 blur-[100px] rounded-full pointer-events-none" />

                {plans.map((plan) => (
                    <div
                        key={plan.id}
                        className={`relative flex flex-col p-6 md:p-8 rounded-2xl border transition-all duration-300 hover:-translate-y-2 h-full
              ${plan.active
                                ? 'bg-slate-900/80 border-slate-700 ring-2 ring-emerald-500/50 shadow-emerald-900/20'
                                : plan.highlight
                                    ? 'bg-slate-900/90 border-emerald-500/30 shadow-2xl shadow-emerald-900/20 z-10 scale-105'
                                    : 'bg-slate-950/50 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                            }
            `}
                    >
                        {plan.highlight && (
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-4 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-lg">
                                Most Popular
                            </div>
                        )}

                        <div className="mb-6">
                            <h3 className={`text-xl font-bold mb-2 ${plan.highlight ? 'text-white' : 'text-slate-200'}`}>
                                {plan.name}
                            </h3>
                            <div className="flex items-baseline gap-1">
                                <span className={`text-4xl font-bold ${plan.highlight ? 'text-emerald-400' : 'text-white'}`}>
                                    {plan.price}
                                </span>
                                <span className="text-slate-500 text-sm font-medium">{plan.period}</span>
                            </div>
                            <p className="text-slate-400 text-sm mt-3 leading-relaxed">
                                {plan.description}
                            </p>
                        </div>

                        <div className="flex-1 space-y-4 mb-8">
                            {plan.features.map((feature, idx) => (
                                <div key={idx} className="flex items-start gap-3 text-sm">
                                    {feature.included ? (
                                        <div className={`mt-0.5 p-0.5 rounded-full ${feature.highlight ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                                            <Check size={12} strokeWidth={3} />
                                        </div>
                                    ) : (
                                        <div className="mt-0.5 p-0.5 text-slate-700">
                                            <X size={14} />
                                        </div>
                                    )}
                                    <span className={`${!feature.included ? 'text-slate-600 line-through decoration-slate-700' :
                                        feature.highlight ? 'text-slate-100 font-medium' :
                                            feature.warning ? 'text-amber-500/80' : 'text-slate-300'
                                        }`}>
                                        {feature.text}
                                    </span>
                                </div>
                            ))}
                        </div>

                        <button
                            disabled={plan.active || processing !== null}
                            onClick={() => handleUpgrade(plan.id)}
                            className={`w-full py-3 rounded-xl font-bold text-sm transition-all active:scale-[0.98]
                ${plan.active
                                    ? 'bg-slate-800 text-slate-400 cursor-default border border-slate-700'
                                    : plan.highlight
                                        ? 'bg-emerald-500 hover:bg-emerald-400 text-white shadow-lg shadow-emerald-500/25'
                                        : 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-700'
                                }
              `}
                        >
                            <span className="flex items-center justify-center gap-2 opacity-100">
                                {plan.active ? <><Check size={16} /> Current Plan</> : processing === plan.id ? "Processing..." : getButtonText(plan.id)}
                            </span>
                        </button>
                    </div>
                ))}
            </div>
            {/* Footer removed per user request */}
        </div>
    );
};
