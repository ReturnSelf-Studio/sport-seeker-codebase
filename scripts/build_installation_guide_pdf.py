#!/usr/bin/env python3
"""
build_installation_guide_pdf.py – Build PDF hướng dẫn cài đặt Sport Seeker
từ file .md + screenshot + font tiếng Việt.

Usage:
    python build_installation_guide_pdf.py -i docs/ -o dist/pdf/ -a assets/
    python build_installation_guide_pdf.py -i docs/ -o dist/pdf/ -a assets/ installation_guide_windows.md
"""

import sys
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Preformatted, Image, KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── Màu sắc ──────────────────────────────────────────────────────────────────
COLOR_HEADING  = colors.HexColor("#C0392B")
COLOR_SUBTEXT  = colors.HexColor("#555555")
COLOR_CODE_BG  = colors.HexColor("#F4F4F4")
COLOR_CODE_TXT = colors.HexColor("#2C2C2C")
COLOR_WARN_BG  = colors.HexColor("#FFF8E1")
COLOR_WARN_TXT = colors.HexColor("#7B4F00")
COLOR_HR       = colors.HexColor("#DDDDDD")
COLOR_FOOTER   = colors.HexColor("#AAAAAA")
COLOR_CAPTION  = colors.HexColor("#888888")
COLOR_BLACK    = colors.black

# ─── Page layout ──────────────────────────────────────────────────────────────
W, H       = A4
MARGIN_L   = 20 * mm
MARGIN_R   = 20 * mm
MARGIN_T   = 18 * mm
MARGIN_B   = 18 * mm
TEXT_WIDTH = W - MARGIN_L - MARGIN_R

# ─── Font loader ──────────────────────────────────────────────────────────────
FONT_NORMAL  = "Helvetica"
FONT_BOLD    = "Helvetica-Bold"
FONT_ITALIC  = "Helvetica-Oblique"
FONT_BOLDITA = "Helvetica-BoldOblique"
FONT_MONO    = "Courier"

def load_fonts(assets_dir: Path) -> bool:
    """
    Thử load Be Vietnam Pro từ assets/fonts/Be_Vietnam_Pro/.
    Fallback theo thứ tự: DejaVuSans → Helvetica.
    Trả về True nếu load được custom font.
    """
    global FONT_NORMAL, FONT_BOLD, FONT_ITALIC, FONT_BOLDITA, FONT_MONO

    # 1. Be Vietnam Pro từ assets/
    bvp_dir = assets_dir / "fonts" / "Be_Vietnam_Pro"
    candidates = {
        "BeVietnamPro-Regular":    bvp_dir / "BeVietnamPro-Regular.ttf",
        "BeVietnamPro-Bold":       bvp_dir / "BeVietnamPro-Bold.ttf",
        "BeVietnamPro-Italic":     bvp_dir / "BeVietnamPro-Italic.ttf",
        "BeVietnamPro-BoldItalic": bvp_dir / "BeVietnamPro-BoldItalic.ttf",
    }
    if all(p.exists() for p in candidates.values()):
        for name, path in candidates.items():
            pdfmetrics.registerFont(TTFont(name, str(path)))
        from reportlab.pdfbase.fontfinder import FontFinder
        FONT_NORMAL  = "BeVietnamPro-Regular"
        FONT_BOLD    = "BeVietnamPro-Bold"
        FONT_ITALIC  = "BeVietnamPro-Italic"
        FONT_BOLDITA = "BeVietnamPro-BoldItalic"
        print("  ✓ Font: Be Vietnam Pro")
        return True

    # 2. DejaVuSans (thường có sẵn trên Linux)
    dv_regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    dv_bold    = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    dv_mono    = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    if dv_regular.exists():
        pdfmetrics.registerFont(TTFont("DejaVuSans",      str(dv_regular)))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(dv_bold)))
        pdfmetrics.registerFont(TTFont("DejaVuSansMono",  str(dv_mono)))
        FONT_NORMAL  = "DejaVuSans"
        FONT_BOLD    = "DejaVuSans-Bold"
        FONT_ITALIC  = "DejaVuSans"       # DejaVu không có Italic riêng
        FONT_BOLDITA = "DejaVuSans-Bold"
        FONT_MONO    = "DejaVuSansMono"
        print("  ✓ Font: DejaVuSans (fallback)")
        return True

    # 3. Helvetica built-in
    print("  ℹ Font: Helvetica (tiếng Việt có thể bị mất dấu)")
    return False

