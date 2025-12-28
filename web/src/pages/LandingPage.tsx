// web/src/pages/LandingPage.tsx
import React from "react";
import { ArrowRight, Shield, LineChart, Bot, CheckCircle2 } from "lucide-react";
import { Link } from "react-router-dom";

type Plan = {
    name: string;
    price: string;
    subtitle: string;
    bullets: string[];
    ctaLabel: string;
    ctaHref: string;
    highlight?: boolean;
};

type FAQ = {
    q: string;
    a: string;
};

const PLANS: Plan[] = [
    {
        name: "FREE",
        price: "$0",
        subtitle: "Start with the scanner. Learn the workflow.",
        bullets: [
            "LITE technical scanner (RSI / MACD / EMA)",
            "Limited daily AI credits (plan-gated)",
            "Tokens: BTC / ETH / SOL",
            "Timeframes: 15m / 30m / 1h / 4h / 1d",
        ],
        ctaLabel: "Get started",
        ctaHref: "/register",
    },
    {
        name: "TRADER",
        price: "Plan-gated",
        subtitle: "More coverage, more daily AI credits.",
        bullets: [
            "Top-25 token access (plan-gated)",
            "More daily AI credits",
            "Dashboard feed + logs",
            "Advisor chat (plan limits apply)",
        ],
        ctaLabel: "Request access",
        ctaHref: "/register",
        highlight: true,
    },
    {
        name: "PRO",
        price: "Plan-gated",
        subtitle: "Broad token coverage + high daily credits.",
        bullets: [
            "PRO structured Markdown reports (DeepSeek w/ Gemini fallback)",
            "Broad token coverage (plan-gated)",
            "Higher daily AI credits",
            "Quant Lab access (strategies + stats)",
        ],
        ctaLabel: "Book a demo",
        ctaHref: "/register",
    },
];

const FAQS: FAQ[] = [
    {
        q: "Does TraderCopilot execute trades?",
        a: "No. TraderCopilot generates analysis and signals only. There are no order-execution endpoints.",
    },
    {
        q: "Do I need to connect exchange API keys?",
        a: "No. Users never enter exchange API keys.",
    },
    {
        q: "Where does the market data come from?",
        a: "Primary source is Binance via CCXT, with caching and fallback logic for reliability.",
    },
    {
        q: "What indicators are used in LITE?",
        a: "RSI, MACD, and EMA are used to generate fast Long/Short setups with TP/SL.",
    },
    {
        q: "What makes PRO different?",
        a: "PRO generates a structured Markdown report with levels, plan, invalidation, and risk framing using live quotes plus scanner context.",
    },
    {
        q: "Which timeframes are supported?",
        a: "15m, 30m, 1h, 4h, and 1d.",
    },
    {
        q: "Are Telegram alerts available?",
        a: "Yes, alerts are available today, but chat-ID configuration is manual for now (UI upgrade planned).",
    },
    {
        q: "Is this financial advice?",
        a: "No. TraderCopilot is software for analysis and decision support. No guarantees.",
    },
];

