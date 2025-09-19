<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import axios from 'axios'

// --- Refs e reactive state ---
const currentMessage = ref('')
const messages = reactive([])
const isLoading = ref(false)
const messageIdCounter = ref(0)
const apiUrl = 'http://localhost:8000'

const exampleQuestions = [
  'Mostrami tutti i file PDF caricati',
  'Qual\'è il documento più recente?',
  'Restituisci la media dei costi dei file caricati nell\'ultimo mese',
  'Elenca i file più grandi di 1MB'
]

const isCategoryValid = ref(true)
const docsInDb = ref(true)
const chatPlaceholder = ref('')

// --- Refs per DOM ---
const messageInput = ref(null)
const messagesContainer = ref(null)

// --- Computed ---
const isSendDisabled = computed(() => !currentMessage.value.trim() || isLoading.value || !isCategoryValid.value)

// --- Helper functions ---
const formatTime = (date) => date.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
const formatDate = (dateString) => dateString ? new Date(dateString).toLocaleString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''
const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B','KB','MB','GB']
  const i = Math.floor(Math.log(bytes)/Math.log(k))
  return parseFloat((bytes/Math.pow(k,i)).toFixed(1)) + ' ' + sizes[i]
}

// --- Funzioni principali ---
const setExampleQuestion = (question) => {
  currentMessage.value = question
  focusInput()
}

const handleKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }

  // Auto resize textarea
  nextTick(() => {
    const textarea = event.target
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
  })
}

const fetchCategory = async () => {
  try {
    const { data } = await axios.get(`${apiUrl}/get-category`)
    isCategoryValid.value = !!data.category?.trim()
  } catch (err) {
    console.error('Errore nel recupero della categoria:', err)
    isCategoryValid.value = false
  } finally {
    computePlaceholder()
  }
}

const checkDocs = async () => {
  try {
    const { data } = await axios.get(`${apiUrl}/count-docs`)
    docsInDb.value = data.result > 0
  } catch (err) {
    console.error('Errore nel recupero count dei documenti:', err)
    docsInDb.value = false
  } finally {
    computePlaceholder()
  }
}

const computePlaceholder = () => {
  if (!isCategoryValid.value) {
    chatPlaceholder.value = "Definisci la categoria dei documenti nella sezione /settings per abilitare l'assistente"
  } else if (isLoading.value) {
    chatPlaceholder.value = "Elaborazione in corso..."
  } else if (!docsInDb.value) {
    chatPlaceholder.value = "Carica dei documenti nella sezione /upload per iniziare a fare domande"
  } else {
    chatPlaceholder.value = "Fai una domanda sui tuoi documenti..."
  }
}

const focusInput = () => {
  nextTick(() => messageInput.value?.focus())
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
}

const clearChat = () => {
  messages.splice(0, messages.length)
  focusInput()
}

