from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from PIL import Image
import io

app = FastAPI(title="Recipe Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Ingredient(BaseModel):
    name: str
    amount: str
    
    @validator('name')
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 50:
            raise ValueError('材料名は1-50文字で入力してください')
        return v
    
    @validator('amount')
    def validate_amount(cls, v: str) -> str:
        if not v or len(v) > 20:
            raise ValueError('分量は1-20文字で入力してください')
        return v

class Step(BaseModel):
    description: Optional[str] = None
    photo_id: Optional[int] = None

class Recipe(BaseModel):
    name: str
    ingredients: List[Ingredient] = []
    keywords: List[str] = []
    steps: List[Step] = []
    servings: int = 1
    
    @validator('name')
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 100:
            raise ValueError('レシピ名は1-100文字で入力してください')
        return v
    
    @validator('servings')
    def validate_servings(cls, v: int) -> int:
        if v < 1 or v > 99:
            raise ValueError('人数分は1-99で入力してください')
        return v
    
    @validator('keywords')
    def validate_keywords(cls, v: List[str]) -> List[str]:
        if len(v) > 10:
            raise ValueError('キーワードは最大10個まで')
        for keyword in v:
            if len(keyword) > 20:
                raise ValueError('キーワードは1-20文字で入力してください')
        return v

class PhotoManager:
    def __init__(self, db_config: Dict[str, str]) -> None:
        self.config = db_config
    
    def _connect(self) -> psycopg2.extensions.connection:
        return psycopg2.connect(**self.config)
    
    def _compress_image(self, image_data: bytes, max_size: int = 2 * 1024 * 1024) -> Tuple[bytes, str]:
        """画像を圧縮（2MB超過時）"""
        if len(image_data) <= max_size:
            # 元の形式を判定
            img = Image.open(io.BytesIO(image_data))
            return image_data, img.format.lower()
        
        # 圧縮処理
        img = Image.open(io.BytesIO(image_data))
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        return output.getvalue(), 'jpeg'
    
    def add_photo(self, file_data: bytes, original_name: str, content_type: str) -> int:
        compressed_data, format_type = self._compress_image(file_data)
        
        with self._connect() as conn:
            with conn.cursor() as cur:
                # 連番ファイル名生成
                cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM photos")
                next_id = cur.fetchone()[0]
                filename = f"{next_id:03d}.{format_type}"
                
                cur.execute(
                    "INSERT INTO photos (filename, original_name, content_type, file_size, image_data) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (filename, original_name, f"image/{format_type}", len(compressed_data), compressed_data)
                )
                return cur.fetchone()[0]
    
    def get_photo(self, photo_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM photos WHERE id = %s AND deleted = FALSE",
                    (photo_id,)
                )
                return cur.fetchone()
    
    def delete_photo(self, photo_id: int) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE photos SET deleted = TRUE WHERE id = %s AND deleted = FALSE",
                    (photo_id,)
                )
                return cur.rowcount > 0