# ─── Styles ───────────────────────────────────────────────────────────────────
def make_styles() -> dict:
    return {
        "brand": ParagraphStyle(
            "brand", fontName=FONT_BOLD, fontSize=28,
            textColor=COLOR_BLACK, spaceAfter=2,
            alignment=TA_CENTER, leading=34,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName=FONT_ITALIC, fontSize=13,
            textColor=COLOR_SUBTEXT, spaceAfter=10,
            alignment=TA_CENTER, leading=18,
        ),
        "h2": ParagraphStyle(
            "h2", fontName=FONT_BOLD, fontSize=15,
            textColor=COLOR_HEADING, spaceBefore=14, spaceAfter=4, leading=20,
        ),
        "h3": ParagraphStyle(
            "h3", fontName=FONT_BOLD, fontSize=12,
            textColor=COLOR_HEADING, spaceBefore=10, spaceAfter=3, leading=16,
        ),
        "body": ParagraphStyle(
            "body", fontName=FONT_NORMAL, fontSize=10,
            textColor=COLOR_BLACK, spaceAfter=6,
            leading=15, alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName=FONT_NORMAL, fontSize=10,
            textColor=COLOR_BLACK, spaceAfter=4,
            leading=15, leftIndent=14,
        ),
        "numbered": ParagraphStyle(
            "numbered", fontName=FONT_NORMAL, fontSize=10,
            textColor=COLOR_BLACK, spaceAfter=4,
            leading=15, leftIndent=20,
        ),
        "blockquote": ParagraphStyle(
            "blockquote", fontName=FONT_ITALIC, fontSize=10,
            textColor=COLOR_WARN_TXT, backColor=COLOR_WARN_BG,
            spaceAfter=6, spaceBefore=4, leading=15,
            leftIndent=12, rightIndent=12,
            borderPadding=(5, 8, 5, 8),
        ),
        "code": ParagraphStyle(
            "code", fontName=FONT_MONO, fontSize=9,
            textColor=COLOR_CODE_TXT, backColor=COLOR_CODE_BG,
            spaceAfter=6, spaceBefore=4, leading=14,
            leftIndent=10, rightIndent=10,
            borderPadding=(6, 8, 6, 8),
        ),
        "caption": ParagraphStyle(
            "caption", fontName=FONT_ITALIC, fontSize=8,
            textColor=COLOR_CAPTION, alignment=TA_CENTER,
            spaceAfter=6, leading=11,
        ),
        "footer": ParagraphStyle(
            "footer", fontName=FONT_ITALIC, fontSize=8,
            textColor=COLOR_FOOTER, alignment=TA_CENTER, leading=11,
        ),
    }

# ─── Screenshot loader ────────────────────────────────────────────────────────
def load_screenshots(assets_dir: Path, guide_stem: str) -> dict[str, Path]:
    """
    Scan assets/pdf-screenshots/<guide-stem>/ cho các file sc-<guide-stem>-<field>.png.
    Trả về dict: field_name → Path.
    guide_stem ví dụ: "installation-guide-windows"
    """
    screen_dir = assets_dir / "pdf-screenshots" / guide_stem
    result: dict[str, Path] = {}
    if not screen_dir.exists():
        return result
    prefix = f"sc-{guide_stem}-"
    for f in sorted(screen_dir.glob("sc-*.png")):
        if f.stem.startswith(prefix):
            field = f.stem[len(prefix):]   # bỏ "sc-<guide>-"
            result[field] = f
    return result

def make_image_flowable(img_path: Path, styles: dict, max_width: float = None) -> list:
    """Trả về [Image, caption Paragraph] với width fit TEXT_WIDTH."""
    from PIL import Image as PILImage
    max_w = max_width or TEXT_WIDTH
    with PILImage.open(img_path) as im:
        iw, ih = im.size
    ratio  = ih / iw
    width  = min(max_w, iw)          # không phóng to hơn thật
    height = width * ratio

    # Caption: bỏ prefix sc-<guide>-, replace - → space, title case
    stem   = img_path.stem           # sc-installation-guide-windows-extract-zip
    parts  = stem.split("-")
    # Tìm vị trí bắt đầu field (sau "sc-<pdf-name>-")
    # Convention: sc + guide(2 tokens) + field(>=1 token) → bỏ 3 token đầu (sc, guide-part1, guide-part2...)
    # Đơn giản hơn: bỏ prefix "sc-installation-guide-windows-"
    prefix_tokens = ["sc"] + [p for p in stem.split("-")[1:] if p]
    # Lấy tên file sau prefix sc-<guide_stem>-
    guide_token_count = len(img_path.parent.name.split("-"))  # vd "installation-guide-windows" → 3
    field_parts = parts[1 + guide_token_count:]               # bỏ "sc" + guide tokens
    caption_text = " ".join(field_parts).replace("-", " ").title()

    img_flowable = Image(str(img_path), width=width, height=height)
    img_flowable.hAlign = "CENTER"
    cap_flowable = Paragraph(caption_text, styles["caption"])

    return [img_flowable, cap_flowable]

