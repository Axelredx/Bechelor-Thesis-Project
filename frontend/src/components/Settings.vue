<script setup>
import { ref, onMounted, watchEffect } from 'vue'
import axios from 'axios'

const apiUrl = 'http://localhost:8000'

// --- State ---
const categoryInput = ref('')
const nlpInput = ref('') // per delete-docs
const isLoading = ref(false)
const statusMessage = ref('')
const statusType = ref('')
const createdCategory = ref('')
const fullDescription = ref('')
const currentCategory = ref('')
const currentDescription = ref('')
const isFetchingCurrent = ref(false)

// --- Status handling ---
const clearStatus = () => {
  statusMessage.value = ''
  statusType.value = ''
  createdCategory.value = ''
  fullDescription.value = ''
}

const showStatus = (message, type = 'success') => {
  statusMessage.value = message
  statusType.value = type
  setTimeout(clearStatus, 5000)
}

// --- Fetch categorie (in db) ---
const fetchCurrentCategory = async () => {
  isFetchingCurrent.value = true
  try {
    const { data } = await axios.get(`${apiUrl}/get-category`)
    currentCategory.value = data.category || ''
    currentDescription.value = data.description || ''
  } catch (err) {
    currentCategory.value = ''
    currentDescription.value = ''
  } finally {
    isFetchingCurrent.value = false
  }
}

const createCategory = async () => {
  if (!categoryInput.value.trim()) return
  isLoading.value = true
  clearStatus()

  try {
    const { data } = await axios.post(`${apiUrl}/create-category`, {
      text: categoryInput.value
    })
    if (data.query === 'NO') {
      showStatus(data.message, 'error')
      categoryInput.value = ''
      isLoading.value = false
      return
    }
    createdCategory.value = data.category
    fullDescription.value = data.description
    showStatus(data.message, 'success')
    categoryInput.value = ''
    await fetchCurrentCategory()
  } catch (err) {
    showStatus(err.response?.data?.detail || 'Errore durante la creazione', 'error')
  } finally {
    isLoading.value = false
  }
}

const updateCategory = async () => {
  if (!categoryInput.value.trim() || !currentCategory.value) return
  isLoading.value = true
  clearStatus()

  try {
    const { data } = await axios.put(`${apiUrl}/update-category`, {
      text: categoryInput.value
    })
    if (data.query === 'NO') {
      showStatus(data.message, 'error')
      categoryInput.value = ''
      isLoading.value = false
      return
    }
    createdCategory.value = data.category
    fullDescription.value = data.description
    showStatus(data.message, 'success')
    categoryInput.value = ''
    await fetchCurrentCategory()
  } catch (err) {
    showStatus(err.response?.data?.detail || "Errore durante l'aggiornamento", 'error')
  } finally {
    isLoading.value = false
  }
}

const deleteAllCategories = async () => {
  if (!confirm("Sei sicuro di voler eliminare tutte le categorie?")) return
  isLoading.value = true
  clearStatus()

  try {
    const { data } = await axios.delete(`${apiUrl}/delete-all-categories`)
    showStatus(data.message, 'success')
    createdCategory.value = ''
    fullDescription.value = ''
    await fetchCurrentCategory()
  } catch (err) {
    showStatus(err.response?.data?.detail || "Errore durante la cancellazione", 'error')
  } finally {
    isLoading.value = false
  }
}

