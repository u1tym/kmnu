<template>
  <div class="app">
    <header class="header">
      <h1>🍳 レシピ管理</h1>
      <div class="search-bar">
        <input 
          v-model="searchQuery" 
          @keyup.enter="search"
          placeholder="レシピを検索..."
          class="search-input"
        >
        <select v-model="searchType" class="search-type">
          <option value="name">名前</option>
          <option value="keyword">キーワード</option>
          <option value="ingredient">材料</option>
        </select>
        <button @click="search" class="search-btn">検索</button>
      </div>
      <button @click="showCreateForm = true" class="create-btn">+ 新規レシピ</button>
    </header>

    <main class="main">
      <!-- レシピ作成フォーム -->
      <div v-if="showCreateForm" class="modal">
        <div class="modal-content">
          <h2>新規レシピ作成</h2>
          <form @submit.prevent="createRecipe">
            <div class="form-group">
              <label>レシピ名 *</label>
              <input v-model="newRecipe.name" required maxlength="100" class="form-input">
            </div>
            
            <div class="form-group">
              <label>人数分</label>
              <input v-model.number="newRecipe.servings" type="number" min="1" max="99" class="form-input">
            </div>
            
            <div class="form-group">
              <label>キーワード</label>
              <input 
                v-model="keywordInput" 
                @keydown.enter.prevent="addKeyword" 
                placeholder="キーワードを入力してEnter" 
                class="form-input"
              >
              <div class="keywords">
                <span v-for="(keyword, index) in newRecipe.keywords" :key="index" class="keyword-tag">
                  {{ keyword }}
                  <button type="button" @click="removeKeyword(index)" class="remove-btn">×</button>
                </span>
              </div>
            </div>
            
            <div class="form-group">
              <label>材料</label>
              <div v-for="(ingredient, index) in newRecipe.ingredients" :key="index" class="ingredient-row">
                <input v-model="ingredient.name" placeholder="材料名" maxlength="50" class="ingredient-input">
                <input v-model="ingredient.amount" placeholder="分量" maxlength="20" class="amount-input">
                <button type="button" @click="removeIngredient(index)" class="remove-btn">削除</button>
              </div>
              <button type="button" @click="addIngredient" class="add-btn">+ 材料追加</button>
            </div>
            
            <div class="form-group">
              <label>手順</label>
              <div v-for="(step, index) in newRecipe.steps" :key="index" class="step-row">
                <span class="step-number">{{ index + 1 }}.</span>
                <div class="step-content">
                  <textarea v-model="step.description" placeholder="手順を入力" class="step-input"></textarea>
                  <div class="photo-upload">
                    <input 
                      type="file" 
                      :id="`photo-${index}`" 
                      @change="uploadStepPhoto(index, $event)" 
                      accept="image/jpeg,image/png"
                      class="photo-input"
                    >
                    <label :for="`photo-${index}`" class="photo-label">📷 写真追加</label>
                    <div v-if="step.photo_id" class="photo-preview">
                      <img :src="`/api/photos/${step.photo_id}`" alt="手順写真" class="step-photo">
                      <button type="button" @click="removeStepPhoto(index)" class="remove-photo-btn">×</button>
                    </div>
                  </div>
                </div>
                <button type="button" @click="removeStep(index)" class="remove-btn">削除</button>
              </div>
              <button type="button" @click="addStep" class="add-btn">+ 手順追加</button>
            </div>
            
            <div class="form-actions">
              <button type="button" @click="cancelCreate" class="cancel-btn">キャンセル</button>
              <button type="submit" class="submit-btn">作成</button>
            </div>
          </form>
        </div>
      </div>

      <!-- レシピ一覧 -->
      <div class="recipe-list">
        <div v-if="loading" class="loading">読み込み中...</div>
        <div v-else-if="recipes.length === 0" class="empty">レシピがありません</div>
        <div v-else>
          <div v-for="recipe in recipes" :key="recipe.id" class="recipe-card" @click="viewRecipe(recipe.id)">
            <h3>{{ recipe.name || 'レシピ名なし' }}</h3>
            <p v-if="recipe.servings">{{ recipe.servings }}人分</p>
            <small v-if="recipe.created">{{ formatDate(recipe.created) }}</small>
            <!-- デバッグ用 -->
            <div style="font-size: 10px; color: #ccc; margin-top: 5px;">
              ID: {{ recipe.id }}, Type: {{ typeof recipe }}
            </div>
          </div>
        </div>
      </div>

      <!-- レシピ詳細 -->
      <div v-if="selectedRecipe" class="modal">
        <div class="modal-content recipe-detail">
          <div class="recipe-header">
            <h2>{{ selectedRecipe.name }}</h2>
            <div class="recipe-actions">
              <button @click="editRecipe" class="edit-btn">編集</button>
              <button @click="deleteRecipe" class="delete-btn">削除</button>
              <button @click="selectedRecipe = null" class="close-btn">×</button>
            </div>
          </div>
          
          <div class="recipe-info">
            <p><strong>人数分:</strong> {{ selectedRecipe.servings }}人</p>
            <div v-if="selectedRecipe.keywords?.length">
              <strong>キーワード:</strong>
              <span v-for="keyword in selectedRecipe.keywords" :key="keyword" class="keyword-tag">{{ keyword }}</span>
            </div>
          </div>
          
          <div v-if="selectedRecipe.ingredients?.length" class="ingredients">
            <h3>材料</h3>
            <ul>
              <li v-for="ingredient in selectedRecipe.ingredients" :key="ingredient.name">
                {{ ingredient.name }} - {{ ingredient.amount }}
              </li>
            </ul>
          </div>
          
          <div v-if="selectedRecipe.steps?.length" class="steps">
            <h3>手順</h3>
            <ol>
              <li v-for="step in selectedRecipe.steps" :key="step.description" class="step-item">
                <div class="step-text">{{ step.description }}</div>
                <div v-if="step.photo_id" class="step-photo-container">
                  <img :src="`/api/photos/${step.photo_id}`" alt="手順写真" class="step-photo-detail">
                </div>
              </li>
            </ol>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface Ingredient {
  name: string
  amount: string
}

