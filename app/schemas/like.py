from pydantic import BaseModel


class LikeStatusResponse(BaseModel):
    liked: bool


class LikeCountResponse(BaseModel):
    like_count: int


class LikeToggleResponse(BaseModel):
    message: str
    is_liked: bool
    like_count: int
    post_id: str
