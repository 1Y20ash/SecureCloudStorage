from unittest.mock import patch

import pytest

from ocr_service import (
    OCRUnsupportedFormatError,
    calculate_source_hash,
    extract_text,
)


def test_source_hash_is_deterministic():
    assert calculate_source_hash(b"SecureCloudStorage") == calculate_source_hash(b"SecureCloudStorage")
    assert len(calculate_source_hash(b"SecureCloudStorage")) == 64


def test_ocr_rejects_unsupported_format_before_engine_lookup():
    with pytest.raises(OCRUnsupportedFormatError):
        extract_text(b"not an image", "report.pdf")


def test_tesseract_is_invoked_locally_and_text_is_returned(tmp_path):
    with patch("ocr_service._tesseract_executable", return_value="tesseract") as executable:
        with patch("ocr_service.subprocess.run") as run:
            run.return_value.returncode = 0

            def create_output(command, **kwargs):
                output_base = command[2]
                with open(output_base + ".txt", "w", encoding="utf-8") as output:
                    output.write("CASE-2026-001\nForensic report")
                return run.return_value

            run.side_effect = create_output
            text = extract_text(b"image-bytes", "report.png")

    executable.assert_called_once()
    assert text == "CASE-2026-001\nForensic report"
    command = run.call_args.args[0]
    assert command[0] == "tesseract"
    assert command[-2:] == ["-l", "eng"]
