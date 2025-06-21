from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: str
    name: str
