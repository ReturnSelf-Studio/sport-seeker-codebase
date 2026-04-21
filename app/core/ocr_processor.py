"""
app/core/ocr_processor.py

Factory — route sang platform-specific implementation.
"""

import sys

if sys.platform == "win32":
    from app.core.ocr_processor_windows import OCRProcessor
else:
    from app.core.ocr_processor_macos import OCRProcessor

__all__ = ["OCRProcessor"]