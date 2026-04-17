import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT_DIR / "version.json"

def main():
    if not VERSION_FILE.exists():
        print("Không tìm thấy version.json")
        return

    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Lấy build_number hiện tại và tăng thêm 1
    current_build = data.get("build_number", 0)
    new_build = current_build + 1
    data["build_number"] = new_build

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Đã tăng Build Number lên: {new_build}")

if __name__ == "__main__":
    main()
