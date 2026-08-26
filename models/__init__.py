# Import all models so SQLAlchemy knows about every table during application startup.
from models.case import Case  # noqa: F401
from models.case_document import CaseDocument  # noqa: F401
from models.file import StoredFile  # noqa: F401
from models.user import User  # noqa: F401