function classNames(...xs: Array<string | false | null | undefined>) {
    return xs.filter(Boolean).join(" ");
}

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-slate-950 text-slate-100">
            {/* Top gradient */}
            <div className="pointer-events-none absolute inset-x-0 top-0 h-[520px] bg-gradient-to-b from-slate-900/60 via-slate-950 to-slate-950" />
            <div className="relative">
                {/* NAV */}
                <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
                    <div className="flex items-center gap-2">
                        <div className="h-9 w-9 rounded-xl bg-slate-800 ring-1 ring-slate-700" />
                        <div className="leading-tight">
                            <div className="text-sm font-semibold tracking-wide">TraderCopilot</div>
                            <div className="text-xs text-slate-400">Signals + AI Reports + Strategy Stats</div>
                        </div>
                    </div>

                    <nav className="hidden items-center gap-6 text-sm text-slate-300 md:flex">
                        <a href="#how" className="hover:text-slate-100">How it works</a>
                        <a href="#proof" className="hover:text-slate-100">Proof</a>
                        <a href="#pricing" className="hover:text-slate-100">Pricing</a>
                        <a href="#faq" className="hover:text-slate-100">FAQ</a>
                    </nav>

                    <div className="flex items-center gap-3">
                        <Link
                            to="/login"
                            className="hidden rounded-xl px-4 py-2 text-sm text-slate-300 ring-1 ring-slate-700 hover:bg-slate-900 md:inline-flex"
                        >
                            Sign in
                        </Link>
                        <Link
                            to="/register"
                            className="inline-flex items-center gap-2 rounded-xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-white"
                        >
                            Request early access <ArrowRight className="h-4 w-4" />
                        </Link>
                    </div>
                </header>

                {/* HERO */}
                <section className="mx-auto w-full max-w-6xl px-6 pb-10 pt-8 md:pt-14">
                    <div className="grid gap-10 md:grid-cols-12 md:items-center">
                        <div className="md:col-span-7">
                            <div className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-3 py-1 text-xs text-slate-300 ring-1 ring-slate-800">
                                <Shield className="h-4 w-4" />
                                Non-custodial. No exchange API keys. No order execution.
                            </div>

                            <h1 className="mt-5 text-3xl font-semibold tracking-tight md:text-5xl">
                                TraderCopilot turns signals into decisions you can justify.
                            </h1>

                            <p className="mt-4 max-w-2xl text-base leading-relaxed text-slate-300 md:text-lg">
                                Instant technical scanning plus structured AI reports built from live market data.
                                A clean workflow: setup, rationale, invalidation, and a plan you can follow.
                            </p>

                            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
                                <Link
                                    to="/register"
                                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-100 px-5 py-3 text-sm font-semibold text-slate-900 hover:bg-white"
                                >
                                    Request early access <ArrowRight className="h-4 w-4" />
                                </Link>
                                <a
                                    href="#demo"
                                    className="inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm text-slate-200 ring-1 ring-slate-800 hover:bg-slate-900"
                                >
                                    See the 90-second demo path
                                </a>
                            </div>

                            <div className="mt-7 grid gap-3 text-sm text-slate-300 sm:grid-cols-2">
                                <div className="flex items-start gap-2">
                                    <LineChart className="mt-0.5 h-4 w-4 text-slate-300" />
                                    <span>Live market data via Binance (CCXT) + caching</span>
                                </div>
                                <div className="flex items-start gap-2">
                                    <Bot className="mt-0.5 h-4 w-4 text-slate-300" />
                                    <span>PRO reports: DeepSeek with Gemini fallback (structured Markdown)</span>
                                </div>
                            </div>
                        </div>

                        {/* HERO VISUAL */}
                        <div className="md:col-span-5">
                            <div className="rounded-2xl bg-slate-900/60 p-4 ring-1 ring-slate-800">
                                <div className="rounded-xl bg-slate-950 p-4 ring-1 ring-slate-800">
                                    <div className="flex items-center justify-between">
                                        <div className="text-sm font-semibold">Example Output</div>
                                        <div className="text-xs text-slate-400">PRO (Markdown)</div>
                                    </div>
                                    <div className="mt-4 space-y-2 text-sm text-slate-300">
                                        <div className="rounded-lg bg-slate-900/60 p-3 ring-1 ring-slate-800">
                                            <div className="text-xs text-slate-400">#PLAN</div>
                                            <div className="mt-1">Entry logic, invalidation, and risk framing...</div>
                                        </div>
                                        <div className="rounded-lg bg-slate-900/60 p-3 ring-1 ring-slate-800">
                                            <div className="text-xs text-slate-400">#INSIGHT</div>
                                            <div className="mt-1">Levels, momentum context, and scenario planning...</div>
                                        </div>
                                        <div className="rounded-lg bg-slate-900/60 p-3 ring-1 ring-slate-800">
                                            <div className="text-xs text-slate-400">LITE Signal</div>
                                            <div className="mt-1">Long/Short + TP/SL + rationale card...</div>
                                        </div>
                                    </div>
                                    <div className="mt-4 text-xs text-slate-500">
                                        Replace this mock with real screenshots: Dashboard + PRO report + Signal card.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* PROBLEM */}
                <section className="mx-auto w-full max-w-6xl px-6 py-10">
                    <div className="grid gap-6 md:grid-cols-12">
                        <div className="md:col-span-5">
                            <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
                                Most tools give you either numbers without context, or context without numbers.
                            </h2>
                            <p className="mt-3 text-slate-300">
                                Signals without rationale become noise. AI chats without hard grounding become vibes.
                                TraderCopilot is built to force a repeatable decision workflow you can audit.
                            </p>
                        </div>
                        <div className="md:col-span-7">
                            <div className="grid gap-4 sm:grid-cols-2">
                                <FeatureCard
                                    title="Not a black box"
                                    desc="Every setup includes direction, TP/SL, and rationale. The output is meant to be used, not worshipped."
                                />
                                <FeatureCard
                                    title="Hybrid by design"
                                    desc="Hard indicators first (scanner). LLM synthesis second (structured report), using live quotes."
                                />
                                <FeatureCard
                                    title="Non-custodial"
                                    desc="No exchange API keys. No order-execution endpoints. It’s decision support, not automated trading."
                                />
                                <FeatureCard
                                    title="Plan-gated usage"
                                    desc="Tokens and daily AI credits are enforced by plan to keep boundaries clear and costs predictable."
                                />
                            </div>
                        </div>
                    </div>
                </section>

                {/* HOW IT WORKS */}
                <section id="how" className="mx-auto w-full max-w-6xl px-6 py-10">
                    <div className="rounded-3xl bg-slate-900/40 p-6 ring-1 ring-slate-800 md:p-10">
                        <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">How it works</h2>
                        <p className="mt-2 text-slate-300">
                            Three steps. Same workflow every time. Less randomness.
                        </p>

                        <div className="mt-6 grid gap-4 md:grid-cols-3">
                            <StepCard
                                step="Step 1"
                                title="Pick token + timeframe"
                                desc="Supported timeframes: 15m, 30m, 1h, 4h, 1d. Token access is plan-gated."
                            />
                            <StepCard
                                step="Step 2"
                                title="Launch LITE Scanner"
                                desc="Instant RSI/MACD/EMA scan → Long/Short setup with TP/SL and rationale."
                            />
                            <StepCard
                                step="Step 3"
                                title="Open PRO depth (optional)"
                                desc="Structured Markdown report with levels, plan, invalidation, and risk framing."
                            />
                        </div>
                    </div>
                </section>

                {/* PROOF */}
                <section id="proof" className="mx-auto w-full max-w-6xl px-6 py-10">
                    <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">Proof-backed boundaries</h2>
                    <p className="mt-2 max-w-3xl text-slate-300">
                        TraderCopilot is intentionally strict about what it is (and isn’t).
                    </p>

                    <div className="mt-6 grid gap-4 md:grid-cols-3">
                        <ProofCard
                            title="No trade execution"
                            desc="There are no order endpoints. TraderCopilot generates signals and analysis only."
                        />
                        <ProofCard
                            title="No exchange API keys"
                            desc="Users never enter exchange API keys. Non-custodial by design."
                        />
                        <ProofCard
                            title="Evaluation logic exists"
                            desc="Signals can be evaluated by TP/SL touch logic and a timeout rule (breakeven)."
                        />
                    </div>

                    <div id="demo" className="mt-8 rounded-3xl bg-slate-900/40 p-6 ring-1 ring-slate-800 md:p-10">
                        <h3 className="text-xl font-semibold">90-second demo path</h3>
                        <ol className="mt-4 space-y-2 text-slate-300">
                            <li className="flex gap-2">
                                <span className="mt-0.5 text-slate-500">1)</span> Login → land on the Dashboard
                            </li>
                            <li className="flex gap-2">
                                <span className="mt-0.5 text-slate-500">2)</span> Open <span className="font-semibold text-slate-100">AI Radar</span>
                            </li>
                            <li className="flex gap-2">
                                <span className="mt-0.5 text-slate-500">3)</span> Use <span className="font-semibold text-slate-100">SOL / 1h</span> → click “Launch Scanner”
                            </li>
                            <li className="flex gap-2">
                                <span className="mt-0.5 text-slate-500">4)</span> Watch the LITE signal card appear instantly (TP/SL + rationale)
                            </li>
                            <li className="flex gap-2">
                                <span className="mt-0.5 text-slate-500">5)</span> Click “Ask Copilot (PRO)” → get the structured Markdown report
                            </li>
                            <li className="flex gap-2">
                                <span className="mt-0.5 text-slate-500">6)</span> Open “Strategies” → see bots + stats
                            </li>
                        </ol>
                    </div>
                </section>

                {/* PRICING */}
                <section id="pricing" className="mx-auto w-full max-w-6xl px-6 py-10">
                    <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">Pricing</h2>
                    <p className="mt-2 max-w-3xl text-slate-300">
                        Plans are enforced via entitlements (token access + daily AI credits). Billing UI can be added next.
                    </p>

                    <div className="mt-6 grid gap-4 md:grid-cols-3">
                        {PLANS.map((p) => (
                            <div
                                key={p.name}
                                className={classNames(
                                    "rounded-3xl p-6 ring-1",
                                    p.highlight
                                        ? "bg-slate-100 text-slate-900 ring-slate-200"
                                        : "bg-slate-900/40 text-slate-100 ring-slate-800"
                                )}
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <div className={classNames("text-sm font-semibold", p.highlight ? "text-slate-900" : "text-slate-100")}>
                                            {p.name}
                                        </div>
                                        <div className={classNames("mt-1 text-3xl font-semibold", p.highlight ? "text-slate-900" : "text-slate-100")}>
                                            {p.price}
                                        </div>
                                        <div className={classNames("mt-2 text-sm", p.highlight ? "text-slate-700" : "text-slate-300")}>
                                            {p.subtitle}
                                        </div>
                                    </div>
                                    {p.highlight && (
                                        <div className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-slate-100">
                                            Most popular
                                        </div>
                                    )}
                                </div>

                                <ul className="mt-5 space-y-2 text-sm">
                                    {p.bullets.map((b) => (
                                        <li key={b} className="flex items-start gap-2">
                                            <CheckCircle2 className={classNames("mt-0.5 h-4 w-4", p.highlight ? "text-slate-900" : "text-slate-300")} />
                                            <span className={p.highlight ? "text-slate-800" : "text-slate-300"}>{b}</span>
                                        </li>
                                    ))}
                                </ul>

                                <Link
                                    to={p.ctaHref}
                                    className={classNames(
                                        "mt-6 inline-flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold",
                                        p.highlight ? "bg-slate-900 text-slate-100 hover:bg-black" : "bg-slate-100 text-slate-900 hover:bg-white"
                                    )}
                                >
                                    {p.ctaLabel} <ArrowRight className="h-4 w-4" />
                                </Link>

                                <div className={classNames("mt-3 text-xs", p.highlight ? "text-slate-600" : "text-slate-500")}>
                                    Token access + daily AI credits are enforced by plan.
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* FAQ */}
                <section id="faq" className="mx-auto w-full max-w-6xl px-6 py-10">
                    <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">FAQ</h2>
                    <div className="mt-6 grid gap-4 md:grid-cols-2">
                        {FAQS.map((f) => (
                            <div key={f.q} className="rounded-3xl bg-slate-900/40 p-6 ring-1 ring-slate-800">
                                <div className="text-sm font-semibold">{f.q}</div>
                                <div className="mt-2 text-sm text-slate-300">{f.a}</div>
                            </div>
                        ))}
                    </div>

                    <div className="mt-8 rounded-3xl bg-slate-900/40 p-6 ring-1 ring-slate-800">
                        <div className="text-sm font-semibold">Disclaimer</div>
                        <div className="mt-2 text-sm text-slate-300">
                            TraderCopilot provides analysis and signals for informational purposes only. It does not execute trades and does not guarantee outcomes.
                        </div>
                    </div>
                </section>

                {/* FOOTER */}
                <footer className="mx-auto w-full max-w-6xl px-6 py-10">
                    <div className="flex flex-col items-start justify-between gap-6 border-t border-slate-800 pt-8 md:flex-row md:items-center">
                        <div className="text-sm text-slate-400">
                            © {new Date().getFullYear()} TraderCopilot. Built for disciplined decision-making.
                        </div>
                        <div className="flex items-center gap-3">
                            <Link to="/login" className="text-sm text-slate-300 hover:text-slate-100">Sign in</Link>
                            <Link
                                to="/register"
                                className="inline-flex items-center gap-2 rounded-xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-white"
                            >
                                Request access <ArrowRight className="h-4 w-4" />
                            </Link>
                        </div>
                    </div>
                </footer>
            </div>
        </div>
    );
}

function FeatureCard({ title, desc }: { title: string; desc: string }) {
    return (
        <div className="rounded-2xl bg-slate-900/40 p-5 ring-1 ring-slate-800">
            <div className="text-sm font-semibold">{title}</div>
            <div className="mt-2 text-sm text-slate-300">{desc}</div>
        </div>
    );
}

function StepCard({ step, title, desc }: { step: string; title: string; desc: string }) {
    return (
        <div className="rounded-2xl bg-slate-950/60 p-5 ring-1 ring-slate-800">
            <div className="text-xs font-semibold text-slate-400">{step}</div>
            <div className="mt-2 text-sm font-semibold">{title}</div>
            <div className="mt-2 text-sm text-slate-300">{desc}</div>
        </div>
    );
}

function ProofCard({ title, desc }: { title: string; desc: string }) {
    return (
        <div className="rounded-2xl bg-slate-900/40 p-5 ring-1 ring-slate-800">
            <div className="text-sm font-semibold">{title}</div>
            <div className="mt-2 text-sm text-slate-300">{desc}</div>
        </div>
    );
}
