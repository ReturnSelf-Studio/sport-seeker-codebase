import json
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT_DIR / "version.json"

# Các file/folder Python ảnh hưởng đến backend
BACKEND_SOURCES = [
    ROOT_DIR / "main.py",
    ROOT_DIR / "app",
    ROOT_DIR / "requirements-windows.txt",
    ROOT_DIR / "requirements.txt",
    ROOT_DIR / "pyproject.toml",
    ROOT_DIR / "uv.toml",
]

def compute_backend_hash() -> str:
    """Hash toàn bộ file Python/config trong backend sources."""
    sha256 = hashlib.sha256()
    files = []

    for src in BACKEND_SOURCES:
        if not src.exists():
            continue
        if src.is_file():
            files.append(src)
        elif src.is_dir():
            files.extend(sorted(src.rglob("*.py")))

    for f in sorted(files):
        sha256.update(str(f.relative_to(ROOT_DIR)).encode())
        sha256.update(f.read_bytes())

    return sha256.hexdigest()

def bump_version(version: str) -> str:
    """Bump patch: 1.0.1 → 1.0.2"""
    parts = version.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)

def main():
    if not VERSION_FILE.exists():
        print("Không tìm thấy version.json")
        return

    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Bump build number
    current_build = data.get("build_number", 0)
    data["build_number"] = current_build + 1
    print(f"Build Number: {current_build} → {data['build_number']}")

    # Check backend hash
    current_hash = compute_backend_hash()
    stored_hash = data.get("backend_source_hash", "")

    if current_hash != stored_hash:
        old_ver = data.get("backend_version", "1.0.0")
        new_ver = bump_version(old_ver)
        data["backend_version"] = new_ver
        data["backend_source_hash"] = current_hash
        print(f"Backend thay đổi → backend_version: {old_ver} → {new_ver}")
    else:
        print(f"Backend không thay đổi → backend_version giữ nguyên: {data.get('backend_version')}")

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
