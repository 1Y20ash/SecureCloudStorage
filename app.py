import io
import os
import secrets
import hashlib
from datetime import datetime, timezone

from models.audit_log import AuditLog
from models.document_version import DocumentVersion
from models.evidence_custody import EvidenceCustody
from evidentiary import get_next_version, get_previous_hash

from cryptography.exceptions import InvalidTag
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from authz import (
    can_access_case,
    can_download_document,
    can_manage_case,
    can_manage_case_assignments,
    is_admin,
)
from config import Config
from crypto.encryption import decrypt_file, encrypt_file
from extensions import db, login_manager
from models.case import Case
from models.case_assignment import CaseAssignment
from models.case_document import CaseDocument
from models.document_share import DocumentShare
from models.file import StoredFile
from models.user import ROLES, User

try:
    from supabase import create_client
except ImportError:
    create_client = None

app = Flask(__name__)
app.config.from_object(Config)

MAX_FILE_SIZE = 10 * 1024 * 1024
CASE_STATUSES = ["Open", "Under Investigation", "Filed", "Under Trial", "Closed"]
DOCUMENT_CATEGORIES = [
    "FIR", "Police Report", "Witness Statement", "Charge Sheet", "Court Filing",
    "Evidence", "Forensic Report", "Legal Notice", "Judgment", "Other",
]

SUPABASE_URL = app.config.get("SUPABASE_URL")
SUPABASE_SECRET_KEY = app.config.get("SUPABASE_SECRET_KEY")
SUPABASE_STORAGE_BUCKET = app.config.get("SUPABASE_STORAGE_BUCKET", "encrypted-files")
USE_SUPABASE_STORAGE = bool(SUPABASE_URL and SUPABASE_SECRET_KEY)

supabase = None
if USE_SUPABASE_STORAGE:
    if create_client is None:
        raise RuntimeError("The supabase package is required when Supabase Storage is configured.")
    supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
else:
    UPLOAD_FOLDER = os.path.join(app.root_path, "uploads", "encrypted")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def store_encrypted_file(filename, encrypted_data):
    if USE_SUPABASE_STORAGE:
        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            path=filename, file=encrypted_data,
            file_options={"content-type": "application/octet-stream", "upsert": "false"},
        )
        return
    encrypted_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(encrypted_path, "wb") as encrypted_file:
        encrypted_file.write(encrypted_data)


def read_encrypted_file(filename):
    if USE_SUPABASE_STORAGE:
        return supabase.storage.from_(SUPABASE_STORAGE_BUCKET).download(filename)
    with open(os.path.join(UPLOAD_FOLDER, filename), "rb") as encrypted_file:
        return encrypted_file.read()


def delete_encrypted_file(filename):
    if USE_SUPABASE_STORAGE:
        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove([filename])
        return
    encrypted_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.isfile(encrypted_path):
        os.remove(encrypted_path)


