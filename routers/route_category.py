from fastapi import APIRouter
from fastapi import HTTPException
from cruds.crud_category import db_get_categories
from schemas.category import CategoryResponse
from typing import List

router = APIRouter()


@router.get("/api/categories", response_model=List[CategoryResponse])
def get_categories():
    try:
        categories = db_get_categories()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get categories failed")
    return categories
