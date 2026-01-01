file_path = "backend/main.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find start of function
start_idx = -1
for i, line in enumerate(lines):
    if "def _build_pro_markdown(" in line:
        start_idx = i
        break

if start_idx == -1:
    print("Could not find _build_pro_markdown")
    exit(1)

# Find end of function (the mock return)
end_idx = -1
for i in range(start_idx, len(lines)):
    line = lines[i]  # Fix variable scope
    if "return markdown" in line and line.strip() == "return markdown":
        end_idx = i
        break
# Fallback search if 'return markdown' is missing or slightly different
if end_idx == -1:
    # Look for the next function definition or major block
    for i in range(start_idx + 10, len(lines)):
        if line.startswith("# ===") or line.startswith("@app"):
            end_idx = i - 1
            break

if end_idx == -1:
    print("Could not find end of function")
    exit(1)

print(f"Replacing lines {start_idx + 1} to {end_idx + 1}")

# Construct new function body
new_code = """def _build_pro_markdown(
    req: ProReq,
    lite: LiteSignal,
    indicators: Dict[str, Any],
    brain: Dict[str, str],
) -> str:
    \"\"\"
    Construye un prompt y delega en Gemini Flash para el análisis PRO.
    \"\"\"
    # 1. Extract context
    token_up = lite.token
    tf = lite.timeframe
    user_msg = (req.user_message or "").strip()

    rsi = indicators.get("rsi", "N/D")
    trend = indicators.get("trend", "NEUTRAL")
    ema21 = indicators.get("ema21", "N/D")
    
    # Format numbers
    rsi_str = f"{rsi:.1f}" if isinstance(rsi, (int, float)) else str(rsi)
    ema21_str = f"{ema21:.2f}" if isinstance(ema21, (int, float)) else str(ema21)

    insights = brain.get("insights", "Sin información").strip()
    news = brain.get("news", "Sin noticias recientes").strip()
    onchain = brain.get("onchain", "Sin datos onchain relevantes").strip()
    sentiment_txt = brain.get("sentiment", "Neutral").strip()
    snapshot = brain.get("snapshot", "").strip()

    # 2. Build Prompt
    from gemini_client import generate_pro

    prompt = f\"\"\"
Has recibido una solicitud de análisis PRO para {token_up} en timeframe {tf}.

DATOS TÉCNICOS (LITE):
- Dirección: {lite.direction.upper()}
- Entrada Sugerida: {lite.entry}
- TP Sugerido: {lite.tp}
- SL Sugerido: {lite.sl}
- RSI: {rsi_str}
- EMA21: {ema21_str}
- Tendencia: {trend}

CONTEXTO DE MERCADO (RAG):
- Insight Clave: {insights}
- Noticias: {news}
- OnChain: {onchain}
- Sentimiento: {sentiment_txt}
- Snapshot Precio: {snapshot}

MENSAJE DEL USUARIO:
{user_msg if user_msg else "Ninguno"}

TAREA:
Genera un informe profesional institucional.
Debes rellenar EXACTAMENTE las secciones requeridas.
Sé conciso pero "insightful". No uses relleno. Queremos que el usuario sienta que habla con un Senior Quant.
Integra los datos técnicos con el contexto fundamental/onchain si tiene sentido.
Si el sentimiento o noticias contradicen la señal técnica, menciónalo como riesgo.

FORMATO DE SALIDA (Estricto):
#ANALYSIS_START
#CTXT#
(Resumen ejecutivo de la situación macro/técnica)
#TA#
(Análisis técnico detallado: estructura, liquidez, indicadores)
#PLAN#
(Plan de ejecución, gestión de la posición)
#INSIGHT#
(Un dato clave fundamental, onchain o psicológico que apoye la tesis)
#PARAMS#
Entry: {lite.entry}
TP: {lite.tp}
SL: {lite.sl}
#ANALYSIS_END
\"\"\"

    # 3. Call AI
    return generate_pro(prompt)
"""

# Replace content
final_lines = lines[:start_idx] + [new_code + "\n"] + lines[end_idx + 1 :]

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(final_lines)

print("SUCCESS")
