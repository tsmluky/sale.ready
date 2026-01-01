# Script para ver el contenido de la base de datos TraderCopilot
# Uso: python view_db.py

from database import SessionLocal
from models_db import Signal, SignalEvaluation
from sqlalchemy import func

def main():
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("📊 CONTENIDO DE LA BASE DE DATOS - TraderCopilot")
        print("="*80 + "\n")
        
        # Contar señales
        total_signals = db.query(func.count(Signal.id)).scalar()
        print(f"📈 Total de Señales: {total_signals}")
        
        if total_signals > 0:
            # Señales por modo
            print("\n🔍 Señales por Modo:")
            modes = db.query(Signal.mode, func.count(Signal.id)).group_by(Signal.mode).all()
            for mode, count in modes:
                print(f"   - {mode}: {count}")
            
            # Señales por token
            print("\n💰 Señales por Token:")
            tokens = db.query(Signal.token, func.count(Signal.id)).group_by(Signal.token).all()
            for token, count in tokens:
                print(f"   - {token}: {count}")
            
            # Últimas 10 señales
            print("\n📋 Últimas 10 Señales:")
            print("-" * 80)
            recent_signals = db.query(Signal).order_by(Signal.timestamp.desc()).limit(10).all()
            for sig in recent_signals:
                print(f"  {sig.timestamp} | {sig.token:6} | {sig.mode:8} | {sig.direction:5} | Entry: ${sig.entry:,.2f}")
        
        # Evaluaciones
        total_evals = db.query(func.count(SignalEvaluation.id)).scalar()
        print(f"\n✅ Total de Evaluaciones: {total_evals}")
        
        if total_evals > 0:
            print("\n📊 Resultados de Evaluaciones:")
            results = db.query(SignalEvaluation.result, func.count(SignalEvaluation.id)).group_by(SignalEvaluation.result).all()
            for result, count in results:
                print(f"   - {result}: {count}")
            
            # Últimas evaluaciones
            print("\n📋 Últimas 10 Evaluaciones:")
            print("-" * 80)
            recent_evals = db.query(SignalEvaluation).join(Signal).order_by(SignalEvaluation.evaluated_at.desc()).limit(10).all()
            for ev in recent_evals:
                sig = ev.signal
                print(f"  {ev.evaluated_at} | {sig.token:6} | {ev.result:8} | Exit: ${ev.exit_price:,.2f}")
        
        print("\n" + "="*80)
        print("✨ Fin del reporte")
        print("="*80 + "\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
