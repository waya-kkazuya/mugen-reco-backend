from pydantic import BaseModel


class LikeStatusResponse(BaseModel):
    liked: bool


class LikeCountResponse(BaseModel):
    like_count: int
