# 🔐 SecureCloudStorage

### Privacy-first cloud storage with client-side file encryption

**SecureCloudStorage** is a full-stack secure file-storage web application built to demonstrate how modern web applications can combine **authentication, cryptography, database management, and cloud storage** into one practical system.

Files are encrypted with **AES-256-GCM before they are persisted**, while authenticated users can upload, manage, download, decrypt, and delete their own files.

<p align="center">
  <a href="https://secure-cloud-storage-nine.vercel.app"><strong>🚀 Live Demo</strong></a> ·
  <a href="https://github.com/1Y20ash/SecureCloudStorage"><strong>💻 Source Code</strong></a>
</p>

---

## 🌐 Live Project

| | Link |
|---|---|
| 🚀 **Live Demo** | https://secure-cloud-storage-nine.vercel.app |
| 💻 **GitHub Repository** | https://github.com/1Y20ash/SecureCloudStorage |

> **Project focus:** Secure file storage, authenticated access, AES-256-GCM encryption, cloud storage, and secure file lifecycle management.

---

## ✨ Why I Built This

Cloud storage makes file access convenient, but sensitive files should not simply be treated as ordinary uploads.

This project explores a simple security-first approach:

**Authenticate → Encrypt → Store → Authenticate → Decrypt → Download**

The goal was to build a practical application where security is part of the file-storage workflow rather than an afterthought.

---

## 🚀 Key Features

- 🔐 **User authentication** — registration, login, logout, and protected dashboard access
- 🛡️ **AES-256-GCM encryption** — files are encrypted before storage
- 🔑 **Password-based key derivation** — PBKDF2-HMAC-SHA256 with 600,000 iterations
- 🧂 **Unique cryptographic salt** — a fresh 16-byte salt is generated for each encrypted file
- 🎲 **Unique nonce** — a fresh 12-byte nonce is generated for each encryption operation
- ☁️ **Cloud storage** — encrypted objects can be stored in Supabase Storage
- 👤 **User isolation** — file operations are scoped to the authenticated owner
- ⬇️ **Secure download** — the correct decryption password is required to recover the original file
- 🗑️ **File management** — users can delete their stored files
- 📦 **Multiple file types** — designed to handle documents, images, archives, code files, and other binary files
- 📏 **10 MB upload limit** — intentionally enforced for the current project
- ⚡ **Deployment-ready architecture** — configured for serverless deployment on Vercel

---

## 🔒 Security Architecture

The core encryption implementation uses **AES-256-GCM**, an authenticated encryption mode that provides both confidentiality and integrity.

### Encryption flow

```text
                    USER
                     │
                     │ File + encryption password
                     ▼
              ┌───────────────┐
              │   Flask App   │
              └───────┬───────┘
                      │
                      ▼
            ┌───────────────────┐
            │   PBKDF2-HMAC     │
            │   SHA-256         │
            │   600,000 rounds  │
            └─────────┬─────────┘
                      │
                      ▼
               256-bit AES key
                      │
                      ▼
            ┌───────────────────┐
            │    AES-256-GCM    │
            └─────────┬─────────┘
                      │
                      ▼
             Encrypted ciphertext
                      │
                      ▼
             Supabase Storage
```

### Stored encrypted format

The application stores encrypted data in the following structure:

```text
MAGIC | SALT | NONCE | CIPHERTEXT + AUTHENTICATION TAG
```

The original plaintext file is not written to persistent storage by the upload workflow.

---

## 🧩 Technology Stack

### Backend

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)

- Python
- Flask
- Flask-Login
- Flask-SQLAlchemy
- SQLAlchemy
- Jinja2
- Werkzeug

### Security

![Cryptography](https://img.shields.io/badge/Cryptography-AES--256--GCM-1F2937?style=flat-square)

- `cryptography`
- AES-256-GCM
- PBKDF2-HMAC-SHA256
- Random salt and nonce generation
- Authenticated encryption

### Frontend

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)

