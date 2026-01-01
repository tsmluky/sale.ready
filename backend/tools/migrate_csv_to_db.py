#!/usr/bin/env python3
"""
Script para migrar datos históricos de CSV a SQLite.
Uso: cd backend && python tools/migrate_csv_to_db.py
"""

import sys
import csv
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path is set
import database
import models_db

# Create tables
database.Base.metadata.create_all(bind=database.engine)

LOGS_DIR = Path(__file__).parent.parent / "logs"


def parse_timestamp(ts_str):
    """Parse ISO timestamp string to datetime object."""
    if not ts_str:
        return None
    try:
        ts_str = ts_str.replace('Z', '+00:00')
        return datetime.fromisoformat(ts_str)
    except:
        try:
            return datetime.fromisoformat(ts_str)
        except:
            return None


def migrate_signals():
    """Migrate signals from CSV files to database."""
    db = database.SessionLocal()
    migrated = 0
    skipped = 0
    
    print("🔄 Migrating signals from CSV to database...")
    
    for mode in ['LITE', 'PRO', 'ADVISOR']:
        mode_dir = LOGS_DIR / mode
        if not mode_dir.exists():
            print(f"  ⚠️  Directory not found: {mode_dir}")
            continue
            
        print(f"\n📁 Processing {mode} signals...")
        
        for csv_file in mode_dir.glob("*.csv"):
            token = csv_file.stem.upper()
            print(f"  📄 {csv_file.name}...", end=" ")
            
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    count = 0
                    
                    for row in reader:
                        timestamp = parse_timestamp(row.get('timestamp'))
                        if not timestamp:
                            skipped += 1
                            continue
                        
                        existing = db.query(models_db.Signal).filter(
                            models_db.Signal.timestamp == timestamp,
                            models_db.Signal.token == token,
                            models_db.Signal.mode == mode
                        ).first()
                        
                        if existing:
                            skipped += 1
                            continue
                        
                        signal = models_db.Signal(
                            timestamp=timestamp,
                            token=token,
                            timeframe=row.get('timeframe', ''),
                            direction=row.get('direction', ''),
                            entry=float(row.get('entry', 0) or 0),
                            tp=float(row.get('tp', 0) or 0),
                            sl=float(row.get('sl', 0) or 0),
                            confidence=float(row.get('confidence', 0) or 0),
                            rationale=row.get('rationale', ''),
                            source=row.get('source', ''),
                            mode=mode,
                            raw_response=None
                        )
                        
                        db.add(signal)
                        count += 1
                        migrated += 1
                    
                    db.commit()
                    print(f"✅ {count} signals migrated")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                db.rollback()
    
    db.close()
    return migrated, skipped


def main():
    print("=" * 60)
    print("📊 TraderCopilot - CSV to Database Migration")
    print("=" * 60)
    
    signals_migrated, signals_skipped = migrate_signals()
    
    print("\n" + "=" * 60)
    print("✨ Migration Summary")
    print("=" * 60)
    print(f"Signals migrated:     {signals_migrated}")
    print(f"Signals skipped:      {signals_skipped}")
    print("=" * 60)
    print("✅ Migration completed!")


if __name__ == "__main__":
    main()
