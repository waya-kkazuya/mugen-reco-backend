from pydantic import BaseModel, Field
from decouple import config
from datetime import datetime


class PostBody(BaseModel):
    category: str = Field(..., example="anime")
    title: str = Field(..., example="おすすめのアニメ3選")
    description: str = Field(..., example="今期注目のアニメを紹介します。")
    recommend1: str = Field(..., example="進撃の巨人")
    recommend2: str = Field(..., example="鬼滅の刃")
    recommend3: str = Field(..., example="SPY×FAMILY")


class PostResponse(PostBody):
    id: str
    created_at: datetime
    updated_at: datetime
