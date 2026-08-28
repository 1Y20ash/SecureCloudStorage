"""HTTP integration for Phase 4 document lifecycle operations."""

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from authz import can_access_case, can_manage_case
from extensions import db
from lifecycle import transition_status
from models.audit_log import AuditLog
from models.case_document import CaseDocument
from models.document_version import DocumentVersion
from models.evidence_custody import EvidenceCustody
from evidentiary import get_next_version


def register_phase4_routes(app):
    @app.route("/documents/<int:document_id>/lifecycle", methods=["POST"])
    @login_required
    def update_document_lifecycle(document_id):
        document = db.session.get(CaseDocument, document_id)
        if document is None or not can_access_case(current_user, document.case):
            flash("Document not found or access denied.", "error")
            return redirect(url_for("dashboard"))
        if not can_manage_case(current_user, document.case):
            flash("You are not authorized to change the document lifecycle.", "error")
            return redirect(url_for("case_detail", case_id=document.case_id))

        new_status = request.form.get("status", "").strip()
        current_version = db.session.scalar(
            db.select(DocumentVersion).where(
                DocumentVersion.case_document_id == document.id,
                DocumentVersion.version == document.version,
            )
        )
        if current_version is None:
            flash("The current document version could not be found.", "error")
            return redirect(url_for("case_detail", case_id=document.case_id))

        old_status = current_version.lifecycle_status
        try:
            transition_status(current_version, new_status)
        except ValueError:
            flash(f"Invalid lifecycle transition: {old_status} → {new_status}.", "error")
            return redirect(url_for("case_detail", case_id=document.case_id))

        document.status = new_status
        db.session.add(AuditLog(
            user_id=current_user.id,
            action="DOCUMENT_LIFECYCLE_CHANGED",
            resource_type="document_version",
            resource_id=current_version.id,
            case_id=document.case_id,
            success=True,
            ip_address=request.remote_addr,
            details=f"Lifecycle changed from {old_status} to {new_status} for version {current_version.version}",
        ))
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("The document lifecycle change could not be saved.", "error")
            return redirect(url_for("case_detail", case_id=document.case_id))

        flash(f"Document v{current_version.version} moved to {new_status}.", "success")
        return redirect(url_for("case_detail", case_id=document.case_id))

    @app.route("/documents/<int:document_id>/versions/<int:version>/restore", methods=["POST"])
    @login_required
    def restore_document_version(document_id, version):
        document = db.session.get(CaseDocument, document_id)
        if document is None or not can_access_case(current_user, document.case):
            flash("Document not found or access denied.", "error")
            return redirect(url_for("dashboard"))
        if not can_manage_case(current_user, document.case):
            flash("You are not authorized to restore document versions.", "error")
            return redirect(url_for("case_detail", case_id=document.case_id))

        current_version = db.session.scalar(
            db.select(DocumentVersion).where(
                DocumentVersion.case_document_id == document.id,
                DocumentVersion.version == document.version,
            )
        )
        target_version = db.session.scalar(
            db.select(DocumentVersion).where(
                DocumentVersion.case_document_id == document.id,
                DocumentVersion.version == version,
            )
        )
        if current_version is None or target_version is None:
            flash("The requested document version was not found.", "error")
            return redirect(url_for("case_detail", case_id=document.case_id))
        if current_version.lifecycle_status == DocumentVersion.LIFECYCLE_ARCHIVED:
            flash("Archived documents cannot be restored.", "error")
            return redirect(url_for("case_detail", case_id=document.case_id))
        if target_version.version == current_version.version:
            flash("That version is already current.", "error")
            return redirect(url_for("case_detail", case_id=document.case_id))

        next_version = get_next_version(document.id)
        try:
            restored = DocumentVersion(
                case_document_id=document.id,
                version=next_version,
                stored_file_id=target_version.stored_file_id,
                sha256_hash=target_version.sha256_hash,
                previous_hash=current_version.sha256_hash,
                created_by=current_user.id,
                change_description=f"Restored from version {target_version.version}",
                lifecycle_status=DocumentVersion.LIFECYCLE_DRAFT,
            )
            db.session.add(restored)
            document.stored_file_id = target_version.stored_file_id
            document.version = next_version
            document.status = DocumentVersion.LIFECYCLE_DRAFT
            db.session.add(AuditLog(
                user_id=current_user.id,
                action="DOCUMENT_VERSION_RESTORED",
                resource_type="document_version",
                resource_id=next_version,
                case_id=document.case_id,
                success=True,
                ip_address=request.remote_addr,
                details=f"Restored version {target_version.version} as new version {next_version}",
            ))
            db.session.add(EvidenceCustody(
                case_document_id=document.id,
                action="VERSION_RESTORED",
                actor_user_id=current_user.id,
                sha256_hash=target_version.sha256_hash,
                notes=f"Restored version {target_version.version} as version {next_version}",
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("The document version could not be restored.", "error")
            return redirect(url_for("case_detail", case_id=document.case_id))

        flash(f"Version {target_version.version} restored as version {next_version}.", "success")
        return redirect(url_for("case_detail", case_id=document.case_id))
