
import sys
import os
import json
import subprocess
import datetime
from pathlib import Path
import re

# Add parent to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

from main import app
from database import engine, Base
from sqlalchemy import create_mock_engine

def dump_schema(url, metadata, stream):
    def dump(sql, *multiparams, **params):
        stream.write(f"{sql.compile(dialect=engine.dialect)};\n")
    
    mock_engine = create_mock_engine(url, dump)
    metadata.create_all(mock_engine, checkfirst=False)

def scan_env_keys(root_dir):
    keys = set()
    regex = re.compile(r'os\.getenv\(["\']([A-Z_]+)["\']')
    
    for path in Path(root_dir).rglob("*.py"):
        if "venv" in str(path) or "__pycache__" in str(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
            matches = regex.findall(content)
            keys.update(matches)
        except:
            pass
    return sorted(list(keys))

def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = BACKEND_DIR / "audit" / "runs" / ts
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating bundle in: {output_dir}")

    # 1. OpenAPI
    print("Generating openapi.json...")
    with open(output_dir / "openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)

    # 2. Routes
    print("Generating routes.txt...")
    from fastapi.routing import APIRoute
    with open(output_dir / "routes.txt", "w") as f:
        for route in app.routes:
            if isinstance(route, APIRoute):
                methods = ",".join(route.methods)
                f.write(f"{methods} | {route.path_format} | {route.name}\n")

    # 3. DB Schema
    print("Generating db_schema.sql...")
    with open(output_dir / "db_schema.sql", "w") as f:
        # Use existing engine URL or mock
        url = "postgresql://" 
        dump_schema(url, Base.metadata, f)

    # 4. Env Keys
    print("Scanning Env Keys...")
    keys = scan_env_keys(BACKEND_DIR)
    with open(output_dir / "env_keys.txt", "w") as f:
        for k in keys:
            f.write(f"{k}\n")

    # 5. Smoke Test
    print("Running Smoke Test...")
    smoke_path = BACKEND_DIR / "verify_system.py"
    if smoke_path.exists():
        try:
            res = subprocess.run([sys.executable, str(smoke_path)], capture_output=True, text=True, timeout=10)
            with open(output_dir / "smoke_local.txt", "w") as f:
                f.write(res.stdout)
                f.write("\n--- STDERR ---\n")
                f.write(res.stderr)
        except Exception as e:
            with open(output_dir / "smoke_local.txt", "w") as f:
                f.write(f"Error running smoke test: {e}")
    else:
        with open(output_dir / "smoke_local.txt", "w") as f:
            f.write("verify_system.py not found.")

    # 6. Security Checks
    print("Running Security Matrix & Collision Detectors...")
    security_out = []
    
    # Matrix
    try:
        res = subprocess.run(
            [sys.executable, str(BACKEND_DIR / "audit" / "test_security_matrix.py")],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=BACKEND_DIR
        )
        security_out.append(f"=== SECURITY MATRIX ===\n{res.stdout}\n{res.stderr}")
    except Exception as e:
        security_out.append(f"Matrix Test Failed: {e}")

    # Collision
    try:
        res = subprocess.run(
            [sys.executable, str(BACKEND_DIR / "audit" / "detect_route_collisions.py")],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=BACKEND_DIR
        )
        security_out.append(f"=== ROUTE COLLISIONS ===\n{res.stdout}\n{res.stderr}")
    except Exception as e:
        security_out.append(f"Collision Test Failed: {e}")
        
    with open(output_dir / "security_checks.txt", "w") as f:
        f.write("\n\n".join(security_out))

if __name__ == "__main__":
    main()
