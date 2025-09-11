# レシピ管理Webアプリ v1.0

料理レシピを管理するWebアプリケーション。スマホ・PC対応、写真付きレシピの作成・管理・検索が可能。

## 🚀 セットアップ

### 必要な環境
- Python 3.8+
- PostgreSQL 12+
- Node.js 18+

### 1. データベース準備
```sql
-- PostgreSQLでデータベース作成
CREATE DATABASE recipes_db;
```

```bash
# テーブル作成
psql -d recipes_db -f setup.sql
```

### 2. バックエンド起動
```bash
# 依存関係インストール
pip install -r requirements.txt

# サーバー起動
python main.py
```

### 3. フロントエンド起動
```bash
cd frontend

# 依存関係インストール
npm install

# 開発サーバー起動
npm run dev
```

## 📱 使用方法

1. **レシピ作成**: 「+ 新規レシピ」ボタンから作成
2. **レシピ表示**: カードをクリックして詳細表示
3. **検索**: ヘッダーの検索バーで名前・キーワード・材料検索
4. **削除**: レシピ詳細画面で削除（論理削除）

## 🛠️ 技術スタック

- **バックエンド**: FastAPI + PostgreSQL
- **フロントエンド**: Vue3 + TypeScript + Vite
- **スタイル**: CSS（レスポンシブ対応）

## 📋 実装済み機能

### Phase 1 ✅
- [x] レシピCRUD操作
- [x] 材料・手順管理
- [x] キーワード機能
- [x] 検索機能（名前・キーワード・材料）
- [x] 論理削除
- [x] レスポンシブデザイン
- [x] バリデーション

### Phase 2 ✅
- [x] 写真アップロード
- [x] 画像圧縮（2MB超過時自動圧縮）
- [x] 写真表示
- [x] 連番ファイル名管理
- [x] DB保存（BYTEA型）

### Phase 3 🚧（準備中）
- [ ] 編集機能
- [ ] 確認ダイアログ
- [ ] エラーハンドリング改善

## 🔧 開発

### API仕様
```
GET    /api/recipes          - レシピ一覧
GET    /api/recipes/{id}     - レシピ詳細
POST   /api/recipes          - レシピ作成
PUT    /api/recipes/{id}     - レシピ更新
DELETE /api/recipes/{id}     - レシピ削除
GET    /api/recipes/search/{type}/{keyword} - 検索
```

### データベース構成
- `recipes`: レシピ基本情報
- `recipe_ingredients`: 材料
- `recipe_steps`: 手順
- `photos`: 写真データ（Phase 2で実装）

## 📄 ライセンス

MIT License