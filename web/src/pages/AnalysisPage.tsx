"use client"

import { useState, useEffect, useRef } from "react"
import { useSearchParams } from "react-router-dom"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Bot, Zap, BrainCircuit, LineChart, Activity, ChevronRight, Target, Terminal } from "lucide-react"
import toast from "react-hot-toast"

import { api } from "../services/api"
import { useAuth } from "../context/AuthContext"
import { SignalCard } from "../components/SignalCard"
import { SignalChart } from "../components/SignalChart"
import { ProAnalysisViewer } from "../components/ProAnalysisViewer"
import { ThinkingOverlay } from "@/components/ThinkingOverlay"
import { TokenSelector } from "@/components/TokenSelector"

// Full Token Whitelist (Matching Backend VALID_TOKENS_FULL)
const TOKENS = [
  // Top 10
  "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC",
  // Top 20-50
  "TRX", "LTC", "SHIB", "UNI", "ATOM", "LINK", "XLM", "BCH", "ALGO", "NEAR",
  "FIL", "VET", "ICP", "HBAR", "EGLD", "SAND", "MANA", "AXS", "THETA", "EOS",
  "AAVE", "XTZ", "FLOW", "FTM", "GRT", "KCS", "MKR", "SNX", "ZEC", "RUNE",
  // Top 50-100 & Emerging
  "NEO", "CRV", "CHZ", "BAT", "ENJ", "DASH", "CAKE", "STX", "SUSHI", "COMP",
  "PEPE", "FLOKI", "BONK", "WIF", "JUP", "PYTH", "TIA", "SEI", "SUI", "APT",
  "ARB", "OP", "BLUR", "LDO", "RNDR", "INJ", "IMX", "KAS", "FET", "AGIX"
]

