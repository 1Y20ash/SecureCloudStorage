"""Web UI routes for Phase 5 evidence and chain-of-custody workflows."""

from datetime import datetime, timezone
import hashlib

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from authz import can_access_case
from evidence_management import (
    TRANSITIONS,
    create_evidence,
    get_custody_chain,
    receive_evidence,
    transfer_evidence,
    transition_evidence,
    verify_evidence_integrity,
)
from extensions import db
from models.case import Case
from models.file import StoredFile
from models.user import User
from models.evidence import Evidence


phase5_ui = Blueprint("phase5_ui", __name__)


def _accessible_cases():
    return db.session.scalars(
        db.select(Case).order_by(Case.created_at.desc())
    ).all()


def _evidence_or_404(evidence_id):
    evidence = db.session.get(Evidence, evidence_id)
    if evidence is None or not can_access_case(current_user, evidence.case):
        return None
    return evidence


def _accessible_users(case):
    assigned_ids = {case.created_by} | {assignment.user_id for assignment in case.assignments}
    if not assigned_ids:
        return []
    return db.session.scalars(
        db.select(User).where(User.id.in_(assigned_ids)).order_by(User.name.asc())
    ).all()


@phase5_ui.route("/evidence")
@login_required
def evidence_list():
    cases = _accessible_cases()
    case_ids = [case.id for case in cases if can_access_case(current_user, case)]
    if not case_ids:
        evidence_items = []
    else:
        evidence_items = db.session.scalars(
            db.select(Evidence)
            .where(Evidence.case_id.in_(case_ids))
            .order_by(Evidence.created_at.desc())
        ).all()
    return render_template("evidence_list.html", evidence_items=evidence_items)


@phase5_ui.route("/evidence/new", methods=["GET", "POST"])
@login_required
def evidence_new():
    cases = [case for case in _accessible_cases() if can_access_case(current_user, case)]
    files = db.session.scalars(
        db.select(StoredFile)
        .where(StoredFile.user_id == current_user.id)
        .order_by(StoredFile.uploaded_at.desc())
    ).all()

    if request.method == "POST":
        case_id = request.form.get("case_id", type=int)
        evidence_type = request.form.get("evidence_type", "").strip()
        description = request.form.get("description", "").strip()
        collection_location = request.form.get("collection_location", "").strip()
        collection_datetime = request.form.get("collection_datetime", "").strip()
        stored_file_id = request.form.get("stored_file_id", type=int)
        uploaded = request.files.get("integrity_file")
        sha256_hash = request.form.get("sha256_hash", "").strip()

        case = db.session.get(Case, case_id) if case_id else None
        if case is None or not can_access_case(current_user, case):
            flash("Select a case you are authorized to access.", "error")
            return render_template("evidence_form.html", cases=cases, files=files)

        stored_file = db.session.get(StoredFile, stored_file_id) if stored_file_id else None
        if stored_file is not None and stored_file.user_id != current_user.id:
            stored_file = None
        if stored_file is not None and stored_file.sha256_hash:
            sha256_hash = stored_file.sha256_hash

        if uploaded and uploaded.filename:
            file_bytes = uploaded.read()
            if len(file_bytes) > 10 * 1024 * 1024:
                flash("Integrity verification files must be 10 MB or less.", "error")
                return render_template("evidence_form.html", cases=cases, files=files)
            sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        if not sha256_hash:
            flash("Select a stored file, upload the evidence bytes, or enter a SHA-256 hash.", "error")
            return render_template("evidence_form.html", cases=cases, files=files)

        collected_by = request.form.get("collected_by", type=int) or current_user.id
        try:
            parsed_datetime = datetime.fromisoformat(collection_datetime) if collection_datetime else datetime.now(timezone.utc)
            evidence = create_evidence(
                case_id=case.id,
                evidence_type=evidence_type,
                description=description,
                collected_by=collected_by,
                collection_location=collection_location,
                collection_datetime=parsed_datetime,
                sha256_hash=sha256_hash,
                actor_user_id=current_user.id,
                stored_file_id=stored_file.id if stored_file else None,
            )
        except (ValueError, PermissionError) as exc:
            db.session.rollback()
            flash(str(exc), "error")
            return render_template("evidence_form.html", cases=cases, files=files)

        flash(f"Evidence {evidence.evidence_id} registered successfully.", "success")
        return redirect(url_for("phase5_ui.evidence_detail", evidence_id=evidence.id))

    return render_template("evidence_form.html", cases=cases, files=files)


