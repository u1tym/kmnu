from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

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
    
    def list(self, page: int = 1, limit: int = 20) -> List[Tuple[Any, ...]]:
        offset: int = (page - 1) * limit
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, servings, created FROM recipes WHERE deleted = FALSE ORDER BY created DESC LIMIT %s OFFSET %s",
                    (limit, offset)
                )
                return cur.fetchall()
    
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
    
    def search_name(self, keyword: str) -> List[Tuple[Any, ...]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name FROM recipes WHERE name ILIKE %s AND deleted = FALSE ORDER BY created DESC",
                    (f'%{keyword}%',)
                )
                return cur.fetchall()
    
    def search_keyword(self, keyword: str) -> List[Tuple[Any, ...]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name FROM recipes WHERE %s = ANY(keywords) AND deleted = FALSE ORDER BY created DESC",
                    (keyword,)
                )
                return cur.fetchall()
    
    def search_ingredient(self, keyword: str) -> List[Tuple[Any, ...]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT r.id, r.name FROM recipes r JOIN recipe_ingredients i ON r.id = i.recipe_id WHERE i.name ILIKE %s AND r.deleted = FALSE AND i.deleted = FALSE ORDER BY r.created DESC",
                    (f'%{keyword}%',)
                )
                return cur.fetchall()

rm = RecipeManager()

@app.get("/api/recipes")
def get_recipes(page: int = 1) -> List[Tuple[Any, ...]]:
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
def search_recipes_by_name(keyword: str) -> List[Tuple[Any, ...]]:
    return rm.search_name(keyword)

@app.get("/api/recipes/search/keyword/{keyword}")
def search_recipes_by_keyword(keyword: str) -> List[Tuple[Any, ...]]:
    return rm.search_keyword(keyword)

@app.get("/api/recipes/search/ingredient/{keyword}")
def search_recipes_by_ingredient(keyword: str) -> List[Tuple[Any, ...]]:
    return rm.search_ingredient(keyword)

@app.get("/health")
def health_check() -> Dict[str, Any]:
    return {"status": "ok", "timestamp": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)