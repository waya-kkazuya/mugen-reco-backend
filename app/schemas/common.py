from pydantic import BaseModel


class SuccessMsg(BaseModel):
    message: str
