class DatabaseError(Exception):
    """DynamoDBデータベース一般エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class PasswordValidationError(Exception):
    """パスワードバリデーションエラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class UserCreationError(Exception):
    """ユーザー作成エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class UserAlreadyExistsError(Exception):
    """ユーザー既存エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class UsernameAlreadyExistsError(Exception):
    """ユーザー名重複エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class SignupError(Exception):
    """ユーザー登録エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class UserAuthenticationError(Exception):
    """ログイン認証エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class LoginError(Exception):
    """ログインエラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class UserRetrievalError(Exception):
    """ユーザー取得エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class PostRetrievalError(Exception):
    """投稿取得エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class PostNotFoundError(Exception):
    """投稿取得エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class PostCreationError(Exception):
    """投稿作成エラー"""

    def __init__(
        self, message: str, username: str = "", original_error: Exception = None
    ):
        self.message = message
        self.username = username
        self.original_error = original_error
        super().__init__(self.message)


class PostUpdateError(Exception):
    """投稿更新エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class PostOwnershipError(Exception):
    """投稿所有権エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class PostDeletionError(Exception):
    """投稿削除エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class UserPermissionError(Exception):
    """ユーザー権限エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class CommentCreationError(Exception):
    """コメント作成エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class PostNotFoundError(Exception):
    """投稿未発見エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class CommentRetrievalError(Exception):
    """コメント取得エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class CommentNotFoundError(Exception):
    """コメント未発見エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class CommentDeletionError(Exception):
    """コメント削除エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class CommentOwnershipError(Exception):
    """コメント所有権エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class LikeRetrievalError(Exception):
    """いいね取得エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class LikeAlreadyExistsError(Exception):
    """いいね重複エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class LikeCreationError(Exception):
    """いいね作成エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class LikeDeletionError(Exception):
    """いいね削除エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class LikeNotFoundError(Exception):
    """いいね未発見エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class LikeOwnershipError(Exception):
    """いいね所有権エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class CategoryRetrievalError(Exception):
    """カテゴリ取得エラー"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)
