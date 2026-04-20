import os
import json
import platform
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"
VERSION_FILE = ROOT_DIR / "version.json"
DART_OUT = ROOT_DIR / "frontend/lib/core/env.dart"

def main():
    env_data = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        env_data[parts[0].strip()] = parts[1].strip().strip('"').strip("'")

    backend_url = env_data.get("BACKEND_UPDATE_URL", "https://raw.githubusercontent.com/YourName/YourRepo/main/release_data/")
    models_url = env_data.get("MODELS_UPDATE_URL", "https://raw.githubusercontent.com/YourName/YourRepo/main/release_models/")

    if not backend_url.endswith("/"): backend_url += "/"
    if not models_url.endswith("/"): models_url += "/"

    # Đọc version.json
    app_ver = "1.0.5"
    build_num = 1
    backend_ver = "1.0.1"
    model_ver = "1.0.1"
    
    if VERSION_FILE.exists():
        try:
            info = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
            app_ver = info.get("app_version", "1.0.0")
            build_num = info.get("build_number", 1)
            backend_ver = info.get("backend_version", "1.0.0")
            model_ver = info.get("model_version", "1.0.0")
        except Exception as e:
            print(f"⚠️ Lỗi đọc version.json: {e}")

    os_name = "Windows" if platform.system() == "Windows" else "macOS"

    dart_content = f"""// AUTO-GENERATED FILE. DO NOT EDIT.
class Env {{
  // App Version Info
  static const String appVersion = "{app_ver}";
  static const int buildNumber = {build_num};
  static const String platform = "{os_name}";
  static const String fullVersion = "{app_ver}+{build_num} ({os_name})";

  // Backend
  static const String backendBaseUrl = "{backend_url}";
  static const String backendVersionUrl = "{backend_url}version.json";
  static const String bundledBackendVersion = "{backend_ver}";

  // AI Models
  static const String modelsBaseUrl = "{models_url}";
  static const String modelsVersionUrl = "{models_url}models_version.json";
  static const String bundledModelVersion = "{model_ver}";
}}
"""
    os.makedirs(os.path.dirname(DART_OUT), exist_ok=True)
    with open(DART_OUT, "w", encoding="utf-8") as f:
        f.write(dart_content)
    print(f"✅ Đã tạo env.dart | App v{app_ver}+{build_num} ({os_name}) | Backend v{backend_ver} | Model v{model_ver}")

if __name__ == "__main__":
    main()
