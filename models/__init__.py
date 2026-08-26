# Import all models so SQLAlchemy knows about every table during application startup.
from models.audit_log import AuditLog  # noqa: F401
from models.case import Case  # noqa: F401
from models.case_assignment import CaseAssignment  # noqa: F401
from models.case_document import CaseDocument  # noqa: F401
from models.document_share import DocumentShare  # noqa: F401
from models.file import StoredFile  # noqa: F401
from models.user import User  # noqa: F401

# Register database-level Phase 3 audit hooks after all audited models exist.
import audit_hooks  # noqa: F401,E402
