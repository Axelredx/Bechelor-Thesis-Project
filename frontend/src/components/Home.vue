<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import axios from 'axios'

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

const messageInput = ref(null)
const messagesContainer = ref(null)

const isSendDisabled = computed(() => !currentMessage.value.trim() || 
                                        isLoading.value || 
                                        !isCategoryValid.value)

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

onMounted(() => {
  fetchCategory()
  checkDocs()
  computePlaceholder()
})

watch([isCategoryValid, isLoading, docsInDb], computePlaceholder)
</script>

<template>
  <div class="chat-wrapper">
    <!-- Messaggi -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="msg in messages" :key="msg.id" :class="['chat-msg', msg.type]">
        <div class="chat-bubble">
          <div class="msg-text">{{ msg.text }}</div>

          <!-- Se è un array di file -->
          <div v-if="Array.isArray(msg.result) && msg.result.length" class="msg-result">
            <div v-for="file in msg.result" :key="file.filename" class="file-item">
              <span>{{ file.display }}</span>
              <button v-if="file.id" @click="downloadFile(file.id,file.filename)">Scarica File</button>
            </div>
          </div>

          <!-- Se è testo -->
          <div v-else-if="msg.result" class="msg-result">{{ msg.result }}</div>

          <!-- Query SQL / API -->
          <pre v-if="msg.query" class="msg-query">Query elaborata: {{ msg.query }}</pre>

          <small class="msg-time">{{ formatTime(msg.timestamp) }}</small>
        </div>
      </div>

      <div v-if="isLoading" class="loading">AI sta ragionando...</div>
    </div>

    <!-- Example Questions -->
    <div v-if="docsInDb && isCategoryValid && exampleQuestions.length" class="example-questions">
      <p>Prova a chiedere:</p>
      <div class="examples-list">
        <button v-for="(q, i) in exampleQuestions" :key="i" @click="setExampleQuestion(q)">
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

<style >
:root {
  --bg-main: #202123;
  --bg-msg: #444654;
  --bg-user: #0d6efd;
  --bg-query: #2a2b35;
  --bg-examples: #343541;
  --bg-button: #40414f;
  --bg-button-hover: #4a4b57;
  --color-text: #fff;
  --color-secondary: #e5e5e5;
  --color-meta: #b3b3b3;
  --color-muted: #aaa;
}

.chat-wrapper { 
  display:flex; 
  flex-direction:column; 
  height:100vh; 
  background:var(--bg-main); 
  color:var(--color-text); 
}

.chat-messages { 
  flex:1; 
  overflow-y:auto; 
  padding:20px; 
}

.chat-msg { 
  display:flex; 
  margin-bottom:16px; 
}

.chat-msg.user { justify-content:flex-end; }

.chat-bubble {
  max-width:70%; padding:12px; border-radius:8px; line-height:1.4; word-wrap:break-word;
  background:var(--bg-msg); color:var(--color-secondary);
}

.chat-msg.user .chat-bubble { 
  background:var(--bg-user); 
  color:var(--color-text); 
}

.msg-result { margin-top:8px; font-size:0.85rem; color:var(--color-meta); }

.msg-result .file-item { 
  display:flex; 
  justify-content:space-between; 
  margin-bottom:4px; 
}

.msg-result button {
  background:var(--bg-user); color:var(--color-text); border:none; border-radius:4px;
  padding:2px 6px; cursor:pointer; font-size:0.75rem;
}

.msg-time { 
  display:block; 
  font-size:0.7rem; 
  margin-top:6px; 
  color:var(--color-muted); 
  text-align:right; 
}

.msg-query {
  background:var(--bg-query); color:#cfcfcf; font-size:0.75rem; padding:6px 8px;
  margin-top:6px; border-radius:4px; white-space:pre-wrap; word-break:break-word;
}

.example-questions {
  border-top:1px solid #565869; padding:12px 16px; background:var(--bg-examples);
}

.example-questions p { font-size:0.9rem; margin-bottom:8px; color:var(--color-meta); }

.examples-list { display:flex; flex-wrap:wrap; gap:8px; }

.examples-list button {
  background:var(--bg-button); border:none; padding:6px 10px; border-radius:6px;
  color:var(--color-secondary); font-size:0.85rem; cursor:pointer;
}

.examples-list button:hover { background:var(--bg-button-hover); }

.loading { color:var(--color-muted); font-style:italic; margin-top:10px; }

.chat-input { 
  display:flex; 
  padding:12px; 
  border-top:1px solid #565869; 
  background:var(--bg-examples); 
}

.chat-input textarea {
  flex:1; resize:none; padding:10px; border-radius:6px; border:none; outline:none;
  background:#40414f; color:var(--color-text); font-size:1rem;
}

.chat-input button {
  margin-left:8px; padding:10px 16px; background:var(--bg-user); color:var(--color-text);
  border:none; border-radius:6px; cursor:pointer;
}

.chat-input button:disabled { background:#666; cursor:not-allowed; }
</style>
