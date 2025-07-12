import jwt
from fastapi import HTTPException
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from decouple import config
from typing import Optional

JWT_KEY = config("JWT_KEY")


class AuthJwtCsrf:
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    secret_key = JWT_KEY

    def generate_hashed_pw(self, password) -> str:
        return self.pwd_ctx.hash(password)

    def verify_pw(self, plain_pw, hashed_pw) -> bool:
        return self.pwd_ctx.verify(plain_pw, hashed_pw)

    def encode_jwt(self, username) -> str:
        payload = {
            "exp": datetime.now(timezone.utc)
            + timedelta(days=0, minutes=5),  # expires有効期限 5分
            "iat": datetime.now(timezone.utc),  # issuedat JWTの生成日時
            "sub": username,
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def decode_jwt(self, token) -> str:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="The JWT has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail="JWT is not valid")

    def verify_jwt(self, request) -> str:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(
                status_code=401, detail="No JWT exist: may not set yet or deleted"
            )
        _, _, value = token.partition(" ")
        subject = self.decode_jwt(value)
        return subject

    def verify_update_jwt(self, request) -> tuple[str, str]:
        subject = self.verify_jwt(request)
        new_token = self.encode_jwt(subject)  # jWTを生成し直す
        return new_token, subject

    def verify_csrf_update_jwt(self, request, csrf_protect, headers) -> tuple[str, str]:
        # CSRF
        csrf_token = csrf_protect.get_csrf_from_headers(headers)
        csrf_protect.validate_csrf(
            csrf_token
        )  # 例外処理が発生しなければCSRFトークンが有効
        # JWT
        subject = self.verify_jwt(request)
        new_token = self.encode_jwt(subject)
        return new_token, subject

    def get_current_user_optional(self, request) -> Optional[str]:
        """オプショナルなJWT認証（失敗してもNoneを返す）"""
        try:
            return self.verify_jwt(request)
        except HTTPException:
            return None