- HTML5
- CSS3
- JavaScript
- Jinja2 templates

### Data & Infrastructure

![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=flat-square&logo=supabase&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white)

- Supabase Storage
- PostgreSQL-compatible database configuration
- SQLite fallback for local development
- Vercel deployment

---

## 📂 Project Structure

```text
SecureCloudStorage/
│
├── app.py                    # Flask application and routes
├── config.py                 # Environment-based configuration
├── extensions.py             # Flask extensions
├── requirements.txt          # Python dependencies
├── supabase_schema.sql       # Database schema
│
├── crypto/
│   └── encryption.py         # AES-256-GCM encryption/decryption
│
├── models/
│   ├── file.py               # Stored file model
│   └── user.py               # User model
│
├── templates/                # Jinja2 HTML templates
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── upload.html
│   └── download.html
│
└── static/                   # CSS and JavaScript assets
```

---

## ⚙️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/1Y20ash/SecureCloudStorage.git
cd SecureCloudStorage
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file with the configuration required by the application:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
SUPABASE_URL=your-supabase-url
SUPABASE_SECRET_KEY=your-supabase-secret-key
SUPABASE_STORAGE_BUCKET=encrypted-files
```

For local development, the application can fall back to a SQLite database when `DATABASE_URL` is not provided.

### 5. Start the application

```bash
python app.py
```

Open the local Flask URL shown in your terminal.

---

## 🛡️ Security Practices

This project currently implements several security-focused practices:

- Files are encrypted before being persisted.
- AES-256-GCM provides confidentiality and authentication.
- A random salt is generated for every encrypted file.
- A random nonce is generated for every encryption operation.
- Password-derived keys are generated with PBKDF2-HMAC-SHA256.
- File download and deletion require authentication.
- File queries are restricted to the currently authenticated user.
- Secret configuration values are read from environment variables.
- Encrypted storage uses opaque generated filenames rather than the original filename.
- The upload size is limited to 10 MB in the current implementation.

> **Important:** This is an educational/project implementation, not a replacement for a professionally audited production security system. Strong user passwords and secure secret management remain essential.

---

## 📊 Application Workflow

```text
Register / Login
       │
       ▼
   Dashboard
       │
       ├───────────────┐
       │               │
       ▼               ▼
    Upload          Manage Files
       │               │
       ▼               ├── Download
   Encrypt            └── Delete
       │
       ▼
 Store encrypted data
       │
       ▼
 Supabase / Local Storage
```

---

## 🎯 What This Project Demonstrates

This project brings together several concepts that are important in modern software development:

- **Applied cryptography** — implementing authenticated encryption correctly using established primitives
- **Secure authentication** — protecting application routes and user-specific resources
- **Backend development** — designing Flask routes and application logic
- **Database integration** — storing users and file metadata with SQLAlchemy
- **Cloud storage** — integrating Supabase Storage for encrypted objects
- **Environment-based configuration** — keeping deployment secrets outside source code
- **Serverless deployment** — adapting database connections and storage for Vercel
- **Security-aware system design** — considering confidentiality, integrity, authentication, and access control together

---

## 🔮 Future Improvements

Possible future enhancements include:

- Larger-file and streaming encryption support
- Password reset and account recovery
- Multi-factor authentication
- File sharing with controlled permissions
- Folder management
- File previews
- Stronger rate limiting and abuse protection
- Automated security testing and dependency scanning
- Expanded audit logging

---

## 👨‍💻 Author

### Yash Chitmalwar

Computer Science & Engineering (AI/ML) Student

- GitHub: https://github.com/1Y20ash
- Project: https://github.com/1Y20ash/SecureCloudStorage
- Live Demo: https://secure-cloud-storage-nine.vercel.app

---

## ⭐ Support the Project

If you find the project interesting, consider giving the repository a ⭐ on GitHub and sharing feedback or suggestions.

---

<p align="center">
  <strong>🔐 Secure your files. Own your data.</strong>
</p>
