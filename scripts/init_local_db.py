#!/usr/bin/env python3
"""
ベスト3投稿アプリ用 DynamoDB初期化とダミーデータ挿入スクリプト
"""

import boto3
import uuid
import hashlib
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import random

# DynamoDB接続設定
DYNAMODB_CONFIG = {
    "endpoint_url": "http://localhost:8000",
    "region_name": "ap-northeast-1",
    "aws_access_key_id": "DUMMYID",
    "aws_secret_access_key": "DUMMYKEY",
}

# テーブル定義
TABLE_SCHEMA = {
    "TableName": "MugenRecoTable",
    "KeySchema": [
        {"AttributeName": "PK", "KeyType": "HASH"},
        {"AttributeName": "SK", "KeyType": "RANGE"},
    ],
    "AttributeDefinitions": [
        {"AttributeName": "PK", "AttributeType": "S"},
        {"AttributeName": "SK", "AttributeType": "S"},
        {"AttributeName": "GSI1_PK", "AttributeType": "S"},
        {"AttributeName": "GSI1_SK", "AttributeType": "S"},
        {"AttributeName": "GSI2_PK", "AttributeType": "S"},
        {"AttributeName": "GSI2_SK", "AttributeType": "S"},
        {"AttributeName": "GSI3_PK", "AttributeType": "S"},
        {"AttributeName": "GSI3_SK", "AttributeType": "S"},
        {"AttributeName": "GSI4_PK", "AttributeType": "S"},
        {"AttributeName": "GSI4_SK", "AttributeType": "S"},
        {"AttributeName": "GSI5_PK", "AttributeType": "S"},
        {"AttributeName": "GSI5_SK", "AttributeType": "S"},
    ],
    "BillingMode": "PAY_PER_REQUEST",
    "GlobalSecondaryIndexes": [
        {
            "IndexName": "GSI_PostList",  # GSI1: 全投稿一覧
            "KeySchema": [
                {"AttributeName": "GSI1_PK", "KeyType": "HASH"},
                {"AttributeName": "GSI1_SK", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},
        },
        {
            "IndexName": "GSI_Category",  # GSI2: カテゴリ別
            "KeySchema": [
                {"AttributeName": "GSI2_PK", "KeyType": "HASH"},
                {"AttributeName": "GSI2_SK", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},
        },
        {
            "IndexName": "GSI_UserPosts",  # GSI3: ユーザー別
            "KeySchema": [
                {"AttributeName": "GSI3_PK", "KeyType": "HASH"},
                {"AttributeName": "GSI3_SK", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},
        },
        {
            "IndexName": "GSI_Username",  # GSI4: ユーザー名検索
            "KeySchema": [
                {"AttributeName": "GSI4_PK", "KeyType": "HASH"},
                {"AttributeName": "GSI4_SK", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},
        },
        {
            "IndexName": "GSI_UserLikes",  # GSI5: ユーザーのいいね
            "KeySchema": [
                {"AttributeName": "GSI5_PK", "KeyType": "HASH"},
                {"AttributeName": "GSI5_SK", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},
        },
    ],
}

# ダミーユーザーデータ
SAMPLE_USERS = [
    {"username": "alice_food", "password": "password123"},
    {"username": "bob_tech", "password": "password456"},
    {"username": "charlie_travel", "password": "password789"},
    {"username": "diana_books", "password": "passwordabc"},
    {"username": "eve_movies", "password": "passworddef"},
]

# カテゴリとベスト3投稿のサンプルデータ
SAMPLE_POSTS = [
    {
        "username": "alice_food",
        "category": "BOOK",
        "title": "人生を変えた自己啓発書ベスト3",
        "description": "実際に読んで価値観や行動が変わった、おすすめの自己啓発書を紹介します。",
        "recommend1": "7つの習慣 - 効果的な人格形成の原則",
        "recommend2": "思考は現実化する - 成功哲学の古典",
        "recommend3": "エッセンシャル思考 - 最少の時間で最大の成果",
    },
    {
        "username": "bob_tech",
        "category": "HEALTH",
        "title": "毎日続けられる健康習慣ベスト3",
        "description": "忙しい日常でも継続しやすく、効果を実感できる健康習慣をまとめました。",
        "recommend1": "朝の10分ウォーキング - 代謝アップと気分転換",
        "recommend2": "水を1日2リットル - デトックス効果抜群",
        "recommend3": "22時就寝 - 良質な睡眠で疲労回復",
    },
    {
        "username": "charlie_travel",
        "category": "SWEETS",
        "title": "東京で絶対食べたいスイーツベスト3",
        "description": "インスタ映えも味も最高！都内で話題のスイーツ店を厳選しました。",
        "recommend1": "ルタオ チーズケーキ - 濃厚でなめらかな食感",
        "recommend2": "とろけるプリン専門店 - 口の中でとろける極上プリン",
        "recommend3": "高級いちご大福 - 季節限定の贅沢な味わい",
    },
    {
        "username": "eve_movies",
        "category": "APP",
        "title": "生活が便利になるアプリベスト3",
        "description": "日常生活で本当に役立つ、手放せなくなったアプリを厳選して紹介します。",
        "recommend1": "Google マップ - 最強のナビゲーションアプリ",
        "recommend2": "PayPay - キャッシュレス決済の定番",
        "recommend3": "Notion - メモ・タスク管理の万能ツール",
    },
    {
        "username": "alice_food",
        "category": "GAME",
        "title": "友達と盛り上がるゲームベスト3",
        "description": "オンラインでもオフラインでも楽しめる、みんなでワイワイできるゲーム！",
        "recommend1": "Among Us - 推理と騙し合いが楽しい",
        "recommend2": "マリオカート - 定番の対戦レースゲーム",
        "recommend3": "Apex Legends - チームワークが重要なバトロワ",
    },
    {
        "username": "bob_tech",
        "category": "COMIC",
        "title": "一気読み必至の名作マンガベスト3",
        "description": "読み始めたら止まらない！徹夜してでも読みたくなる傑作マンガです。",
        "recommend1": "鬼滅の刃 - 感動的なストーリーと美しい作画",
        "recommend2": "ワンピース - 冒険とロマンの王道少年マンガ",
        "recommend3": "進撃の巨人 - 予想不可能な展開にハラハラドキドキ",
    },
    {
        "username": "charlie_travel",
        "category": "FOOD",
        "title": "東京の絶品ラーメン店ベスト3",
        "description": "都内で食べ歩いた中から、本当に美味しいラーメン店を厳選しました。",
        "recommend1": "一蘭 渋谷店 - 豚骨スープの濃厚さが絶品",
        "recommend2": "ラーメン二郎 三田本店 - ボリューム満点で学生に人気",
        "recommend3": "麺屋 サマー太陽 - あっさり醤油で女性にもおすすめ",
    },
    {
        "username": "diana_books",
        "category": "ALCOHOL",
        "title": "家飲みにおすすめの日本酒ベスト3",
        "description": "日本酒初心者でも飲みやすく、コンビニでも買える美味しい銘柄を紹介。",
        "recommend1": "獺祭 純米大吟醸 - フルーティーで飲みやすい",
        "recommend2": "久保田 千寿 - すっきりとした辛口",
        "recommend3": "八海山 特別本醸造 - バランスの取れた定番酒",
    },
    {
        "username": "eve_movies",
        "category": "TRAVEL",
        "title": "日本の絶景温泉地ベスト3",
        "description": "一度は訪れたい、景色も温泉も最高の癒しスポットを厳選しました。",
        "recommend1": "草津温泉 - 湯畑の景色と良質な湯",
        "recommend2": "箱根温泉 - 富士山を望む絶景露天風呂",
        "recommend3": "由布院温泉 - 大分の自然に囲まれた静寂の湯",
    },
    {
        "username": "alice_food",
        "category": "MUSIC",
        "title": "作業BGMにぴったりな音楽ベスト3",
        "description": "集中力がアップする！リラックスしながら作業できる音楽を紹介します。",
        "recommend1": "Lo-fi Hip Hop - 心地よいビートでリラックス",
        "recommend2": "クラシック音楽 - 脳の活性化に効果的",
        "recommend3": "自然音 (雨音、波音) - ストレス解消にも最適",
    },
    {
        "username": "bob_tech",
        "category": "ANIME",
        "title": "大人が見ても面白いアニメベスト3",
        "description": "子供だけでなく大人も楽しめる、深いストーリーのアニメ作品です。",
        "recommend1": "君の名は。 - 美しい映像と感動的なストーリー",
        "recommend2": "千と千尋の神隠し - ジブリの名作ファンタジー",
        "recommend3": "アニメ映画 君の膵臓をたべたい - 涙なしには見られない青春物語",
    },
    {
        "username": "charlie_travel",
        "category": "MOVIE",
        "title": "心に残る感動映画ベスト3",
        "description": "何度見ても泣いてしまう、心に響く感動的な映画をセレクトしました。",
        "recommend1": "タイタニック - 永遠の愛を描いた名作",
        "recommend2": "ライフ・イズ・ビューティフル - 父と子の愛に涙",
        "recommend3": "おくりびと - 日本の美しい人間ドラマ",
    },
]


def get_dynamodb_client():
    """DynamoDB クライアントを取得"""
    return boto3.client("dynamodb", **DYNAMODB_CONFIG)


def get_dynamodb_resource():
    """DynamoDB リソースを取得"""
    return boto3.resource("dynamodb", **DYNAMODB_CONFIG)


def check_dynamodb_connection():
    """DynamoDB Local への接続確認"""
    try:
        client = get_dynamodb_client()
        client.list_tables()
        print("✅ DynamoDB Local接続成功")
        return True
    except Exception as e:
        print(f"❌ DynamoDB Local接続失敗: {e}")
        print("💡 docker-compose up -d を実行してDynamoDB Localを起動してください")
        return False


def create_table():
    """テーブル作成"""
    dynamodb = get_dynamodb_resource()

    try:
        table = dynamodb.create_table(**TABLE_SCHEMA)
        print(f"📊 テーブル '{TABLE_SCHEMA['TableName']}' を作成中...")
        table.wait_until_exists()
        print(f"✅ テーブル '{TABLE_SCHEMA['TableName']}' 作成完了")
        return table
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"⚠️ テーブル '{TABLE_SCHEMA['TableName']}' は既に存在します")
            return dynamodb.Table(TABLE_SCHEMA["TableName"])
        else:
            print(f"❌ テーブル作成エラー: {e}")
            raise


def hash_password(password: str) -> str:
    """
    パスワードハッシュ化（デモ用簡易版）

    注意: 実際のアプリケーションでは以下の理由でbcryptを使用すべき:
    1. SHA256は高速すぎてブルートフォース攻撃に弱い
    2. ソルトが自動で生成されない
    3. レインボーテーブル攻撃に脆弱
    4. 計算コストの調整ができない

    本番では: pip install bcrypt && import bcrypt
    bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    """
    return hashlib.sha256(password.encode()).hexdigest()


def create_sample_users():
    """サンプルユーザー作成"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(TABLE_SCHEMA["TableName"])

    print("👤 サンプルユーザーを作成中...")

    users_created = []
    for user_data in SAMPLE_USERS:
        try:
            user_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            username = user_data["username"]
            password_hash = hash_password(user_data["password"])

            item = {
                "PK": f"USER#{user_id}",
                "SK": "META",
                "username": username,
                "password": password_hash,
                "created_at": now,
                # GSI4: username検索用
                "GSI4_PK": f"USERNAME#{username}",
                "GSI4_SK": "PROFILE",
            }

            table.put_item(Item=item)
            users_created.append(username)
            print(f"  ✅ ユーザー作成: {username}")

        except Exception as e:
            print(f"  ❌ ユーザー作成エラー ({username}): {e}")

    print(f"🎉 {len(users_created)}/{len(SAMPLE_USERS)} 件のユーザー作成完了")
    return users_created


def create_sample_posts():
    """サンプル投稿作成"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(TABLE_SCHEMA["TableName"])

    print("📝 サンプル投稿を作成中...")

    posts_created = []
    base_time = datetime.utcnow()

    for i, post_data in enumerate(SAMPLE_POSTS):
        try:
            post_id = str(uuid.uuid4())
            # 時間を少しずつずらして作成
            # 例: i=0: 現在時刻, i=1: 2時間10分前, i=2: 4時間20分前...
            created_time = base_time - timedelta(hours=i * 2, minutes=i * 10)
            now = created_time.isoformat()

            username = post_data["username"]

            item = {
                "PK": f"POST#{post_id}",
                "SK": "META",
                "user_id": f"USER#{username}",
                "category": post_data["category"],
                "title": post_data["title"],
                "description": post_data["description"],
                "recommend1": post_data["recommend1"],
                "recommend2": post_data["recommend2"],
                "recommend3": post_data["recommend3"],
                "created_at": now,
                "updated_at": now,
                # GSI1: 全投稿一覧
                "GSI1_PK": "POST#ALL",
                "GSI1_SK": f"{now}#{post_id}",
                # GSI2: カテゴリ別
                "GSI2_PK": f"CATEGORY#{post_data['category']}",
                "GSI2_SK": f"{now}#{post_id}",
                # GSI3: ユーザー別
                "GSI3_PK": f"USER#{username}",
                "GSI3_SK": f"{now}#{post_id}",
            }

            table.put_item(Item=item)
            posts_created.append(
                {
                    "post_id": post_id,
                    "username": username,
                    "category": post_data["category"],
                    "title": post_data["title"],
                }
            )
            print(f"  ✅ 投稿作成: {post_data['title']} (@{username})")

        except Exception as e:
            print(f"  ❌ 投稿作成エラー ({post_data['title']}): {e}")

    print(f"🎉 {len(posts_created)}/{len(SAMPLE_POSTS)} 件の投稿作成完了")
    return posts_created


def create_sample_likes(posts_created):
    """サンプルいいね作成"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(TABLE_SCHEMA["TableName"])

    print("❤️ サンプルいいねを作成中...")

    likes_created = 0
    usernames = [user["username"] for user in SAMPLE_USERS]

    for post in posts_created:
        # ランダムに2-4人がいいねする
        num_likes = random.randint(2, 4)
        # usernames全体からnum_likes人をランダムに選択
        # random.sample(population, k) = populationからk個を重複なしで選択
        likers = random.sample(usernames, num_likes)

        for liker in likers:
            # 自分の投稿にはいいねしない
            if liker == post["username"]:
                continue

            try:
                post_id = post["post_id"]
                now = datetime.utcnow().isoformat()

                item = {
                    "PK": f"POST#{post_id}",
                    "SK": f"LIKE#{liker}",
                    "post_id": post_id,
                    "user_id": f"USER#{liker}",
                    "created_at": now,
                    # GSI5: ユーザーがいいねした投稿を効率的に取得
                    "GSI5_PK": f"USER#{liker}",
                    "GSI5_SK": f"{now}#{post_id}",
                }

                table.put_item(
                    Item=item,
                    ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
                )
                likes_created += 1
                print(f"  ✅ いいね: @{liker} → {post['title'][:20]}...")

            except ClientError as e:
                if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                    print(f"  ❌ いいね作成エラー: {e}")
            except Exception as e:
                print(f"  ❌ いいね作成エラー: {e}")

    print(f"🎉 {likes_created} 件のいいね作成完了")


def show_summary():
    """作成されたデータの概要表示"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(TABLE_SCHEMA["TableName"])

    try:
        # 全データ取得
        response = table.scan()
        items = response["Items"]

        # データ分類
        users = [
            item
            for item in items
            if item["SK"] == "META" and item["PK"].startswith("USER#")
        ]
        posts = [
            item
            for item in items
            if item["SK"] == "META" and item["PK"].startswith("POST#")
        ]
        likes = [item for item in items if item["SK"].startswith("LIKE#")]

        print(f"\n📊 作成データ概要")
        print("-" * 60)
        print(f"👤 ユーザー: {len(users)} 件")
        print(f"📝 投稿: {len(posts)} 件")
        print(f"❤️ いいね: {len(likes)} 件")

        if posts:
            print(f"\n📝 投稿一覧:")
            categories = {}
            for post in posts:
                category = post.get("category", "その他")
                if category not in categories:
                    categories[category] = []
                categories[category].append(post)

            for category, category_posts in categories.items():
                print(f"  📂 {category} ({len(category_posts)}件)")
                for post in category_posts[:3]:  # 最大3件表示
                    print(
                        f"    • {post.get('title', 'タイトルなし')} (@{post.get('user_id', '').replace('USER#', '')})"
                    )
                if len(category_posts) > 3:
                    print(f"    ... 他{len(category_posts)-3}件")

        print(f"\n💡 次のステップ:")
        print(f"   1. uvicorn app.main:app --reload --port 8001")
        print(f"   2. http://localhost:8001/docs でAPI確認")
        print(f"   3. NoSQL Workbenchでデータ確認 (localhost:8000)")

    except Exception as e:
        print(f"❌ データ概要取得エラー: {e}")


def reset_table():
    """テーブルリセット"""
    dynamodb = get_dynamodb_resource()

    try:
        table = dynamodb.Table(TABLE_SCHEMA["TableName"])
        table.delete()
        print(f"🗑️ テーブル '{TABLE_SCHEMA['TableName']}' を削除中...")
        table.wait_until_not_exists()
        print("✅ テーブル削除完了")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print("⚠️ テーブルが存在しません")
        else:
            print(f"❌ テーブル削除エラー: {e}")


def delete_table_and_exit():
    """テーブル削除のみ実行して終了"""
    print("🗑️ テーブル削除モード")
    print("=" * 60)

    # 接続確認
    if not check_dynamodb_connection():
        return

    # 危険な操作なので二重確認
    print(f"⚠️ テーブル '{TABLE_SCHEMA['TableName']}' を完全に削除します")
    print("⚠️ この操作は取り消せません！")

    confirm1 = input("本当にテーブルを削除しますか？ (DELETE と入力): ")
    if confirm1 != "DELETE":
        print("❌ テーブル削除をキャンセルしました")
        return

    confirm2 = input("最終確認: 本当に削除しますか？ (yes/no): ")
    if confirm2.lower() != "yes":
        print("❌ テーブル削除をキャンセルしました")
        return

    # テーブル削除実行
    reset_table()
    print("🎉 テーブル削除完了")


def show_help():
    """ヘルプ表示"""
    help_text = """
🚀 ベスト3投稿アプリ DB初期化スクリプト

使用方法:
  python scripts/init_db.py [オプション]

オプション:
  (なし)     テーブル作成とサンプルデータ挿入
  --reset    既存テーブルを削除して再作成
  --delete   テーブルを削除のみ（データ全削除）
  --help     このヘルプを表示

例:
  python scripts/init_db.py           # 初期化実行
  python scripts/init_db.py --reset   # リセット実行
  python scripts/init_db.py --delete  # テーブル削除
  python scripts/init_db.py --help    # ヘルプ表示
"""
    print(help_text)


def main():
    """メイン処理"""
    import sys

    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--help" or arg == "-h":
            show_help()
            return
        elif arg == "--delete":
            delete_table_and_exit()
            return
        elif arg == "--reset":
            print("🚀 ベスト3投稿アプリ DB初期化スクリプト開始（リセットモード）")
            print("=" * 60)

            # 接続確認
            if not check_dynamodb_connection():
                return

            print("\n🔄 リセットモード: 既存データを削除して再作成します")
            confirm = input("本当にテーブルを削除しますか？ (yes/no): ")
            if confirm.lower() != "yes":
                print("❌ リセットをキャンセルしました")
                return
            reset_table()
            print()
        else:
            print(f"❌ 不明なオプション: {arg}")
            print("💡 --help でヘルプを表示")
            return
    else:
        print("🚀 ベスト3投稿アプリ DB初期化スクリプト開始")
        print("=" * 60)

        # 接続確認
        if not check_dynamodb_connection():
            return

    # 通常の初期化処理（--deleteの場合は実行されない）
    # テーブル作成
    create_table()

    # サンプルデータ作成
    create_sample_users()
    posts_created = create_sample_posts()
    create_sample_likes(posts_created)

    # 結果表示
    show_summary()

    print("\n" + "=" * 60)
    print("🎉 ベスト3投稿アプリ初期化完了!")


if __name__ == "__main__":
    main()
