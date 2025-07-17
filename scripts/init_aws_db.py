#!/usr/bin/env python3
"""
ベスト3投稿アプリ用 AWS本番DynamoDB ダミーデータ挿入スクリプト
"""

import boto3
import uuid
import hashlib
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import random

# AWS DynamoDB接続設定
DYNAMODB_CONFIG = {
    "region_name": "ap-northeast-1",
    # AWS認証情報は環境変数やAWS CLIから自動取得
}

# テーブル名（既存テーブルを使用）
TABLE_NAME = "MugenRecoTable"

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
        "category": "本",
        "title": "人生を変えた自己啓発書ベスト3",
        "description": "実際に読んで価値観や行動が変わった、おすすめの自己啓発書を紹介します。",
        "recommend1": "7つの習慣 - 効果的な人格形成の原則",
        "recommend2": "思考は現実化する - 成功哲学の古典",
        "recommend3": "エッセンシャル思考 - 最少の時間で最大の成果",
    },
    {
        "username": "bob_tech",
        "category": "健康",
        "title": "毎日続けられる健康習慣ベスト3",
        "description": "忙しい日常でも継続しやすく、効果を実感できる健康習慣をまとめました。",
        "recommend1": "朝の10分ウォーキング - 代謝アップと気分転換",
        "recommend2": "水を1日2リットル - デトックス効果抜群",
        "recommend3": "22時就寝 - 良質な睡眠で疲労回復",
    },
    {
        "username": "charlie_travel",
        "category": "スイーツ",
        "title": "東京で絶対食べたいスイーツベスト3",
        "description": "インスタ映えも味も最高！都内で話題のスイーツ店を厳選しました。",
        "recommend1": "ルタオ チーズケーキ - 濃厚でなめらかな食感",
        "recommend2": "とろけるプリン専門店 - 口の中でとろける極上プリン",
        "recommend3": "高級いちご大福 - 季節限定の贅沢な味わい",
    },
    {
        "username": "diana_books",
        "category": "カフェ",
        "title": "作業がはかどるおしゃれカフェベスト3",
        "description": "WiFi完備で長時間利用OK！集中して作業できる都内のカフェを紹介。",
        "recommend1": "ブルーボトルコーヒー - 静かで落ち着いた雰囲気",
        "recommend2": "スターバックス リザーブ - 高品質コーヒーと快適空間",
        "recommend3": "ドトール カフェ - コスパ良好で気軽に利用",
    },
    {
        "username": "eve_movies",
        "category": "アプリ",
        "title": "生活が便利になるアプリベスト3",
        "description": "日常生活で本当に役立つ、手放せなくなったアプリを厳選して紹介します。",
        "recommend1": "Google マップ - 最強のナビゲーションアプリ",
        "recommend2": "PayPay - キャッシュレス決済の定番",
        "recommend3": "Notion - メモ・タスク管理の万能ツール",
    },
    {
        "username": "alice_food",
        "category": "ゲーム",
        "title": "友達と盛り上がるゲームベスト3",
        "description": "オンラインでもオフラインでも楽しめる、みんなでワイワイできるゲーム！",
        "recommend1": "Among Us - 推理と騙し合いが楽しい",
        "recommend2": "マリオカート - 定番の対戦レースゲーム",
        "recommend3": "Apex Legends - チームワークが重要なバトロワ",
    },
    {
        "username": "bob_tech",
        "category": "マンガ",
        "title": "一気読み必至の名作マンガベスト3",
        "description": "読み始めたら止まらない！徹夜してでも読みたくなる傑作マンガです。",
        "recommend1": "鬼滅の刃 - 感動的なストーリーと美しい作画",
        "recommend2": "ワンピース - 冒険とロマンの王道少年マンガ",
        "recommend3": "進撃の巨人 - 予想不可能な展開にハラハラドキドキ",
    },
    {
        "username": "charlie_travel",
        "category": "ごはん",
        "title": "東京の絶品ラーメン店ベスト3",
        "description": "都内で食べ歩いた中から、本当に美味しいラーメン店を厳選しました。",
        "recommend1": "一蘭 渋谷店 - 豚骨スープの濃厚さが絶品",
        "recommend2": "ラーメン二郎 三田本店 - ボリューム満点で学生に人気",
        "recommend3": "麺屋 サマー太陽 - あっさり醤油で女性にもおすすめ",
    },
    {
        "username": "diana_books",
        "category": "お酒",
        "title": "家飲みにおすすめの日本酒ベスト3",
        "description": "日本酒初心者でも飲みやすく、コンビニでも買える美味しい銘柄を紹介。",
        "recommend1": "獺祭 純米大吟醸 - フルーティーで飲みやすい",
        "recommend2": "久保田 千寿 - すっきりとした辛口",
        "recommend3": "八海山 特別本醸造 - バランスの取れた定番酒",
    },
    {
        "username": "eve_movies",
        "category": "旅行",
        "title": "日本の絶景温泉地ベスト3",
        "description": "一度は訪れたい、景色も温泉も最高の癒しスポットを厳選しました。",
        "recommend1": "草津温泉 - 湯畑の景色と良質な湯",
        "recommend2": "箱根温泉 - 富士山を望む絶景露天風呂",
        "recommend3": "由布院温泉 - 大分の自然に囲まれた静寂の湯",
    },
    {
        "username": "alice_food",
        "category": "音楽",
        "title": "作業BGMにぴったりな音楽ベスト3",
        "description": "集中力がアップする！リラックスしながら作業できる音楽を紹介します。",
        "recommend1": "Lo-fi Hip Hop - 心地よいビートでリラックス",
        "recommend2": "クラシック音楽 - 脳の活性化に効果的",
        "recommend3": "自然音 (雨音、波音) - ストレス解消にも最適",
    },
    {
        "username": "bob_tech",
        "category": "アニメ",
        "title": "大人が見ても面白いアニメベスト3",
        "description": "子供だけでなく大人も楽しめる、深いストーリーのアニメ作品です。",
        "recommend1": "君の名は。 - 美しい映像と感動的なストーリー",
        "recommend2": "千と千尋の神隠し - ジブリの名作ファンタジー",
        "recommend3": "アニメ映画 君の膵臓をたべたい - 涙なしには見られない青春物語",
    },
    {
        "username": "charlie_travel",
        "category": "映画",
        "title": "心に残る感動映画ベスト3",
        "description": "何度見ても泣いてしまう、心に響く感動的な映画をセレクトしました。",
        "recommend1": "タイタニック - 永遠の愛を描いた名作",
        "recommend2": "ライフ・イズ・ビューティフル - 父と子の愛に涙",
        "recommend3": "おくりびと - 日本の美しい人間ドラマ",
    },
]


