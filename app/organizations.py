from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, Organization, Department, UserOrganization
from .auth import oauth2_scheme
from pydantic import BaseModel
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
load_dotenv()

router = APIRouter(prefix="/api/organizations")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "mega-secret-key")

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
    except jwt.PyJWTError:
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
