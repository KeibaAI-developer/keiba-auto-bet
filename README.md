# keiba-auto-bet

## 概要

`keiba-auto-bet`は、JRA即パットを使用した馬券の自動購入機能を提供するライブラリです。
現在は単勝・複勝に対応しています。
自動購入は締切直前に行われることを想定しているため、当日のレースに対してのみ利用可能です。

## 動作要件

- Python 3.12以上
- Google Chrome
- ChromeDriver（Chromeのバージョンに対応したもの）

## 依存パッケージ

- selenium>=4.0.0
- python-dotenv>=1.0.0

## インストール

```bash
pip install -e /path/to/keiba-auto-bet
```

## 安全性について

本ライブラリは以下の安全機構により、想定外の金額が購入されることを防ぎます：

### 1. 自動入金機能なし

**`keiba-auto-bet`には自動入金機能は一切ありません。** 即パット口座に入金されている金額以上に購入されることは絶対にありません。事前に入金した金額が購入の上限となります。

### 2. 購入金額の制限

`AutoBetConfig`の`max_bet`パラメータにより、一度の実行で購入できる合計金額に上限を設けることができます：

```python
config = AutoBetConfig(
    max_bet=10000,  # 1回の実行で最大10,000円まで
)
```

`max_bet`を超える購入注文を渡すと、実際の購入処理が始まる前に`ValidationError`が発生し、1円も購入されません。

### 3. バリデーション

購入注文は以下の項目について事前にバリデーションされます：
- レース番号（1〜12）
- 馬番（1以上）
- 購入金額（100円単位、100円以上）
- 合計金額（max_bet以下）

不正な値が含まれている場合、購入処理が始まる前に`ValidationError`が発生します。

## セットアップ

即パットの口座に事前に入金しておく必要があります。

### 認証情報の設定

`.env.example`を`.env`にコピーして、実際の認証情報を設定してください：

```bash
cp .env.example .env
```

`.env`ファイルに以下の情報を設定：
- `IPAT_INET_ID`: INET ID
- `IPAT_USER_NUMBER`: 加入者番号
- `IPAT_PASSWORD`: パスワード
- `IPAT_P_ARS`: P-ARS番号

## 使い方

### 基本的な使い方

```python
from keiba_auto_bet import AutoBetter, AutoBetConfig, BetOrder, TicketType

# 購入注文の作成
orders = [
    BetOrder(
        venue="東京",
        race_number=11,
        ticket_type=TicketType.WIN,  # 単勝
        horse_number=3,
        amount=500,
    ),
    BetOrder(
        venue="阪神",
        race_number=12,
        ticket_type=TicketType.SHOW,  # 複勝
        horse_number=7,
        amount=300,
    ),
]

# 設定（任意）
config = AutoBetConfig(
    headless=True,          # ヘッドレスモードで実行
    max_bet=10000,          # 最大合計購入金額（円）- この金額を超える注文は実行前にエラー
)

# 自動購入を実行（認証情報は.envから自動読み込み）
client = AutoBetter(config=config)
result = client.auto_bet(orders)
```

### 認証情報を明示的に指定する場合

```python
from keiba_auto_bet import AutoBetter, IpatCredentials

credentials = IpatCredentials(
    inet_id="your_inet_id",
    user_number="your_user_number",
    password="your_password",
    p_ars="your_p_ars",
)

client = AutoBetter(credentials=credentials, config=config)
result = client.auto_bet(orders)
```

### ChromeDriverのパスを指定する場合

```python
config = AutoBetConfig(
    chrome_driver_path="/usr/local/bin/chromedriver",
)
```

## エラーハンドリング

本ライブラリが送出する例外は全て`KeibaAutoBetError`を基底クラスとしています：

| 例外クラス | 説明 |
|---|---|
| `KeibaAutoBetError` | 基底例外クラス |
| `BrowserError` | Chromeの起動・終了に関するエラー |
| `LoginError` | 即パットへのログインに関するエラー |
| `BetError` | 馬券選択に関するエラー |
| `PurchaseError` | 購入確定に関するエラー |
| `ValidationError` | 入力バリデーションに関するエラー |

```python
from keiba_auto_bet import AutoBetter, KeibaAutoBetError, LoginError

try:
    client = AutoBetter(credentials=credentials)
    client.auto_bet(orders)
except LoginError:
    print("ログインに失敗しました。認証情報を確認してください。")
except KeibaAutoBetError as e:
    print(f"自動購入中にエラーが発生しました: {e}")
```
