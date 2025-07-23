import logging
import logging.config
import json
import os
from datetime import datetime
from typing import Dict, Any


class LoggingConfig:
    """ログ設定クラス（シンプル版）"""

    @staticmethod
    def get_log_level() -> str:
        """環境変数からログレベルを取得"""
        return os.getenv("LOG_LEVEL", "INFO").upper()

    @staticmethod
    def get_environment() -> str:
        """環境変数から環境を取得"""
        return os.getenv("ENVIRONMENT", "development")

    @staticmethod
    def setup_logging() -> logging.Logger:
        """ログ設定のメイン関数"""

        log_level = LoggingConfig.get_log_level()
        environment = LoggingConfig.get_environment()

        # 既存のハンドラーをクリア
        root_logger = logging.getLogger()
        if root_logger.handlers:
            for handler in root_logger.handlers:
                root_logger.removeHandler(handler)

        # ハンドラーとフォーマッターを設定
        handler = logging.StreamHandler()

        if environment == "development":
            # 開発環境: コンソール中心（読みやすさ重視）
            formatter = logging.Formatter(
                "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
                datefmt="%H:%M:%S",  # 時分秒のみで十分
            )
        else:
            # 本番環境: 基本的なログ形式（後で構造化ログに変更予定）
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        handler.setFormatter(formatter)

        # ルートロガーに設定
        root_logger.addHandler(handler)
        root_logger.setLevel(getattr(logging, log_level))

        # アプリケーション専用ロガーを返す
        app_logger = logging.getLogger("portfolio_app")

        # 初期化完了ログ
        app_logger.info(
            f"Logging configuration initialized - Environment: {environment}, Level: {log_level}"
        )

        return app_logger
