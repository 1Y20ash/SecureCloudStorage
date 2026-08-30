"""Local, privacy-conscious OCR service for Phase 7.

Tesseract is invoked locally; document bytes are never sent to an external OCR
provider. OCR output is derived data and never replaces the original document.
"""

import hashlib
import os
import shutil
import subprocess
import tempfile


OCR_ENGINE = "tesseract"
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


class OCRUnavailableError(RuntimeError):
    """Raised when the configured local OCR engine is unavailable."""


class OCRUnsupportedFormatError(ValueError):
    """Raised when the local OCR foundation cannot process a file format."""


def calculate_source_hash(document_bytes: bytes) -> str:
    """Return the SHA-256 hash used to bind OCR output to its source."""
    return hashlib.sha256(document_bytes).hexdigest()


def _tesseract_executable() -> str:
    executable = os.getenv("TESSERACT_CMD") or shutil.which("tesseract")
    if not executable:
        raise OCRUnavailableError(
            "Local OCR is unavailable on this deployment because Tesseract is not installed. "
            "Run SecureCloudStorage locally on a machine with Tesseract installed to use OCR."
        )
    return executable


def is_ocr_available() -> bool:
    """Return whether a local Tesseract executable can be discovered."""
    try:
        _tesseract_executable()
    except OCRUnavailableError:
        return False
    return True


def extract_text(document_bytes: bytes, filename: str, language: str = "eng") -> str:
    """Extract text locally with Tesseract from a supported image.

    No network calls are made. The temporary source image is deleted after OCR.
    """
    if not document_bytes:
        raise ValueError("The document must contain data.")
    extension = os.path.splitext(filename or "")[1].lower()
    if extension not in SUPPORTED_IMAGE_EXTENSIONS:
        raise OCRUnsupportedFormatError(
            f"Tesseract image OCR currently supports: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}."
        )
    executable = _tesseract_executable()
    with tempfile.TemporaryDirectory(prefix="securecloud-ocr-") as temp_dir:
        source_path = os.path.join(temp_dir, "source" + extension)
        output_base = os.path.join(temp_dir, "ocr")
        with open(source_path, "wb") as source_file:
            source_file.write(document_bytes)
        try:
            completed = subprocess.run(
                [executable, source_path, output_base, "-l", language],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
            raise OCRUnavailableError(
                "Local OCR could not start or complete because Tesseract is unavailable on this deployment."
            ) from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or "Tesseract returned a non-zero exit code."
            raise OCRUnavailableError(detail)
        text_path = output_base + ".txt"
        try:
            with open(text_path, "r", encoding="utf-8") as text_file:
                return text_file.read().strip()
        except FileNotFoundError as exc:
            raise OCRUnavailableError("Tesseract completed without producing text output.") from exc
