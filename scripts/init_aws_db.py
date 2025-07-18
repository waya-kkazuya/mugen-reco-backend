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

# カテゴリとベスト3投稿のサンプルデータ（各カテゴリ10件）
SAMPLE_POSTS = [
    # BOOK カテゴリ（10件）
    {
        "username": "alice_books",
        "category": "BOOK",
        "title": "人生を変えた自己啓発書ベスト3",
        "description": "実際に読んで価値観や行動が変わった、おすすめの自己啓発書を紹介します。",
        "recommend1": "7つの習慣 - 効果的な人格形成の原則",
        "recommend2": "思考は現実化する - 成功哲学の古典",
        "recommend3": "エッセンシャル思考 - 最少の時間で最大の成果",
    },
    {
        "username": "bookworm_jane",
        "category": "BOOK",
        "title": "プログラミング初心者におすすめの技術書ベスト3",
        "description": "未経験からエンジニアになった私が実際に役立った技術書を厳選しました。",
        "recommend1": "リーダブルコード - より良いコードを書くための原則",
        "recommend2": "スッキリわかるJava入門 - 基礎から応用まで",
        "recommend3": "達人プログラマー - 職人から名匠への道",
    },
    {
        "username": "novel_lover",
        "category": "BOOK",
        "title": "今年読んだ感動小説ベスト3",
        "description": "涙なしには読めない、心に響く感動的な小説作品を紹介します。",
        "recommend1": "52ヘルツのクジラたち - 町田そのこ",
        "recommend2": "推し、燃ゆ - 宇佐見りん",
        "recommend3": "流浪の月 - 凪良ゆう",
    },
    {
        "username": "history_fan",
        "category": "BOOK",
        "title": "歴史好きが選ぶ面白い歴史小説ベスト3",
        "description": "史実に基づいた面白い歴史小説で、楽しく歴史を学べる作品です。",
        "recommend1": "竜馬がゆく - 司馬遼太郎",
        "recommend2": "燃えよ剣 - 司馬遼太郎",
        "recommend3": "三国志 - 吉川英治",
    },
    {
        "username": "business_reader",
        "category": "BOOK",
        "title": "キャリアアップに役立つビジネス書ベスト3",
        "description": "仕事で成果を出すために読んでおきたいビジネス書を厳選しました。",
        "recommend1": "FACT FULNESS - ハンス・ロスリング",
        "recommend2": "嫌われる勇気 - 岸見一郎・古賀史健",
        "recommend3": "人を動かす - デール・カーネギー",
    },
    {
        "username": "mystery_fan",
        "category": "BOOK",
        "title": "どんでん返しが凄いミステリー小説ベスト3",
        "description": "最後まで犯人が分からない、トリックが巧妙な推理小説を紹介します。",
        "recommend1": "そして誰もいなくなった - アガサ・クリスティ",
        "recommend2": "容疑者Xの献身 - 東野圭吾",
        "recommend3": "十角館の殺人 - 綾辻行人",
    },
    {
        "username": "scifi_enthusiast",
        "category": "BOOK",
        "title": "読み応え抜群のSF小説ベスト3",
        "description": "想像力をかき立てる壮大なスケールのSF作品を厳選しました。",
        "recommend1": "星を継ぐもの - ジェイムズ・P・ホーガン",
        "recommend2": "ファウンデーション - アイザック・アシモフ",
        "recommend3": "ソラリス - スタニスワフ・レム",
    },
    {
        "username": "essay_lover",
        "category": "BOOK",
        "title": "心がほっこりする癒し系エッセイベスト3",
        "description": "疲れた心に優しく寄り添ってくれる、読後感の良いエッセイ集です。",
        "recommend1": "ツナグ - 辻村深月",
        "recommend2": "コーヒーが冷めないうちに - 川口俊和",
        "recommend3": "君の膵臓をたべたい - 住野よる",
    },
    {
        "username": "classic_reader",
        "category": "BOOK",
        "title": "大学生におすすめの名著ベスト3",
        "description": "教養として読んでおきたい、時代を超えて愛される古典作品です。",
        "recommend1": "こころ - 夏目漱石",
        "recommend2": "人間失格 - 太宰治",
        "recommend3": "羅生門 - 芥川龍之介",
    },
    {
        "username": "kids_books",
        "category": "BOOK",
        "title": "子供と一緒に読みたい絵本ベスト3",
        "description": "親子で楽しめる、心温まる絵本を厳選しました。読み聞かせにもぴったり。",
        "recommend1": "100万回生きたねこ - 佐野洋子",
        "recommend2": "からすのパンやさん - かこさとし",
        "recommend3": "ぐりとぐら - 中川李枝子",
    },
    # HEALTH カテゴリ（10件）
    {
        "username": "fitness_guru",
        "category": "HEALTH",
        "title": "毎日続けられる健康習慣ベスト3",
        "description": "忙しい日常でも継続しやすく、効果を実感できる健康習慣をまとめました。",
        "recommend1": "朝の10分ウォーキング - 代謝アップと気分転換",
        "recommend2": "水を1日2リットル - デトックス効果抜群",
        "recommend3": "22時就寝 - 良質な睡眠で疲労回復",
    },
    {
        "username": "yoga_master",
        "category": "HEALTH",
        "title": "在宅ワーカーのための運動習慣ベスト3",
        "description": "デスクワークの疲れを解消し、運動不足を解決する簡単エクササイズです。",
        "recommend1": "肩甲骨ストレッチ - 肩こり解消に効果的",
        "recommend2": "スクワット10回 - 下半身の筋力維持",
        "recommend3": "深呼吸瞑想5分 - ストレス軽減とリフレッシュ",
    },
    {
        "username": "nutrition_pro",
        "category": "HEALTH",
        "title": "免疫力アップの食材ベスト3",
        "description": "風邪をひきにくくなる、免疫力を高める効果的な食材を紹介します。",
        "recommend1": "にんにく - 抗菌・抗ウイルス作用",
        "recommend2": "ヨーグルト - 腸内環境を整える",
        "recommend3": "緑茶 - カテキンで免疫力向上",
    },
    {
        "username": "sleep_specialist",
        "category": "HEALTH",
        "title": "質の良い睡眠のための習慣ベスト3",
        "description": "ぐっすり眠れて朝スッキリ目覚めるための、科学的根拠のある方法です。",
        "recommend1": "寝る前1時間はスマホを見ない - ブルーライト対策",
        "recommend2": "室温を18-22度に保つ - 理想的な睡眠環境",
        "recommend3": "就寝3時間前に夕食を済ませる - 消化による睡眠阻害を防ぐ",
    },
    {
        "username": "mental_health",
        "category": "HEALTH",
        "title": "ストレス解消に効果的な方法ベスト3",
        "description": "心の健康を保つために実践している、科学的に証明されたストレス対策です。",
        "recommend1": "森林浴 - 自然の中で心を落ち着ける",
        "recommend2": "日記を書く - 感情の整理とデトックス",
        "recommend3": "好きな音楽を聴く - リラックス効果で気分転換",
    },
    {
        "username": "diet_coach",
        "category": "HEALTH",
        "title": "無理なく続けられるダイエット方法ベスト3",
        "description": "リバウンドしない、健康的で継続可能なダイエット法を実体験から紹介。",
        "recommend1": "食事の最初に野菜を食べる - 血糖値の急上昇を防ぐ",
        "recommend2": "1日8000歩歩く - 無理のない有酸素運動",
        "recommend3": "間食をナッツに変える - 良質な脂質とタンパク質",
    },
    {
        "username": "posture_expert",
        "category": "HEALTH",
        "title": "デスクワーカーの姿勢改善方法ベスト3",
        "description": "腰痛・肩こりを予防し、正しい姿勢を保つための実践的なテクニックです。",
        "recommend1": "1時間に1回立ち上がる - 長時間座りっぱなしを避ける",
        "recommend2": "モニターを目線の高さに調整 - 首への負担軽減",
        "recommend3": "椅子に深く座り背中をつける - 腰椎のカーブを保つ",
    },
    {
        "username": "hydration_tips",
        "category": "HEALTH",
        "title": "水分補給を習慣化するコツベスト3",
        "description": "意識せずに十分な水分を取れるようになる、実践的な方法を紹介します。",
        "recommend1": "起床後にコップ一杯の水 - 1日のスタートに水分補給",
        "recommend2": "デスクに常に水筒を置く - 目に見える場所に置いて意識づけ",
        "recommend3": "アプリで水分摂取量を記録 - ゲーム感覚で楽しく管理",
    },
    {
        "username": "vitamin_guide",
        "category": "HEALTH",
        "title": "現代人に不足しがちな栄養素ベスト3",
        "description": "食生活の偏りで不足しやすい栄養素と、効率的な摂取方法を解説します。",
        "recommend1": "ビタミンD - 太陽光を浴びるか魚類で摂取",
        "recommend2": "食物繊維 - 野菜・きのこ・海藻を意識的に",
        "recommend3": "オメガ3脂肪酸 - 青魚やナッツで良質な脂質を",
    },
    {
        "username": "morning_routine",
        "category": "HEALTH",
        "title": "一日を元気に始める朝習慣ベスト3",
        "description": "朝の時間を有効活用して、一日を活力にあふれた状態でスタートする方法です。",
        "recommend1": "朝日を浴びながら深呼吸 - 体内時計をリセット",
        "recommend2": "軽いストレッチで体をほぐす - 血流促進で目覚めスッキリ",
        "recommend3": "朝食にタンパク質を取り入れる - 筋肉維持と満腹感の持続",
    },
    # SWEETS カテゴリ（10件）
    {
        "username": "sweet_tooth",
        "category": "SWEETS",
        "title": "東京で絶対食べたいスイーツベスト3",
        "description": "インスタ映えも味も最高！都内で話題のスイーツ店を厳選しました。",
        "recommend1": "ルタオ チーズケーキ - 濃厚でなめらかな食感",
        "recommend2": "とろけるプリン専門店 - 口の中でとろける極上プリン",
        "recommend3": "高級いちご大福 - 季節限定の贅沢な味わい",
    },
    {
        "username": "chocolate_lover",
        "category": "SWEETS",
        "title": "チョコレート好きが選ぶ極上スイーツベスト3",
        "description": "チョコレートの深い味わいを堪能できる、本格派スイーツを厳選しました。",
        "recommend1": "ゴディバ トリュフ - なめらかなガナッシュが絶品",
        "recommend2": "ピエール・エルメ マカロン - 上品な甘さとサクッと食感",
        "recommend3": "ショコラティエの生チョコ - 口溶けの良さが格別",
    },
    {
        "username": "cake_master",
        "category": "SWEETS",
        "title": "手作りお菓子初心者でも作れるレシピベスト3",
        "description": "失敗知らずで美味しく作れる、簡単で人気のお菓子レシピを紹介します。",
        "recommend1": "ホットケーキミックスのマフィン - 混ぜて焼くだけ簡単",
        "recommend2": "3つの材料だけガトーショコラ - 材料費も時間も節約",
        "recommend3": "混ぜるだけレアチーズケーキ - オーブン不要で失敗なし",
    },
    {
        "username": "traditional_sweets",
        "category": "SWEETS",
        "title": "京都で味わいたい伝統和菓子ベスト3",
        "description": "老舗の技術が光る、本格的な和菓子の美味しさを堪能できる名店です。",
        "recommend1": "鍵善良房のくずきり - 透明感のある美しさと上品な甘さ",
        "recommend2": "茶寮都路里の抹茶パフェ - 濃厚抹茶と季節のフルーツ",
        "recommend3": "俵屋吉富の雲龍 - 職人技が光る繊細な味わい",
    },
    {
        "username": "ice_cream_fan",
        "category": "SWEETS",
        "title": "夏に食べたい絶品アイスクリームベスト3",
        "description": "暑い日に食べたくなる、濃厚で美味しいアイスクリームを厳選しました。",
        "recommend1": "ハーゲンダッツ バニラ - 王道の美味しさで間違いなし",
        "recommend2": "31アイスクリーム ポッピングシャワー - 楽しい食感がクセになる",
        "recommend3": "地方限定ソフトクリーム - 旅行先でしか味わえない特別感",
    },
    {
        "username": "french_pastry",
        "category": "SWEETS",
        "title": "本格フランス菓子が楽しめる店ベスト3",
        "description": "パリで修行したシェフが作る、本場の味を日本で楽しめる名店です。",
        "recommend1": "パティスリー・サダハル・アオキ - 日仏融合の革新的な味",
        "recommend2": "ピエール・ガニェール - ミシュラン星付きの洗練された味",
        "recommend3": "セドリック・グロレ - フランス伝統の技法を忠実に再現",
    },
    {
        "username": "donut_explorer",
        "category": "SWEETS",
        "title": "今話題のドーナツ専門店ベスト3",
        "description": "従来のドーナツを超えた、新感覚で美味しいドーナツが楽しめる店です。",
        "recommend1": "クリスピー・クリーム・ドーナツ - ふわふわ食感のオリジナルグレーズド",
        "recommend2": "ミスタードーナツ ポン・デ・リング - もちもち食感が大人気",
        "recommend3": "フロレスタ 天然酵母ドーナツ - 体に優しい自然な甘さ",
    },
    {
        "username": "pancake_lover",
        "category": "SWEETS",
        "title": "ふわふわパンケーキの名店ベスト3",
        "description": "SNSでも話題の、雲のようにふわふわなパンケーキが味わえる店です。",
        "recommend1": "グラム カフェ - 3段重ねのボリューム満点パンケーキ",
        "recommend2": "星乃珈琲店 - しっとりとした大人のパンケーキ",
        "recommend3": "Eggs 'n Things - ハワイ発祥のふわふわパンケーキ",
    },
    {
        "username": "convenience_sweets",
        "category": "SWEETS",
        "title": "コンビニスイーツの隠れた名品ベスト3",
        "description": "手軽に買えるのに本格的な味わい、コスパ最高のコンビニスイーツです。",
        "recommend1": "セブンイレブン 濃厚チーズケーキ - 専門店に負けない濃厚さ",
        "recommend2": "ローソン プレミアムロールケーキ - しっとりふわふわ食感",
        "recommend3": "ファミリーマート ダブルクリームサンド - ボリューム満点",
    },
    {
        "username": "seasonal_sweets",
        "category": "SWEETS",
        "title": "季節限定スイーツの楽しみ方ベスト3",
        "description": "その時期にしか味わえない、季節感あふれるスイーツの魅力を紹介します。",
        "recommend1": "春の桜スイーツ - 桜の香りと淡いピンクの美しさ",
        "recommend2": "夏のかき氷専門店 - 天然氷で作る絶品かき氷",
        "recommend3": "秋の栗・芋スイーツ - 自然の甘みを活かした素朴な美味しさ",
    },
    # APP カテゴリ（10件）
    {
        "username": "app_enthusiast",
        "category": "APP",
        "title": "生活が便利になるアプリベスト3",
        "description": "日常生活で本当に役立つ、手放せなくなったアプリを厳選して紹介します。",
        "recommend1": "Google マップ - 最強のナビゲーションアプリ",
        "recommend2": "PayPay - キャッシュレス決済の定番",
        "recommend3": "Notion - メモ・タスク管理の万能ツール",
    },
    {
        "username": "productivity_guru",
        "category": "APP",
        "title": "作業効率が劇的に上がるアプリベスト3",
        "description": "仕事や勉強の生産性を向上させる、実際に使って効果を感じたアプリです。",
        "recommend1": "Todoist - タスク管理とプロジェクト整理",
        "recommend2": "Forest - スマホ依存を防ぐ集中アプリ",
        "recommend3": "RescueTime - 時間の使い方を可視化",
    },
    {
        "username": "photo_editor",
        "category": "APP",
        "title": "写真編集が楽しくなるアプリベスト3",
        "description": "プロ並みの写真加工が簡単にできる、使いやすくて高機能なアプリです。",
        "recommend1": "VSCO - おしゃれなフィルターで雰囲気作り",
        "recommend2": "Snapseed - Google製の本格的な写真編集",
        "recommend3": "Canva - SNS投稿用のデザイン作成",
    },
    {
        "username": "fitness_tracker",
        "category": "APP",
        "title": "健康管理に役立つアプリベスト3",
        "description": "運動や食事の記録で健康的な生活をサポートしてくれるアプリです。",
        "recommend1": "MyFitnessPal - カロリー計算と栄養管理",
        "recommend2": "Nike Training Club - 自宅でできる本格トレーニング",
        "recommend3": "Sleep Cycle - 睡眠の質を分析・改善",
    },
    {
        "username": "music_lover",
        "category": "APP",
        "title": "音楽好きにおすすめのアプリベスト3",
        "description": "音楽をもっと楽しめる、発見や管理に便利なアプリを紹介します。",
        "recommend1": "Spotify - 豊富な楽曲とプレイリスト機能",
        "recommend2": "Shazam - 流れている曲を瞬時に特定",
        "recommend3": "GarageBand - 本格的な音楽制作",
    },
    {
        "username": "language_learner",
        "category": "APP",
        "title": "語学学習が楽しくなるアプリベスト3",
        "description": "ゲーム感覚で続けられる、効果的な言語学習アプリです。",
        "recommend1": "Duolingo - 楽しみながら基礎を身につける",
        "recommend2": "HelloTalk - ネイティブとの言語交換",
        "recommend3": "Anki - 効率的な単語暗記",
    },
    {
        "username": "finance_manager",
        "category": "APP",
        "title": "家計管理が簡単になるアプリベスト3",
        "description": "お金の流れを把握し、貯金を増やすのに役立つ家計簿アプリです。",
        "recommend1": "マネーフォワード ME - 銀行口座と連携で自動記録",
        "recommend2": "Zaim - レシート撮影で簡単入力",
        "recommend3": "家計簿アプリ Dr.Wallet - AI自動仕分けで手間いらず",
    },
    {
        "username": "news_reader",
        "category": "APP",
        "title": "情報収集に最適なニュースアプリベスト3",
        "description": "効率的に情報をキャッチアップできる、使いやすいニュースアプリです。",
        "recommend1": "SmartNews - 最新ニュースを見やすくまとめ",
        "recommend2": "グノシー - 個人の関心に合わせた情報配信",
        "recommend3": "NewsPicks - ビジネス情報と専門家のコメント",
    },
    {
        "username": "travel_planner",
        "category": "APP",
        "title": "旅行がもっと楽しくなるアプリベスト3",
        "description": "旅行の計画から現地での活動まで、旅を充実させるアプリです。",
        "recommend1": "じゃらん - 宿泊予約とクーポンでお得に",
        "recommend2": "Google 翻訳 - 海外旅行の言語の壁を解決",
        "recommend3": "TripAdvisor - 観光地の口コミとレビュー",
    },
    {
        "username": "meditation_guide",
        "category": "APP",
        "title": "心の健康を保つ瞑想アプリベスト3",
        "description": "ストレス解消とメンタルヘルスケアに効果的な瞑想・マインドフルネスアプリです。",
        "recommend1": "Headspace - ガイド付き瞑想で初心者も安心",
        "recommend2": "Calm - 睡眠改善と不安解消",
        "recommend3": "Insight Timer - 世界中の瞑想音源が無料",
    },
    # 他のカテゴリも同様に10件ずつ続きます...
    # GAME カテゴリ（10件）
    {
        "username": "gamer_alex",
        "category": "GAME",
        "title": "友達と盛り上がるゲームベスト3",
        "description": "オンラインでもオフラインでも楽しめる、みんなでワイワイできるゲーム！",
        "recommend1": "Among Us - 推理と騙し合いが楽しい",
        "recommend2": "マリオカート - 定番の対戦レースゲーム",
        "recommend3": "Apex Legends - チームワークが重要なバトロワ",
    },
    {
        "username": "puzzle_master",
        "category": "GAME",
        "title": "頭を使う面白いパズルゲームベスト3",
        "description": "時間を忘れて夢中になれる、知的好奇心を刺激するパズルゲームです。",
        "recommend1": "Monument Valley - 美しいアートワークの幾何学パズル",
        "recommend2": "テトリス99 - 古典的だが奥深いブロックパズル",
        "recommend3": "Portal 2 - 3D空間を使った革新的なパズル",
    },
    {
        "username": "rpg_fanatic",
        "category": "GAME",
        "title": "ストーリーが秀逸なRPGベスト3",
        "description": "感動的な物語と魅力的なキャラクターで、心に残る体験ができるRPGです。",
        "recommend1": "ファイナルファンタジーVII - 名作中の名作JRPG",
        "recommend2": "ペルソナ5 - 現代社会を描いた大人のRPG",
        "recommend3": "ニーア:オートマタ - 哲学的テーマの深いストーリー",
    },
    {
        "username": "indie_gamer",
        "category": "GAME",
        "title": "隠れた名作インディーゲームベスト3",
        "description": "大手では作れない独創性に富んだ、アイデアが光るインディーゲームです。",
        "recommend1": "Hollow Knight - 美しい手描きアニメーションのメトロイドヴァニア",
        "recommend2": "Celeste - 精神的な成長を描いた感動的なプラットフォーマー",
        "recommend3": "Undertale - プレイヤーの選択が結末を変える革新的RPG",
    },
    {
        "username": "mobile_gamer",
        "category": "GAME",
        "title": "通勤時間に楽しめるスマホゲームベスト3",
        "description": "短時間でも楽しめる、移動中やスキマ時間にぴったりのモバイルゲームです。",
        "recommend1": "Clash Royale - 戦略性の高いリアルタイムバトル",
        "recommend2": "ポケモンGO - 歩きながら楽しめるAR体験",
        "recommend3": "パズル&ドラゴンズ - パズルとRPGの融合",
    },
    {
        "username": "retro_gamer",
        "category": "GAME",
        "title": "今でも色褪せないレトロゲームベスト3",
        "description": "時代を超えて愛される、ゲーム史に名を刻む不朽の名作です。",
        "recommend1": "スーパーマリオブラザーズ3 - アクションゲームの完成形",
        "recommend2": "ゼルダの伝説 時のオカリナ - 3Dアクションアドベンチャーの金字塔",
        "recommend3": "ストリートファイターII - 格闘ゲームブームの火付け役",
    },
    {
        "username": "horror_gamer",
        "category": "GAME",
        "title": "心臓に悪いホラーゲームベスト3",
        "description": "夜中にプレイするのは危険！本気で怖いホラーゲームを厳選しました。",
        "recommend1": "サイレントヒル2 - 心理的恐怖の最高峰",
        "recommend2": "バイオハザード7 - VRで体験する極上の恐怖",
        "recommend3": "Phasmophobia - 友達と一緒に楽しむゴーストハンティング",
    },
    {
        "username": "strategy_fan",
        "category": "GAME",
        "title": "戦略思考が鍛えられるゲームベスト3",
        "description": "頭脳戦が熱い、深い戦略性と長期的思考が要求されるゲームです。",
        "recommend1": "Civilization VI - 文明を発展させる壮大な戦略ゲーム",
        "recommend2": "Chess.com - オンラインで世界中とチェス対戦",
        "recommend3": "Total War: Warhammer III - 大規模戦闘の戦術シミュレーション",
    },
    {
        "username": "fighting_pro",
        "category": "GAME",
        "title": "格闘ゲーム初心者におすすめベスト3",
        "description": "格ゲーに興味があるけど難しそう...という人でも楽しめる入門作品です。",
        "recommend1": "ストリートファイター6 - 親切なチュートリアルで基礎から学べる",
        "recommend2": "大乱闘スマッシュブラザーズ - 直感的な操作で誰でも楽しめる",
        "recommend3": "TEKKEN 7 - 3D格闘ゲームの入門に最適",
    },
    {
        "username": "simulation_lover",
        "category": "GAME",
        "title": "現実逃避にぴったりなシミュレーションゲームベスト3",
        "description": "のんびりとした時間を過ごせる、癒し系シミュレーションゲームです。",
        "recommend1": "あつまれ どうぶつの森 - 無人島生活でスローライフ",
        "recommend2": "Stardew Valley - 農場経営と田舎暮らしの魅力",
        "recommend3": "Cities: Skylines - 理想の街を作り上げる都市建設",
    },
    # COMIC カテゴリ（10件）
    {
        "username": "manga_otaku",
        "category": "COMIC",
        "title": "一気読み必至の名作マンガベスト3",
        "description": "読み始めたら止まらない！徹夜してでも読みたくなる傑作マンガです。",
        "recommend1": "鬼滅の刃 - 感動的なストーリーと美しい作画",
        "recommend2": "ワンピース - 冒険とロマンの王道少年マンガ",
        "recommend3": "進撃の巨人 - 予想不可能な展開にハラハラドキドキ",
    },
    {
        "username": "shoujo_fan",
        "category": "COMIC",
        "title": "胸キュン必至の少女マンガベスト3",
        "description": "恋愛の甘酸っぱさと感動が詰まった、心温まる少女マンガの名作です。",
        "recommend1": "君に届け - 純粋な恋心に心が温まる",
        "recommend2": "のだめカンタービレ - 音楽とロマンスの完璧な融合",
        "recommend3": "花より男子 - 逆ハーレムの金字塔",
    },
    {
        "username": "seinen_reader",
        "category": "COMIC",
        "title": "大人向けの深いマンガベスト3",
        "description": "人生の複雑さや社会問題を描いた、読み応えのある青年マンガです。",
        "recommend1": "MONSTER - 心理サスペンスの最高峰",
        "recommend2": "宇宙兄弟 - 夢を追う大人の成長物語",
        "recommend3": "20世紀少年 - 壮大なスケールのSFサスペンス",
    },
    {
        "username": "comedy_manga",
        "category": "COMIC",
        "title": "笑いが止まらないギャグマンガベスト3",
        "description": "疲れた時に読むと元気が出る、抜群に面白いコメディマンガです。",
        "recommend1": "銀魂 - シリアスとギャグのバランスが絶妙",
        "recommend2": "日常 - 何でもない日常の可笑しさを描く",
        "recommend3": "坂本ですが？ - クールな主人公のシュールなギャグ",
    },
    {
        "username": "sports_manga",
        "category": "COMIC",
        "title": "熱血スポーツマンガベスト3",
        "description": "努力と友情、勝利への執念が胸を熱くする、王道スポーツマンガです。",
        "recommend1": "スラムダンク - バスケマンガの不動の名作",
        "recommend2": "ハイキュー!! - バレーボールの魅力を120%伝える",
        "recommend3": "黒子のバスケ - 超人的な技の応酬が見どころ",
    },
    {
        "username": "horror_manga",
        "category": "COMIC",
        "title": "背筋が凍るホラーマンガベスト3",
        "description": "夜中に読むのは危険！本当に怖くて眠れなくなるホラーマンガです。",
        "recommend1": "うずまき - 伊藤潤二の代表作、螺旋の恐怖",
        "recommend2": "彼岸島 - 吸血鬼との戦いを描くバトルホラー",
        "recommend3": "富江 - 美しさに隠された狂気",
    },
    {
        "username": "fantasy_manga",
        "category": "COMIC",
        "title": "壮大な世界観のファンタジーマンガベスト3",
        "description": "異世界の冒険と魔法に心躍る、スケールの大きなファンタジー作品です。",
        "recommend1": "ベルセルク - ダークファンタジーの金字塔",
        "recommend2": "七つの大罪 - 王道ファンタジーの面白さ",
        "recommend3": "マギ - アラビアンナイトの世界観",
    },
    {
        "username": "slice_of_life",
        "category": "COMIC",
        "title": "日常系癒しマンガベスト3",
        "description": "ほのぼのとした日常を描いた、心が癒される優しいマンガです。",
        "recommend1": "よつばと！ - 子供の純粋さに心温まる",
        "recommend2": "ばらかもん - 書道家と島の人々の交流",
        "recommend3": "ゆるキャン△ - キャンプの楽しさを伝える癒し系",
    },
    {
        "username": "historical_manga",
        "category": "COMIC",
        "title": "歴史が学べる歴史マンガベスト3",
        "description": "史実を基にした面白い歴史マンガで、楽しく歴史を学べます。",
        "recommend1": "キングダム - 中国春秋戦国時代の英雄譚",
        "recommend2": "ヴィンランド・サガ - ヴァイキング時代の壮大な物語",
        "recommend3": "アンゴルモア 元寇合戦記 - 蒙古襲来を描く戦記もの",
    },
    {
        "username": "mystery_manga",
        "category": "COMIC",
        "title": "推理が楽しい謎解きマンガベスト3",
        "description": "読者も一緒に謎解きできる、本格的なミステリーマンガです。",
        "recommend1": "名探偵コナン - 推理マンガの王道",
        "recommend2": "金田一少年の事件簿 - 本格的なトリックが見どころ",
        "recommend3": "LIAR GAME - 心理戦とだまし合いの頭脳戦",
    },
    # FOOD カテゴリ（10件）
    {
        "username": "ramen_hunter",
        "category": "FOOD",
        "title": "東京の絶品ラーメン店ベスト3",
        "description": "都内で食べ歩いた中から、本当に美味しいラーメン店を厳選しました。",
        "recommend1": "一蘭 渋谷店 - 豚骨スープの濃厚さが絶品",
        "recommend2": "ラーメン二郎 三田本店 - ボリューム満点で学生に人気",
        "recommend3": "麺屋 サマー太陽 - あっさり醤油で女性にもおすすめ",
    },
    {
        "username": "sushi_master",
        "category": "FOOD",
        "title": "コスパ最高の回転寿司店ベスト3",
        "description": "安くて美味しい、家族で楽しめる回転寿司チェーンを比較しました。",
        "recommend1": "スシロー - ネタの新鮮さと豊富なメニュー",
        "recommend2": "はま寿司 - 醤油にこだわった老舗の味",
        "recommend3": "くら寿司 - 無添加にこだわった安心品質",
    },
    {
        "username": "yakiniku_lover",
        "category": "FOOD",
        "title": "肉好きが通う焼肉店ベスト3",
        "description": "質の高いお肉を堪能できる、本当に美味しい焼肉店を厳選しました。",
        "recommend1": "叙々苑 - 高級感のある上質な和牛",
        "recommend2": "安楽亭 - コスパの良いファミリー焼肉",
        "recommend3": "牛角 - 若者に人気の食べ放題システム",
    },
    {
        "username": "italian_foodie",
        "category": "FOOD",
        "title": "本格イタリアンが味わえる店ベスト3",
        "description": "イタリアで修行したシェフが作る、本場の味を楽しめるレストランです。",
        "recommend1": "リストランテ・ホンダ - ミシュラン星獲得の名店",
        "recommend2": "サイゼリヤ - 手軽に本格的なイタリアンを",
        "recommend3": "カプリチョーザ - ボリューム満点のパスタが自慢",
    },
    {
        "username": "sweets_baker",
        "category": "FOOD",
        "title": "手作りパンが美味しいベーカリーベスト3",
        "description": "毎朝焼きたてのパンが楽しめる、地元で愛されるパン屋さんです。",
        "recommend1": "ル・プチメック - フランス仕込みの本格クロワッサン",
        "recommend2": "俺のベーカリー&カフェ - 食パンの食感が絶妙",
        "recommend3": "神戸屋 - 老舗の安定した美味しさ",
    },
    {
        "username": "cafe_hopper",
        "category": "FOOD",
        "title": "居心地の良いカフェベスト3",
        "description": "勉強や読書、友人との会話に最適な雰囲気の良いカフェです。",
        "recommend1": "スターバックス - 全国どこでも安定した品質",
        "recommend2": "ドトール - 手頃な価格で気軽に利用",
        "recommend3": "コメダ珈琲店 - 昭和レトロな落ち着く空間",
    },
    {
        "username": "home_cook",
        "category": "FOOD",
        "title": "簡単で美味しい時短料理ベスト3",
        "description": "忙しい平日でも30分以内で作れる、栄養満点の時短レシピです。",
        "recommend1": "鶏もも肉のガーリック炒め - ご飯が進む簡単メイン",
        "recommend2": "豚バラ大根の煮物 - 煮込み時間を短縮したコツあり",
        "recommend3": "海老とブロッコリーの中華炒め - 彩りも栄養も抜群",
    },
    {
        "username": "local_gourmet",
        "category": "FOOD",
        "title": "大阪のB級グルメベスト3",
        "description": "大阪生まれ大阪育ちが選ぶ、地元民に愛される本当に美味しいB級グルメです。",
        "recommend1": "今川焼き（鶴橋風月） - 外はサクサク中はとろとろ",
        "recommend2": "たこ焼き（たこ昌） - 地元で評判の老舗の味",
        "recommend3": "串カツ（だるま） - 大阪名物の元祖串カツ",
    },
    {
        "username": "healthy_eater",
        "category": "FOOD",
        "title": "栄養バランスの良い朝食メニューベスト3",
        "description": "一日を元気に始められる、栄養士おすすめの朝食メニューです。",
        "recommend1": "アボカドトースト＋ゆで卵 - 良質な脂質とタンパク質",
        "recommend2": "オートミール＋フルーツ - 食物繊維とビタミンが豊富",
        "recommend3": "納豆ご飯＋味噌汁 - 日本の伝統的な完璧な朝食",
    },
    {
        "username": "convenience_food",
        "category": "FOOD",
        "title": "一人暮らしにおすすめの冷凍食品ベスト3",
        "description": "一人暮らし歴8年が選ぶ、本当に美味しくて便利な冷凍食品です。",
        "recommend1": "冷凍餃子（味の素） - 手作りに負けない本格的な味",
        "recommend2": "冷凍チャーハン（ニチレイ） - パラパラ食感が自慢",
        "recommend3": "冷凍パスタ（オーマイ） - レンジで簡単本格イタリアン",
    },
    # ALCOHOL カテゴリ（10件）
    {
        "username": "sake_connoisseur",
        "category": "ALCOHOL",
        "title": "家飲みにおすすめの日本酒ベスト3",
        "description": "日本酒初心者でも飲みやすく、コンビニでも買える美味しい銘柄を紹介。",
        "recommend1": "獺祭 純米大吟醸 - フルーティーで飲みやすい",
        "recommend2": "久保田 千寿 - すっきりとした辛口",
        "recommend3": "八海山 特別本醸造 - バランスの取れた定番酒",
    },
    {
        "username": "wine_enthusiast",
        "category": "ALCOHOL",
        "title": "ワイン初心者におすすめの赤ワインベスト3",
        "description": "渋みが少なく飲みやすい、ワイン入門に最適な赤ワインを厳選しました。",
        "recommend1": "シャトー・メルシャン 桔梗ヶ原メルロー - 日本産の上質なワイン",
        "recommend2": "ボージョレ・ヌーボー - フレッシュで軽やかな味わい",
        "recommend3": "カベルネ・ソーヴィニヨン - 果実味豊かで親しみやすい",
    },
    {
        "username": "beer_master",
        "category": "ALCOHOL",
        "title": "暑い夏に飲みたいビールベスト3",
        "description": "キンキンに冷やして飲むと最高に美味しい、夏にぴったりのビールです。",
        "recommend1": "アサヒスーパードライ - キレの良さが夏にぴったり",
        "recommend2": "サッポロ黒ラベル - コクと爽やかさのバランス",
        "recommend3": "キリン一番搾り - 麦の美味しさを感じる上品な味",
    },
    {
        "username": "whiskey_lover",
        "category": "ALCOHOL",
        "title": "ウイスキー初心者向けの銘柄ベスト3",
        "description": "ストレートでも水割りでも美味しい、クセが少なく飲みやすいウイスキーです。",
        "recommend1": "山崎 - 日本を代表するシングルモルト",
        "recommend2": "白州 - 爽やかでスモーキーな風味",
        "recommend3": "響 - ブレンデッドウイスキーの最高峰",
    },
    {
        "username": "cocktail_bartender",
        "category": "ALCOHOL",
        "title": "自宅で作れる簡単カクテルベスト3",
        "description": "特別な道具不要で、家にある材料で作れる美味しいカクテルレシピです。",
        "recommend1": "モスコミュール - ウォッカとジンジャエールで爽やか",
        "recommend2": "カシスオレンジ - 甘くて飲みやすい女性に人気",
        "recommend3": "ハイボール - ウイスキーと炭酸水のシンプルな美味しさ",
    },
    {
        "username": "craft_beer_fan",
        "category": "ALCOHOL",
        "title": "個性豊かなクラフトビールベスト3",
        "description": "大手とは一味違う、こだわりの製法で作られた個性的なクラフトビールです。",
        "recommend1": "よなよなエール - ホップの香りが印象的なペールエール",
        "recommend2": "コエドビール 瑠璃 - さっぱりとした飲み口のピルスナー",
        "recommend3": "銀河高原ビール - 小麦を使った白ビールの先駆け",
    },
    {
        "username": "shochu_expert",
        "category": "ALCOHOL",
        "title": "飲み方色々楽しめる焼酎ベスト3",
        "description": "ロック、水割り、お湯割りと様々な飲み方で楽しめる美味しい焼酎です。",
        "recommend1": "いいちこ - 大分県産の麦焼酎、まろやかな味",
        "recommend2": "黒霧島 - 宮崎県産の芋焼酎、コクのある味わい",
        "recommend3": "鳥飼 - 熊本県産の米焼酎、上品でクリアな味",
    },
    {
        "username": "sparkling_wine",
        "category": "ALCOHOL",
        "title": "お祝いにぴったりなスパークリングワインベスト3",
        "description": "特別な日やパーティーを華やかに彩る、泡立ちの美しいスパークリングワインです。",
        "recommend1": "ドン・ペリニヨン - シャンパンの王様、特別な日に",
        "recommend2": "プロセッコ - イタリア産の軽やかで親しみやすい泡",
        "recommend3": "カヴァ - スペイン産のコスパの良いスパークリング",
    },
    {
        "username": "liqueur_mixer",
        "category": "ALCOHOL",
        "title": "甘くて飲みやすいリキュールベスト3",
        "description": "お酒が苦手な人でも楽しめる、デザート感覚で飲める甘いリキュールです。",
        "recommend1": "ベイリーズ - クリーミーで濃厚なアイリッシュクリーム",
        "recommend2": "アマレット - アーモンドの香りが特徴的なイタリアリキュール",
        "recommend3": "カルーア - コーヒー風味のメキシコ産リキュール",
    },
    {
        "username": "non_alcoholic",
        "category": "ALCOHOL",
        "title": "お酒の代わりに楽しめるノンアルコール飲料ベスト3",
        "description": "アルコールは飲めないけど雰囲気を楽しみたい人におすすめのドリンクです。",
        "recommend1": "オールフリー - ビールの味わいを再現したノンアルコールビール",
        "recommend2": "のんある気分 - 梅酒風味のノンアルコールドリンク",
        "recommend3": "シャメイ - ノンアルコールワインの定番ブランド",
    },
    # TRAVEL カテゴリ（10件）
    {
        "username": "onsen_lover",
        "category": "TRAVEL",
        "title": "日本の絶景温泉地ベスト3",
        "description": "一度は訪れたい、景色も温泉も最高の癒しスポットを厳選しました。",
        "recommend1": "草津温泉 - 湯畑の景色と良質な湯",
        "recommend2": "箱根温泉 - 富士山を望む絶景露天風呂",
        "recommend3": "由布院温泉 - 大分の自然に囲まれた静寂の湯",
    },
    {
        "username": "backpacker_tom",
        "category": "TRAVEL",
        "title": "バックパッカーにおすすめの国ベスト3",
        "description": "低予算でも充実した旅ができる、バックパッカー初心者にも優しい国です。",
        "recommend1": "タイ - 物価が安く親日的、美味しい料理と美しいビーチ",
        "recommend2": "ベトナム - 歴史ある文化と絶品フォー、縦断旅行が人気",
        "recommend3": "インド - 多様な文化と圧倒的なエネルギー、人生観が変わる体験",
    },
    {
        "username": "family_travel",
        "category": "TRAVEL",
        "title": "子連れ旅行におすすめの国内スポットベスト3",
        "description": "子供も大人も楽しめる、ファミリー旅行に最適な観光地を厳選しました。",
        "recommend1": "沖縄 - 美しい海とリゾート気分、子供向け施設も充実",
        "recommend2": "東京ディズニーランド - 夢の国で家族の思い出作り",
        "recommend3": "軽井沢 - 自然豊かで涼しく、アウトレットでショッピングも",
    },
    {
        "username": "gourmet_traveler",
        "category": "TRAVEL",
        "title": "グルメ旅行におすすめの都市ベスト3",
        "description": "その土地でしか味わえない絶品グルメを堪能できる都市を紹介します。",
        "recommend1": "大阪 - たこ焼き、お好み焼き、串カツなどのB級グルメ天国",
        "recommend2": "北海道 - 新鮮な海鮮、ジンギスカン、乳製品の宝庫",
        "recommend3": "京都 - 伝統的な懐石料理と上品な和菓子",
    },
    {
        "username": "nature_photographer",
        "category": "TRAVEL",
        "title": "絶景写真が撮れる国内スポットベスト3",
        "description": "カメラ好きにはたまらない、息をのむような美しい景色が楽しめる場所です。",
        "recommend1": "富士山五合目 - 雲海に浮かぶ富士山の絶景",
        "recommend2": "美瑛の丘 - 北海道のパッチワークのような田園風景",
        "recommend3": "奥入瀬渓流 - 青森の清流と紅葉の美しいコントラスト",
    },
    {
        "username": "culture_explorer",
        "category": "TRAVEL",
        "title": "歴史と文化を感じる海外都市ベスト3",
        "description": "古い歴史と豊かな文化に触れられる、教養を深める旅におすすめの都市です。",
        "recommend1": "ローマ - 古代ローマ遺跡とバチカン市国",
        "recommend2": "パリ - ルーブル美術館と美しい街並み",
        "recommend3": "京都 - 日本の伝統文化と美しい寺社仏閣",
    },
    {
        "username": "beach_vacation",
        "category": "TRAVEL",
        "title": "世界の美しいビーチリゾートベスト3",
        "description": "透明度抜群の海と白い砂浜、一生に一度は訪れたいビーチリゾートです。",
        "recommend1": "モルディブ - エメラルドグリーンの海と水上ヴィラ",
        "recommend2": "ボラボラ島 - タヒチの楽園、山と海の絶景",
        "recommend3": "サントリーニ島 - 白い建物と青い海のコントラスト",
    },
    {
        "username": "mountain_climber",
        "category": "TRAVEL",
        "title": "登山初心者におすすめの山ベスト3",
        "description": "体力に自信がなくても登りやすく、素晴らしい景色が楽しめる山です。",
        "recommend1": "高尾山 - 東京から近く、ケーブルカーでも登れる",
        "recommend2": "筑波山 - 関東平野を一望できる美しい眺望",
        "recommend3": "金時山 - 富士山の絶景を望める箱根の名山",
    },
    {
        "username": "solo_traveler",
        "category": "TRAVEL",
        "title": "一人旅におすすめの国内スポットベスト3",
        "description": "一人でも安心して楽しめる、自分のペースで観光できる場所を厳選しました。",
        "recommend1": "金沢 - 兼六園と古い街並み、美味しい海鮮",
        "recommend2": "鎌倉 - 歴史ある寺社と江ノ電の旅",
        "recommend3": "熱海 - 温泉とレトロな雰囲気の温泉街",
    },
    {
        "username": "luxury_travel",
        "category": "TRAVEL",
        "title": "特別な日に泊まりたい高級リゾートベスト3",
        "description": "記念日や特別な旅行にふさわしい、最高級のホテル・リゾートです。",
        "recommend1": "星のや軽井沢 - 日本のラグジュアリーリゾートの代表格",
        "recommend2": "ザ・リッツ・カールトン日光 - 中禅寺湖畔の絶景リゾート",
        "recommend3": "アマン東京 - 都心にいながら和の心を感じる空間",
    },
    # MUSIC カテゴリ（10件）
    {
        "username": "music_curator",
        "category": "MUSIC",
        "title": "作業BGMにぴったりな音楽ベスト3",
        "description": "集中力がアップする！リラックスしながら作業できる音楽を紹介します。",
        "recommend1": "Lo-fi Hip Hop - 心地よいビートでリラックス",
        "recommend2": "クラシック音楽 - 脳の活性化に効果的",
        "recommend3": "自然音 (雨音、波音) - ストレス解消にも最適",
    },
    {
        "username": "jpop_fan",
        "category": "MUSIC",
        "title": "2024年話題になったJ-POPベスト3",
        "description": "今年最も印象に残った、多くの人に愛されたJ-POPの名曲です。",
        "recommend1": "Ado - 唱 - 圧倒的な歌唱力で話題沸騰",
        "recommend2": "Official髭男dism - Subtitle - 心に響くメロディーライン",
        "recommend3": "YOASOBI - アイドル - アニメタイアップで大ヒット",
    },
    {
        "username": "rock_enthusiast",
        "category": "MUSIC",
        "title": "ロック初心者におすすめのバンドベスト3",
        "description": "ロックの入門に最適な、聴きやすくてカッコいいバンドを厳選しました。",
        "recommend1": "ONE OK ROCK - 国際的に活躍する日本のロックバンド",
        "recommend2": "Queen - 伝説的なイギリスのロックバンド",
        "recommend3": "緑黄色社会 - 親しみやすいメロディーのオルタナティブロック",
    },
    {
        "username": "jazz_lover",
        "category": "MUSIC",
        "title": "ジャズ入門におすすめのアルバムベスト3",
        "description": "ジャズを聴いたことがない人でも楽しめる、名盤中の名盤です。",
        "recommend1": "マイルス・デイビス - Kind of Blue - ジャズの最高傑作",
        "recommend2": "ジョン・コルトレーン - A Love Supreme - スピリチュアルジャズの金字塔",
        "recommend3": "ビル・エヴァンス - Waltz for Debby - 美しいピアノトリオ",
    },
    {
        "username": "electronic_music",
        "category": "MUSIC",
        "title": "EDM初心者におすすめの楽曲ベスト3",
        "description": "エレクトロニックミュージックの魅力を伝える、入門にぴったりな楽曲です。",
        "recommend1": "Avicii - Wake Me Up - メロディックで感動的なEDM",
        "recommend2": "Calvin Harris - Summer - 夏にぴったりな爽快感",
        "recommend3": "Marshmello - Alone - キャッチーで覚えやすいメロディー",
    },
    {
        "username": "indie_music",
        "category": "MUSIC",
        "title": "知る人ぞ知るインディーバンドベスト3",
        "description": "メジャーではないけれど、音楽好きなら知っておきたい素晴らしいバンドです。",
        "recommend1": "Cero - 洗練されたサウンドの東京のバンド",
        "recommend2": "Overhang Party - 実験的で革新的なサウンド",
        "recommend3": "toe - インストゥルメンタルロックの名手",
    },
    {
        "username": "healing_music",
        "category": "MUSIC",
        "title": "心が癒される音楽ベスト3",
        "description": "疲れた心を癒し、リラックスできる穏やかな音楽を集めました。",
        "recommend1": "坂本龍一 - 戦場のメリークリスマス - 美しいピアノの調べ",
        "recommend2": "久石譲 - ジブリ音楽集 - 懐かしくて心温まるメロディー",
        "recommend3": "Max Richter - Sleep - 8時間の睡眠のための音楽",
    },
    {
        "username": "world_music",
        "category": "MUSIC",
        "title": "世界各国の民族音楽ベスト3",
        "description": "異文化の魅力を音楽で感じられる、世界の美しい民族音楽です。",
        "recommend1": "アイルランド民謡 - ケルト音楽の神秘的な美しさ",
        "recommend2": "ボサノヴァ - ブラジルの洗練されたリズム",
        "recommend3": "フラメンコ - スペインの情熱的なギターと歌声",
    },
    {
        "username": "anime_music",
        "category": "MUSIC",
        "title": "アニメソングの名曲ベスト3",
        "description": "アニメの世界観を彩る、心に残る素晴らしいアニメソングです。",
        "recommend1": "宇多田ヒカル - Beautiful World - エヴァンゲリオンの名テーマ",
        "recommend2": "LiSA - 紅蓮華 - 鬼滅の刃の代表的な楽曲",
        "recommend3": "RADWIMPS - 前前前世 - 君の名は。の感動的な挿入歌",
    },
    {
        "username": "classical_guide",
        "category": "MUSIC",
        "title": "クラシック音楽入門におすすめの名曲ベスト3",
        "description": "クラシック初心者でも親しみやすい、誰もが知っている名曲です。",
        "recommend1": "ベートーヴェン - 交響曲第9番「歓喜の歌」",
        "recommend2": "モーツァルト - レクイエム - 神聖で美しい鎮魂曲",
        "recommend3": "ショパン - 夜想曲 - ピアノの詩人が奏でる美しい調べ",
    },
    # ANIME カテゴリ（10件）
    {
        "username": "anime_critic",
        "category": "ANIME",
        "title": "大人が見ても面白いアニメベスト3",
        "description": "子供だけでなく大人も楽しめる、深いストーリーのアニメ作品です。",
        "recommend1": "君の名は。 - 美しい映像と感動的なストーリー",
        "recommend2": "千と千尋の神隠し - ジブリの名作ファンタジー",
        "recommend3": "アニメ映画 君の膵臓をたべたい - 涙なしには見られない青春物語",
    },
    {
        "username": "shounen_anime",
        "category": "ANIME",
        "title": "熱血少年アニメの名作ベスト3",
        "description": "友情・努力・勝利をテーマにした、見ていて熱くなる少年アニメです。",
        "recommend1": "鬼滅の刃 - 美しい作画と感動的なストーリー",
        "recommend2": "僕のヒーローアカデミア - 現代版ヒーロー物語",
        "recommend3": "ハイキュー!! - バレーボールに青春をかける高校生",
    },
    {
        "username": "ghibli_fan",
        "category": "ANIME",
        "title": "スタジオジブリの傑作ベスト3",
        "description": "宮崎駿監督をはじめとするジブリ作品の中から、特に名作を厳選しました。",
        "recommend1": "もののけ姫 - 自然と人間の共存を描いた深いテーマ",
        "recommend2": "魔女の宅急便 - 少女の成長を描いた心温まる物語",
        "recommend3": "天空の城ラピュタ - 冒険とロマンスの王道アニメ",
    },
    {
        "username": "psychological_anime",
        "category": "ANIME",
        "title": "心理戦が面白いアニメベスト3",
        "description": "頭脳戦や心理描写が秀逸な、考えさせられるアニメ作品です。",
        "recommend1": "DEATH NOTE - 頭脳戦の最高峰、善悪の境界線",
        "recommend2": "約束のネバーランド - 子供たちの脱出劇",
        "recommend3": "コードギアス - 戦略と政治が絡む壮大な物語",
    },
    {
        "username": "slice_of_life_anime",
        "category": "ANIME",
        "title": "日常系癒しアニメベスト3",
        "description": "ほのぼのとした日常を描いた、見ていて心が癒されるアニメです。",
        "recommend1": "けいおん! - 軽音部の女子高生たちの日常",
        "recommend2": "ゆるキャン△ - キャンプの魅力を伝える癒し系",
        "recommend3": "たまゆら - 写真を通して描かれる優しい時間",
    },
    {
        "username": "romance_anime",
        "category": "ANIME",
        "title": "胸キュン必至の恋愛アニメベスト3",
        "description": "甘酸っぱい恋愛模様に心がときめく、ロマンチックなアニメです。",
        "recommend1": "君に届け - 純粋な恋心に心が温まる",
        "recommend2": "とらドラ! - 高校生の複雑な恋愛関係",
        "recommend3": "orange - 手紙で過去を変える感動的な物語",
    },
    {
        "username": "fantasy_anime",
        "category": "ANIME",
        "title": "壮大なファンタジーアニメベスト3",
        "description": "異世界の冒険と魔法に心躍る、スケールの大きなファンタジー作品です。",
        "recommend1": "Re:ゼロから始める異世界生活 - 死に戻りの能力を持つ主人公",
        "recommend2": "この素晴らしい世界に祝福を! - コメディ要素満載の異世界もの",
        "recommend3": "オーバーロード - ゲーム世界に閉じ込められた最強プレイヤー",
    },
    {
        "username": "sci_fi_anime",
        "category": "ANIME",
        "title": "SF設定が秀逸なアニメベスト3",
        "description": "科学技術や未来世界を舞台にした、想像力をかき立てるSFアニメです。",
        "recommend1": "攻殻機動隊 - サイバーパンクの金字塔",
        "recommend2": "STEINS;GATE - タイムトラベルを扱った傑作",
        "recommend3": "新世紀エヴァンゲリオン - 社会現象を起こした名作",
    },
    {
        "username": "sports_anime",
        "category": "ANIME",
        "title": "スポーツアニメの名作ベスト3",
        "description": "努力と情熱で勝利を目指す、熱いスポーツアニメを厳選しました。",
        "recommend1": "スラムダンク - バスケアニメの不動の名作",
        "recommend2": "キャプテン翼 - サッカー少年の夢と情熱",
        "recommend3": "あしたのジョー - ボクシングで描かれる男の生き様",
    },
    {
        "username": "mystery_anime",
        "category": "ANIME",
        "title": "推理・ミステリーアニメベスト3",
        "description": "謎解きが楽しく、最後まで犯人が分からないミステリーアニメです。",
        "recommend1": "名探偵コナン - 推理アニメの王道",
        "recommend2": "氷菓 - 日常の小さな謎を解く青春ミステリー",
        "recommend3": "MONSTER - 心理サスペンスの最高峰",
    },
    # MOVIE カテゴリ（10件）
    {
        "username": "movie_buff",
        "category": "MOVIE",
        "title": "心に残る感動映画ベスト3",
        "description": "何度見ても泣いてしまう、心に響く感動的な映画をセレクトしました。",
        "recommend1": "タイタニック - 永遠の愛を描いた名作",
        "recommend2": "ライフ・イズ・ビューティフル - 父と子の愛に涙",
        "recommend3": "おくりびと - 日本の美しい人間ドラマ",
    },
    {
        "username": "action_fan",
        "category": "MOVIE",
        "title": "手に汗握るアクション映画ベスト3",
        "description": "スリリングなアクションシーンで最後まで目が離せない映画です。",
        "recommend1": "マッドマックス 怒りのデス・ロード - 圧巻のカーアクション",
        "recommend2": "ジョン・ウィック - 洗練されたガンアクション",
        "recommend3": "ミッション:インポッシブル - トム・クルーズの命がけスタント",
    },
    {
        "username": "horror_movie",
        "category": "MOVIE",
        "title": "本気で怖いホラー映画ベスト3",
        "description": "夜中に一人で見るのは危険！心臓に悪い本格ホラー映画です。",
        "recommend1": "IT - ピエロの恐怖が忘れられない",
        "recommend2": "エクソシスト - ホラー映画の金字塔",
        "recommend3": "リング - 日本のホラーの代表作",
    },
    {
        "username": "comedy_lover",
        "category": "MOVIE",
        "title": "腹の底から笑えるコメディ映画ベスト3",
        "description": "疲れた時に見ると元気が出る、抱腹絶倒のコメディ映画です。",
        "recommend1": "ハングオーバー! - 記憶をなくした男たちの珍騒動",
        "recommend2": "アンカーマン - アメリカンコメディの傑作",
        "recommend3": "アメリ - フランス映画の心温まるコメディ",
    },
    {
        "username": "sci_fi_movies",
        "category": "MOVIE",
        "title": "想像力をかき立てるSF映画ベスト3",
        "description": "未来の可能性や科学技術の進歩を描いた、壮大なスケールのSF映画です。",
        "recommend1": "ブレードランナー 2049 - ビジュアルが美しいSFの名作",
        "recommend2": "インターステラー - 宇宙と時間を扱った感動的なSF",
        "recommend3": "マトリックス - 現実とは何かを問う革新的作品",
    },
    {
        "username": "animation_fan",
        "category": "MOVIE",
        "title": "大人も楽しめるアニメーション映画ベスト3",
        "description": "子供向けと侮れない、大人が見ても感動する高品質なアニメーション映画です。",
        "recommend1": "トイ・ストーリー - ピクサーアニメの金字塔",
        "recommend2": "アナと雪の女王 - 姉妹の絆を描いたディズニーの名作",
        "recommend3": "ズートピア - 現代社会の問題を巧妙に描いた作品",
    },
    {
        "username": "romance_movies",
        "category": "MOVIE",
        "title": "胸キュン必至のロマンス映画ベスト3",
        "description": "恋愛の甘酸っぱさと美しさを描いた、心がときめくロマンス映画です。",
        "recommend1": "ラ・ラ・ランド - 夢と恋を歌とダンスで描いたミュージカル",
        "recommend2": "ノートブック - 永遠の愛を描いた感動的なラブストーリー",
        "recommend3": "ローマの休日 - オードリー・ヘプバーンの代表作",
    },
    {
        "username": "thriller_fan",
        "category": "MOVIE",
        "title": "最後まで予想がつかないサスペンス映画ベスト3",
        "description": "どんでん返しが凄く、最後まで犯人が分からないスリリングな映画です。",
        "recommend1": "シックス・センス - 衝撃のラストが忘れられない",
        "recommend2": "ユージュアル・サスペクツ - 騙される快感を味わえる傑作",
        "recommend3": "羊たちの沈黙 - ハンニバル・レクターの恐怖",
    },
    {
        "username": "war_movies",
        "category": "MOVIE",
        "title": "戦争の現実を描いた重厚な映画ベスト3",
        "description": "戦争の悲惨さと人間の強さを描いた、見る者に深い印象を残す作品です。",
        "recommend1": "プライベート・ライアン - リアルな戦闘シーンで有名",
        "recommend2": "シンドラーのリスト - ホロコーストを描いた名作",
        "recommend3": "永遠の0 - 日本の戦争映画の傑作",
    },
    {
        "username": "indie_films",
        "category": "MOVIE",
        "title": "知る人ぞ知るインディーズ映画ベスト3",
        "description": "大手スタジオでは作れない独創性に富んだ、芸術性の高い映画です。",
        "recommend1": "ムーンライト - LGBTQをテーマにした感動作",
        "recommend2": "リトル・ミス・サンシャイン - 家族の絆を描いたハートフル・コメディ",
        "recommend3": "500日のサマー - 非線形の構成が印象的な恋愛映画",
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
