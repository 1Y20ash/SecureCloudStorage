# SecureCloudStorage

A secure web-based cloud storage application that encrypts files before storing them and allows authenticated users to safely upload, manage, download, and delete their files.

## 🌐 Live Demo

**Website:** https://secure-cloud-storage-nine.vercel.app

## ✨ Features

- 🔐 User registration and login
- 🔒 Password-protected file encryption
- ☁️ Secure cloud storage using Supabase Storage
- 📁 Upload and manage encrypted files
- ⬇️ Download and decrypt files with the correct password
- 🗑️ Delete stored files
- 👤 User-specific file access
- 🛡️ Authentication-protected dashboard and file operations
- 📦 Supports different file types within the project size limit
- 📏 Maximum file size: **10 MB**
- 💻 Responsive web interface

## 🔄 How It Works

```text
User selects a file
        ↓
File is read by the application
        ↓
File is encrypted using the encryption password
        ↓
Encrypted data is stored
        ↓
File metadata is saved in the database
        ↓
User can later enter the password
        ↓
Encrypted file is decrypted
        ↓
Original file is downloaded
```

The application stores the encrypted version of the uploaded file rather than the original file. Decryption requires the correct password.

## 🛠️ Tech Stack

### Backend

- Python
- Flask
- Flask-Login
- SQLAlchemy / Flask-SQLAlchemy
- Cryptography

### Frontend

- HTML5
- CSS3
- JavaScript
- Jinja2 templates

### Storage & Database

- Supabase Storage for encrypted file storage
- PostgreSQL-compatible database through SQLAlchemy

### Deployment

- Vercel

## 📂 Project Structure

```text
SecureCloudStorage/
├── app.py
├── config.py
├── extensions.py
├── requirements.txt
├── crypto/
│   └── encryption.py
├── models/
│   ├── file.py
│   └── user.py
├── static/
│   ├── css/
│   └── js/
├── templates/
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── upload.html
│   └── download.html
└── uploads/
```

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/1Y20ash/SecureCloudStorage.git
cd SecureCloudStorage
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file and provide the required application, database, and Supabase configuration values used by `config.py`.

Do **not** commit passwords, secret keys, database credentials, or Supabase secret keys to GitHub.

### 5. Start the application

```bash
python app.py
```

Then open the local address shown by Flask in your browser.

## 🔐 Security Notes

- Uploaded files are encrypted before being stored.
- Each stored file is associated with the authenticated user who uploaded it.
- File download and deletion operations require authentication and ownership of the file.
- Incorrect decryption passwords are rejected.
- Secret configuration values should be supplied through environment variables.
- The current project intentionally limits uploads to 10 MB.

## 📌 Project Purpose

SecureCloudStorage is designed as a practical demonstration of secure file storage concepts, combining web authentication, file encryption, database-backed metadata, and cloud object storage in a single application.

## 👨‍💻 Author

**Yash Chitmalwar**

GitHub: https://github.com/1Y20ash

## 📄 License

This project currently does not specify a separate open-source license.