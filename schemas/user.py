from pydantic import BaseModel, Field, validator
from typing import Optional


class UserBody(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, example="user1")
    password: str = Field(..., min_length=8, max_length=72)

    # ユーザー名のバリデーションチェック

    # パスワードのバリデーションチェック
    @validator("password")
    def password_complexity(cls, v):
        if (
            not any(c.islower() for c in v)
            or not any(c.isupper() for c in v)
            or not any(c.isdigit() for c in v)
        ):
            raise ValueError("パスワードには大文字・小文字・数字を含めてください")
        return v


class UserInfo(BaseModel):
    id: Optional[str] = None
    username: str
