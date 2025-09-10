# レシピ管理Webアプリ仕様書 v1.0

## 概要
料理レシピを管理するWebアプリケーション。スマホ・PC対応、写真付きレシピの作成・管理・検索が可能。

## 機能要件

### 1. レシピ管理
- **追加**: 名前、材料、手順、人数分、キーワードを登録
- **表示**: ID指定でレシピ詳細表示（削除フラグ除外）
- **一覧**: 全レシピのID・名前一覧（削除フラグ除外）
- **編集**: 手順・写真の変更可能（「置き換えますか？」ダイアログ）
- **削除**: レシピ・工程・材料・写真の論理削除（「削除しますか？」ダイアログ）
- **検索**: 名前・キーワード・材料で検索（削除フラグ除外）

### 2. データ構造
```json
{
  "1": {
    "name": "レシピ名",
    "ingredients": [
      {"name": "鶏肉", "amount": "200g"},
      {"name": "玉ねぎ", "amount": "1個"}
    ],
    "keywords": ["和食", "簡単", "10分"],
    "steps": [
      {"description": "手順1", "photo": "step1.jpg"},
      {"description": "手順2", "photo": "step2.jpg"}
    ],
    "servings": 2,
    "created": "2024-01-01T12:00:00"
  }
}
```

### 3. ユーザーインターフェース
- Webブラウザベース
- Vue3 + TypeScript
- レスポンシブデザイン（スマホ・タブレット・PC対応）
- 日本語対応
- タッチ操作対応

### 4. データ永続化
- PostgreSQLデータベース
- 4テーブル: recipes, recipe_ingredients, recipe_steps, photos
- 論理削除方式、自動コミット

### 5. データベーススキーマ
```sql
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    keywords TEXT[],
    servings INTEGER DEFAULT 1,
    deleted BOOLEAN DEFAULT FALSE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    amount VARCHAR(100) NOT NULL,
    deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE recipe_steps (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    description TEXT,
    photo_id INTEGER REFERENCES photos(id),
    deleted BOOLEAN DEFAULT FALSE,
    UNIQUE(recipe_id, step_order)
);

CREATE TABLE photos (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    image_data BYTEA NOT NULL,
    deleted BOOLEAN DEFAULT FALSE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6. API仕様
```
GET    /api/recipes          - レシピ一覧取得
GET    /api/recipes/{id}     - レシピ詳細取得
POST   /api/recipes          - レシピ作成
PUT    /api/recipes/{id}     - レシピ更新
DELETE /api/recipes/{id}     - レシピ論理削除
DELETE /api/recipes/{id}/ingredients/{ingredient_id} - 材料論理削除
DELETE /api/recipes/{id}/steps/{step_id}             - 工程論理削除
POST   /api/photos           - 写真アップロード
GET    /api/photos/{id}      - 写真取得
DELETE /api/photos/{id}      - 写真論理削除
GET    /api/recipes/search/name/{keyword}       - 名前検索
GET    /api/recipes/search/keyword/{keyword}    - キーワード検索
GET    /api/recipes/search/ingredient/{keyword} - 材料検索
```

## 技術スタック

### バックエンド
- FastAPI
- PostgreSQL
- psycopg2
- uvicorn

### フロントエンド
- Vue3
- TypeScript
- Vite

### 7. 写真管理
- **アップロード上限**: 5MB
- **対応形式**: JPG, PNG
- **自動圧縮**: 2MB超過時はJPG形式で圧縮
- **ファイル名**: 連番管理（001.jpg, 002.png...）
- **保存先**: PostgreSQL BYTEA型でDB保存
- **圧縮品質**: JPEG 85%品質
- **メタデータ**: 元ファイル名、サイズ、MIMEタイプを保存

### 8. バリデーション
- **レシピ名**: 1-100文字、**必須**
- **材料名**: 1-50文字、任意
- **分量**: 1-20文字、任意
- **手順説明**: 文字数制限なし、任意
- **人数分**: 1-99人、整数、デフォルト1
- **キーワード**: 1-20文字、最大10個、任意
- **写真**: JPG/PNG、最大5MB、任意、自動圧縮対応

### 8.1. 必須項目
- レシピ名のみ必須
- 材料、工程、手順、写真はすべて任意
- 空のレシピでも作成可能

### 9. エラーハンドリング
- バリデーションエラー: フィールド単位で表示
- ネットワークエラー: リトライ機能付き
- DBエラー: ユーザーフレンドリーメッセージ

### 10. 確認ダイアログ
- **編集時**: 「置き換えますか？」（手順・写真変更時）
- **削除時**: 「削除しますか？」（レシピ・工程・材料・写真）
- ボタン: 「はい」「いいえ」「キャンセル」

### 11. 論理削除仕様
- 物理削除は行わず、deletedフラグをTRUEに設定
- 一覧・検索時はdeleted=FALSEのみ表示
- 削除日時はupdatedフィールドで管理

### 12. パフォーマンス
- ページ読み込み: 2秒以内
- 検索結果: 1秒以内
- 一覧表示: ページネーション（20件/ページ）
- 写真表示: キャッシュ機能付き

## 非機能要件

### コード品質
- 最小限のコード実装
- TypeScriptで型安全性確保
- REST API設計原則遵守

### セキュリティ
- XSS対策（エスケープ処理）
- SQLインジェクション対策（プリペアドステートメント）
- CORS対応
- ファイルアップロード制限

### 保守性
- 論理削除でデータ保護
- エラーハンドリング充実
- バックアップ・復旧可能

---

## 実装優先度
1. **Phase 1**: 基本機能（CRUD、検索）
2. **Phase 2**: 写真機能（アップロード、圧縮）
3. **Phase 3**: UI/UX改善（レスポンシブ、ダイアログ）