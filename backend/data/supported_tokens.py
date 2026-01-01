# backend/data/supported_tokens.py

# Free Plan: Basic Major Caps
VALID_TOKENS_FREE = [
    "BTC", "ETH", "SOL"
]

# Pro / Trader Plan: Top ~150 Tokens (High Volume / Liquid)
VALID_TOKENS_FULL = [
    # Top 10
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC",
    # Top 20-50
    "TRX", "LTC", "SHIB", "UNI", "ATOM", "LINK", "XLM", "BCH", "ALGO", "NEAR",
    "FIL", "VET", "ICP", "HBAR", "EGLD", "SAND", "MANA", "AXS", "THETA", "EOS",
    "AAVE", "XTZ", "FLOW", "FTM", "GRT", "KCS", "MKR", "SNX", "ZEC", "RUNE",
    # Top 50-100 (Defi/L1/L2/Gaming)
    "NEO", "CRV", "CHZ", "BAT", "ENJ", "DASH", "CAKE", "STX", "SUSHI", "COMP",
    "ZIL", "YFI", "1INCH", "LRC", "WAVES", "KSM", "RVN", "ONE", "OMG", "ONT",
    "IOST", "QTUM", "ICX", "ANKR", "ZEN", "ZRX", "DGB", "SC", "UMA", "HOT",
    # Emerging / Meme / New Gen
    "PEPE", "FLOKI", "BONK", "WIF", "JUP", "PYTH", "TIA", "SEI", "SUI", "APT",
    "ARB", "OP", "BLUR", "LDO", "RNDR", "INJ", "IMX", "KAS", "FET", "AGIX",
    "OCEAN", "GALA", "CFX", "ACH", "WOO", "JASMY", "GLM", "GMT", "APE", "LUNC",
    # Stablecoins excluded usually for trading, but useful for reference if needed.
    # Excluded: USDT, USDC, DAI, FDUSD
]

def get_tokens_for_plan(plan: str) -> list[str]:
    """Returns the list of allowed tokens for a given user plan."""
    if plan.upper() in ["PRO", "TRADER", "WHALE", "OWNER", "ADMIN"]:
        return VALID_TOKENS_FULL
    return VALID_TOKENS_FREE
