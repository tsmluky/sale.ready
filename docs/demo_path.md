# A-02 Demo Path

**Goal**: A replicable, high-impact demo in 3-5 minutes.

## 1. The Hook (Login & Dashboard)
- **Start**: Login Page (`/login`)
- **Action**: Enter credentials (pre-filled or quick type).
- **Wow Moment**: Dashboard loads with a **smooth fade-in animation**.
- **Visuals**: "Market Health" gauge breathing, "Active Strategies" cards glowing.

## 2. The Core (Scanner & Signals)
- **Navigate**: Click "Scanner" (or "Signals").
- **Action**: Show a list of recent signals (seeded data).
- **Highlight**: Click a signal to expand details. Show "Confidence Score" and "AI Rationale".

## 3. The Special Sauce (Strategies)
- **Navigate**: Click "Strategies".
- **Action**: Scroll through "Strategy Registry".
- **Visuals**: Glass-morphic cards with "Win Rate" and "PnL" in gold/green.
- **Micro-interaction**: Hover over a card to see "Activate" button pulse.

## 4. The AI (Advisor)
- **Navigate**: Click "Advisor" (or use FAB).
- **Action**: Ask: "Why is ETH bearish today?"
- **Response**: Streaming response with technical context (RSI, levels).

## 5. The Close (Pricing/Upgrade)
- **Navigate**: Click "Upgrade" / "Pricing".
- **Action**: Show "Professional" vs "Institutional" tiers.
- **Finish**: "Ready to deploy?"

## Recovery Path
- If Backend fails: Have `mock_mode=True` variable in frontend config? (Future Item)
- If Data empty: Run `scripts/seed_demo_data.py`.