export const AnalysisPage = () => {
  const [params] = useSearchParams()
  const { userProfile } = useAuth()
  const resultsRef = useRef<HTMLDivElement>(null)

  const [token, setToken] = useState(params.get("token") || "BTC")
  const [timeframe, setTimeframe] = useState("1h")
  const [mode, setMode] = useState<"lite" | "pro">("lite")
  const [isLoading, setIsLoading] = useState(false)

  const [liteResult, setLiteResult] = useState<any>(null)
  const [proResult, setProResult] = useState<any>(null)
  const [ohlcv, setOhlcv] = useState<any[]>([])

  useEffect(() => {
    const t = params.get("token")
    if (t) setToken(t)
  }, [params])

  // Reset to BTC if current token is not allowed (e.g. after plan downgrade or init)
  useEffect(() => {
    if (userProfile?.user?.allowed_tokens && token) {
      if (!userProfile.user.allowed_tokens.includes(token) && !userProfile.user.allowed_tokens.includes(token.toUpperCase())) {
        setToken('BTC');
        toast('Token restricted on your current plan. Resetting to BTC.', { icon: '🔒' });
      }
    }
  }, [userProfile, token])

  // Auto-scroll when results appear
  useEffect(() => {
    if ((liteResult || proResult) && !isLoading) {
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
      }, 100)
    }
  }, [liteResult, proResult, isLoading])

  const handleAnalyze = async () => {
    if (!token) return toast.error("Please enter a token symbol")

    setIsLoading(true)
    setLiteResult(null)
    setProResult(null)
    setOhlcv([])

    try {
      const candles = await api.getOHLCV(token, timeframe)
      setOhlcv(candles || [])

      if (mode === "lite") {
        const res = await api.analyzeLite(token, timeframe)
        setLiteResult(res)
        toast.success(`Analysis complete for ${token}`)
      } else {
        if (userProfile?.user?.plan === "free") {
          toast.error("Pro Analysis requires a Premium plan")
          setMode("lite")
          setIsLoading(false)
          return
        }

        const res = await api.analyzePro(token, timeframe, true)
        setProResult(res)
        toast.success("Deep Dive complete")
      }
    } catch (e: any) {
      console.error("Analysis error:", e)
      toast.error(e?.message || "Analysis failed")
    } finally {
      setIsLoading(false)
    }
  }

  const isPro = userProfile?.user?.plan !== "free"

  return (
    <div className="min-h-screen bg-[#020617] text-white selection:bg-brand-500/30 overflow-x-hidden font-sans relative pb-20">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:64px_64px] opacity-30" />
        <div className="absolute top-[-10%] left-[-10%] w-[700px] h-[700px] bg-brand-500/8 rounded-full blur-[150px] mix-blend-screen"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-emerald-500/5 blur-[140px] rounded-full mix-blend-screen"></div>
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-8 lg:py-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
          <div className="pl-6 relative">
            <div className="absolute left-0 top-2 bottom-2 w-1 bg-gradient-to-b from-gold-400 to-orange-500 rounded-full shadow-[0_0_15px_rgba(251,191,36,0.5)]"></div>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-gold-500/20 text-xs font-bold text-gold-400 mb-4 shadow-[0_0_15px_rgba(251,191,36,0.15)]">
              <Terminal size={12} />
              AI Analysis Terminal
            </div>
            <h1 className="text-4xl lg:text-5xl font-bold tracking-tight leading-tight mb-3">
              Market{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-400 via-orange-400 to-gold-500 drop-shadow-sm">
                Intelligence
              </span>
            </h1>
            <p className="text-slate-400 text-base font-light max-w-2xl flex items-center gap-2">
              Deploy AI engines to scan any asset.
              <span className="w-1 h-1 rounded-full bg-slate-600"></span>
              <span className="text-xs text-slate-500 font-mono">DeepSeek V2 & Gemini Flash</span>
            </p>
          </div>
        </div>

        {/* Control Panel */}
        <div className="mb-8 relative group">
          <div className="absolute -inset-1 bg-gradient-to-br from-brand-500/10 to-indigo-500/10 rounded-3xl blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>

          <div className="relative glass-card rounded-2xl p-6 lg:p-8 border border-white/10 bg-[#0f172a]/70 backdrop-blur-xl shadow-2xl overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            <div className="flex flex-col lg:flex-row gap-6">
              {/* Left: Input Controls */}
              <div className="flex-1 space-y-5">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      Select Asset
                    </label>
                    {userProfile?.user?.plan === 'free' && (
                      <span className="text-[9px] text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                        Upgrade for {TOKENS.length - 3} more
                      </span>
                    )}
                  </div>
                  {/* Filter tokens based on user entitlements */}
                  <TokenSelector
                    value={token}
                    onChange={setToken}
                    tokens={
                      userProfile?.user?.allowed_tokens
                        ? TOKENS.filter(t => userProfile.user.allowed_tokens?.includes(t))
                        : ['BTC', 'ETH', 'SOL']
                    }
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Timeframe
                  </label>
                  <Select value={timeframe} onValueChange={setTimeframe}>
                    <SelectTrigger className="w-full bg-black/40 border-white/10 hover:border-white/20 text-white rounded-xl h-10 text-sm transition-all focus:ring-1 focus:ring-brand-500/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#0f172a] border-white/10 text-sm">

                      <SelectItem value="15m">15 Minutes</SelectItem>
                      <SelectItem value="1h">1 Hour</SelectItem>
                      <SelectItem value="4h">4 Hours</SelectItem>
                      <SelectItem value="1d">1 Day</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Analysis Mode
                  </label>
                  <Tabs value={mode} onValueChange={(v) => setMode(v as "lite" | "pro")} className="w-full">
                    <TabsList className="grid w-full grid-cols-2 bg-black/40 border border-white/10 p-1 rounded-xl h-auto">
                      <TabsTrigger
                        value="lite"
                        className="data-[state=active]:bg-emerald-500 data-[state=active]:text-white rounded-lg py-2 font-bold text-xs transition-all"
                      >
                        <div className="flex items-center gap-2">
                          <Zap size={14} />
                          <span>LITE</span>
                        </div>
                      </TabsTrigger>
                      <TabsTrigger
                        value="pro"
                        className="data-[state=active]:bg-brand-500 data-[state=active]:text-white rounded-lg py-2 font-bold text-xs transition-all"
                        disabled={!isPro}
                      >
                        <div className="flex items-center gap-2">
                          <BrainCircuit size={14} />
                          <span>PRO</span>
                          {!isPro && (
                            <Badge variant="secondary" className="ml-1 text-[9px] px-1.5 py-0">
                              Premium
                            </Badge>
                          )}
                        </div>
                      </TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>

                <Button
                  onClick={handleAnalyze}
                  disabled={isLoading || !token}
                  className="w-full h-11 bg-gradient-to-r from-gold-500 to-orange-600 hover:from-gold-400 hover:to-orange-500 text-white text-sm font-bold rounded-xl shadow-lg shadow-gold-500/30 hover:shadow-gold-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed group/btn relative overflow-hidden"
                >
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Analyzing...</span>
                    </div>
                  ) : (
                    <>
                      <div className="absolute inset-0 -translate-x-full group-hover/btn:animate-shine bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                      <div className="flex items-center gap-2 relative">
                        <Target size={18} />
                        <span>Run Analysis</span>
                        <ChevronRight size={18} className="group-hover/btn:translate-x-1 transition-transform" />
                      </div>
                    </>
                  )}
                </Button>
              </div>

              {/* Right: Engine Info */}
              <div className="flex-1 lg:border-l lg:border-white/10 lg:pl-6 space-y-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-xl bg-brand-500/10 border border-brand-500/20">
                    <Bot className="text-brand-400" size={20} />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Engine Status</h3>
                    <p className="text-xs text-slate-400 font-mono">Ready to deploy</p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-emerald-500/30 transition-all group/card">
                    <div className="flex items-center gap-2 mb-1.5">
                      <div className="p-1 rounded bg-emerald-500/10 border border-emerald-500/20">
                        <Zap size={14} className="text-emerald-400" />
                      </div>
                      <span className="font-bold text-white text-xs">LITE Scanner</span>
                    </div>
                    <p className="text-[10px] text-slate-400 leading-relaxed mb-2">
                      Instant technical analysis (RSI, MACD, EMA). Zero hallucination.
                    </p>
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono">
                      <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                      Latency: ~120ms
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-brand-500/30 transition-all group/card">
                    <div className="flex items-center gap-2 mb-1.5">
                      <div className="p-1 rounded bg-brand-500/10 border border-brand-500/20">
                        <BrainCircuit size={14} className="text-brand-400" />
                      </div>
                      <span className="font-bold text-white text-xs">PRO Intelligence</span>
                      {!isPro && (
                        <Badge variant="secondary" className="text-[8px] h-4 px-1.5">
                          Premium
                        </Badge>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-400 leading-relaxed mb-2">
                      Deep generative analysis (DeepSeek V2 + Gemini). Strategic narrative reports.
                    </p>
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono">
                      <span className="w-1.5 h-1.5 bg-brand-500 rounded-full animate-pulse"></span>
                      Latency: ~8-12s
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Results Section */}
        {(liteResult || proResult) && (
          <div ref={resultsRef} className="space-y-8 pb-12 animate-in slide-in-from-bottom-5 duration-700 scroll-mt-6">

            <SignalCard
              signal={liteResult || proResult}
              chartNode={
                ohlcv.length > 0 ? (
                  <SignalChart
                    data={ohlcv}
                    entry={(liteResult || proResult)?.entry || 0}
                    tp={(liteResult || proResult)?.tp || 0}
                    sl={(liteResult || proResult)?.sl || 0}
                    direction={(liteResult || proResult)?.direction || 'long'}
                  />
                ) : null
              }
            />

            {proResult && (
              <div className="animate-in slide-in-from-bottom-5 duration-700 delay-200">
                <ProAnalysisViewer raw={proResult.raw || proResult} token={token} />
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!liteResult && !proResult && !isLoading && (
          <div className="text-center py-12">
            <div className="inline-flex p-4 rounded-2xl bg-white/5 border border-white/10 mb-4 opacity-50">
              <LineChart className="text-slate-500" size={32} />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Ready to Analyze</h3>
            <p className="text-slate-500 text-xs max-w-sm mx-auto">
              Select an asset and deploy AI engines.
            </p>
          </div>
        )}
      </div>

      {/* Thinking Overlay */}
      {isLoading && <ThinkingOverlay />}
    </div>
  )
}
