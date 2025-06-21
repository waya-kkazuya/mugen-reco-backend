from pydantic import BaseModel, Field
from datetime import datetime


class CommentBody(BaseModel):
    content: str = Field(..., example="このアニメ最高でした！")


class CommentResponse(CommentBody):
    id: str
    username: str
    post_id: str
    content: str
    created_at: datetime
