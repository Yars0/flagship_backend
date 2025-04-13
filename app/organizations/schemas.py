from pydantic import BaseModel
from typing import List, Optional

class OrganizationResponse(BaseModel):
    org_id: int
    name: str

class DepartmentResponse(BaseModel):
    dep_id: int
    name: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: Optional[str] = None
    department: Optional[str] = None

class DocumentResponse(BaseModel):
    document_id: int
    title: str
    status: str

class SearchUserRequest(BaseModel):
    token: str
    name: str

class AddUserRequest(BaseModel):
    token: str
    user_id: int

class CreateDocumentRequest(BaseModel):
    token: str
    title: str
    date: str
    file_url: str
    recipients: List[int]

class SubscribeDocumentRequest(BaseModel):
    token: str
    document_id: int

class SuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

class OrganizationsResponse(SuccessResponse):
    organizations: List[OrganizationResponse] = []

class DepartmentsResponse(SuccessResponse):
    departments: List[DepartmentResponse] = []

class UsersResponse(SuccessResponse):
    users: List[UserResponse] = []

class DocumentsResponse(SuccessResponse):
    documents: List[DocumentResponse] = []

class DocumentIdResponse(SuccessResponse):
    document_id: Optional[int] = None