@phase5_ui.route("/evidence/<int:evidence_id>")
@login_required
def evidence_detail(evidence_id):
    evidence = _evidence_or_404(evidence_id)
    if evidence is None:
        flash("Evidence not found or access denied.", "error")
        return redirect(url_for("phase5_ui.evidence_list"))
    users = _accessible_users(evidence.case)
    chain = get_custody_chain(evidence.id)
    return render_template(
        "evidence_detail.html",
        evidence=evidence,
        chain=chain,
        users=users,
        transitions=TRANSITIONS,
    )


@phase5_ui.route("/evidence/<int:evidence_id>/transition", methods=["POST"])
@login_required
def evidence_transition(evidence_id):
    evidence = _evidence_or_404(evidence_id)
    if evidence is None:
        flash("Evidence not found or access denied.", "error")
        return redirect(url_for("phase5_ui.evidence_list"))
    target_status = request.form.get("target_status", "")
    notes = request.form.get("notes", "").strip() or None
    try:
        transition_evidence(evidence.id, target_status, current_user.id, notes)
        flash(f"Evidence moved to {target_status}.", "success")
    except (ValueError, PermissionError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("phase5_ui.evidence_detail", evidence_id=evidence.id))


@phase5_ui.route("/evidence/<int:evidence_id>/transfer", methods=["POST"])
@login_required
def evidence_transfer(evidence_id):
    evidence = _evidence_or_404(evidence_id)
    if evidence is None:
        flash("Evidence not found or access denied.", "error")
        return redirect(url_for("phase5_ui.evidence_list"))
    to_user_id = request.form.get("to_user_id", type=int)
    try:
        transfer_evidence(evidence.id, to_user_id, current_user.id, request.form.get("notes", "").strip() or None)
        flash("Custody transfer recorded.", "success")
    except (ValueError, PermissionError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("phase5_ui.evidence_detail", evidence_id=evidence.id))


@phase5_ui.route("/evidence/<int:evidence_id>/receive", methods=["POST"])
@login_required
def evidence_receive(evidence_id):
    evidence = _evidence_or_404(evidence_id)
    if evidence is None:
        flash("Evidence not found or access denied.", "error")
        return redirect(url_for("phase5_ui.evidence_list"))
    try:
        receive_evidence(evidence.id, current_user.id, request.form.get("notes", "").strip() or None)
        flash("Evidence receipt recorded.", "success")
    except (ValueError, PermissionError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("phase5_ui.evidence_detail", evidence_id=evidence.id))


@phase5_ui.route("/evidence/<int:evidence_id>/verify", methods=["POST"])
@login_required
def evidence_verify(evidence_id):
    evidence = _evidence_or_404(evidence_id)
    if evidence is None:
        flash("Evidence not found or access denied.", "error")
        return redirect(url_for("phase5_ui.evidence_list"))
    uploaded = request.files.get("integrity_file")
    if not uploaded or not uploaded.filename:
        flash("Select the plaintext evidence file to verify its SHA-256 integrity.", "error")
        return redirect(url_for("phase5_ui.evidence_detail", evidence_id=evidence.id))
    file_bytes = uploaded.read(10 * 1024 * 1024 + 1)
    if len(file_bytes) > 10 * 1024 * 1024:
        flash("Integrity verification files must be 10 MB or less.", "error")
        return redirect(url_for("phase5_ui.evidence_detail", evidence_id=evidence.id))
    try:
        verified = verify_evidence_integrity(evidence.id, file_bytes, current_user.id)
        flash(
            "Integrity verified: SHA-256 matches the immutable evidence record." if verified
            else "Integrity check failed: SHA-256 does not match the immutable evidence record.",
            "success" if verified else "error",
        )
    except (ValueError, PermissionError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("phase5_ui.evidence_detail", evidence_id=evidence.id))


def register_phase5_ui(app):
    """Register the Phase 5 UI blueprint on the main Flask application."""
    if "phase5_ui" not in app.blueprints:
        app.register_blueprint(phase5_ui)
