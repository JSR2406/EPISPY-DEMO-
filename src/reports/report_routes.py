from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .report_service import ReportService
from ..auth.jwt_handler import decode_token

router = APIRouter(prefix="/api/reports", tags=["Reports"])
security = HTTPBearer()

@router.post("/upload")
async def upload_report(
    file: UploadFile = File(...),
    report_type: str = "blood_test",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    patient_id = payload["user_id"]
    
    report_service = ReportService()
    try:
        result = await report_service.upload_and_analyze_report(
            patient_id, file, report_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report processing failed: {str(e)}")
