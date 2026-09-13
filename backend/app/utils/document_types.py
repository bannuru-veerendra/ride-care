"""Document vault type rules (expiry + display labels)."""

from app.models.document import Document, DocumentType

# Keep free-text identity fields short — riders paste certificate numbers, not essays.
MAX_DOCUMENT_TEXT_LENGTH = 120

DOCUMENT_TYPE_LABELS: dict[DocumentType, str] = {
    DocumentType.INSURANCE: "Insurance",
    DocumentType.DRIVING_LICENSE: "Driving Licence",
    DocumentType.REGISTRATION_CERTIFICATE: "Registration Certificate",
    DocumentType.POLLUTION: "Pollution",
    DocumentType.OTHER: "Other",
}

# Expiry is required for these common renewing certificates.
EXPIRY_REQUIRED_TYPES = frozenset(
    {
        DocumentType.INSURANCE,
        DocumentType.DRIVING_LICENSE,
        DocumentType.POLLUTION,
    }
)

# RC never expires — omit field and skip digests/reminders.
NO_EXPIRY_TYPES = frozenset({DocumentType.REGISTRATION_CERTIFICATE})


def document_allows_expiry(document_type: DocumentType) -> bool:
    return document_type not in NO_EXPIRY_TYPES


def document_requires_expiry(document_type: DocumentType) -> bool:
    return document_type in EXPIRY_REQUIRED_TYPES


def document_display_label(
    document_type: DocumentType | str,
    custom_label: str | None = None,
) -> str:
    """Human-readable type for cards, digests, and reminders."""
    if isinstance(document_type, str):
        try:
            document_type = DocumentType(document_type)
        except ValueError:
            return custom_label.strip() if custom_label else document_type.replace("_", " ").title()

    if document_type == DocumentType.OTHER:
        label = (custom_label or "").strip()
        return label or DOCUMENT_TYPE_LABELS[DocumentType.OTHER]

    return DOCUMENT_TYPE_LABELS[document_type]


def document_display_label_from_row(document: Document) -> str:
    return document_display_label(document.document_type, document.custom_label)