const downloadFile = async (fileId, filename) => {
  try {
    const response = await axios.get(`${apiUrl}/download-file/${fileId}`, { responseType: 'blob' })
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Errore durante il download:', error)
    messages.push({
      id: messageIdCounter.value++,
      type: 'assistant',
      text: 'Errore Download',
      result: `Impossibile scaricare il file: ${error.response?.data || 'Errore sconosciuto'}`,
      timestamp: new Date()
    })
    scrollToBottom()
  }
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isLoading.value) return

  messages.push({
    id: messageIdCounter.value++,
    type: 'user',
    text: currentMessage.value.trim(),
    timestamp: new Date()
  })

  const userQuestion = currentMessage.value.trim()
  currentMessage.value = ''

  nextTick(() => { if (messageInput.value) messageInput.value.style.height = 'auto' })

  isLoading.value = true
  scrollToBottom()

  try {
    const { data } = await axios.get(`${apiUrl}/ask-docs-info`, { params: { text: userQuestion } })
    
    // Gestione risultati array (file) o testo
    let resultData = data.result
    if (Array.isArray(resultData) && resultData.length) {
      resultData = resultData.map(f => ({
        ...f,
        display: `${f.filename} ${f.file_size ? '(' + formatFileSize(f.file_size) + ')' : ''}`
      }))
    }

    messages.push({
      id: messageIdCounter.value++,
      type: 'assistant',
      text: data.message,
      query: data.query, // <-- query SQL o API mostrata
      result: resultData,
      timestamp: new Date()
    })
  } catch (error) {
    console.error('Errore API:', error)
    messages.push({
      id: messageIdCounter.value++,
      type: 'assistant',
      text: 'Errore',
      result: error.response?.data?.detail || "Si è verificato un errore durante l'elaborazione della richiesta.",
      timestamp: new Date()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
    focusInput()
  }
}

// --- Lifecycle ---
onMounted(() => {
  fetchCategory()
  checkDocs()
  computePlaceholder()
})

// --- Watchers ---
watch([isCategoryValid, isLoading, docsInDb], computePlaceholder)
</script>

<template>
  <div class="chat-wrapper">
    <!-- Messaggi -->
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="msg in messages" 
        :key="msg.id"
        :class="['chat-msg', msg.type]"
      >
        <div class="chat-bubble">
          <div class="msg-text">Risultato: {{ msg.text }}</div>

          <!-- Se è un array di file -->
          <div v-if="Array.isArray(msg.result) && msg.result.length" class="msg-result">
            <div 
              v-for="file in msg.result" 
              :key="file.filename"
              class="file-item"
            >
              <span>{{ file.display }}</span>
              <button v-if="file.id" @click="downloadFile(file.id,file.filename)"> Scarica File </button>
            </div>
          </div>

          <!-- Se è testo -->
          <div v-else-if="msg.result" class="msg-result">
            {{ msg.result }}
          </div>

          <!-- Query SQL / API -->
          <pre v-if="msg.query" class="msg-query">Query elaborata: {{ msg.query }}</pre>

          <small class="msg-time">{{ formatTime(msg.timestamp) }}</small>
        </div>
      </div>

      <div v-if="isLoading" class="loading">AI sta ragionando...</div>
    </div>

    <!-- Example Questions -->
    <div v-if="docsInDb && isCategoryValid && exampleQuestions.length" 
      class="example-questions">
      <p>Prova a chiedere:</p>
      <div class="examples-list">
        <button 
          v-for="(q, i) in exampleQuestions" 
          :key="i" 
          @click="setExampleQuestion(q)"
        >
          {{ q }}
        </button>
      </div>
    </div>

    <!-- Input -->
    <div class="chat-input">
      <textarea
        ref="messageInput"
        v-model="currentMessage"
        :placeholder="chatPlaceholder"
        @keydown="handleKeydown"
      ></textarea>
      <button @click="sendMessage" :disabled="isSendDisabled">Invia</button>
    </div>
  </div>
</template>

<style scoped>
.chat-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #202123;
  color: #fff;
}

/* Messaggi */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.msg-query {
  background: #2a2b35;
  color: #cfcfcf;
  font-size: 0.75rem;
  padding: 6px 8px;
  margin-top: 6px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-msg {
  margin-bottom: 16px;
  display: flex;
}

.chat-msg.user {
  justify-content: flex-end;
}

.chat-bubble {
  max-width: 70%;
  padding: 12px;
  border-radius: 8px;
  line-height: 1.4;
  word-wrap: break-word;
  background: #444654;
  color: #e5e5e5;
}

.chat-msg.user .chat-bubble {
  background: #0d6efd;
  color: #fff;
}

.msg-result {
  margin-top: 8px;
  font-size: 0.85rem;
  color: #b3b3b3;
}

.msg-result .file-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.msg-result button {
  background: #0d6efd;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 2px 6px;
  cursor: pointer;
  font-size: 0.75rem;
}

.msg-time {
  display: block;
  font-size: 0.7rem;
  margin-top: 6px;
  color: #aaa;
  text-align: right;
}

/* Example Questions */
.example-questions {
  border-top: 1px solid #565869;
  padding: 12px 16px;
  background: #343541;
}

.example-questions p {
  font-size: 0.9rem;
  margin-bottom: 8px;
  color: #b3b3b3;
}

.examples-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.examples-list button {
  background: #40414f;
  border: none;
  padding: 6px 10px;
  border-radius: 6px;
  color: #e5e5e5;
  font-size: 0.85rem;
  cursor: pointer;
}

.examples-list button:hover {
  background: #4a4b57;
}

/* Loading */
.loading {
  color: #aaa;
  font-style: italic;
  margin-top: 10px;
}

/* Input */
.chat-input {
  display: flex;
  padding: 12px;
  border-top: 1px solid #565869;
  background: #343541;
}

.chat-input textarea {
  flex: 1;
  resize: none;
  padding: 10px;
  border-radius: 6px;
  border: none;
  outline: none;
  background: #40414f;
  color: #fff;
  font-size: 1rem;
}

.chat-input button {
  margin-left: 8px;
  padding: 10px 16px;
  background: #0d6efd;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.chat-input button:disabled {
  background: #666;
  cursor: not-allowed;
}
</style>