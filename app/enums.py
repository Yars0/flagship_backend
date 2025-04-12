from enum import Enum

class UserRole(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    MANAGER = "manager"
    ADMIN = "admin"

class DocumentStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    SIGNED = "signed"
    DECLINED = "declined"

class InviteStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