# ─── Inline markdown ──────────────────────────────────────────────────────────
def inline_md(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", rf'<font name="{FONT_MONO}" color="#c0392b">\1</font>', text)
    return text

# ─── MD → flowables ───────────────────────────────────────────────────────────
def md_to_flowables(
    md_text: str,
    styles: dict,
    screenshots: dict[str, Path],   # field → Path
    guide_stem: str,
) -> list:
    """
    Parse markdown → ReportLab flowables.
    Sau mỗi H3 step, inject screenshot tương ứng nếu có.
    Map: H3 text → field name bằng cách slugify H3.
    """
    story      = []
    lines      = md_text.splitlines()
    i          = 0
    in_code    = False
    code_lines: list[str] = []
    footer_text = ""

    def slugify(text: str) -> str:
        """'Bước 1 – Giải nén file' → 'giai-nen-file'"""
        text = text.lower()
        # Bỏ dấu tiếng Việt cơ bản (ASCII-safe slug)
        vi_map = str.maketrans(
            "àáâãäåèéêëìíîïòóôõöùúûüýăắặầấẩẫằặẻẽẹếềểễệỉịọốồổỗộớờởỡợụứừửữựỳỷỹỵđ"
            "ÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÝĂẮẶẦẤẨẪẰẶẺẼẸẾỀỂỄỆỈỊỌỐỒỔỖỘỚỜỞỠỢỤỨỪỬỮỰỲỶỸỴĐ",
            "aaaaaaeeeeiiiioooooouuuuyaaaaaaaaaeeeeeeeeiioooooooooouuuuuuyyyyd"
            "aaaaaaeeeeiiiioooooouuuuyaaaaaaaaaeeeeeeeeiioooooooooouuuuuuyyyyd",
        )
        text = text.translate(vi_map)
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_–—]+", "-", text).strip("-")
        # Bỏ phần "buoc-N-" ở đầu nếu có
        text = re.sub(r"^buoc-\d+-", "", text)
        return text

    def inject_screenshot(h3_text: str):
        """Tìm screenshot map với H3 và thêm vào story."""
        slug = slugify(h3_text)
        matched = None
        # Tìm field gần đúng nhất
        for field, path in screenshots.items():
            if slug in field or field in slug:
                matched = path
                break
        if matched:
            story.extend(make_image_flowable(matched, styles))

    while i < len(lines):
        line = lines[i]

        # ── Code block ──
        if line.strip().startswith("```"):
            if not in_code:
                in_code    = True
                code_lines = []
            else:
                in_code = False
                story.append(Preformatted("\n".join(code_lines), styles["code"]))
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        # ── Footer italic line ──
        if re.match(r"^\*[^*].*[^*]\*$", line.strip()):
            footer_text = line.strip().strip("*")
            i += 1
            continue

        # ── H1 ──
        if line.startswith("# "):
            story.append(Spacer(1, 4 * mm))
            story.append(Paragraph(line[2:].strip(), styles["brand"]))
            i += 1
            continue

        # ── H2 ──
        if line.startswith("## "):
            text = inline_md(line[3:].strip())
            if story and hasattr(story[-1], "style") and story[-1].style.name == "brand":
                story.append(Paragraph(text, styles["subtitle"]))
                story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_HR, spaceAfter=8))
            else:
                story.append(Paragraph(text, styles["h2"]))
            i += 1
            continue

        # ── H3 ──
        if line.startswith("### "):
            h3_raw  = line[4:].strip()
            h3_text = inline_md(h3_raw)
            story.append(Paragraph(h3_text, styles["h3"]))
            # Collect nội dung block này rồi inject screenshot ở cuối
            i += 1
            block: list = []
            while i < len(lines):
                l = lines[i]
                if l.startswith("#") or l.strip() == "---":
                    break
                if l.strip().startswith("```"):
                    if not in_code:
                        in_code    = True
                        code_lines = []
                    else:
                        in_code = False
                        block.append(Preformatted("\n".join(code_lines), styles["code"]))
                    i += 1
                    continue
                if in_code:
                    code_lines.append(l)
                    i += 1
                    continue
                if l.startswith("> "):
                    block.append(Paragraph(inline_md(l[2:].strip()), styles["blockquote"]))
                elif re.match(r"^\d+\.\s", l):
                    m = re.match(r"^(\d+)\.\s+(.*)", l)
                    block.append(Paragraph(f"{m.group(1)}. {inline_md(m.group(2))}", styles["numbered"]))
                elif l.startswith("- "):
                    block.append(Paragraph(f"• {inline_md(l[2:].strip())}", styles["bullet"]))
                elif l.strip() == "":
                    block.append(Spacer(1, 2 * mm))
                else:
                    t = inline_md(l.strip())
                    if t:
                        block.append(Paragraph(t, styles["body"]))
                i += 1
            story.extend(block)
            inject_screenshot(h3_raw)
            continue

        # ── HR ──
        if line.strip() == "---":
            story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_HR, spaceBefore=4, spaceAfter=4))
            i += 1
            continue

        # ── Blockquote ──
        if line.startswith("> "):
            story.append(Paragraph(inline_md(line[2:].strip()), styles["blockquote"]))
            i += 1
            continue

        # ── Numbered list ──
        m = re.match(r"^(\d+)\.\s+(.*)", line)
        if m:
            story.append(Paragraph(f"{m.group(1)}. {inline_md(m.group(2))}", styles["numbered"]))
            i += 1
            continue

        # ── Bullet ──
        if line.startswith("- "):
            story.append(Paragraph(f"• {inline_md(line[2:].strip())}", styles["bullet"]))
            i += 1
            continue

        # ── Empty ──
        if line.strip() == "":
            story.append(Spacer(1, 3 * mm))
            i += 1
            continue

        # ── Body ──
        t = inline_md(line.strip())
        if t:
            story.append(Paragraph(t, styles["body"]))
        i += 1

    # Footer
    if footer_text:
        story.append(Spacer(1, 8 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_HR, spaceAfter=4))
        story.append(Paragraph(footer_text, styles["footer"]))

    return story

