import os
import ast

# Define the root of the backend
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def check_imports(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=file_path)
        except SyntaxError:
            print(f"❌ SyntaxError in {file_path}")
            return []

    errors = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module
            if module:
                # Check for known legacy/problematic modules
                if module == "market_data_api":
                    errors.append(
                        f"Line {node.lineno}: Import validation failed: "
                        f"'market_data_api' should be 'core.market_data_api'"
                    )
                elif module == "strategies.donchian":
                    errors.append(
                        f"Line {node.lineno}: Import validation failed: "
                        f"'strategies.donchian' is deprecated. "
                        f"Use 'strategies.DonchianBreakoutV2'"
                    )

                # Check existence of local modules
                # This is a basic check and might have false positives if not careful
                # We assume imports are relative to BACKEND_ROOT if they don't
                # start with builtin

        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name == "market_data_api":
                    errors.append(
                        f"Line {node.lineno}: Import validation failed: "
                        f"'market_data_api' should be 'core.market_data_api'"
                    )

    return errors


def main():
    print(f"🔍 Scanning for broken imports in {BACKEND_ROOT}...")
    count = 0
    for root, _, files in os.walk(BACKEND_ROOT):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, BACKEND_ROOT)

                # Skip venv and __pycache__ if present (though usually not in src)
                if ".venv" in rel_path or "__pycache__" in rel_path:
                    continue

                issues = check_imports(file_path)
                if issues:
                    print(f"\n📂 {rel_path}:")
                    for issue in issues:
                        print(f"  - {issue}")
                    count += 1

    if count == 0:
        print("\n✅ No obvious legacy import patterns found.")
    else:
        print(f"\n⚠️ Found issues in {count} files.")


if __name__ == "__main__":
    main()
