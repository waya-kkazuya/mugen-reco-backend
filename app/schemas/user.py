from pydantic import BaseModel, Field, validator
from typing import Optional
import re


class UserBody(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, example="user1")
    password: str = Field(..., min_length=8, max_length=72)

    # ユーザー名のバリデーションチェック
    @validator("username")
    def validate_username(cls, v):
        # 文字種チェック（半角英数字と_-.のみ）
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("ユーザー名は半角英数字と_-.のみ使用可能です")

        # 先頭文字チェック（英字または数字で始まる）
        if not re.match(r"^[a-zA-Z0-9]", v):
            raise ValueError("ユーザー名は英字または数字で始まる必要があります")

        # 連続する記号の禁止
        if re.search(r"[_.-]{2,}", v):
            raise ValueError("記号を連続して使用することはできません")

        # 予約語チェック（最低限）
        reserved_words = [
            "admin",
            "administrator",
            "root",
            "system",
            "api",
            "www",
            "mail",
            "support",
            "help",
        ]

        if v.lower() in reserved_words:
            raise ValueError(f'"{v}" は予約語のため使用できません')

        return v.lower()  # 小文字に統一

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


class UsernameCheckResponse(BaseModel):
    is_available: bool = Field(..., description="ユーザー名が利用可能かどうか")
    message: str = Field(..., description="結果メッセージ")
