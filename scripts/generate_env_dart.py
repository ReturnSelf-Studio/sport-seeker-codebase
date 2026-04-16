import os
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"
RELEASE_INFO_FILE = ROOT_DIR / "release_info.json"
DART_OUT = ROOT_DIR / "flutter_ui/lib/core/env.dart"

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

    backend_ver = "1.0.0"
    model_ver = "1.0.0"
    if RELEASE_INFO_FILE.exists():
        try:
            info = json.loads(RELEASE_INFO_FILE.read_text(encoding="utf-8"))
            backend_ver = info.get("backend_version", "1.0.0")
            model_ver = info.get("model_version", "1.0.0")
        except Exception as e:
            print(f"⚠️ Lỗi đọc release_info.json: {e}. Dùng version mặc định 1.0.0")

    dart_content = f"""// AUTO-GENERATED FILE. DO NOT EDIT.
class Env {{
  // Backend
  static const String backendBaseUrl = "{backend_url}";
  static const String backendVersionUrl = "{backend_url}version.json";
  static const String bundledBackendVersion = "{backend_ver}"; // Version gốc nhúng sẵn trong App

  // Alias cho BackendManager cũ
  static const String versionUrl = "{backend_url}version.json";

  // AI Models
  static const String modelsBaseUrl = "{models_url}";
  static const String modelsVersionUrl = "{models_url}models_version.json";
  static const String bundledModelVersion = "{model_ver}";
}}
"""
    os.makedirs(os.path.dirname(DART_OUT), exist_ok=True)
    with open(DART_OUT, "w", encoding="utf-8") as f:
        f.write(dart_content)
    print(f"✅ Đã tạo {DART_OUT.relative_to(ROOT_DIR)} với Backend v{backend_ver} | Model v{model_ver}")

if __name__ == "__main__":
    main()