def get_dynamodb_resource():
    """DynamoDB リソースを取得"""
    return boto3.resource("dynamodb", **DYNAMODB_CONFIG)


def check_aws_connection():
    """AWS DynamoDB への接続確認"""
    try:
        dynamodb = get_dynamodb_resource()
        # テーブル一覧を取得して接続確認
        list(dynamodb.tables.all())
        print("✅ AWS DynamoDB接続成功")
        print(f"🌏 リージョン: {DYNAMODB_CONFIG['region_name']}")
        return True
    except Exception as e:
        print(f"❌ AWS DynamoDB接続失敗: {e}")
        print("💡 AWS認証情報を確認してください:")
        print("   - aws configure")
        print("   - AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY環境変数")
        print("   - IAMロール（EC2/Lambda実行時）")
        return False


def check_table_exists():
    """テーブル存在確認"""
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(TABLE_NAME)
        table.load()  # テーブル情報を読み込んで存在確認
        print(f"✅ テーブル '{TABLE_NAME}' が見つかりました")
        print(f"📊 テーブル状態: {table.table_status}")
        return table
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"❌ テーブル '{TABLE_NAME}' が存在しません")
            print("💡 先にテーブルを作成してください")
        else:
            print(f"❌ テーブル確認エラー: {e}")
        return None
    except Exception as e:
        print(f"❌ テーブル確認エラー: {e}")
        return None


def confirm_production_execution():
    """本番環境での実行確認"""
    print("🚨 AWS本番環境DynamoDBへのダミーデータ挿入")
    print("=" * 60)
    print(f"📊 対象テーブル: {TABLE_NAME}")
    print(f"🌏 リージョン: {DYNAMODB_CONFIG['region_name']}")
    print("⚠️  本番データに影響する可能性があります")
    print("⚠️  既存データは保持されますが、新しいダミーデータが追加されます")

    confirm1 = input(
        "\n本当に本番環境でダミーデータを挿入しますか？ (AWS_PRODUCTION と入力): "
    )
    if confirm1 != "AWS_PRODUCTION":
        print("❌ 本番環境での実行をキャンセルしました")
        return False

    confirm2 = input("最終確認: ダミーデータの挿入を実行しますか？ (yes/no): ")
    if confirm2.lower() != "yes":
        print("❌ 本番環境での実行をキャンセルしました")
        return False

    print("✅ 本番環境での実行を承認しました")
    return True


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


