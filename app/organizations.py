from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from .database import get_db
from .schemas import (
    OrganizationsResponse, DepartmentsResponse,
    UsersResponse, DocumentIdResponse,
    SearchUserRequest, AddUserRequest,
    CreateDocumentRequest, SubscribeDocumentRequest,
    DocumentsResponse, SuccessResponse
)
from .models import (
    Organization, Department, User,
    UserOrganization, UserDepartmentRole,
    Document, Signature
)
from .auth import oauth2_scheme
from pydantic import BaseModel
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
load_dotenv()

router = APIRouter(prefix="/api/organizations")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "mega-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return {
            "user_id": user.id,  
            "is_admin": payload.get("is_admin", False)
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

class NewOrganizationRequest(BaseModel):
    name: str
    token: str

class NewDepartmentRequest(BaseModel):
    name: str

def get_current_user(db: Session, token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/new")
async def create_organization(
    request: NewOrganizationRequest,
    db: Session = Depends(get_db)
):
    user = get_current_user(db, request.token)

    org = Organization(name=request.name, owner_id=user.id)
    db.add(org)
    db.commit()
    db.refresh(org)

    user_org = UserOrganization(user_id=user.id, organization_id=org.id)
    db.add(user_org)
    db.commit()

    return {"status": "success", "id": org.id}

@router.get("/{org_id}")
async def get_organization(org_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    dept_count = db.query(Department).filter(
        Department.organization_id == org_id
    ).count()

    emp_count = db.query(UserOrganization).filter(
        UserOrganization.organization_id == org_id
    ).count()

    return {
        "organizations": [{
            "id": org.id,
            "name": org.name,
            "departments_count": dept_count,
            "employees_count": emp_count
        }]
    }

@router.post("/{org_id}/departments/new")
async def create_department(
    org_id: int,
    request: NewDepartmentRequest,
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    dept = Department(name=request.name, organization_id=org_id)
    db.add(dept)
    db.commit()
    db.refresh(dept)

    return {
        "success": True,
        "id_organization": org_id,
        "id_depatrament": dept.id
    }

@router.get("/{org_id}/departments/{dep_id}")
async def get_department(
    org_id: int,
    dep_id: int,
    db: Session = Depends(get_db)
):
    dept = db.query(Department).filter(
        Department.id == dep_id,
        Department.organization_id == org_id
    ).first()

    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    emp_count = db.query(UserDepartmentRole).filter(
        UserDepartmentRole.department_id == dep_id
    ).count()

    return {
        "departaments": [{
            "id": dept.id,
            "name": dept.name,
            "employees_count": emp_count
        }]
    }


@router.post("/organizations/get", response_model=OrganizationsResponse)
def get_user_organizations(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user_id = token_data["user_id"]
    orgs = db.query(Organization).join(
        UserOrganization,
        UserOrganization.organization_id == Organization.id
    ).filter(
        UserOrganization.user_id == user_id
    ).all()

    return OrganizationsResponse(
        success=True,
        organizations=[{"org_id": org.id, "name": org.name} for org in orgs]
    )

@router.post("/organizations/{org_id}/departments/get", response_model=DepartmentsResponse)
def get_organization_departments(
    org_id: int = Path(..., title="Organization ID"),
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == token_data["user_id"],
        UserOrganization.organization_id == org_id
    ).first()

    if not user_org:
        return DepartmentsResponse(
            success=False,
            error="Organization not found or access denied"
        )

    departments = db.query(Department).filter(
        Department.organization_id == org_id
    ).all()

    return DepartmentsResponse(
        success=True,
        departments=[{"dep_id": dep.id, "name": dep.name} for dep in departments]
    )

@router.post("/organizations/{org_id}/departments/{dep_id}/users", response_model=UsersResponse)
def get_department_users(
    org_id: int = Path(..., title="Organization ID"),
    dep_id: int = Path(..., title="Department ID"),
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == token_data["user_id"],
        UserOrganization.organization_id == org_id
    ).first()

    if not user_org:
        return UsersResponse(
            success=False,
            error="Organization not found or access denied"
        )

    department = db.query(Department).filter(
        Department.id == dep_id,
        Department.organization_id == org_id
    ).first()

    if not department:
        return UsersResponse(
            success=False,
            error="Department not found"
        )

    users = db.query(User).join(
        UserDepartmentRole,
        UserDepartmentRole.user_id == User.id
    ).filter(
        UserDepartmentRole.department_id == dep_id
    ).all()

    return UsersResponse(
        success=True,
        users=[{"user_id": u.id, "name": u.name, "email": u.email} for u in users]
    )

@router.get("/organizations/{org_id}/users", response_model=UsersResponse)
def get_organization_users(
    org_id: int = Path(..., title="Organization ID"),
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == token["user_id"],
        UserOrganization.organization_id == org_id
    ).first()

    if not user_org:
        return UsersResponse(
            success=False,
            error="Organization not found or access denied"
        )

    users = db.query(User).join(
        UserOrganization,
        UserOrganization.user_id == User.id
    ).filter(
        UserOrganization.organization_id == org_id
    ).all()

    return UsersResponse(
        success=True,
        users=[{"user_id": u.id, "name": u.name} for u in users]
    )

@router.post("/organizations/{org_id}/departments/{dep_id}/addUser", response_model=SuccessResponse)
def add_user_to_department(
    org_id: int = Path(..., title="Organization ID"),
    dep_id: int = Path(..., title="Department ID"),
    request: AddUserRequest = Depends(),
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    if not token_data.get("is_admin"):
        return SuccessResponse(
            success=False,
            error="Permission denied"
        )

    existing = db.query(UserDepartmentRole).filter(
        UserDepartmentRole.user_id == request.user_id,
        UserDepartmentRole.department_id == dep_id
    ).first()

    if existing:
        return SuccessResponse(
            success=False,
            error="User already exists in department"
        )

    new_role = UserDepartmentRole(
        user_id=request.user_id,
        department_id=dep_id,
        role="viewer"
    )
    db.add(new_role)
    db.commit()

    return SuccessResponse(
        success=True,
        message="User added successfully"
    )

@router.post("/users/search", response_model=UsersResponse)
def search_users(
    request: SearchUserRequest,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    users = db.query(User).filter(
        User.name.ilike(f"%{request.name}%")
    ).limit(10).all()

    if not users:
        return UsersResponse(
            success=False,
            error="No users found"
        )

    return UsersResponse(
        success=True,
        users=[{"user_id": u.id, "name": u.name} for u in users]
    )

@router.post("/document/new", response_model=DocumentIdResponse)
def create_document(
    request: CreateDocumentRequest,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    recipients = db.query(User).filter(
        User.id.in_(request.recipients)
    ).all()

    if len(recipients) != len(request.recipients):
        return DocumentIdResponse(
            success=False,
            error="Invalid recipients"
        )

    document = Document(
        title=request.title,
        content=request.file_url,
        sender_id=token_data["user_id"],
        status="draft"
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    for recipient in recipients:
        signature = Signature(
            document_id=document.id,
            signer_id=recipient.id,
            status="pending"
        )
        db.add(signature)

    db.commit()

    return DocumentIdResponse(
        success=True,
        document_id=document.id
    )

@router.post("/document/get", response_model=DocumentsResponse)
def get_user_documents(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    sent_docs = db.query(Document).filter(
        Document.sender_id == token_data["user_id"]
    ).all()

    received_docs = db.query(Document).join(
        Signature,
        Signature.document_id == Document.id
    ).filter(
        Signature.signer_id == token_data["user_id"]
    ).all()

    all_docs = list(set(sent_docs + received_docs))

    if not all_docs:
        return DocumentsResponse(
            success=False,
            error="No documents found"
        )

    return DocumentsResponse(
        success=True,
        documents=[{
            "document_id": doc.id,
            "title": doc.title,
            "status": doc.status
        } for doc in all_docs]
    )

@router.post("/document/subscribe", response_model=SuccessResponse)
def subscribe_document(
    request: SubscribeDocumentRequest,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Находим подпись, которую нужно подтвердить
    signature = db.query(Signature).filter(
        Signature.document_id == request.document_id,
        Signature.signer_id == token_data["user_id"],
        Signature.status == "pending"
    ).first()

    if not signature:
        return SuccessResponse(
            success=False,
            error="Document not found or already signed"
        )

    signature.status = "signed"
    signature.signed_at = datetime.utcnow()

    pending_signatures = db.query(Signature).filter(
        Signature.document_id == request.document_id,
        Signature.status == "pending"
    ).count()

    if pending_signatures == 0:
        document = db.query(Document).get(request.document_id)
        document.status = "signed"

    db.commit()

    return SuccessResponse(
        success=True,
        message="Document signed successfully"
    )
