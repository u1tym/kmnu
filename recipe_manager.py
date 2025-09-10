import psycopg2
from psycopg2.extras import RealDictCursor

class RecipeManager:
    def __init__(self, db_config=None):
        self.config = db_config or {
            'host': 'localhost',
            'database': 'recipes_db',
            'user': 'postgres',
            'password': 'password'
        }
    
    def _connect(self):
        return psycopg2.connect(**self.config)
    
    def add(self, name, ingredients, steps, servings=1):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO recipes (name, ingredients, servings) VALUES (%s, %s, %s) RETURNING id",
                    (name, ingredients, servings)
                )
                recipe_id = cur.fetchone()[0]
                
                for i, step in enumerate(steps, 1):
                    cur.execute(
                        "INSERT INTO recipe_steps (recipe_id, step_order, description, photo) VALUES (%s, %s, %s, %s)",
                        (recipe_id, i, step['description'], step.get('photo'))
                    )
                return recipe_id
    
    def get(self, id):
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM recipes WHERE id = %s", (id,))
                recipe = cur.fetchone()
                if recipe:
                    cur.execute(
                        "SELECT description, photo FROM recipe_steps WHERE recipe_id = %s ORDER BY step_order",
                        (id,)
                    )
                    recipe['steps'] = cur.fetchall()
                return recipe
    
    def list(self):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name FROM recipes ORDER BY id")
                return cur.fetchall()
    
    def delete(self, id):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM recipes WHERE id = %s", (id,))
                return cur.rowcount > 0
    
    def search(self, keyword):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name FROM recipes WHERE name ILIKE %s ORDER BY id",
                    (f'%{keyword}%',)
                )
                return cur.fetchall()

def input_list(prompt):
    print(f"{prompt}（空行で終了）:")
    items = []
    while True:
        item = input()
        if not item:
            break
        items.append(item)
    return items

def input_steps():
    print("工程を入力してください（空行で終了）:")
    steps = []
    while True:
        desc = input("説明: ")
        if not desc:
            break
        photo = input("写真ファイル名(省略可): ") or None
        steps.append({'description': desc, 'photo': photo})
    return steps

def main():
    try:
        rm = RecipeManager()
        
        while True:
            print("\n1.追加 2.一覧 3.表示 4.削除 5.検索 0.終了")
            choice = input("選択: ")
            
            if choice == "1":
                name = input("名前: ")
                ingredients = input_list("材料")
                steps = input_steps()
                servings = int(input("人数分: ") or "1")
                id = rm.add(name, ingredients, steps, servings)
                print(f"追加完了 ID:{id}")
            
            elif choice == "2":
                recipes = rm.list()
                print("\n=== 一覧 ===" if recipes else "レシピなし")
                for id, name in recipes:
                    print(f"{id}: {name}")
            
            elif choice == "3":
                id = int(input("ID: "))
                recipe = rm.get(id)
                if recipe:
                    print(f"\n=== {recipe['name']} ({recipe['servings']}人分) ===")
                    print("材料:")
                    for ing in recipe['ingredients']:
                        print(f"- {ing}")
                    print("工程:")
                    for i, step in enumerate(recipe['steps'], 1):
                        print(f"{i}. {step['description']}")
                        if step['photo']:
                            print(f"   写真: {step['photo']}")
                else:
                    print("見つかりません")
            
            elif choice == "4":
                id = int(input("削除ID: "))
                print("削除完了" if rm.delete(id) else "見つかりません")
            
            elif choice == "5":
                keyword = input("キーワード: ")
                results = rm.search(keyword)
                print("\n=== 検索結果 ===" if results else "該当なし")
                for id, name in results:
                    print(f"{id}: {name}")
            
            elif choice == "0":
                break
    
    except psycopg2.Error as e:
        print(f"DB接続エラー: {e}")
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    main()