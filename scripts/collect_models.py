import shutil
from pathlib import Path
from cli_config import ROOT_DIR, get_env, copy_dir, copy_first_found, copy_all_found

HF_MODEL = "models--sentence-transformers--all-MiniLM-L6-v2"


def _build_candidates(env_dir: Path | None) -> dict:
    """Trả về candidates cho từng model, tính từ env_dir và các vị trí mặc định."""
    home = Path.home()
    return {
        "insightface": (
            ([env_dir / "models" / "buffalo_l", env_dir / "buffalo_l"] if env_dir else [])
            + [
                ROOT_DIR / "models" / "models" / "buffalo_l",
                ROOT_DIR / "models" / "buffalo_l",
                home / ".insightface" / "models" / "buffalo_l",
                home / "SportSeeker" / "models" / "models" / "buffalo_l",
            ]
        ),
        "paddle": (
            ([(env_dir / "paddleocr", None)] if env_dir else [])
            + [
                (ROOT_DIR / "models" / "paddleocr", None),
                (home / ".paddleocr",               None),
                (home / ".paddlex",                 "paddlex"),
                (home / ".paddle",                  "paddle"),
            ]
        ),
        "huggingface": (
            ([env_dir / "huggingface" / "hub" / HF_MODEL, env_dir / HF_MODEL] if env_dir else [])
            + [
                ROOT_DIR / "models" / "huggingface" / "hub" / HF_MODEL,
                home / ".cache" / "huggingface" / "hub" / HF_MODEL,
                home / "SportSeeker" / "models" / "huggingface" / "hub" / HF_MODEL,
            ]
        ),
    }


def collect_models_into(dest: Path):
    """
    Thu thập AI models từ máy dev vào dest/ với layout chuẩn để
    install.bat/collect_models.py deploy đúng vị trí trên máy khách.

    Layout:
      dest/models/buffalo_l/        -> %USERPROFILE%\\SportSeeker\\models\\models\\buffalo_l\\
      dest/paddleocr/               -> %USERPROFILE%\\.paddleocr\\
      dest/paddlex/                 -> %USERPROFILE%\\.paddlex\\
      dest/huggingface/hub/<model>/ -> %USERPROFILE%\\.cache\\huggingface\\hub\\
    """
    env_dir_str = get_env("LOCAL_MODELS_SOURCE_DIR")
    env_dir = Path(env_dir_str) if env_dir_str else None
    candidates = _build_candidates(env_dir)

    print("\n[1/3] InsightFace (buffalo_l)...")
    copy_first_found(candidates["insightface"], dest / "models" / "buffalo_l", "InsightFace")

    print("\n[2/3] PaddleOCR / PaddleX...")
    # dst_name=None -> dest/paddleocr, dst_name="paddlex" -> dest/paddlex, dst_name="paddle" -> dest/paddle
    paddle_pairs = [(src, dest / (dst_name if dst_name else "paddleocr")) for src, dst_name in candidates["paddle"]]
    copy_all_found(paddle_pairs, "PaddleOCR/PaddleX")

    print("\n[3/3] HuggingFace (all-MiniLM-L6-v2)...")
    copy_first_found(
        candidates["huggingface"],
        dest / "huggingface" / "hub" / HF_MODEL,
        "HuggingFace model",
    )


def run_collection():
    print("\n===================================================")
    print("   DEEP SCANNING AI MODELS FOR OTA UPDATE")
    print("===================================================")

    staging_dir = ROOT_DIR / "build" / "models_staging"
    zip_out = ROOT_DIR / "build" / "offline_models_payload"

    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)

    collect_models_into(staging_dir)

    zip_out_path = zip_out.with_suffix(".zip")
    if zip_out_path.exists():
        zip_out_path.unlink()

    print("\nDang nen cac models thanh file ZIP...")
    shutil.make_archive(str(zip_out), "zip", str(staging_dir))
    shutil.rmtree(staging_dir)
    print("THANH CONG! File Models Zip tai: build/offline_models_payload.zip")


if __name__ == "__main__":
    run_collection()