def parse_expiry(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def calculate_sha256(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")
        if db.session.scalar(db.select(User).where(User.email == email)):
            flash("An account with that email already exists.", "error")
            return render_template("register.html")
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully. You can now sign in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = db.session.scalar(db.select(User).where(User.email == email))
        if user and user.check_password(password):
            login_user(user)
            flash("Welcome back.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    cases = db.session.scalars(db.select(Case).order_by(Case.created_at.desc())).all()
    cases = [case for case in cases if can_access_case(current_user, case)]
    files = db.session.scalars(
        db.select(StoredFile).where(StoredFile.user_id == current_user.id).order_by(StoredFile.uploaded_at.desc())
    ).all()
    shared_documents = db.session.scalars(
        db.select(CaseDocument).join(DocumentShare, DocumentShare.case_document_id == CaseDocument.id).where(
            DocumentShare.shared_with_user_id == current_user.id,
        ).order_by(CaseDocument.created_at.desc())
    ).all()
    return render_template("dashboard.html", cases=cases, files=files, shared_documents=shared_documents)


@app.route("/cases/new", methods=["GET", "POST"])
@login_required
def create_case():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        department = request.form.get("department", "").strip()
        status = request.form.get("status", "Open")
        if not title:
            flash("Case title is required.", "error")
            return render_template("case_form.html", statuses=CASE_STATUSES)
        if status not in CASE_STATUSES:
            flash("Invalid case status.", "error")
            return render_template("case_form.html", statuses=CASE_STATUSES)
        case_count = db.session.scalar(db.select(db.func.count(Case.id))) or 0
        case = Case(
            case_number=f"CASE-{datetime.now(timezone.utc).year}-{case_count + 1:03d}",
            title=title,
            description=description or None,
            department=department or None,
            status=status,
            created_by=current_user.id,
        )
        db.session.add(case)
        db.session.commit()
        flash(f"{case.case_number} created successfully.", "success")
        return redirect(url_for("case_detail", case_id=case.id))
    return render_template("case_form.html", statuses=CASE_STATUSES)


@app.route("/cases/<int:case_id>")
@login_required
def case_detail(case_id):
    case = db.session.get(Case, case_id)
    if case is None or not can_access_case(current_user, case):
        flash("Case not found or access denied.", "error")
        return redirect(url_for("dashboard"))
    return render_template("case_detail.html", case=case, categories=DOCUMENT_CATEGORIES)


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    cases = db.session.scalars(db.select(Case).order_by(Case.created_at.desc())).all()
    cases = [case for case in cases if can_access_case(current_user, case)]
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        case_id = request.form.get("case_id", type=int)
        category = request.form.get("category", "").strip()
        encryption_password = request.form.get("encryption_password", "")
        case = db.session.get(Case, case_id) if case_id else None
        if case is None or not can_manage_case(current_user, case):
            flash("You are not authorized to upload to the selected case.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        if not uploaded_file or not uploaded_file.filename:
            flash("Please select a file.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        if category not in DOCUMENT_CATEGORIES:
            flash("Please select a valid document category.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        if not encryption_password:
            flash("An encryption password is required.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        original_filename = secure_filename(uploaded_file.filename)
        if not original_filename:
            flash("The selected filename is invalid.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        file_bytes = uploaded_file.read(MAX_FILE_SIZE + 1)
        if len(file_bytes) > MAX_FILE_SIZE:
            flash("File size must be 10 MB or less.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        sha256_hash = calculate_sha256(file_bytes)
        encrypted_data = encrypt_file(file_bytes, encryption_password)
        encrypted_filename = f"{secrets.token_hex(16)}.enc"
        storage_uploaded = False
        try:
            store_encrypted_file(encrypted_filename, encrypted_data)
            storage_uploaded = True
            stored_file = StoredFile(
                user_id=current_user.id,
                original_filename=original_filename,
                encrypted_filename=encrypted_filename,
                file_size=len(file_bytes),
                sha256_hash=sha256_hash,
            )
            db.session.add(stored_file)
            db.session.flush()
            case_document = CaseDocument(
                case_id=case.id,
                stored_file_id=stored_file.id,
                category=category,
                version=1,
                status="Draft",
            )
            db.session.add(case_document)
            db.session.flush()
            db.session.add(DocumentVersion(case_document_id=case_document.id, version=1, stored_file_id=stored_file.id, sha256_hash=sha256_hash, previous_hash=None, created_by=current_user.id))
            db.session.add(EvidenceCustody(case_document_id=case_document.id, action="ACQUIRED", actor_user_id=current_user.id, sha256_hash=sha256_hash, notes="Initial evidence upload"))
            db.session.commit()
        except Exception:
            db.session.rollback()
            if storage_uploaded:
                try:
                    delete_encrypted_file(encrypted_filename)
                except Exception:
                    pass
            flash("The file could not be encrypted and stored.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        flash("Document encrypted and added to the case successfully.", "success")
        return redirect(url_for("case_detail", case_id=case.id))
    return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)


@app.route("/documents/<int:file_id>/download")
@login_required
def download(file_id):
    stored_file = db.session.get(StoredFile, file_id)
    if stored_file is None:
        flash("File not found.", "error")
        return redirect(url_for("dashboard"))
    document = db.session.scalar(db.select(CaseDocument).where(CaseDocument.stored_file_id == stored_file.id))
    if document is None or not can_download_document(current_user, document):
        flash("You are not authorized to download this document.", "error")
        return redirect(url_for("dashboard"))
    password = request.args.get("password", "")
    if not password:
        flash("A document password is required.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    try:
        decrypted = decrypt_file(read_encrypted_file(stored_file.encrypted_filename), password)
    except InvalidTag:
        flash("Incorrect password or corrupted encrypted file.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    return send_file(io.BytesIO(decrypted), as_attachment=True, download_name=stored_file.original_filename)


@app.route("/documents/<int:document_id>/versions", methods=["POST"])
@login_required
def create_document_version(document_id):
    document = db.session.get(CaseDocument, document_id)
    if document is None or not can_access_case(current_user, document.case):
        flash("Document not found or access denied.", "error")
        return redirect(url_for("dashboard"))
    if not can_manage_case(current_user, document.case):
        flash("You are not authorized to create a new document version.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    uploaded_file = request.files.get("file")
    encryption_password = request.form.get("encryption_password", "")
    if not uploaded_file or not uploaded_file.filename:
        flash("Please select a file.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    if not encryption_password:
        flash("An encryption password is required.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    original_filename = secure_filename(uploaded_file.filename)
    if not original_filename:
        flash("The selected filename is invalid.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    file_bytes = uploaded_file.read(MAX_FILE_SIZE + 1)
    if len(file_bytes) > MAX_FILE_SIZE:
        flash("File size must be 10 MB or less.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    sha256_hash = calculate_sha256(file_bytes)
    encrypted_data = encrypt_file(file_bytes, encryption_password)
    encrypted_filename = f"{secrets.token_hex(16)}.enc"
    next_version = get_next_version(document.id)
    previous_hash = get_previous_hash(document.id)
    storage_uploaded = False
    try:
        store_encrypted_file(encrypted_filename, encrypted_data)
        storage_uploaded = True
        stored_file = StoredFile(user_id=current_user.id, original_filename=original_filename, encrypted_filename=encrypted_filename, file_size=len(file_bytes), sha256_hash=sha256_hash)
        db.session.add(stored_file)
        db.session.flush()
        db.session.add(DocumentVersion(case_document_id=document.id, version=next_version, stored_file_id=stored_file.id, sha256_hash=sha256_hash, previous_hash=previous_hash, created_by=current_user.id))
        document.stored_file_id = stored_file.id
        document.version = next_version
        db.session.add(EvidenceCustody(case_document_id=document.id, action="VERSION_CREATED", actor_user_id=current_user.id, sha256_hash=sha256_hash, notes=f"Created document version {next_version}"))
        db.session.commit()
    except Exception:
        db.session.rollback()
        if storage_uploaded:
            try:
                delete_encrypted_file(encrypted_filename)
            except Exception:
                pass
        flash("The new document version could not be saved.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    flash(f"Document version {next_version} created successfully.", "success")
    return redirect(url_for("case_detail", case_id=document.case_id))


@app.route("/documents/<int:document_id>/share", methods=["POST"])
@login_required
def share_document(document_id):
    document = db.session.get(CaseDocument, document_id)
    if document is None or not can_manage_case(current_user, document.case):
        flash("Document not found or sharing access denied.", "error")
        return redirect(url_for("dashboard"))
    email = request.form.get("email", "").strip().lower()
    user = db.session.scalar(db.select(User).where(User.email == email))
    if user is None:
        flash("The selected recipient does not have an account.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    if user.id == current_user.id:
        flash("You cannot share a document with yourself.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    expires_at = parse_expiry(request.form.get("expires_at", ""))
    if request.form.get("expires_at") and expires_at is None:
        flash("Invalid sharing expiry date.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    if expires_at and expires_at <= datetime.now(timezone.utc):
        flash("Sharing expiry must be in the future.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    existing = db.session.scalar(db.select(DocumentShare).where(DocumentShare.case_document_id == document.id, DocumentShare.shared_with_user_id == user.id))
    if existing:
        existing.can_view = True
        existing.can_download = request.form.get("can_download") == "on"
        existing.expires_at = expires_at
        existing.shared_by_user_id = current_user.id
    else:
        db.session.add(DocumentShare(case_document_id=document.id, shared_with_user_id=user.id, shared_by_user_id=current_user.id, can_view=True, can_download=request.form.get("can_download") == "on", can_manage=False, expires_at=expires_at))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("The document could not be shared.", "error")
        return redirect(url_for("case_detail", case_id=document.case_id))
    flash("Document sharing permissions saved.", "success")
    return redirect(url_for("case_detail", case_id=document.case_id))


@app.route("/documents/<int:document_id>/shares/<int:share_id>/revoke", methods=["POST"])
@login_required
def revoke_share(document_id, share_id):
    document = db.session.get(CaseDocument, document_id)
    share = db.session.get(DocumentShare, share_id)
    if document is None or share is None or share.case_document_id != document.id:
        flash("Share not found.", "error")
        return redirect(url_for("dashboard"))
    if not can_manage_case(current_user, document.case):
        flash("You are not authorized to revoke this share.", "error")
        return redirect(url_for("dashboard"))
    db.session.delete(share)
    db.session.commit()
    flash("Document share revoked.", "success")
    return redirect(url_for("case_detail", case_id=document.case_id))


@app.route("/cases/<int:case_id>/assignments", methods=["GET", "POST"])
@login_required
def manage_case_assignments(case_id):
    case = db.session.get(Case, case_id)
    if not can_manage_case_assignments(current_user, case):
        flash("You are not authorized to manage case assignments.", "error")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        user_id = request.form.get("user_id", type=int)
        user = db.session.get(User, user_id) if user_id else None
        if user is None:
            flash("Selected user was not found.", "error")
            return redirect(url_for("manage_case_assignments", case_id=case.id))
        if user.id == case.created_by:
            flash("The case owner already has access and does not need an assignment.", "error")
            return redirect(url_for("manage_case_assignments", case_id=case.id))
        if user.role == "Admin" and not is_admin(current_user):
            flash("Only an Admin can assign an Admin account to a case.", "error")
            return redirect(url_for("manage_case_assignments", case_id=case.id))
        existing = db.session.scalar(db.select(CaseAssignment).where(CaseAssignment.case_id == case.id, CaseAssignment.user_id == user.id))
        if existing:
            flash("That user is already assigned to this case.", "error")
            return redirect(url_for("manage_case_assignments", case_id=case.id))
        db.session.add(CaseAssignment(case_id=case.id, user_id=user.id, assigned_by=current_user.id))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("The assignment could not be created.", "error")
            return redirect(url_for("manage_case_assignments", case_id=case.id))
        flash(f"{user.name} was assigned to {case.case_number}.", "success")
        return redirect(url_for("manage_case_assignments", case_id=case.id))
    assigned_ids = {assignment.user_id for assignment in case.assignments}
    available_users = db.session.scalars(db.select(User).where(User.id != case.created_by).order_by(User.name.asc())).all()
    return render_template("case_assignments.html", case=case, assignments=case.assignments, available_users=available_users, assigned_ids=assigned_ids)


@app.route("/cases/<int:case_id>/assignments/<int:assignment_id>/remove", methods=["POST"])
@login_required
def remove_case_assignment(case_id, assignment_id):
    case = db.session.get(Case, case_id)
    assignment = db.session.get(CaseAssignment, assignment_id)
    if not can_manage_case_assignments(current_user, case):
        flash("You are not authorized to manage case assignments.", "error")
        return redirect(url_for("dashboard"))
    if assignment is None or assignment.case_id != case.id:
        flash("Assignment not found.", "error")
        return redirect(url_for("manage_case_assignments", case_id=case.id))
    db.session.delete(assignment)
    db.session.commit()
    flash("Case assignment removed.", "success")
    return redirect(url_for("manage_case_assignments", case_id=case.id))


@app.route("/admin/users", methods=["GET", "POST"])
@login_required
def manage_users():
    if not is_admin(current_user):
        flash("Admin access is required.", "error")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        user = db.session.get(User, request.form.get("user_id", type=int))
        role = request.form.get("role", "")
        if user is None:
            flash("User not found.", "error")
            return redirect(url_for("manage_users"))
        if role not in ROLES:
            flash("Invalid role selected.", "error")
            return redirect(url_for("manage_users"))
        if user.id == current_user.id and role != "Admin":
            flash("You cannot remove your own Admin role.", "error")
            return redirect(url_for("manage_users"))
        user.role = role
        db.session.commit()
        flash(f"Role updated for {user.email}.", "success")
        return redirect(url_for("manage_users"))
    users = db.session.scalars(db.select(User).order_by(User.name.asc())).all()
    return render_template("admin_users.html", users=users, roles=ROLES)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


from phase5_ui import register_phase5_ui
register_phase5_ui(app)

from phase6_ui import register_phase6_ui
register_phase6_ui(app)

from phase7_ui import register_phase7_ui
register_phase7_ui(app)

from security_monitoring import register_security_monitoring
register_security_monitoring(app)


if __name__ == "__main__":
    app.run(debug=True)