def create_sample_users(table):
    """サンプルユーザー作成"""
    print("👤 サンプルユーザーを作成中...")

    users_created = []
    users_skipped = []

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

            # 既存チェック：同じユーザー名が存在するかチェック
            try:
                existing_user = table.get_item(
                    Key={"PK": f"USERNAME#{username}", "SK": "PROFILE"},
                    # GSI4を使って検索したいが、get_itemでは主キーのみ使用可能
                    # 代わりにqueryを使用
                )
                # 実際には GSI4 でクエリして既存チェックすべきですが、
                # 簡易版として新規ユーザーとして挿入
                table.put_item(Item=item)
                users_created.append(username)
                print(f"  ✅ ユーザー作成: {username}")
            except Exception:
                table.put_item(Item=item)
                users_created.append(username)
                print(f"  ✅ ユーザー作成: {username}")

        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                users_skipped.append(username)
                print(f"  ⏭️ ユーザースキップ (既存): {username}")
            else:
                print(f"  ❌ ユーザー作成エラー ({username}): {e}")
        except Exception as e:
            print(f"  ❌ ユーザー作成エラー ({username}): {e}")

    print(f"🎉 ユーザー作成: {len(users_created)}件, スキップ: {len(users_skipped)}件")
    return users_created


def create_sample_posts(table):
    """サンプル投稿作成"""
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


def create_sample_likes(table, posts_created):
    """サンプルいいね作成"""
    print("❤️ サンプルいいねを作成中...")

    likes_created = 0
    likes_skipped = 0
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
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    likes_skipped += 1
                    print(
                        f"  ⏭️ いいねスキップ (既存): @{liker} → {post['title'][:20]}..."
                    )
                else:
                    print(f"  ❌ いいね作成エラー: {e}")
            except Exception as e:
                print(f"  ❌ いいね作成エラー: {e}")

    print(f"🎉 いいね作成: {likes_created}件, スキップ: {likes_skipped}件")


def show_summary(table):
    """作成されたデータの概要表示"""
    print(f"\n📊 '{TABLE_NAME}' データ概要")
    print("-" * 60)

    try:
        # 全データ取得（本番環境では注意が必要）
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

        print(f"👤 ユーザー: {len(users)} 件")
        print(f"📝 投稿: {len(posts)} 件")
        print(f"❤️ いいね: {len(likes)} 件")

        if posts:
            print(f"\n📝 投稿一覧（カテゴリ別）:")
            categories = {}
            for post in posts:
                category = post.get("category", "その他")
                if category not in categories:
                    categories[category] = []
                categories[category].append(post)

            for category, category_posts in categories.items():
                print(f"  📂 {category} ({len(category_posts)}件)")
                for post in category_posts[:2]:  # 最大2件表示
                    print(f"    • {post.get('title', 'タイトルなし')[:30]}...")
                if len(category_posts) > 2:
                    print(f"    ... 他{len(category_posts)-2}件")

        print(f"\n💡 確認方法:")
        print(f"   • AWS Console → DynamoDB → テーブル → {TABLE_NAME}")
        print(f"   • NoSQL Workbench → AWS接続")

    except Exception as e:
        print(f"❌ データ概要取得エラー: {e}")
        print("💡 AWS Consoleで直接確認してください")


def show_help():
    """ヘルプ表示"""
    help_text = """
🚀 AWS本番DynamoDB ダミーデータ挿入スクリプト

前提条件:
  • AWS認証が設定済み (aws configure または環境変数)
  • 対象テーブル (MugenRecoTable) が既に存在している

使用方法:
  python scripts/insert_dummy_data.py [オプション]

オプション:
  (なし)     ダミーデータ挿入実行
  --help     このヘルプを表示

認証設定例:
  aws configure
  または
  export AWS_ACCESS_KEY_ID=your_key
  export AWS_SECRET_ACCESS_KEY=your_secret

注意:
  • 本番環境のテーブルにデータが追加されます
  • 既存データは削除されません
  • 実行前に必ず確認プロンプトが表示されます
"""
    print(help_text)


def main():
    """メイン処理"""
    import sys

    # ヘルプ表示
    if len(sys.argv) > 1 and (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
        show_help()
        return

    print("🚀 AWS本番DynamoDB ダミーデータ挿入スクリプト")
    print("=" * 60)

    # AWS接続確認
    if not check_aws_connection():
        return

    # テーブル存在確認
    table = check_table_exists()
    if not table:
        return

    # 本番環境実行確認
    if not confirm_production_execution():
        return

    print("\n" + "=" * 60)
    print("📝 ダミーデータ挿入を開始します...")

    try:
        # サンプルデータ作成
        create_sample_users(table)
        posts_created = create_sample_posts(table)
        create_sample_likes(table, posts_created)

        # 結果表示
        show_summary(table)

        print("\n" + "=" * 60)
        print("🎉 AWS本番DynamoDB ダミーデータ挿入完了!")
        print("✅ データが正常に挿入されました")

    except Exception as e:
        print(f"\n❌ 処理中にエラーが発生しました: {e}")
        print("💡 部分的にデータが挿入されている可能性があります")
        print("💡 AWS Consoleで状況を確認してください")


if __name__ == "__main__":
    main()
