from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from .enums import UserRole, DocumentStatus, InviteStatus

class UserBase(BaseModel):
    email: EmailStr
    phone: str = Field(..., min_length=5, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=5, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=6)

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class OrganizationCreate(OrganizationBase):
    owner_id: Optional[int] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    owner_id: Optional[int] = None

class Organization(OrganizationBase):
    id: int
    owner_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    organization_id: int

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    organization_id: Optional[int] = None

class Department(DepartmentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class UserOrganizationBase(BaseModel):
    user_id: int
    organization_id: int

class UserOrganizationCreate(UserOrganizationBase):
    pass

class UserOrganization(UserOrganizationBase):
    model_config = ConfigDict(from_attributes=True)

class UserDepartmentRoleBase(BaseModel):
    user_id: int
    department_id: int
    role: UserRole

class UserDepartmentRoleCreate(UserDepartmentRoleBase):
    pass

class UserDepartmentRoleUpdate(BaseModel):
    role: Optional[UserRole] = None

class UserDepartmentRole(UserDepartmentRoleBase):
    model_config = ConfigDict(from_attributes=True)

class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    organization_id: int
    sender_id: Optional[int] = None
    status: DocumentStatus = DocumentStatus.DRAFT

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    status: Optional[DocumentStatus] = None
    sender_id: Optional[int] = None

class Document(DocumentBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SignatureBase(BaseModel):
    document_id: int
    signer_id: int
    signature_hash: str
    confirmed_via: Optional[str] = Field(None, max_length=20)

class SignatureCreate(SignatureBase):
    pass

class SignatureUpdate(BaseModel):
    signature_hash: Optional[str] = None
    signed_at: Optional[datetime] = None
    confirmed_via: Optional[str] = Field(None, max_length=20)

class Signature(SignatureBase):
    id: int
    signed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class InviteBase(BaseModel):
    organization_id: int
    email_or_phone: str = Field(..., min_length=3, max_length=255)
    token: str = Field(..., min_length=64, max_length=64)

class InviteCreate(InviteBase):
    pass

class InviteUpdate(BaseModel):
    status: Optional[InviteStatus] = None

class Invite(InviteBase):
    id: int
    status: InviteStatus = InviteStatus.PENDING
    model_config = ConfigDict(from_attributes=True)

class UserWithOrganizations(User):
    organizations: List[Organization] = []

class OrganizationWithUsers(Organization):
    users: List[User] = []
    departments: List[Department] = []

class DocumentWithSignatures(Document):
    signatures: List[Signature] = []
