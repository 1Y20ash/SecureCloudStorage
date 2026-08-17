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
from models.file import StoredFile
from models.user import User

try:
    from supabase import create_client
except ImportError:  # Keeps local development errors clear if the optional dependency is missing.
    create_client = None


app = Flask(__name__)
app.config.from_object(Config)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB for the mini-project
ALLOWED_EXTENSIONS = {
    "pdf", "txt", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "jpg", "jpeg", "png", "gif", "zip", "csv"
}

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
    # Local fallback only. Vercel uses Supabase Storage and never writes to the deployment filesystem.
    UPLOAD_FOLDER = os.path.join(app.root_path, "uploads", "encrypted")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def store_encrypted_file(filename, encrypted_data):
    if USE_SUPABASE_STORAGE:
        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            path=filename,
            file=encrypted_data,
            file_options={
                "content-type": "application/octet-stream",
                "upsert": "false",
            },
        )
        return

    encrypted_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(encrypted_path, "wb") as encrypted_file:
        encrypted_file.write(encrypted_data)


def read_encrypted_file(filename):
    if USE_SUPABASE_STORAGE:
        return supabase.storage.from_(SUPABASE_STORAGE_BUCKET).download(filename)

    encrypted_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.isfile(encrypted_path):
        raise FileNotFoundError(encrypted_path)

    with open(encrypted_path, "rb") as encrypted_file:
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
        db.select(StoredFile)
        .where(StoredFile.user_id == current_user.id)
        .order_by(StoredFile.uploaded_at.desc())
    ).all()
    return render_template("dashboard.html", files=files)


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        encryption_password = request.form.get("encryption_password", "")

        if not uploaded_file or not uploaded_file.filename:
            flash("Please select a file.", "error")
            return render_template("upload.html")

        if not allowed_file(uploaded_file.filename):
            flash("This file type is not allowed.", "error")
            return render_template("upload.html")

        if not encryption_password:
            flash("An encryption password is required.", "error")
            return render_template("upload.html")

        original_filename = secure_filename(uploaded_file.filename)
        file_bytes = uploaded_file.read(MAX_FILE_SIZE + 1)

        if len(file_bytes) > MAX_FILE_SIZE:
            flash("File size must be 10 MB or less.", "error")
            return render_template("upload.html")

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
            )
            db.session.add(stored_file)
            db.session.commit()
        except Exception:
            db.session.rollback()
            if storage_uploaded:
                try:
                    delete_encrypted_file(encrypted_filename)
                except Exception:
                    pass
            flash("The file could not be encrypted and stored.", "error")
            return render_template("upload.html")

        flash("File encrypted and stored successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("upload.html")


@app.route("/download/<int:file_id>", methods=["GET", "POST"])
@login_required
def download(file_id):
    stored_file = db.session.scalar(
        db.select(StoredFile).where(
            StoredFile.id == file_id,
            StoredFile.user_id == current_user.id,
        )
    )

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
    except InvalidTag:
        flash("Incorrect password or corrupted file. Decryption failed.", "error")
        return render_template("download.html", file=stored_file)
    except (FileNotFoundError, ValueError, OSError):
        flash("The encrypted file is missing or could not be decrypted.", "error")
        return redirect(url_for("dashboard"))
    except Exception:
        flash("The file could not be retrieved from storage.", "error")
        return render_template("download.html", file=stored_file)

    return send_file(
        io.BytesIO(decrypted_data),
        as_attachment=True,
        download_name=stored_file.original_filename,
        mimetype="application/octet-stream",
    )


@app.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    stored_file = db.session.scalar(
        db.select(StoredFile).where(
            StoredFile.id == file_id,
            StoredFile.user_id == current_user.id,
        )
    )

    if stored_file is None:
        flash("File not found.", "error")
        return redirect(url_for("dashboard"))

    try:
        delete_encrypted_file(stored_file.encrypted_filename)

        filename = stored_file.original_filename
        db.session.delete(stored_file)
        db.session.commit()
        flash(f"{filename} was deleted successfully.", "success")
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


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
