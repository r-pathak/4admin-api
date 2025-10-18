import datetime
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/policies",
    tags=["policies"]
)

# In-memory storage for demo purposes
# In production, replace with actual database
policy_storage = {}


# Pydantic Models
class PolicyUploadRequest(BaseModel):
    file_b64: str
    filename: Optional[str] = None
    tenant_id: Optional[str] = None
    retain: bool = Field(default=False)


class PolicyField(BaseModel):
    name: str
    value: Optional[str]
    confidence: Optional[float] = None
    source_pages: list[int] = []
    citation_text: Optional[str] = None
    model_version: Optional[str] = None


class PolicyAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    provider: Optional[str] = None
    plan_type: Optional[str] = None
    extracted_fields: list[PolicyField]
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: Optional[datetime.datetime] = None
    expires_at: Optional[datetime.datetime] = None


class PolicyGetResponse(BaseModel):
    analysis: PolicyAnalysis
    file_url: Optional[str] = None


class PolicyUpdateRequest(BaseModel):
    updated_fields: list[PolicyField]


class PolicyUpdateResponse(BaseModel):
    id: str
    updated_at: datetime.datetime
    message: str = "Policy analysis updated successfully"


# API Endpoints
@router.post("/", response_model=PolicyGetResponse, status_code=status.HTTP_201_CREATED)
async def upload_policy(request: PolicyUploadRequest):
    """
    Upload and analyze a policy document.
    
    - **file_b64**: Base64-encoded file content
    - **filename**: Optional filename
    - **tenant_id**: Optional tenant identifier
    - **retain**: Whether to retain the file after analysis
    """
    # Create a new policy analysis
    # In production, this would:
    # 1. Decode and validate the file
    # 2. Store the file (if retain=True)
    # 3. Process/extract fields using AI/ML
    # 4. Store analysis in database
    
    analysis = PolicyAnalysis(
        tenant_id=request.tenant_id,
        extracted_fields=[
            PolicyField(
                name="example_field",
                value="This is a placeholder",
                confidence=0.95,
                source_pages=[1],
                citation_text="Sample citation"
            )
        ]
    )
    
    # Store in memory
    policy_storage[analysis.id] = {
        "analysis": analysis,
        "file_b64": request.file_b64 if request.retain else None,
        "filename": request.filename
    }
    
    # Generate file URL if retained
    file_url = f"/policies/{analysis.id}/file" if request.retain else None
    
    return PolicyGetResponse(
        analysis=analysis,
        file_url=file_url
    )


@router.get("/{policy_id}", response_model=PolicyGetResponse)
async def get_policy(policy_id: str):
    """
    Retrieve a policy analysis by ID.
    
    - **policy_id**: The unique identifier of the policy analysis
    """
    if policy_id not in policy_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy analysis with id '{policy_id}' not found"
        )
    
    stored_policy = policy_storage[policy_id]
    file_url = f"/policies/{policy_id}/file" if stored_policy.get("file_b64") else None
    
    return PolicyGetResponse(
        analysis=stored_policy["analysis"],
        file_url=file_url
    )


@router.put("/{policy_id}", response_model=PolicyUpdateResponse)
async def update_policy(policy_id: str, request: PolicyUpdateRequest):
    """
    Update an existing policy analysis.
    
    - **policy_id**: The unique identifier of the policy analysis
    - **updated_fields**: List of fields to update
    """
    if policy_id not in policy_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy analysis with id '{policy_id}' not found"
        )
    
    stored_policy = policy_storage[policy_id]
    analysis = stored_policy["analysis"]
    
    # Update the fields
    analysis.extracted_fields = request.updated_fields
    analysis.updated_at = datetime.datetime.utcnow()
    
    return PolicyUpdateResponse(
        id=policy_id,
        updated_at=analysis.updated_at
    )


@router.get("/", response_model=list[PolicyGetResponse])
async def list_policies(tenant_id: Optional[str] = None):
    """
    List all policy analyses, optionally filtered by tenant.
    
    - **tenant_id**: Optional filter by tenant ID
    """
    results = []
    
    for policy_id, stored_policy in policy_storage.items():
        analysis = stored_policy["analysis"]
        
        # Filter by tenant_id if provided
        if tenant_id and analysis.tenant_id != tenant_id:
            continue
        
        file_url = f"/policies/{policy_id}/file" if stored_policy.get("file_b64") else None
        
        results.append(PolicyGetResponse(
            analysis=analysis,
            file_url=file_url
        ))
    
    return results


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: str):
    """
    Delete a policy analysis.
    
    - **policy_id**: The unique identifier of the policy analysis
    """
    if policy_id not in policy_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy analysis with id '{policy_id}' not found"
        )
    
    del policy_storage[policy_id]
    return None

