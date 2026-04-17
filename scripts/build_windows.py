import shutil
import subprocess
import platform
from pathlib import Path
from cli_config import ROOT_DIR, run_cmd
from collect_models import collect_models_into

FLUTTER_UI_DIR = ROOT_DIR / "flutter_ui"
PUBSPEC_FILE = FLUTTER_UI_DIR / "pubspec.yaml"
PUBSPEC_BAK = FLUTTER_UI_DIR / "pubspec.yaml.bak"


def build_windows():
    print("\n===================================================")
    print("   DONG GOI RELEASE WINDOWS (AUTOMATED FLOW)")
    print("===================================================")

    try:
        print("\n[1] Toi uu pubspec.yaml...")
        shutil.copy(PUBSPEC_FILE, PUBSPEC_BAK)
        lines = PUBSPEC_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
        PUBSPEC_FILE.write_text(
            "".join(l for l in lines if "assets/backend/api_payload.zip" not in l),
            encoding="utf-8",
        )

        print("\n[2] Bien dich Flutter...")
        run_cmd("flutter clean", cwd=FLUTTER_UI_DIR)
        run_cmd("flutter pub get", cwd=FLUTTER_UI_DIR)
        run_cmd("flutter build windows", cwd=FLUTTER_UI_DIR)

        dist_dir = ROOT_DIR / "SportSeeker_Windows_Release"
        if dist_dir.exists():
            shutil.rmtree(dist_dir)

        resource_dir = dist_dir / "resource"
        resource_dir.mkdir(parents=True)

        flutter_release = FLUTTER_UI_DIR / "build/windows/x64/runner/Release"
        shutil.copytree(flutter_release, resource_dir, dirs_exist_ok=True)

        backend_dest = resource_dir / "backend"
        backend_dest.mkdir()
        shutil.copy(ROOT_DIR / "main.py", backend_dest)
        shutil.copy(ROOT_DIR / "requirements-windows.txt", backend_dest)
        shutil.copytree(ROOT_DIR / "app", backend_dest / "app")

        print("\n[3] Thu thap AI Models...")
        models_bundle_dir = resource_dir / "models_bundle"
        models_bundle_dir.mkdir(exist_ok=True)
        collect_models_into(models_bundle_dir)

        shutil.copy(ROOT_DIR / "scripts/install_sport_seeker.bat", dist_dir / "install_sport_seeker.bat")
        pdf_guide = ROOT_DIR / "docs/installation_guide_windows.pdf"
        if pdf_guide.exists():
            shutil.copy(pdf_guide, dist_dir / "installation_guide_windows.pdf")

        zip_output = ROOT_DIR / "SportSeeker_Windows"
        zip_output.with_suffix(".zip").unlink(missing_ok=True)

        print(f"\n[4] Nen thanh {zip_output}.zip ...")
        shutil.make_archive(str(zip_output), "zip", str(dist_dir.parent), dist_dir.name)
        shutil.rmtree(dist_dir)
        print("\nHOAN TAT! File gui khach: SportSeeker_Windows.zip")

    finally:
        if PUBSPEC_BAK.exists():
            print("\nKhoi phuc pubspec.yaml nguyen ban...")
            shutil.move(PUBSPEC_BAK, PUBSPEC_FILE)


if __name__ == "__main__":
    if platform.system() != "Windows":
        print("Script nay chi chay tren Windows.")
    else:
        build_windows()
