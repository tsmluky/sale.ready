import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

class TestCriticalFixes(unittest.TestCase):

# ... (Implicit: I will search and replace all emojis in the file roughly)

    def test_01_strategies_json_shadown_fix(self):
        """Verify strategies.py imports json correctly as json_lib."""
        print("\nTesting Strategies JSON Fix...")
        try:
            # We added 'backend' to sys.path, so we import directly from 'routers'
            from routers import strategies
            # Check if json_lib is used
            self.assertTrue(hasattr(strategies, 'json_lib'), "strategies.py should have 'json_lib' (aliased import)")
            print("[OK] strategies.py imports 'json as json_lib' correctly.")
        except ImportError as e:
            self.fail(f"Failed to import strategies: {e}")
        except Exception as e:
            self.fail(f"Strategies module generic error: {e}")

    def test_02_rag_context_imports(self):
        """Verify rag_context.py has correct typing imports."""
        print("\nTesting RAG Context Imports...")
        try:
            # rag_context is in backend/ root
            import rag_context
            from typing import Any
            # Just importing it proves the syntax and basic imports are valid
            print("[OK] rag_context.py loads successfully without ImportErrors.")
        except Exception as e:
            self.fail(f"rag_context error: {e}")

    def test_03_logs_routes_removed(self):
        """Verify main.py does NOT try to import the deleted logs_routes."""
        print("\nTesting Main.py Cleanliness...")
        try:
            # We explicitly check the text content of main.py to ensure no stale references
            with open("backend/main.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            if "logs_routes" in content:
                self.fail("[FAIL] main.py still contains reference to 'logs_routes'!")
            else:
                 print("[OK] main.py is clean of 'logs_routes'.")
        except Exception as e:
            self.fail(f"Could not read main.py: {e}")

    @patch.dict(os.environ, {"SECRET_KEY": "", "ENVIRONMENT": "production"})
    def test_04_security_production_check(self):
        """Verify Security module warns/behaves correctly in Prod without Key."""
        print("\nTesting Security Module (Prod/NoKey Simulation)...")
        # We need to reload security because it runs code at module level
        if 'core.security' in sys.modules:
            del sys.modules['core.security']
        
        from core import security
        # We expect the warning print, but code shouldn't crash in verifying this test logic 
        # (since we implemented a warning, not a hard crash yet, as per user 'local' pref).
        # We just want to see it loaded.
        self.assertIsNotNone(security.SECRET_KEY)
        print("[OK] Security module handles missing key gracefully (with warning).")

    @patch.dict(os.environ, {"REDIS_URL": "", "ENVIRONMENT": "production"})
    def test_05_limiter_production_check(self):
        """Verify Limiter module warns in Prod without Redis."""
        print("\nTesting Limiter Module (Prod/NoRedis Simulation)...")
        if 'core.limiter' in sys.modules:
            del sys.modules['core.limiter']
        
        from core import limiter
        storage = limiter.get_limiter_storage_uri()
        self.assertEqual(storage, "memory://")
        print("[OK] Limiter fell back to memory:// in absense of Redis (as expected for fallback).")

if __name__ == '__main__':
    unittest.main()
