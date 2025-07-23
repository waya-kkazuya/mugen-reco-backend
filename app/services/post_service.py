from typing import Optional
from app.cruds.crud_post import (
    db_get_posts,
    db_get_posts_by_category,
    db_get_single_post,
    db_create_post,
    db_update_post,
    db_get_posts_by_user_paginated,
    db_get_user_liked_posts_paginated,
)
from app.cruds.crud_like import db_get_like_count, db_get_like_status
from app.exceptions import (
    PostRetrievalError,
    PostCreationError,
    PostUpdateError,
    DatabaseError,
    LikeRetrievalError,
)
from botocore.exceptions import BotoCoreError
import logging

logger = logging.getLogger(__name__)


# crud処理を利用したビジネスロジックを記載
class PostService:
    @staticmethod
    def get_posts_with_like_info(
        limit: int = 10,
        last_evaluated_key: Optional[dict] = None,
        username: Optional[str] = None,
    ) -> list[dict]:
        """投稿一覧といいね情報を組み合わせて返す"""
        logger.info(
            f"[SERVICE] Getting posts service: limit={limit}, username={username}"
        )

        try:
            result = db_get_posts(limit=limit, last_evaluated_key=last_evaluated_key)

            # Postsすべてにいいね情報を追加
            for post in result["posts"]:
                try:
                    post["like_count"] = db_get_like_count(post["post_id"])
                    if username:
                        post["is_liked"] = db_get_like_status(post["post_id"], username)
                    else:
                        post["is_liked"] = False
                except LikeRetrievalError as e:
                    logger.warning(
                        f"[SERVICE] Failed to get like info for post {post['post_id']}: {e.message}"
                    )
                    # いいね情報取得失敗時はデフォルト値を設定
                    post["like_count"] = 0
                    post["is_liked"] = False

            logger.info(
                f"[SERVICE] Posts service completed: count={len(result['posts'])}"
            )
            return result

        except PostRetrievalError:
            # PostRetrievalErrorはそのまま再発生
            logger.error("[SERVICE] Post retrieval error in get_posts_with_like_info")
            raise

        except DatabaseError:
            # DatabaseErrorもそのまま再発生
            logger.error("[SERVICE] Database error in get_posts_with_like_info")
            raise

        except Exception as e:
            logger.error(
                f"[SERVICE] Unexpected error in get_posts_with_like_info: error_type={type(e).__name__}, error_message={str(e)}",
                exc_info=True,
            )

            raise PostRetrievalError(
                message="投稿一覧取得サービスで予期しないエラーが発生しました。",
                original_error=e,
            )

    @staticmethod
    def get_posts_by_category_with_like_info(
        category: str,
        limit: int = 10,
        last_evaluated_key: Optional[dict] = None,
        username: Optional[str] = None,
    ) -> list[dict]:
        """カテゴリ別の投稿一覧といいね情報を組み合わせて返す"""
        logger.info(
            f"[SERVICE] Getting posts by category service: category={category}, limit={limit}, username={username}"
        )

        try:
            posts_data = db_get_posts_by_category(
                category, limit=limit, last_evaluated_key=last_evaluated_key
            )

            # Postsすべてにいいね情報を追加
            for post in posts_data["posts"]:
                try:
                    post["like_count"] = db_get_like_count(post["post_id"])
                    if username:
                        post["is_liked"] = db_get_like_status(post["post_id"], username)
                    else:
                        post["is_liked"] = False
                except LikeRetrievalError as e:
                    logger.warning(
                        f"[SERVICE] Failed to get like info for post {post['post_id']}: {e.message}"
                    )
                    post["like_count"] = 0
                    post["is_liked"] = False

            logger.info(
                f"[SERVICE] Posts by category service completed: category={category}, count={len(posts_data['posts'])}"
            )
            return posts_data

        except PostRetrievalError:
            logger.error(
                f"[SERVICE] Post retrieval error in get_posts_by_category_with_like_info: category={category}"
            )
            raise

        except DatabaseError:
            logger.error(
                f"[SERVICE] Database error in get_posts_by_category_with_like_info: category={category}"
            )
            raise

        except Exception as e:
            logger.error(
                f"[SERVICE] Unexpected error in get_posts_by_category_with_like_info: category={category}, error_type={type(e).__name__}, error_message={str(e)}",
                exc_info=True,
            )
            raise PostRetrievalError(
                message=f"カテゴリ'{category}'の投稿一覧取得サービスで予期しないエラーが発生しました。",
                original_error=e,
            )

    @staticmethod
    # 投稿詳細データにいいね情報を含める
    def get_single_post_with_like_info(
        post_id: str, username: Optional[str] = None
    ) -> dict:
        logger.info(
            f"[SERVICE] Getting single post service: post_id={post_id}, username={username}"
        )
        try:
            single_post_data = db_get_single_post(post_id)

            # 投稿詳細データがあるならば、いいね情報を追加する
            try:
                single_post_data["like_count"] = db_get_like_count(post_id)
                # ログイン中なら個人のいいね状態、未ログインならFalse
                if username:
                    single_post_data["is_liked"] = db_get_like_status(post_id, username)
                else:
                    single_post_data["is_liked"] = False
            except LikeRetrievalError as e:
                logger.warning(
                    f"[SERVICE] Failed to get like info for post {post_id}: {e.message}"
                )
                single_post_data["like_count"] = 0
                single_post_data["is_liked"] = False

            logger.info(f"[SERVICE] Single post service completed: post_id={post_id}")
            return single_post_data

        except PostRetrievalError:
            logger.error(
                f"[SERVICE] Post retrieval error in get_single_post_with_like_info: post_id={post_id}"
            )
            raise

        except DatabaseError:
            logger.error(
                f"[SERVICE] Database error in get_single_post_with_like_info: post_id={post_id}"
            )
            raise

        except Exception as e:
            logger.error(
                f"[SERVICE] Unexpected error in get_single_post_with_like_info: post_id={post_id}, error_type={type(e).__name__}, error_message={str(e)}",
                exc_info=True,
            )
            raise PostRetrievalError(
                message="投稿詳細取得サービスで予期しないエラーが発生しました。",
                original_error=e,
            )

    @staticmethod
    def create_post_with_like_info(username: str, post_data: dict) -> dict:
        """投稿を作成し、いいね情報を含むレスポンスを返す"""
        logger.info(f"[SERVICE] Starting post creation service for user: {username}")

        try:
            post_result = db_create_post(username, post_data)

            post_id = post_result["post_id"]

            logger.info(
                f"[SERVICE] Post creation service completed successfully: username={username}, post_id={post_id}"
            )
            # いいね情報を追加
            try:
                like_count = db_get_like_count(post_id)
                is_liked = db_get_like_status(post_id, username)
            except LikeRetrievalError as e:
                logger.warning(
                    f"[SERVICE] Failed to get like info for new post {post_id}: {e.message}"
                )
                like_count = 0
                is_liked = False

            result = {
                **post_result,
                "like_count": like_count,
                "is_liked": is_liked,
            }

            logger.info(
                f"[SERVICE] Post creation service completed successfully: username={username}, post_id={post_id}"
            )
            return result

        except DatabaseError as e:
            logger.error(f"[SERVICE] Database error: {e.message}", exc_info=True)
            raise

        except PostCreationError as e:
            logger.warning(f"[SERVICE] Post creation error: {e.message}", exc_info=True)
            raise

        except Exception as e:
            logger.error(f"[SERVICE] Unexpected error: {str(e)}", exc_info=True)
            raise PostCreationError(
                message="投稿作成サービスで予期しないエラーが発生しました",
                username=username,
                original_error=e,
            )

    @staticmethod
    def update_post_with_like_info(post_id: str, data: dict, username: str) -> dict:
        """投稿を作成し、いいね情報を含むレスポンスを返す"""
        logger.info(
            f"[SERVICE] Starting post update service: post_id={post_id}, username={username}"
        )
        try:
            # 投稿作成
            post_result = db_update_post(post_id, data)

            post_id = post_result["post_id"]

            # いいね情報を追加
            try:
                like_count = db_get_like_count(post_id)
                is_liked = db_get_like_status(post_id, username)
            except LikeRetrievalError as e:
                logger.warning(
                    f"[SERVICE] Failed to get like info for updated post {post_id}: {e.message}"
                )
                like_count = 0
                is_liked = False

            result = {
                **post_result,
                "like_count": like_count,
                "is_liked": is_liked,
            }

            logger.info(f"[SERVICE] Post update service completed: post_id={post_id}")
            return result

        except PostUpdateError:
            logger.error(
                f"[SERVICE] Post update error in update_post_with_like_info: post_id={post_id}"
            )
            raise

        except DatabaseError:
            logger.error(
                f"[SERVICE] Database error in update_post_with_like_info: post_id={post_id}"
            )
            raise

        except Exception as e:
            logger.error(
                f"[SERVICE] Unexpected error in update_post_with_like_info: post_id={post_id}, error_type={type(e).__name__}, error_message={str(e)}",
                exc_info=True,
            )
            raise PostUpdateError(
                message="投稿更新サービスで予期しないエラーが発生しました。",
                original_error=e,
            )

    # いいね情報を追加するだけ
    @staticmethod
    def get_posts_by_user_with_like_info(
        username: str,
        limit: int = 10,
        last_evaluated_key: Optional[dict] = None,
    ) -> dict:
        """ユーザーの投稿一覧といいね情報を組み合わせて返す"""
        logger.info(
            f"[SERVICE] Getting posts by user service: username={username}, limit={limit}"
        )
        try:
            posts_data = db_get_posts_by_user_paginated(
                username=username, limit=limit, last_evaluated_key=last_evaluated_key
            )

            # Postsすべてにいいね情報を追加
            for post in posts_data["posts"]:
                try:
                    post["like_count"] = db_get_like_count(post["post_id"])
                    post["is_liked"] = db_get_like_status(post["post_id"], username)
                except LikeRetrievalError as e:
                    logger.warning(
                        f"[SERVICE] Failed to get like info for post {post['post_id']}: {e.message}"
                    )
                    post["like_count"] = 0
                    post["is_liked"] = False

            logger.info(
                f"[SERVICE] Posts by user service completed: username={username}, count={len(posts_data['posts'])}"
            )
            return posts_data

        except PostRetrievalError:
            logger.error(
                f"[SERVICE] Post retrieval error in get_posts_by_user_with_like_info: username={username}"
            )
            raise

        except DatabaseError:
            logger.error(
                f"[SERVICE] Database error in get_posts_by_user_with_like_info: username={username}"
            )
            raise

        except Exception as e:
            logger.error(
                f"[SERVICE] Unexpected error in get_posts_by_user_with_like_info: username={username}, error_type={type(e).__name__}, error_message={str(e)}",
                exc_info=True,
            )
            raise PostRetrievalError(
                message=f"ユーザー'{username}'の投稿一覧取得サービスで予期しないエラーが発生しました。",
                original_error=e,
            )

    # いいね情報を追加するだけ
    @staticmethod
    def get_user_liked_posts_with_like_info(
        username: str,
        limit: int = 10,
        last_evaluated_key: Optional[dict] = None,
    ) -> dict:
        """ユーザーの投稿一覧といいね情報を組み合わせて返す"""
        logger.info(
            f"[SERVICE] Getting user liked posts service: username={username}, limit={limit}"
        )

        try:
            posts_data = db_get_user_liked_posts_paginated(
                username=username, limit=limit, last_evaluated_key=last_evaluated_key
            )

            # Postsすべてにいいね情報を追加
            for post in posts_data["posts"]:
                try:
                    post["like_count"] = db_get_like_count(post["post_id"])
                    post["is_liked"] = db_get_like_status(post["post_id"], username)
                except LikeRetrievalError as e:
                    logger.warning(
                        f"[SERVICE] Failed to get like info for post {post['post_id']}: {e.message}"
                    )
                    post["like_count"] = 0
                    post["is_liked"] = False

            logger.info(
                f"[SERVICE] User liked posts service completed: username={username}, count={len(posts_data['posts'])}"
            )
            return posts_data

        except PostRetrievalError:
            logger.error(
                f"[SERVICE] Post retrieval error in get_user_liked_posts_with_like_info: username={username}"
            )
            raise

        except DatabaseError:
            logger.error(
                f"[SERVICE] Database error in get_user_liked_posts_with_like_info: username={username}"
            )
            raise

        except Exception as e:
            logger.error(
                f"[SERVICE] Unexpected error in get_user_liked_posts_with_like_info: username={username}, error_type={type(e).__name__}, error_message={str(e)}",
                exc_info=True,
            )
            raise PostRetrievalError(
                message=f"ユーザー'{username}'のいいね投稿一覧取得サービスで予期しないエラーが発生しました。",
                original_error=e,
            )