// --- Delete documents via user NLP ---
const deleteDocuments = async () => {
  if (!nlpInput.value.trim()) return
  isLoading.value = true
  clearStatus()

  try {
    const { data } = await axios.delete(`${apiUrl}/delete-docs`, { data: { text: nlpInput.value } })
    if (data.query === 'NO') {
      showStatus(data.message, 'error')
      nlpInput.value = ''
      isLoading.value = false
      return
    }
    showStatus(data.message, 'success')
    nlpInput.value = ''
  } catch (err) {
    showStatus(err.response?.data?.detail || "Errore durante l'eliminazione", 'error')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => fetchCurrentCategory())
watchEffect(() => {
  if (createdCategory.value || currentCategory.value) {
    fetchCurrentCategory()
  }
})
</script>

<template>
  <div class="file-upload">
    <h1>Impostazioni</h1>

    <!-- Current categories (in DB) -->
    <h3>Categorie attuali con le loro descrizioni:</h3>
    <div class="current-category" v-if="isFetchingCurrent">
      Recupero categorie in corso...
    </div>
    <div class="current-category" v-else>
      {{ currentDescription || 'Nessuna categoria ancora definita' }}
    </div>

    <!-- Delete documents NLP -->
    <div class="nlp-delete">
      <h3>Elimina documenti tramite richiesta specifica:</h3>
      <textarea v-model="nlpInput" placeholder="Inserisci la richiesta di eliminazione..." rows="3"></textarea>
      <button @click="deleteDocuments" :disabled="isLoading || !nlpInput" class="delete-btn">
        Elimina documenti
      </button>
    </div>

    <!-- Status message mid page to be visible -->
    <div v-if="statusMessage" :class="['status', statusType]">
      {{ statusMessage }}
    </div>

    <!-- Add/update category sect. -->
    <h3>Imposta Categorie e Descrizione dei documenti che vuoi riconoscere</h3>
    <textarea
      v-model="categoryInput"
      placeholder="Scrivi nella seguente forma -> BOLLE: documenti di trasporto, FATTURE: fatture di acquisto o vendita, etc."
      rows="4"
    ></textarea>

    <div class="action-buttons">
      <button @click="createCategory" :disabled="isLoading || !categoryInput">
        {{ isLoading ? 'Inviando...' : 'Crea Categoria' }}
      </button>
      <button @click="updateCategory" :disabled="isLoading || !categoryInput || !currentCategory">
        {{ isLoading ? 'Inviando...' : 'Aggiungi Categoria' }}
      </button>
      <button @click="deleteAllCategories" :disabled="isLoading" class="delete-btn">
        Elimina tutte le categorie
      </button>
    </div>

    <div v-if="createdCategory" class="result">
      <strong>Categoria:</strong> {{ createdCategory }}<br>
      <strong>Descrizione completa:</strong><br>
      <pre>{{ fullDescription }}</pre>
    </div>
  </div>
</template>

<style scoped>
.file-upload {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  max-width: 500px;
  margin: 2px auto 40px; 
  font-family: sans-serif;
  color: #fff;
}


h1, h2, h3 {
  color: #fff;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
  padding-bottom: 6px;
  margin-top: 24px;
}

h2 {
  font-size: 1.5rem;
  font-weight: 600;
  border-bottom: 1px dashed;
  padding-bottom: 4px;
  margin-top: 20px;
}

h3 {
  font-size: 1.2rem;
  font-weight: 500;
  border-bottom: 1px dashed;
  padding-bottom: 3px;
  margin-top: 16px;
}

textarea {
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  border: none;
  resize: vertical;
  font-size: 1rem;
  font-family: inherit;
  background-color: #2a2b35; 
  color: #fff;
}

.action-buttons, .nlp-delete {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

button {
  padding: 10px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  background: #3b82f6;
  color: white;
  font-weight: 600;
}

button.delete-btn {
  background: #ef4444;
}

button:disabled {
  background: #6b7280;
  cursor: not-allowed;
}

.status {
  margin-top: 12px;
  padding: 10px;
  border-radius: 8px;
}

.status.success {
  background: #10b981;
  color: #fff;
}

.status.error {
  background: #ef4444;
  color: #fff;
}

.result, .current-category {
  margin-top: 16px;
  background: rgba(255,255,255,0.1);
  padding: 12px;
  border-radius: 8px;
  font-size: 0.9rem;
}

pre {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
