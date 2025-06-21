from pydantic import BaseModel, Field, validator
from decouple import config
from datetime import datetime
from typing import Optional


class PostBody(BaseModel):
    category: str = Field(..., example="anime")
    title: str = Field(..., min_length=1, max_length=20, example="おすすめのアニメ3選")
    description: Optional[str] = Field(
        default=None, example="今期注目のアニメを紹介します。"
    )
    recommend1: str = Field(..., min_length=1, max_length=30, example="進撃の巨人")
    recommend2: str = Field(..., min_length=1, max_length=30, example="鬼滅の刃")
    recommend3: str = Field(..., min_length=1, max_length=30, example="SPY×FAMILY")

    @validator("description")
    def validate_description_length(cls, v):
        if v is not None and not (1 <= len(v) <= 300):
            raise ValueError("description must be between 1 and 300 characters")
        return v


class PostResponse(PostBody):
    id: str
    created_at: datetime
    updated_at: datetime
