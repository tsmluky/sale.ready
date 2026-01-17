// SMART URL DETECTION - Strict Mode (Ignore Env Vars)
const normalizeUrl = (url: string | undefined): string | undefined => {
  if (!url) return undefined;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  // If it looks like a domain (e.g. "api.railway.app"), assume https
  if (url.includes(".") && !url.startsWith("/")) return `https://${url}`;
  return url;
};

const getBaseUrl = () => {
  // Priority 1: Environment Variable (Build-time)
  const envUrl = normalizeUrl(import.meta.env.VITE_API_BASE_URL);
  if (envUrl) {
    return envUrl;
  }

  // Priority 2: Local Development Fallback
  if (typeof window !== "undefined") {
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return "http://localhost:8000";
    }
  }

  // Priority 3: Default Safe Fallback (or empty to force relative path if hosted together)
  return "http://localhost:8000";
};

export const API_BASE_URL: string = getBaseUrl();

// === Tokens soportados ===

export type Token = "eth" | "btc" | "sol" | "xau";

export interface TokenMeta {
  id: Token;
  symbol: string;
  name: string;
}


export const TOKENS = [
  { id: 'btc', name: 'Bitcoin', symbol: 'BTC' },
  { id: 'eth', name: 'Ethereum', symbol: 'ETH' },
  { id: 'sol', name: 'Solana', symbol: 'SOL' },
  { id: 'xrp', name: 'XRP', symbol: 'XRP' },
  { id: 'bnb', name: 'Binance Coin', symbol: 'BNB' },
  { id: 'doge', name: 'Dogecoin', symbol: 'DOGE' },
  { id: 'ada', name: 'Cardano', symbol: 'ADA' },
  { id: 'avax', name: 'Avalanche', symbol: 'AVAX' },
  { id: 'dot', name: 'Polkadot', symbol: 'DOT' },
  { id: 'link', name: 'Chainlink', symbol: 'LINK' },
  { id: 'ltc', name: 'Litecoin', symbol: 'LTC' },
  { id: 'matic', name: 'Polygon', symbol: 'MATIC' },
  { id: 'uni', name: 'Uniswap', symbol: 'UNI' },
  { id: 'atom', name: 'Cosmos', symbol: 'ATOM' },
  { id: 'near', name: 'Near Protocol', symbol: 'NEAR' },
  { id: 'xau', name: 'Gold', symbol: 'XAU' },
];

export const TIMEFRAMES = ['15m', '30m', '1h', '4h', '1d'];

// Mock data for fallback when API is unreachable
export const MOCK_LITE_SIGNAL: any = {
  timestamp: new Date().toISOString(),
  token: "ETH",
  timeframe: "30m",
  direction: "long",
  entry: 3675.50,
  tp: 3720.00,
  sl: 3625.00,
  confidence: 0.68,
  rationale: "EMA crossover on 30m with rising volume. RSI is neutral-bullish (55). Support holding at 3650.",
  source: "lite-rule@v1"
};

export const MOCK_PRO_RESPONSE = `
#ANALYSIS_START
#CTXT#
Market is trending upwards following positive CPI data. ETH correlation with BTC remains high (0.92).
#TA#
Price is above EMA200 (4h). Forming a bull flag pattern.
#PLAN#
Wait for breakout above 3700 for conservative entry. Aggressive entry at current CMP.
#INSIGHT#
On-chain data shows net accumulation by whales in the last 24h.
#PARAMS#
Entry: 3680-3700
TP: 3850
SL: 3600
#ANALYSIS_END
`;

export const MOCK_ADVISOR_RESPONSE: any = {
  token: "ETH",
  direction: "long",
  entry: 3675.50,
  size_quote: 500,
  tp: 3720.00,
  sl: 3625.00,
  alternatives: [
    { if: "breaks 3700 with volume", action: "trail sl to 3668", rr_target: 1.7 },
    { if: "falls below 3640", action: "reduce 50%", rr_target: 1.2 }
  ],
  risk_score: 0.44,
  confidence: 0.63
};
