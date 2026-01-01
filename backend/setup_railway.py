"""
SETUP COMPLETO - TraderCopilot con Railway
==========================================

Este script configura todo el sistema para usar Railway PostgreSQL.
"""

import os
import sys
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

print("=" * 60)
print("🚀 TRADERCOPILOT - SETUP RAILWAY")
print("=" * 60)

# 1. Verificar DATABASE_URL
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("\n❌ ERROR: DATABASE_URL no encontrada en .env")
    print("\nAsegúrate de tener esta línea en tu .env:")
    print("DATABASE_URL=postgresql://postgres:SzApckZdqOnbbbyeLeWLRVfBZWZtAaVu@shinkansen.proxy.rlwy.net:37966/railway")
    sys.exit(1)

print("\n✅ DATABASE_URL encontrada")
print(f"   Host: {db_url.split('@')[1].split(':')[0] if '@' in db_url else 'N/A'}")

# 2. Probar conexión
print("\n📡 Probando conexión a Railway...")
try:
    from database import SessionLocal
    from sqlalchemy import text
    
    db = SessionLocal()
    result = db.execute(text('SELECT 1')).scalar()
    db.close()
    
    if result == 1:
        print("✅ Conexión exitosa a Railway PostgreSQL!")
    else:
        print("❌ Conexión falló")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("\nVerifica que:")
    print("  1. La URL en .env sea correcta")
    print("  2. Railway TCP Proxy esté habilitado")
    print("  3. Tu firewall permita conexiones salientes al puerto 37966")
    sys.exit(1)

# 3. Verificar/Crear tablas
print("\n🗄️  Verificando tablas...")
try:
    from models_db import Base
    from database import engine_sync
    
    Base.metadata.create_all(bind=engine_sync)
    print("✅ Tablas verificadas/creadas")
except Exception as e:
    print(f"❌ Error creando tablas: {e}")
    sys.exit(1)

# 4. Configurar estrategias
print("\n⚙️  Configurando estrategias...")
try:
    from database import SessionLocal
    from models_db import StrategyConfig
    import json
    
    db = SessionLocal()
    
    # Desactivar todas las estrategias viejas
    old_strategies = ['rsi_macd_divergence_v1', 'ma_cross_v1', 'donchian_breakout_v1', 'bb_mean_reversion_v1']
    for sid in old_strategies:
        strat = db.query(StrategyConfig).filter(StrategyConfig.strategy_id == sid).first()
        if strat:
            strat.enabled = 0
            print(f"  ❌ Desactivada: {sid}")
    
    # Crear/Actualizar Donchian V2
    donchian = db.query(StrategyConfig).filter(StrategyConfig.strategy_id == 'donchian_v2').first()
    
    if not donchian:
        donchian = StrategyConfig(
            strategy_id="donchian_v2",
            name="Donchian Breakout V2 (Refined)",
            description="Trend following breakout with Volatility (ATR) and Trend (EMA200) filters.",
            version="2.0.0",
            enabled=1,
            interval_seconds=3600,  # 1 hora (para timeframe 1h)
            tokens=json.dumps(["ETH", "BTC", "SOL"]),
            timeframes=json.dumps(["1h"]),
            risk_profile="medium",
            mode="PRO",
            source_type="ENGINE",
            config_json=json.dumps({
                "period": 20,
                "atr_period": 14,
                "atr_ma_period": 20,
                "ema_trend_period": 200
            })
        )
        db.add(donchian)
        print("  ✅ Creada: donchian_v2")
    else:
        donchian.enabled = 1
        donchian.interval_seconds = 3600
        print("  ✅ Actualizada: donchian_v2")
    
    db.commit()
    db.close()
    
    print("\n✅ Configuración de estrategias completada")
    
except Exception as e:
    print(f"❌ Error configurando estrategias: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. Resumen final
print("\n" + "=" * 60)
print("✅ SETUP COMPLETADO")
print("=" * 60)
print("\n📊 Estado del sistema:")
print("  • Base de datos: Railway PostgreSQL")
print("  • Estrategia activa: Donchian Breakout V2")
print("  • Timeframe: 1h")
print("  • Tokens: ETH, BTC, SOL")
print("  • Intervalo de ejecución: 1 hora")

print("\n🚀 Próximos pasos:")
print("  1. Arranca el scheduler:")
print("     python scheduler.py 60")
print("\n  2. Monitorea señales en Railway:")
print("     SELECT * FROM signal ORDER BY timestamp DESC LIMIT 10;")
print("\n  3. O monitorea logs locales:")
print("     Get-Content -Path 'logs\\PRO\\eth.csv' -Wait -Tail 5")

print("\n" + "=" * 60)
