from fastapi import APIRouter
from fastapi import HTTPException
from app.cruds.crud_category import db_get_categories
from app.schemas.category import CategoryResponse
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/categories", response_model=List[CategoryResponse])
def get_categories():
    logger.info("[ROUTE] Getting all categories")

    categories = db_get_categories()

    logger.info(f"[ROUTE] Categories retrieved successfully: count={len(categories)}")
    return categories
