"""Phase 7 OCR processing and privacy-conscious document search UI."""

from datetime import datetime, timezone

from cryptography.exceptions import InvalidTag
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from authz import can_access_document
from crypto.encryption import decrypt_file
from extensions import db
from models.case_document import CaseDocument
from models.ocr_document import OCRDocument
from ocr_service import (
    OCRUnavailableError,
    OCRUnsupportedFormatError,
    calculate_source_hash,
    extract_text,
    is_ocr_available,
)


phase7_ui = Blueprint("phase7_ui", __name__)


def _accessible_documents():
    documents = db.session.scalars(
        db.select(CaseDocument).order_by(CaseDocument.created_at.desc())
    ).all()
    return [
        document
        for document in documents
        if can_access_document(current_user, document)
    ]


def _document_or_404(document_id):
    document = db.session.get(CaseDocument, document_id)
    if document is None or not can_access_document(current_user, document):
        return None
    return document


@phase7_ui.route("/search")
@login_required
def document_search():
    query = request.args.get("q", "").strip()
    case_number = request.args.get("case_id", "").strip()
    category = request.args.get("category", "").strip()
    officer = request.args.get("officer", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    documents = _accessible_documents()
    if query:
        needle = query.casefold()
        documents = [
            d for d in documents
            if needle in d.stored_file.original_filename.casefold()
            or needle in (d.case.case_number or "").casefold()
            or needle in (d.category or "").casefold()
            or needle in (d.case.title or "").casefold()
            or (d.ocr_document and needle in (d.ocr_document.extracted_text or "").casefold())
        ]
    if case_number:
        documents = [d for d in documents if d.case.case_number.casefold() == case_number.casefold()]
    if category:
        documents = [d for d in documents if d.category == category]
    if officer:
        needle = officer.casefold()
        documents = [
            d for d in documents
            if needle in (d.case.creator.name or "").casefold()
            or any(needle in (assignment.user.name or "").casefold() for assignment in d.case.assignments)
        ]

    def parse_date(value):
        try:
            return datetime.fromisoformat(value).date() if value else None
        except ValueError:
            return None

    start = parse_date(date_from)
    end = parse_date(date_to)
    if start:
        documents = [d for d in documents if d.created_at.date() >= start]
    if end:
        documents = [d for d in documents if d.created_at.date() <= end]

    categories = sorted({d.category for d in _accessible_documents()})
    officers = sorted(
        {d.case.creator for d in _accessible_documents()} |
        {assignment.user for d in _accessible_documents() for assignment in d.case.assignments},
        key=lambda user: user.name.casefold(),
    )
    return render_template(
        "document_search.html",
        documents=documents,
        query=query,
        case_number=case_number,
        category=category,
        officer=officer,
        date_from=date_from,
        date_to=date_to,
        categories=categories,
        officers=officers,
    )


@phase7_ui.route("/documents/<int:document_id>/ocr", methods=["POST"])
@login_required
def document_ocr(document_id):
    document = _document_or_404(document_id)
    if document is None:
        flash("Document not found or access denied.", "error")
        return redirect(url_for("phase7_ui.document_search"))

    # OCR is deliberately local. Vercel can host the application, but it does
    # not provide the system Tesseract executable used by this Phase 7 feature.
    if not is_ocr_available():
        flash(
            "Local OCR is unavailable on this deployment because Tesseract is not installed. "
            "Run SecureCloudStorage locally on a machine with Tesseract installed to use OCR.",
            "error",
        )
        return redirect(request.referrer or url_for("phase7_ui.document_search"))

    password = request.form.get("encryption_password", "")
    if not password:
        flash("Enter the document encryption password to run local OCR.", "error")
        return redirect(request.referrer or url_for("phase7_ui.document_search"))

    stored_file = document.stored_file
    try:
        encrypted_data = _read_encrypted_file(stored_file.encrypted_filename)
        document_bytes = decrypt_file(encrypted_data, password)
        source_hash = calculate_source_hash(document_bytes)
        if stored_file.sha256_hash and source_hash != stored_file.sha256_hash:
            raise ValueError("Decrypted document hash does not match its stored integrity record.")
        extracted_text = extract_text(
            document_bytes,
            stored_file.original_filename,
            request.form.get("language", "eng").strip() or "eng",
        )

        record = document.ocr_document
        if record is None:
            record = OCRDocument(
                case_document_id=document.id,
                source_sha256=source_hash,
                extracted_text=extracted_text,
                engine="tesseract",
                status="COMPLETED",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.session.add(record)
        else:
            record.source_sha256 = source_hash
            record.extracted_text = extracted_text
            record.engine = "tesseract"
            record.status = "COMPLETED"
            record.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    except InvalidTag:
        db.session.rollback()
        flash("Incorrect password or corrupted encrypted file. OCR was not performed.", "error")
        return redirect(request.referrer or url_for("phase7_ui.document_search"))
    except (OCRUnavailableError, OCRUnsupportedFormatError, ValueError, OSError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return redirect(request.referrer or url_for("phase7_ui.document_search"))
    except Exception:
        # OCR must never turn an environment-specific failure into a Flask 500.
        # Log the diagnostic server-side while keeping the user-facing message safe.
        db.session.rollback()
        current_user  # keep authentication context explicit for this protected route
        import logging
        logging.getLogger(__name__).exception("Phase 7 OCR processing failed")
        flash("Local OCR could not be completed. No changes were made to the stored document.", "error")
        return redirect(request.referrer or url_for("phase7_ui.document_search"))

    flash("OCR completed locally. The original encrypted document was preserved.", "success")
    return redirect(request.referrer or url_for("phase7_ui.document_search"))


def _read_encrypted_file(filename):
    from app import USE_SUPABASE_STORAGE, supabase, SUPABASE_STORAGE_BUCKET, UPLOAD_FOLDER
    import os

    if USE_SUPABASE_STORAGE:
        return supabase.storage.from_(SUPABASE_STORAGE_BUCKET).download(filename)
    with open(os.path.join(UPLOAD_FOLDER, filename), "rb") as encrypted_file:
        return encrypted_file.read()


def register_phase7_ui(app):
    """Register the Phase 7 OCR/search blueprint."""
    if "phase7_ui" not in app.blueprints:
        app.register_blueprint(phase7_ui)
