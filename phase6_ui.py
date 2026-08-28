"""Phase 6 Digital Signatures prototype UI."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from authz import can_access_case
from digital_signatures import sign_document, signature_payload, verify_signature
from extensions import db
from models.case_document import CaseDocument
from models.digital_signature import DigitalSignature


phase6_ui = Blueprint("phase6_ui", __name__)


def _accessible_documents():
    documents = db.session.scalars(
        db.select(CaseDocument).order_by(CaseDocument.created_at.desc())
    ).all()
    return [document for document in documents if can_access_case(current_user, document.case)]


def _signature_or_404(signature_id):
    record = db.session.get(DigitalSignature, signature_id)
    if record is None:
        return None
    if record.case_document_id is not None and record.case_document is not None:
        if not can_access_case(current_user, record.case_document.case):
            return None
    elif record.signer_id != current_user.id:
        return None
    return record


@phase6_ui.route("/signatures")
@login_required
def signature_list():
    records = db.session.scalars(
        db.select(DigitalSignature).order_by(DigitalSignature.signed_at.desc())
    ).all()
    records = [record for record in records if _signature_or_404(record.id) is not None]
    return render_template("signature_list.html", signatures=records)


@phase6_ui.route("/signatures/new", methods=["GET", "POST"])
@login_required
def signature_new():
    documents = _accessible_documents()
    if request.method == "POST":
        uploaded = request.files.get("document")
        if not uploaded or not uploaded.filename:
            flash("Select a document to sign.", "error")
            return render_template("signature_form.html", documents=documents)
        document_bytes = uploaded.read(10 * 1024 * 1024 + 1)
        if len(document_bytes) > 10 * 1024 * 1024:
            flash("Documents must be 10 MB or less.", "error")
            return render_template("signature_form.html", documents=documents)

        case_document_id = request.form.get("case_document_id", type=int)
        if case_document_id:
            case_document = db.session.get(CaseDocument, case_document_id)
            if case_document is None or not can_access_case(current_user, case_document.case):
                flash("You are not authorized to associate this signature with the selected document.", "error")
                return render_template("signature_form.html", documents=documents)
        try:
            record = sign_document(document_bytes, current_user, case_document_id)
        except (ValueError, OSError) as exc:
            db.session.rollback()
            flash(str(exc), "error")
            return render_template("signature_form.html", documents=documents)
        flash("Document signed successfully. This is technical cryptographic verification only.", "success")
        return redirect(url_for("phase6_ui.signature_detail", signature_id=record.id))

    return render_template("signature_form.html", documents=documents)


@phase6_ui.route("/signatures/<int:signature_id>")
@login_required
def signature_detail(signature_id):
    record = _signature_or_404(signature_id)
    if record is None:
        flash("Signed record not found or access denied.", "error")
        return redirect(url_for("phase6_ui.signature_list"))
    return render_template("signature_detail.html", signature=record, payload=signature_payload(record))


@phase6_ui.route("/signatures/<int:signature_id>/verify", methods=["POST"])
@login_required
def signature_verify(signature_id):
    record = _signature_or_404(signature_id)
    if record is None:
        flash("Signed record not found or access denied.", "error")
        return redirect(url_for("phase6_ui.signature_list"))
    uploaded = request.files.get("document")
    if not uploaded or not uploaded.filename:
        flash("Select the original document bytes to verify the signature.", "error")
        return redirect(url_for("phase6_ui.signature_detail", signature_id=record.id))
    document_bytes = uploaded.read(10 * 1024 * 1024 + 1)
    if len(document_bytes) > 10 * 1024 * 1024:
        flash("Documents must be 10 MB or less.", "error")
        return redirect(url_for("phase6_ui.signature_detail", signature_id=record.id))
    try:
        valid = verify_signature(record, document_bytes)
        flash(
            "Signature verified: document hash and Ed25519 signature are valid."
            if valid else
            "Signature verification failed: document hash or signature is invalid.",
            "success" if valid else "error",
        )
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("phase6_ui.signature_detail", signature_id=record.id))


def register_phase6_ui(app):
    """Register the Phase 6 digital-signature blueprint."""
    if "phase6_ui" not in app.blueprints:
        app.register_blueprint(phase6_ui)
