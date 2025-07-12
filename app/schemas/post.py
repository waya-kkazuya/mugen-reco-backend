from pydantic import BaseModel, Field, validator
from decouple import config
from datetime import datetime
from typing import Optional, List, Dict


class PostBody(BaseModel):
    category: str = Field(..., example="anime")
    title: str = Field(..., min_length=1, max_length=50, example="おすすめのアニメ3選")
    description: Optional[str] = Field(
        default=None, example="今期注目のアニメを紹介します。"
    )
    recommend1: str = Field(..., min_length=1, max_length=50, example="進撃の巨人")
    recommend2: str = Field(..., min_length=1, max_length=50, example="鬼滅の刃")
    recommend3: str = Field(..., min_length=1, max_length=50, example="SPY×FAMILY")

    @validator("description")
    def validate_description_length(cls, v):
        if v is not None and not (1 <= len(v) <= 300):
            raise ValueError("description must be between 1 and 300 characters")
        return v


# いいね情報を追加
class PostResponse(PostBody):
    post_id: str
    username: str
    like_count: int
    is_liked: bool
    created_at: datetime
    updated_at: datetime


class PaginatedPostsResponse(BaseModel):
    posts: List[PostResponse]
    last_evaluated_key: Optional[str]  # 文字列化したのでstr
