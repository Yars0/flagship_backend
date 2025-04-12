from sqlalchemy import (Column, Integer, String, Text,
    ForeignKey, TIMESTAMP, Enum, Boolean, DateTime)
from sqlalchemy.sql import func
from .database import Base
from .enums import UserRole, DocumentStatus, InviteStatus
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(Text, nullable=False)
    telegram_id =  Column(String(30))

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"))

class UserOrganization(Base):
    __tablename__ = "user_organizations"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)

class UserDepartmentRole(Base):
    __tablename__ = "user_department_roles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), primary_key=True)
    role = Column(Enum(UserRole), nullable=False)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"))
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Signature(Base):
    __tablename__ = "signatures"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    signer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    signature_hash = Column(Text, nullable=False)
    signed_at = Column(TIMESTAMP)
    confirmed_via = Column(String(20))

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

class LoginSession(Base):
    __tablename__ = 'login_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    session_token = Column(String(64), unique=True)
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, default=lambda: datetime.now() + timedelta(minutes=10))

    user = relationship("User")

class Invite(Base):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"))
    email_or_phone = Column(String(255), nullable=False)
    token = Column(String(64), unique=True, nullable=False)
    status = Column(Enum(InviteStatus), default=InviteStatus.PENDING)

class ConfirmationCode(Base):
    __tablename__ = 'confirmation_codes'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    code = Column(String(6), nullable=True)
    expires_at = Column(TIMESTAMP, default=lambda: datetime.now() + timedelta(minutes=15))
    is_used = Column(Boolean, default=False)
    telegram_verified = Column(Boolean, default=False)