interface Step {
  description: string
  photo_id?: number
}

interface Recipe {
  id?: number
  name: string
  ingredients: Ingredient[]
  keywords: string[]
  steps: Step[]
  servings: number
  created?: string
}

const recipes = ref<Recipe[]>([])
const selectedRecipe = ref<Recipe | null>(null)
const showCreateForm = ref(false)
const loading = ref(false)
const searchQuery = ref('')
const searchType = ref('name')
const keywordInput = ref('')

const newRecipe = ref<Recipe>({
  name: '',
  ingredients: [],
  keywords: [],
  steps: [],
  servings: 1
})

const loadRecipes = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/recipes')
    console.log('Load recipes response:', response.data)
    
    // データ形式を統一的に処理
    if (Array.isArray(response.data)) {
      if (response.data.length > 0 && Array.isArray(response.data[0])) {
        // 配列形式の場合
        recipes.value = response.data.map((item: any[]) => ({
          id: item[0],
          name: item[1], 
          servings: item[2],
          created: item[3]
        }))
      } else {
        // オブジェクト形式の場合
        recipes.value = response.data
      }
    } else {
      recipes.value = []
    }
    
    console.log('Processed recipes:', recipes.value)
  } catch (error) {
    console.error('レシピの読み込みに失敗しました:', error)
    recipes.value = []
  } finally {
    loading.value = false
  }
}

const viewRecipe = async (id: number) => {
  try {
    const response = await axios.get(`/api/recipes/${id}`)
    selectedRecipe.value = response.data
  } catch (error) {
    console.error('レシピの取得に失敗しました:', error)
  }
}

const createRecipe = async () => {
  try {
    await axios.post('/api/recipes', newRecipe.value)
    showCreateForm.value = false
    resetForm()
    loadRecipes()
  } catch (error) {
    console.error('レシピの作成に失敗しました:', error)
  }
}

const deleteRecipe = async () => {
  if (!selectedRecipe.value || !confirm('このレシピを削除しますか？')) return
  
  try {
    await axios.delete(`/api/recipes/${selectedRecipe.value.id}`)
    selectedRecipe.value = null
    loadRecipes()
  } catch (error) {
    console.error('レシピの削除に失敗しました:', error)
  }
}

const search = async () => {
  if (!searchQuery.value.trim()) {
    loadRecipes()
    return
  }
  
  loading.value = true
  try {
    const response = await axios.get(`/api/recipes/search/${searchType.value}/${searchQuery.value}`)
    console.log('Search response:', response.data)
    
    // 検索結果を統一形式に変換
    if (Array.isArray(response.data)) {
      if (response.data.length > 0 && Array.isArray(response.data[0])) {
        // 配列形式の場合
        recipes.value = response.data.map((item: any[]) => ({
          id: item[0],
          name: item[1],
          servings: item[2] || null,
          created: item[3] || null
        }))
      } else {
        // オブジェクト形式の場合
        recipes.value = response.data
      }
    } else {
      recipes.value = []
    }
  } catch (error) {
    console.error('検索に失敗しました:', error)
  } finally {
    loading.value = false
  }
}

const addKeyword = () => {
  const keyword = keywordInput.value.trim()
  if (keyword && newRecipe.value.keywords.length < 10 && !newRecipe.value.keywords.includes(keyword)) {
    newRecipe.value.keywords.push(keyword)
    keywordInput.value = ''
  }
}

const removeKeyword = (index: number) => {
  newRecipe.value.keywords.splice(index, 1)
}

