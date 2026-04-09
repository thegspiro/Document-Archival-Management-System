"""Pydantic request/response schemas for the ADMS backend API."""

from app.schemas.common import (
    BulkAction,
    BulkActionRequest,
    BulkActionResponse,
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
)
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse as AuthUserResponse,
)
from app.schemas.user import (
    RoleAssignRequest,
    RoleResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdate,
    MakeUnavailableRequest,
)
from app.schemas.document_file import (
    DocumentFileResponse,
    DocumentPageResponse,
    DocumentPageUpdate,
)
from app.schemas.authority import (
    AuthorityRecordCreate,
    AuthorityRecordResponse,
    AuthorityRecordUpdate,
    AuthorityRelationshipCreate,
    AuthorityRelationshipResponse,
    WikidataLinkRequest,
)
from app.schemas.vocabulary import (
    VocabularyDomainCreate,
    VocabularyDomainResponse,
    VocabularyTermCreate,
    VocabularyTermResponse,
    VocabularyTermUpdate,
    TermMergeRequest,
)
from app.schemas.arrangement import (
    ArrangementNodeCreate,
    ArrangementNodeResponse,
    ArrangementNodeUpdate,
)
from app.schemas.location import (
    LocationCreate,
    LocationResponse,
    LocationUpdate,
)
from app.schemas.event import (
    EventAuthorityLinkCreate,
    EventAuthorityLinkResponse,
    EventCreate,
    EventDocumentLinkCreate,
    EventDocumentLinkResponse,
    EventLocationLinkCreate,
    EventLocationLinkResponse,
    EventResponse,
    EventUpdate,
)
from app.schemas.exhibition import (
    BlockReorderRequest,
    ExhibitionCreate,
    ExhibitionPageBlockCreate,
    ExhibitionPageBlockResponse,
    ExhibitionPageBlockUpdate,
    ExhibitionPageCreate,
    ExhibitionPageResponse,
    ExhibitionPageUpdate,
    ExhibitionResponse,
    ExhibitionUpdate,
)
from app.schemas.review import (
    FieldDecision,
    ReviewActionRequest,
    ReviewAssignRequest,
    ReviewQueueResponse,
)
from app.schemas.search import (
    SearchHit,
    SearchRequest,
    SearchResponse,
)

__all__ = [
    # Common
    "BulkAction",
    "BulkActionRequest",
    "BulkActionResponse",
    "ErrorResponse",
    "MessageResponse",
    "PaginatedResponse",
    # Auth
    "AuthUserResponse",
    "LoginRequest",
    "TokenResponse",
    # User
    "RoleAssignRequest",
    "RoleResponse",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    # Document
    "DocumentCreate",
    "DocumentListResponse",
    "DocumentResponse",
    "DocumentUpdate",
    "MakeUnavailableRequest",
    # Document File
    "DocumentFileResponse",
    "DocumentPageResponse",
    "DocumentPageUpdate",
    # Authority
    "AuthorityRecordCreate",
    "AuthorityRecordResponse",
    "AuthorityRecordUpdate",
    "AuthorityRelationshipCreate",
    "AuthorityRelationshipResponse",
    "WikidataLinkRequest",
    # Vocabulary
    "TermMergeRequest",
    "VocabularyDomainCreate",
    "VocabularyDomainResponse",
    "VocabularyTermCreate",
    "VocabularyTermResponse",
    "VocabularyTermUpdate",
    # Arrangement
    "ArrangementNodeCreate",
    "ArrangementNodeResponse",
    "ArrangementNodeUpdate",
    # Location
    "LocationCreate",
    "LocationResponse",
    "LocationUpdate",
    # Event
    "EventAuthorityLinkCreate",
    "EventAuthorityLinkResponse",
    "EventCreate",
    "EventDocumentLinkCreate",
    "EventDocumentLinkResponse",
    "EventLocationLinkCreate",
    "EventLocationLinkResponse",
    "EventResponse",
    "EventUpdate",
    # Exhibition
    "BlockReorderRequest",
    "ExhibitionCreate",
    "ExhibitionPageBlockCreate",
    "ExhibitionPageBlockResponse",
    "ExhibitionPageBlockUpdate",
    "ExhibitionPageCreate",
    "ExhibitionPageResponse",
    "ExhibitionPageUpdate",
    "ExhibitionResponse",
    "ExhibitionUpdate",
    # Review
    "FieldDecision",
    "ReviewActionRequest",
    "ReviewAssignRequest",
    "ReviewQueueResponse",
    # Search
    "SearchHit",
    "SearchRequest",
    "SearchResponse",
]