class RecipeManager:
    def __init__(self) -> None:
        self.config: Dict[str, str] = {
            'host': 'localhost',
            'database': 'recipes_db',
            'user': 'postgres',
            'password': 'password'
        }
    
    def _connect(self) -> psycopg2.extensions.connection:
        return psycopg2.connect(**self.config)
    
    def add(self, recipe: Recipe) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO recipes (name, keywords, servings) VALUES (%s, %s, %s) RETURNING id",
                    (recipe.name, recipe.keywords, recipe.servings)
                )
                recipe_id: int = cur.fetchone()[0]
                
                for ingredient in recipe.ingredients:
                    cur.execute(
                        "INSERT INTO recipe_ingredients (recipe_id, name, amount) VALUES (%s, %s, %s)",
                        (recipe_id, ingredient.name, ingredient.amount)
                    )
                
                for i, step in enumerate(recipe.steps, 1):
                    cur.execute(
                        "INSERT INTO recipe_steps (recipe_id, step_order, description, photo_id) VALUES (%s, %s, %s, %s)",
                        (recipe_id, i, step.description, step.photo_id)
                    )
                return recipe_id
    
    def get(self, id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM recipes WHERE id = %s AND deleted = FALSE", (id,))
                recipe: Optional[Dict[str, Any]] = cur.fetchone()
                if recipe:
                    cur.execute(
                        "SELECT name, amount FROM recipe_ingredients WHERE recipe_id = %s AND deleted = FALSE",
                        (id,)
                    )
                    recipe['ingredients'] = cur.fetchall()
                    cur.execute(
                        "SELECT description, photo_id FROM recipe_steps WHERE recipe_id = %s AND deleted = FALSE ORDER BY step_order",
                        (id,)
                    )
                    recipe['steps'] = cur.fetchall()
                return recipe
    
    def list(self, page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        offset: int = (page - 1) * limit
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, name, servings, created FROM recipes WHERE deleted = FALSE ORDER BY created DESC LIMIT %s OFFSET %s",
                    (limit, offset)
                )
                recipes = cur.fetchall()
                # 日付をISO形式の文字列に変換
                result = []
                for recipe in recipes:
                    recipe_dict = dict(recipe)
                    if recipe_dict['created']:
                        recipe_dict['created'] = recipe_dict['created'].isoformat()
                    result.append(recipe_dict)
                print(f"List API returning: {result}")
                return result
    
    def update(self, id: int, recipe: Recipe) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE recipes SET name = %s, keywords = %s, servings = %s, updated = %s WHERE id = %s AND deleted = FALSE",
                    (recipe.name, recipe.keywords, recipe.servings, datetime.now(), id)
                )
                return cur.rowcount > 0
    
    def delete(self, id: int) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE recipes SET deleted = TRUE, updated = %s WHERE id = %s AND deleted = FALSE",
                    (datetime.now(), id)
                )
                return cur.rowcount > 0
    
    def search_name(self, keyword: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, name, created FROM recipes WHERE name ILIKE %s AND deleted = FALSE ORDER BY created DESC",
                    (f'%{keyword}%',)
                )
                recipes = cur.fetchall()
                for recipe in recipes:
                    if recipe['created']:
                        recipe['created'] = recipe['created'].isoformat()
                return recipes
    
    def search_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, name, created FROM recipes WHERE %s = ANY(keywords) AND deleted = FALSE ORDER BY created DESC",
                    (keyword,)
                )
                recipes = cur.fetchall()
                for recipe in recipes:
                    if recipe['created']:
                        recipe['created'] = recipe['created'].isoformat()
                return recipes
    
    def search_ingredient(self, keyword: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT r.id, r.name, r.servings, r.created FROM recipes r WHERE r.id IN (SELECT DISTINCT recipe_id FROM recipe_ingredients WHERE name ILIKE %s AND deleted = FALSE) AND r.deleted = FALSE ORDER BY r.created DESC",
                    (f'%{keyword}%',)
                )
                recipes = cur.fetchall()
                print(f"Ingredient search for '{keyword}': {recipes}")
                for recipe in recipes:
                    if recipe['created']:
                        recipe['created'] = recipe['created'].isoformat()
                return recipes

rm = RecipeManager()
pm = PhotoManager(rm.config)

@app.get("/api/recipes")
def get_recipes(page: int = 1) -> List[Dict[str, Any]]:
    return rm.list(page)

@app.get("/api/recipes/{recipe_id}")
def get_recipe(recipe_id: int) -> Dict[str, Any]:
    recipe: Optional[Dict[str, Any]] = rm.get(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@app.post("/api/recipes")
def create_recipe(recipe: Recipe) -> Dict[str, Any]:
    try:
        recipe_id: int = rm.add(recipe)
        return {"id": recipe_id, "message": "Recipe created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/recipes/{recipe_id}")
def update_recipe(recipe_id: int, recipe: Recipe) -> Dict[str, str]:
    try:
        if not rm.update(recipe_id, recipe):
            raise HTTPException(status_code=404, detail="Recipe not found")
        return {"message": "Recipe updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/recipes/{recipe_id}")
def delete_recipe(recipe_id: int) -> Dict[str, str]:
    if not rm.delete(recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"message": "Recipe deleted"}

@app.get("/api/recipes/search/name/{keyword}")
def search_recipes_by_name(keyword: str) -> List[Dict[str, Any]]:
    return rm.search_name(keyword)

@app.get("/api/recipes/search/keyword/{keyword}")
def search_recipes_by_keyword(keyword: str) -> List[Dict[str, Any]]:
    return rm.search_keyword(keyword)

@app.get("/api/recipes/search/ingredient/{keyword}")
def search_recipes_by_ingredient(keyword: str) -> List[Dict[str, Any]]:
    return rm.search_ingredient(keyword)

@app.post("/api/photos")
async def upload_photo(file: UploadFile = File(...)) -> Dict[str, Any]:
    # ファイル形式チェック
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="画像ファイルのみアップロード可能です")
    
    if file.content_type not in ['image/jpeg', 'image/png']:
        raise HTTPException(status_code=400, detail="JPEGまたはPNG形式のみ対応しています")
    
    # ファイルサイズチェック（5MB）
    file_data = await file.read()
    if len(file_data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="ファイルサイズは5MB以下にしてください")
    
    try:
        photo_id = pm.add_photo(file_data, file.filename or "unknown", file.content_type)
        return {"id": photo_id, "message": "Photo uploaded"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/photos/{photo_id}")
def get_photo(photo_id: int) -> Response:
    photo = pm.get_photo(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    return Response(
        content=photo['image_data'],
        media_type=photo['content_type']
    )

@app.delete("/api/photos/{photo_id}")
def delete_photo(photo_id: int) -> Dict[str, str]:
    if not pm.delete_photo(photo_id):
        raise HTTPException(status_code=404, detail="Photo not found")
    return {"message": "Photo deleted"}

@app.get("/health")
def health_check() -> Dict[str, Any]:
    return {"status": "ok", "timestamp": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)