const addIngredient = () => {
  newRecipe.value.ingredients.push({ name: '', amount: '' })
}

const removeIngredient = (index: number) => {
  newRecipe.value.ingredients.splice(index, 1)
}

const addStep = () => {
  newRecipe.value.steps.push({ description: '', photo_id: null })
}

const uploadStepPhoto = async (stepIndex: number, event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  // ファイルサイズチェック
  if (file.size > 5 * 1024 * 1024) {
    alert('ファイルサイズは5MB以下にしてください')
    return
  }
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const response = await axios.post('/api/photos', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    newRecipe.value.steps[stepIndex].photo_id = response.data.id
  } catch (error) {
    console.error('写真アップロードに失敗しました:', error)
    alert('写真アップロードに失敗しました')
  }
}

const removeStepPhoto = async (stepIndex: number) => {
  const photoId = newRecipe.value.steps[stepIndex].photo_id
  if (!photoId) return
  
  try {
    await axios.delete(`/api/photos/${photoId}`)
    newRecipe.value.steps[stepIndex].photo_id = null
  } catch (error) {
    console.error('写真削除に失敗しました:', error)
  }
}

const removeStep = (index: number) => {
  newRecipe.value.steps.splice(index, 1)
}

const cancelCreate = () => {
  showCreateForm.value = false
  resetForm()
}

const resetForm = () => {
  newRecipe.value = {
    name: '',
    ingredients: [],
    keywords: [],
    steps: [],
    servings: 1
  }
  keywordInput.value = ''
}

const editRecipe = () => {
  // 編集機能は後で実装
  alert('編集機能は準備中です')
}

const formatDate = (dateString: string | undefined) => {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return ''
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'numeric', 
      day: 'numeric'
    })
  } catch {
    return ''
  }
}

onMounted(() => {
  loadRecipes()
})
</script>

<style scoped>
.app { min-height: 100vh; background: #f5f5f5; }

.header {
  background: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.header h1 { color: #333; font-size: 1.5rem; }

.search-bar {
  display: flex;
  gap: 0.5rem;
  flex: 1;
  max-width: 500px;
}

.search-input, .search-type {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.search-input { flex: 1; }

.search-btn, .create-btn {
  padding: 0.5rem 1rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.search-btn:hover, .create-btn:hover { background: #0056b3; }

.main { padding: 2rem; }

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  width: 90%;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.form-input, .ingredient-input, .amount-input, .step-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.keywords, .ingredient-row, .step-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.keyword-tag {
  background: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.875rem;
}

.ingredient-input { flex: 2; }
.amount-input { flex: 1; }
.step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.step-input { min-height: 60px; }
.step-number { font-weight: bold; min-width: 30px; }

.photo-upload {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.photo-input {
  display: none;
}

.photo-label {
  padding: 0.25rem 0.5rem;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.photo-label:hover {
  background: #e9ecef;
}

.photo-preview {
  position: relative;
  display: inline-block;
}

.step-photo {
  width: 80px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.remove-photo-btn {
  position: absolute;
  top: -5px;
  right: -5px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #dc3545;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-item {
  margin-bottom: 1rem;
  padding: 0.5rem;
  border-left: 3px solid #007bff;
  background: #f8f9fa;
}

.step-text {
  margin-bottom: 0.5rem;
}

.step-photo-container {
  text-align: center;
}

.step-photo-detail {
  max-width: 300px;
  max-height: 200px;
  object-fit: cover;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.add-btn, .remove-btn {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  background: white;
}

.add-btn:hover { background: #f8f9fa; }
.remove-btn:hover { background: #f8d7da; }

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.cancel-btn {
  padding: 0.5rem 1rem;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.submit-btn {
  padding: 0.5rem 1rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.recipe-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.recipe-card {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: transform 0.2s;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.recipe-card:hover { transform: translateY(-2px); }

.recipe-card h3 {
  margin: 0;
  color: #333;
  font-size: 1.1rem;
}

.recipe-card p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.recipe-card small {
  color: #999;
  font-size: 0.8rem;
  margin-top: auto;
}

.recipe-detail .recipe-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.recipe-actions {
  display: flex;
  gap: 0.5rem;
}

.edit-btn, .delete-btn, .close-btn {
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.edit-btn { background: #ffc107; }
.delete-btn { background: #dc3545; color: white; }
.close-btn { background: #6c757d; color: white; }

.recipe-info, .ingredients, .steps {
  margin-bottom: 1rem;
}

.loading, .empty {
  text-align: center;
  padding: 2rem;
  color: #666;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-bar {
    max-width: none;
  }
  
  .recipe-list {
    grid-template-columns: 1fr;
  }
  
  .step-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .step-content {
    order: 1;
  }
  
  .remove-btn {
    order: 2;
    align-self: flex-end;
  }
}
</style>