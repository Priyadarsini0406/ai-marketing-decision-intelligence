"""Authenticated dataset uploads; management remains in the admin router."""
from fastapi import APIRouter, Depends
from api.auth import current_user
from api.admin import upload_dataset

router = APIRouter(prefix="/datasets", tags=["datasets"], dependencies=[Depends(current_user)])
# Reuse the same validation and storage as administrator uploads.
router.add_api_route("", upload_dataset, methods=["POST"], status_code=201)
