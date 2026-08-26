# Security Policy

## Purpose

SecureCloudStorage is being extended for PS 26190 as a secure digital document management system for legal and investigation documents.

## Mandatory Security Rules

1. Never commit passwords, API keys, database credentials, private keys, session secrets, or `.env` files.
2. Never use real legal/investigation documents or real evidence in development or demo data.
3. All access to protected resources must be authorized server-side; UI hiding is not an authorization mechanism.
4. Security-sensitive changes require negative testing for unauthorized access and failure cases.
5. Existing AES-256-GCM encryption must not be weakened or bypassed to simplify new features.
6. Encryption keys and application secrets must not be stored with encrypted files or committed to source control.
7. Validate uploaded files and enforce configured size limits.
8. Keep dependencies reviewed and avoid unnecessary third-party services.
9. Prefer local/open-source tools for sensitive processing such as OCR or advanced document search.
10. Security findings must be recorded and resolved before a phase is marked complete when they are relevant to that phase.

## Reporting

During development, suspected security issues should be recorded as private team issues where possible and should not be published with sensitive details.

## Development Environment

Use synthetic/sample documents and accounts for testing. Production credentials and sensitive data must remain outside the repository.
