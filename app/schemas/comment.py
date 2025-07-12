from pydantic import BaseModel, Field
from datetime import datetime


class CommentBody(BaseModel):
    comment: str = Field(
        ..., min_length=1, max_length=200, example="このアニメ最高でした！"
    )


# ここはCommentBodyを継承しない
class CommentResponse(BaseModel):
    comment_id: str
    username: str
    post_id: str
    content: str
    created_at: datetime
