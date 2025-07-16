import os
from typing import Optional
from fastapi import Response
from decouple import config

ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int)


class CookieManager:
    domain: Optional[str] = os.getenv("COOKIE_DOMAIN")
    is_local: bool = os.getenv("IS_LOCAL", "false").lower() == "true"
    access_token_expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES

    def set_jwt_cookie(self, response: Response, token: str) -> None:
        """JWT用クッキーの設定"""
        cookie_settings = {
            "key": "access_token",
            "value": f"Bearer {token}",
            "httponly": True,
            "samesite": "none",
            "secure": True,
            "max_age": self.access_token_expire_minutes * 60,
        }

        # ドメインが設定されている場合のみ追加
        if self.domain:
            cookie_settings["domain"] = self.domain

        print(cookie_settings)

        response.set_cookie(**cookie_settings)

    def clear_jwt_cookie(self, response: Response) -> None:
        """JWTクッキーを削除"""
        delete_cookie_settings = {
            "key": "access_token",
            "httponly": True,
            "samesite": "none",
            "secure": True,
        }

        if self.domain:
            delete_cookie_settings["domain"] = self.domain

        response.delete_cookie(**delete_cookie_settings)