# ─── Build ────────────────────────────────────────────────────────────────────
def build_pdf(md_path: Path, out_path: Path, assets_dir: Path):
    print(f"  Building: {md_path.name} → {out_path.name}")

    # guide stem: "installation_guide_windows" → "installation-guide-windows"
    guide_stem  = md_path.stem.replace("_", "-")
    screenshots = load_screenshots(assets_dir, guide_stem)
    if screenshots:
        print(f"  ✓ Screenshots: {list(screenshots.keys())}")
    else:
        print(f"  ℹ Screenshots: không tìm thấy tại assets/pdf-screenshots/{guide_stem}/")

    styles   = make_styles()
    md_text  = md_path.read_text(encoding="utf-8")
    story    = md_to_flowables(md_text, styles, screenshots, guide_stem)

    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T,  bottomMargin=MARGIN_B,
        title=md_path.stem.replace("_", " ").title(),
        author="Returnself Studio",
        subject="Sport Seeker Installation Guide",
    )
    doc.build(story)
    print(f"  ✓ Done: {out_path}")

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Build PDF hướng dẫn cài đặt Sport Seeker từ .md + screenshots + font",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python build_installation_guide_pdf.py -i docs/ -o dist/pdf/ -a assets/
  python build_installation_guide_pdf.py -i docs/ -o dist/pdf/ -a assets/ installation_guide_windows.md
""",
    )
    parser.add_argument(
        "files", nargs="*",
        help="File .md cần build (mặc định: tất cả .md trong --input)",
    )
    parser.add_argument(
        "-i", "--input",  default=".", metavar="DIR",
        help="Thư mục chứa file .md (mặc định: thư mục hiện tại)",
    )
    parser.add_argument(
        "-o", "--output", default=".", metavar="DIR",
        help="Thư mục chứa PDF output (mặc định: thư mục hiện tại)",
    )
    parser.add_argument(
        "-a", "--assets", default="assets", metavar="DIR",
        help="Thư mục assets/ chứa fonts/ và pdf-screenshots/ (mặc định: assets/)",
    )
    args = parser.parse_args()

    input_dir  = Path(args.input)
    output_dir = Path(args.output)
    assets_dir = Path(args.assets)
    output_dir.mkdir(parents=True, exist_ok=True)

    load_fonts(assets_dir)

    if args.files:
        targets = [
            input_dir / f if not Path(f).is_absolute() else Path(f)
            for f in args.files
        ]
    else:
        targets = sorted(input_dir.glob("*.md"))
        if not targets:
            print(f"  ✗ Không tìm thấy file .md trong: {input_dir}")
            return

    for md_path in targets:
        if not md_path.exists():
            print(f"  ✗ Không tìm thấy: {md_path}")
            continue
        out_path = output_dir / (md_path.stem + ".pdf")
        build_pdf(md_path, out_path, assets_dir)

if __name__ == "__main__":
    main()
