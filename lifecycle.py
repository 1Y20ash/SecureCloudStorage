"""Document lifecycle state transitions.

The lifecycle is deliberately strict so application code cannot accidentally
move a document backwards or skip an approval stage.
"""

from models.document_version import DocumentVersion


ALLOWED_TRANSITIONS = {
    DocumentVersion.LIFECYCLE_DRAFT: {DocumentVersion.LIFECYCLE_REVIEWED},
    DocumentVersion.LIFECYCLE_REVIEWED: {DocumentVersion.LIFECYCLE_APPROVED},
    DocumentVersion.LIFECYCLE_APPROVED: {DocumentVersion.LIFECYCLE_ARCHIVED},
    DocumentVersion.LIFECYCLE_ARCHIVED: set(),
}


def can_transition(current_status, new_status):
    """Return True only when the requested lifecycle transition is allowed."""
    if current_status not in DocumentVersion.LIFECYCLE_STATUSES:
        return False
    if new_status not in DocumentVersion.LIFECYCLE_STATUSES:
        return False
    return new_status in ALLOWED_TRANSITIONS[current_status]


def transition_status(version, new_status):
    """Apply one valid lifecycle transition or raise ValueError."""
    if not can_transition(version.lifecycle_status, new_status):
        raise ValueError(
            f"Invalid document lifecycle transition: "
            f"{version.lifecycle_status} -> {new_status}"
        )
    version.lifecycle_status = new_status
    return version
