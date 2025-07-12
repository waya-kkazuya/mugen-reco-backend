from typing import Dict, List, Union, Optional
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


# crud処理を利用したビジネスロジックを記載
class PostService:
    @staticmethod
    def get_posts_with_like_info(
        limit: int = 10,
        last_evaluated_key: Optional[Dict] = None,
        username: Optional[str] = None,
    ) -> List[Dict]:
        """投稿一覧といいね情報を組み合わせて返す"""
        posts_data = db_get_posts(limit=limit, last_evaluated_key=last_evaluated_key)

        # Postsすべてにいいね情報を追加
        for post in posts_data["posts"]:
            post["like_count"] = db_get_like_count(post["post_id"])
            if username:
                post["is_liked"] = db_get_like_status(post["post_id"], username)
            else:
                post["is_liked"] = False

        return posts_data

    @staticmethod
    def get_posts_by_category_with_like_info(
        category: str,
        limit: int = 10,
        last_evaluated_key: Optional[Dict] = None,
        username: Optional[str] = None,
    ) -> List[Dict]:
        """カテゴリ別の投稿一覧といいね情報を組み合わせて返す"""
        posts_data = db_get_posts_by_category(
            category, limit=limit, last_evaluated_key=last_evaluated_key
        )

        # Postsすべてにいいね情報を追加
        for post in posts_data["posts"]:
            post["like_count"] = db_get_like_count(post["post_id"])
            if username:
                post["is_liked"] = db_get_like_status(post["post_id"], username)
            else:
                post["is_liked"] = False

        return posts_data

    @staticmethod
    # 投稿詳細データにいいね情報を含める
    def get_single_post_with_like_info(
        post_id: str, username: Optional[str] = None
    ) -> Dict:
        single_post_data = db_get_single_post(post_id)

        if not single_post_data:
            return False
        # 投稿詳細データがあるならば、いいね情報を追加する
        single_post_data["like_count"] = db_get_like_count(post_id)
        # ログイン中なら個人のいいね状態、未ログインならFalse
        if username:
            single_post_data["is_liked"] = db_get_like_status(post_id, username)
        else:
            single_post_data["is_liked"] = False
        return single_post_data

    @staticmethod
    def create_post_with_like_info(username: str, post_data: Dict) -> Dict:
        """投稿を作成し、いいね情報を含むレスポンスを返す"""
        # 投稿作成
        post_result = db_create_post(username, post_data)
        if not post_result:
            return None
        post_id = post_result["post_id"]
        # いいね情報を追加
        return {
            **post_result,
            "like_count": db_get_like_count(post_id),
            "is_liked": db_get_like_status(post_id, username),
        }

    @staticmethod
    def update_post_with_like_info(post_id: str, data: Dict, username: str) -> Dict:
        """投稿を作成し、いいね情報を含むレスポンスを返す"""
        # 投稿作成
        post_result = db_update_post(post_id, data)
        if not post_result:
            return None
        post_id = post_result["post_id"]
        # いいね情報を追加
        return {
            **post_result,
            "like_count": db_get_like_count(post_id),
            "is_liked": db_get_like_status(post_id, username),
        }

    # いいね情報を追加するだけ
    @staticmethod
    def get_posts_by_user_with_like_info(
        username: str,
        limit: int = 10,
        last_evaluated_key: Optional[Dict] = None,
    ) -> Dict:
        """ユーザーの投稿一覧といいね情報を組み合わせて返す"""
        posts_data = db_get_posts_by_user_paginated(
            username=username, limit=limit, last_evaluated_key=last_evaluated_key
        )

        # Postsすべてにいいね情報を追加
        for post in posts_data["posts"]:
            post["like_count"] = db_get_like_count(post["post_id"])
            post["is_liked"] = db_get_like_status(post["post_id"], username)

        return posts_data

    # いいね情報を追加するだけ
    @staticmethod
    def get_user_liked_posts_with_like_info(
        username: str,
        limit: int = 10,
        last_evaluated_key: Optional[Dict] = None,
    ) -> Dict:
        """ユーザーの投稿一覧といいね情報を組み合わせて返す"""
        posts_data = db_get_user_liked_posts_paginated(
            username=username, limit=limit, last_evaluated_key=last_evaluated_key
        )

        # Postsすべてにいいね情報を追加
        for post in posts_data["posts"]:
            post["like_count"] = db_get_like_count(post["post_id"])
            post["is_liked"] = db_get_like_status(post["post_id"], username)

        return posts_data
