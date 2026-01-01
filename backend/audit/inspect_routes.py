
import sys
import os
import json

# Add parent directory to path to import main
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from fastapi.routing import APIRoute

print("=== TRADERCOPILOT BACKEND ROUTES ===")
print("Method | Path | Auth Required? | Function")
print("---|---|---|---")

routes = []
for route in app.routes:
    if isinstance(route, APIRoute):
        methods = ",".join(route.methods)
        is_auth = "get_current_user" in str(route.dependencies)
        is_pro = "require_pro" in str(route.dependencies)
        auth = "Yes" if is_auth or is_pro else "No (Public?)"
        # Check explicit dependencies inspecting the route object is hard, 
        # but we can look for 'Depends' in the signature repr or manually labeled.
        # Simple heuristic:
        tags = route.tags
        if "Auth" in tags or "/auth/" in route.path_format:
             auth = "Yes"
        
        print(f"{methods} | {route.path_format} | {auth} | {route.name}")
        routes.append({
            "method": methods,
            "path": route.path_format,
            "auth_guess": auth,
            "name": route.name
        })

with open("route_evidence.json", "w") as f:
    json.dump(routes, f, indent=2)

print("\n[SUCCESS] Routes exported to route_evidence.json")
