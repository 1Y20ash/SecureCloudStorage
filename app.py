import io
import os
import secrets

from cryptography.exceptions import InvalidTag
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from config import Config
from crypto.encryption import decrypt_file, encrypt_file
from extensions import db, login_manager
from models.case import Case
from models.case_document import CaseDocument
from models.file import StoredFile
from models.user import User

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


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return render_template("register.html")
        user = User(name=name, email=email)
        user.set_password(password)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An account with this email already exists.", "error")
            return render_template("register.html")
        flash("Registration successful. Please log in.", "success")
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
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    files = db.session.scalars(
        db.select(StoredFile).where(StoredFile.user_id == current_user.id).order_by(StoredFile.uploaded_at.desc())
    ).all()
    cases = db.session.scalars(
        db.select(Case).where(Case.created_by == current_user.id).order_by(Case.created_at.desc())
    ).all()
    return render_template("dashboard.html", files=files, cases=cases)


@app.route("/cases/new", methods=["GET", "POST"])
@login_required
def create_case():
    if request.method == "POST":
        case_number = request.form.get("case_number", "").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        department = request.form.get("department", "").strip()
        status = request.form.get("status", "Open")
        if not case_number or not title:
            flash("Case number and title are required.", "error")
            return render_template("case_form.html", statuses=CASE_STATUSES)
        if status not in CASE_STATUSES:
            flash("Invalid case status.", "error")
            return render_template("case_form.html", statuses=CASE_STATUSES)
        case = Case(case_number=case_number, title=title, description=description,
                    department=department, status=status, created_by=current_user.id)
        try:
            db.session.add(case)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("A case with this Case ID already exists.", "error")
            return render_template("case_form.html", statuses=CASE_STATUSES)
        flash("Case created successfully.", "success")
        return redirect(url_for("case_detail", case_id=case.id))
    return render_template("case_form.html", statuses=CASE_STATUSES)


@app.route("/cases/<int:case_id>")
@login_required
def case_detail(case_id):
    case = db.session.scalar(db.select(Case).where(Case.id == case_id, Case.created_by == current_user.id))
    if case is None:
        flash("Case not found or access denied.", "error")
        return redirect(url_for("dashboard"))
    return render_template("case_detail.html", case=case)


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    cases = db.session.scalars(
        db.select(Case).where(Case.created_by == current_user.id).order_by(Case.created_at.desc())
    ).all()
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        encryption_password = request.form.get("encryption_password", "")
        case_id = request.form.get("case_id", type=int)
        category = request.form.get("category", "Other")
        if not uploaded_file or not uploaded_file.filename:
            flash("Please select a file.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        if not encryption_password:
            flash("An encryption password is required.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        case = db.session.scalar(db.select(Case).where(Case.id == case_id, Case.created_by == current_user.id))
        if case is None:
            flash("Please select a valid case.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        if category not in DOCUMENT_CATEGORIES:
            flash("Invalid document category.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        original_filename = secure_filename(uploaded_file.filename)
        if not original_filename:
            flash("The selected filename is invalid.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        file_bytes = uploaded_file.read(MAX_FILE_SIZE + 1)
        if len(file_bytes) > MAX_FILE_SIZE:
            flash("File size must be 10 MB or less.", "error")
            return render_template("upload.html", cases=cases, categories=DOCUMENT_CATEGORIES)
        encrypted_data = encrypt_file(file_bytes, encryption_password)
        encrypted_filename = f"{secrets.token_hex(16)}.enc"
        storage_uploaded = False
        try:
            store_encrypted_file(encrypted_filename, encrypted_data)
            storage_uploaded = True
            stored_file = StoredFile(user_id=current_user.id, original_filename=original_filename,
                                     encrypted_filename=encrypted_filename, file_size=len(file_bytes))
            db.session.add(stored_file)
            db.session.flush()
            db.session.add(CaseDocument(case_id=case.id, stored_file_id=stored_file.id,
                                        category=category, version=1, status="Draft"))
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


@app.route("/download/<int:file_id>", methods=["GET", "POST"])
@login_required
def download(file_id):
    stored_file = db.session.scalar(db.select(StoredFile).where(
        StoredFile.id == file_id, StoredFile.user_id == current_user.id))
    if stored_file is None:
        flash("File not found.", "error")
        return redirect(url_for("dashboard"))
    if request.method == "GET":
        return render_template("download.html", file=stored_file)
    decryption_password = request.form.get("decryption_password", "")
    if not decryption_password:
        flash("Please enter the decryption password.", "error")
        return render_template("download.html", file=stored_file)
    try:
        encrypted_data = read_encrypted_file(stored_file.encrypted_filename)
        decrypted_data = decrypt_file(encrypted_data, decryption_password)
    except FileNotFoundError:
        flash("The encrypted file is missing from storage.", "error")
        return redirect(url_for("dashboard"))
    except InvalidTag:
        flash("Incorrect password or corrupted file. Decryption failed.", "error")
        return render_template("download.html", file=stored_file)
    except (ValueError, OSError):
        flash("The file could not be decrypted.", "error")
        return render_template("download.html", file=stored_file)
    return send_file(io.BytesIO(decrypted_data), as_attachment=True,
                     download_name=stored_file.original_filename, mimetype="application/octet-stream")


@app.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    stored_file = db.session.scalar(db.select(StoredFile).where(
        StoredFile.id == file_id, StoredFile.user_id == current_user.id))
    if stored_file is None:
        flash("File not found.", "error")
        return redirect(url_for("dashboard"))
    try:
        delete_encrypted_file(stored_file.encrypted_filename)
        filename = stored_file.original_filename
        db.session.delete(stored_file)
        db.session.commit()
        flash(f"{filename} was deleted successfully.", "success")
    except OSError:
        db.session.rollback()
        flash("The encrypted file could not be deleted from storage.", "error")
    except Exception:
        db.session.rollback()
        flash("The file could not be deleted.", "error")
    return redirect(url_for("dashboard"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# Create newly introduced DMS tables without altering existing tables.
# This is intentionally limited to table creation; future schema changes should use migrations.
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
