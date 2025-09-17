<script>
import axios from 'axios'

export default {
  name: 'Home',
  data() {
    return {
      currentMessage: '',
      messages: [],
      isLoading: false,
      apiUrl: 'http://localhost:8000',
      messageIdCounter: 0,
      exampleQuestions: [
        'Mostrami tutti i file PDF caricati',
        'Qual\'è il documento più recente?',
        'Restituisci la media dei costi dei file caricati nell\'ultimo mese',
        'Elenca i file più grandi di 1MB'
      ],
      isCategoryValid: true,
      docsInDb: true,
      chatPlaceholder: ''
    }
  },
  
  mounted() {
    this.fetchCategory()
    this.checkDocs()
    this.computePlaceholder()
  },

  watch: {
    isCategoryValid() {
      this.computePlaceholder()
    },
    isLoading() {
      this.computePlaceholder()
    },
    docsInDb() {
      this.computePlaceholder()
    }
  },
  
  methods: {

    setExampleQuestion(question) {
      this.currentMessage = question
      this.focusInput()
    },
    
    handleKeydown(event) {
      // Enter senza Shift invia il messaggio
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault()
        this.sendMessage()
      }
      
      // Auto-resize della textarea
      this.$nextTick(() => {
        const textarea = event.target
        textarea.style.height = 'auto'
        textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
      })
    },

    async fetchCategory() {
        try {
            const response = await axios.get(this.apiUrl + "/get-category")
            const data = response.data

            // se category vuota → disabilita
            this.isCategoryValid = !!data.category?.trim()

            // aggiorna il placeholder
            this.computePlaceholder()
        } catch (err) {
            console.error("Errore nel recupero della categoria:", err)
            this.isCategoryValid = false
            this.computePlaceholder()
        }
    },

    async checkDocs() {
      try {
          const response = await axios.get(this.apiUrl + "/count-docs")
          const count = response.data.result 

          if (count === 0) {
              this.docsInDb = false
          } else {
              this.docsInDb = true
          }

          this.computePlaceholder()
        } catch (err) {
            console.error("Errore nel recupero count dei documenti:", err)
            this.docsInDb = false
            this.computePlaceholder()
        }
    },  

    computePlaceholder() {
        if (!this.isCategoryValid) {
            this.chatPlaceholder = "Definisci la categoria dei documenti per abilitare l'assistente"
        } else if (this.isLoading) {
            this.chatPlaceholder = "Elaborazione in corso..."
        } else if (!this.docsInDb) {
            this.chatPlaceholder = "Carica dei documenti nella sezione /upload per iniziare a fare domande"
        } else {
            this.chatPlaceholder = "Fai una domanda sui tuoi documenti..."
        }
    },

    async downloadFile(fileId, filename) {
      try {
        const response = await axios.get(`${this.apiUrl}/download-file/${fileId}`, {
          responseType: 'blob'
        })
        
        // Crea un URL per il blob
        const blob = new Blob([response.data])
        const url = window.URL.createObjectURL(blob)
        
        // Crea un elemento <a> temporaneo per il download
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        
        // Pulisci
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
      } catch (error) {
        console.error('Errore durante il download:', error)
        // Mostra un messaggio di errore all'utente
        const errorMessage = {
          id: this.messageIdCounter++,
          type: 'assistant',
          text: 'Errore Download',
          result: `Impossibile scaricare il file: ${error.response?.data || 'Errore sconosciuto'}`,
          timestamp: new Date()
        }
        this.messages.push(errorMessage)
        this.scrollToBottom()
      }
    },

    async sendMessage() {
      if (!this.currentMessage.trim() || this.isLoading) return
      
      const userMessage = {
        id: this.messageIdCounter++,
        type: 'user',
        text: this.currentMessage.trim(),
        timestamp: new Date()
      }
      
      this.messages.push(userMessage)
      const userQuestion = this.currentMessage.trim()
      this.currentMessage = ''
      
      // Reset textarea height
      this.$nextTick(() => {
        if (this.$refs.messageInput) {
          this.$refs.messageInput.style.height = 'auto'
        }
      })
      
      this.isLoading = true
      this.scrollToBottom()
      
      try {
        const response = await axios.get(`${this.apiUrl}/ask-docs-info`, {
          params: {
            text: userQuestion
          }
        })
        
        const assistantMessage = {
          id: this.messageIdCounter++,
          type: 'assistant',
          text: response.data.message,
          query: response.data.query,
          result: response.data.result,
          timestamp: new Date()
        }
        
        this.messages.push(assistantMessage)
        
      } catch (error) {
        console.error('Errore API:', error)
        
        const errorMessage = {
          id: this.messageIdCounter++,
          type: 'assistant',
          text: 'Errore',
          result: error.response?.data?.detail || 'Si è verificato un errore durante l\'elaborazione della richiesta.',
          timestamp: new Date()
        }
        
        this.messages.push(errorMessage)
      } finally {
        this.isLoading = false
        this.scrollToBottom()
        this.focusInput()
      }
    },
    
    clearChat() {
      this.messages = []
      this.focusInput()
    },
    
    focusInput() {
      this.$nextTick(() => {
        if (this.$refs.messageInput) {
          this.$refs.messageInput.focus()
        }
      })
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    },
    
    formatTime(date) {
      return date.toLocaleTimeString('it-IT', {
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    
    formatDate(dateString) {
      if (!dateString) return ''
      return new Date(dateString).toLocaleString('it-IT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    
    formatFileSize(bytes) {
      if (!bytes || bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
    }
  }
}
</script>

<template>
  <div class="home-container">
    <!-- Header della chat -->
    <div class="chat-header" ref="chatHeader">
      <div class="header-content">
        <div class="assistant-info">
          <div class="assistant-avatar">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="3" fill="currentColor"/>
              <path d="M12 1v6m0 8v6m11-7h-6M6 12H0" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="assistant-details">
            <h3>DocBot Assistant</h3>
            <p>Chiedimi qualsiasi cosa sui tuoi documenti</p>
          </div>
        </div>
        
        <div class="chat-actions">
          <button @click="clearChat" class="action-btn" :disabled="messages.length === 0">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="2"/>
            </svg>
            Pulisci Chat
          </button>
        </div>
      </div>
    </div>

    <!-- Area dei messaggi -->
    <div class="messages-container" ref="messagesContainer">
      <!-- Messaggio di benvenuto -->
      <div v-if="messages.length === 0" class="welcome-message">
        <div class="welcome-content">

          <h2>Benvenuto in DocBot</h2>
          <p>Inizia una conversazione facendo una domanda sui tuoi documenti caricati.</p>
          
          <div class="example-questions">
            <h4>Esempi di domande:</h4>
            <button
              v-for="example in exampleQuestions"
              :key="example"
              @click="setExampleQuestion(example)"
              class="example-btn"
            >
              {{ example }}
            </button>
          </div>
        </div>
      </div>

      <!-- Lista messaggi -->
      <div v-else class="messages-list">
        <transition-group name="message" tag="div">
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['message', `message-${message.type}`]"
          >
            <!-- Messaggio utente -->
            <div v-if="message.type === 'user'" class="message-content">
              <div class="user-avatar">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <div class="message-text">
                <div class="message-header">
                  <span class="sender-name">Tu</span>
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                </div>
                <div class="message-body">{{ message.text }}</div>
              </div>
            </div>

            <!-- Messaggio assistente -->
            <div v-else class="message-content">
              <div class="assistant-avatar">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="3" fill="currentColor"/>
                  <path d="M12 1v6m0 8v6m11-7h-6M6 12H0" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <div class="message-text">
                <div class="message-header">
                  <span class="sender-name">DocBot</span>
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                </div>
                <div class="message-body">
                  <!-- Query SQL mostrata -->
                  <div v-if="message.query" class="query-section">
                    <div class="query-header">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <polyline points="16 18 22 12 16 6" stroke="currentColor" stroke-width="2"/>
                        <polyline points="8 6 2 12 8 18" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      Per la tua richiesta ho generato la seguente SQL query:
                    </div>
                    <pre class="query-code">{{ message.query }}</pre>
                  </div>

                  <!-- Risultato -->
                  <div class="result-section">
                    <div v-if="Array.isArray(message.result)" class="files-result">
                      <div class="result-header">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
                          <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        File trovati ({{ message.result.length }})
                      </div>
                      <div class="files-grid">
                        <div
                          v-for="file in message.result"
                          :key="file.filename"
                          class="file-card"
                        >
                          <div class="file-icon">📄</div>
                          <div class="file-info">
                            <h5>{{ file.filename }}</h5>
                            <div class="file-meta">
                              <span v-if="file.file_size">{{ formatFileSize(file.file_size) }}</span>
                              <span v-if="file.upload_date">{{ formatDate(file.upload_date) }}</span>
                            </div>
                          </div>
                          <button
                            v-if="file.id"
                            @click="downloadFile(file.id, file.filename)"
                            class="download-btn"
                            title="Scarica file"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2"/>
                              <polyline points="7,10 12,15 17,10" stroke="currentColor" stroke-width="2"/>
                              <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2"/>
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>

                    <div v-else class="text-result">
                      <div class="result-header">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M14 9V5a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2H9" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        Risposta
                      </div>
                      <div class="text-content">{{ message.result }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </transition-group>

        <!-- Indicatore di digitazione -->
        <div v-if="isLoading" class="typing-indicator">
          <div class="message message-assistant">
            <div class="message-content">
              <div class="assistant-avatar">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="3" fill="currentColor"/>
                  <path d="M12 1v6m0 8v6m11-7h-6M6 12H0" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <div class="message-text">
                <div class="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input area -->
    <div class="input-area">
      <form @submit.prevent="sendMessage" class="input-form">
        <div class="input-container">
          <textarea
            v-model="currentMessage"
            ref="messageInput"
            :placeholder="chatPlaceholder"
            :disabled="isLoading"
            @keydown="handleKeydown"
            rows="1"
            class="message-input"
          ></textarea>
          
          <button
            type="submit"
            :disabled="!currentMessage.trim() || isLoading || !isCategoryValid"
            class="send-button"
          >
            <svg v-if="!isLoading" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="22" y1="2" x2="11" y2="13" stroke="currentColor" stroke-width="2"/>
              <polygon points="22,2 15,22 11,13 2,9" stroke="currentColor" stroke-width="2" fill="none"/>
            </svg>
            <div v-else class="loading-spinner"></div>
          </button>
        </div>
        
        <div class="input-footer">
          <small class="input-hint">
            Premi <kbd>Enter</kbd> per inviare, <kbd>Shift + Enter</kbd> per nuova riga
          </small>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 1000px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

/* Header */
.chat-header {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
  padding: 20px 24px;
  flex-shrink: 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.assistant-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.assistant-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.assistant-details h3 {
  color: #1f2937;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.assistant-details p {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.15);
  transform: translateY(-1px);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Messages Area */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  background: #ffffff;
}

.welcome-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
}

.welcome-content {
  text-align: center;
  max-width: 500px;
}

.welcome-icon {
  color: #3b82f6;
  margin-bottom: 24px;
}

.welcome-content h2 {
  color: #1f2937;
  font-size: 1.875rem;
  font-weight: 700;
  margin-bottom: 12px;
}

.welcome-content p {
  color: #6b7280;
  font-size: 1.125rem;
  margin-bottom: 32px;
}

.example-questions h4 {
  color: #374151;
  font-size: 1rem;
  margin-bottom: 16px;
}

.example-questions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.example-btn {
  padding: 12px 16px;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  border: 1px solid #d1d5db;
  border-radius: 12px;
  color: #374151;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.example-btn:hover {
  background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Messages List */
.messages-list {
  padding: 24px;
}

.message {
  margin-bottom: 24px;
}

.message-content {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.message-user .message-content {
  flex-direction: row-reverse;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.assistant-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-text {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.sender-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
}

.message-time {
  font-size: 0.75rem;
  color: #9ca3af;
}

.message-body {
  color: #1f2937;
  line-height: 1.6;
}

.message-user .message-body {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  padding: 12px 16px;
  border-radius: 16px 16px 4px 16px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

/* Query Section */
.query-section {
  margin-bottom: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}

.query-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f1f5f9;
  color: #475569;
  font-size: 0.875rem;
  font-weight: 500;
  border-bottom: 1px solid #e2e8f0;
}

.query-code {
  padding: 16px;
  margin: 0;
  background: #ffffff;
  color: #1f2937;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
}

/* Result Section */
.result-section {
  background: #f9fafb;
  border: 1px solid #f3f4f6;
  border-radius: 12px;
  overflow: hidden;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f3f4f6;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  border-bottom: 1px solid #e5e7eb;
}

.text-content {
  padding: 16px;
  color: #1f2937;
  line-height: 1.6;
}

.files-grid {
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.file-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.file-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.download-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.download-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.file-icon {
  font-size: 24px;
  opacity: 0.7;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-info h5 {
  margin: 0;
  color: #1f2937;
  font-size: 0.875rem;
  font-weight: 500;
  word-break: break-word;
}

.file-meta {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  font-size: 0.75rem;
  color: #6b7280;
}

/* Typing Indicator */
.typing-indicator {
  margin-bottom: 24px;
}

.typing-dots {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: #f3f4f6;
  border-radius: 16px 16px 16px 4px;
  width: fit-content;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: scale(1);
    opacity: 0.7;
  }
  30% {
    transform: scale(1.2);
    opacity: 1;
  }
}

/* Input Area */
.input-area {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-top: 1px solid #e2e8f0;
  padding: 20px 24px;
  flex-shrink: 0;
}

.input-form {
  max-width: 100%;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  padding: 12px;
  transition: border-color 0.2s ease;
}

.input-container:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.message-input {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.5;
  min-height: 24px;
  max-height: 150px;
  overflow-y: auto;
}

.message-input::placeholder {
  color: #9ca3af;
}

.message-input:disabled {
  opacity: 0.6;
}

.send-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.send-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.input-footer {
  margin-top: 8px;
  text-align: center;
}

.input-hint {
  color: #6b7280;
  font-size: 0.75rem;
}

kbd {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.75rem;
  color: #374151;
}

/* Animations */
.message-enter-active {
  transition: all 0.3s ease;
}

.message-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.message-leave-active {
  transition: all 0.3s ease;
}

.message-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* Responsive Design */
@media (max-width: 768px) {
  .home-container {
    height: 100vh;
    border-radius: 0;
    border: none;
  }
  
  .chat-header {
    padding: 16px 20px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .assistant-info {
    width: 100%;
  }
  
  .assistant-details h3 {
    font-size: 1rem;
  }
  
  .assistant-details p {
    font-size: 0.8rem;
  }
  
  .welcome-message {
    padding: 20px;
  }
  
  .welcome-content {
    max-width: 100%;
  }
  
  .welcome-content h2 {
    font-size: 1.5rem;
  }
  
  .welcome-content p {
    font-size: 1rem;
  }
  
  .messages-list {
    padding: 16px;
  }
  
  .message {
    margin-bottom: 20px;
  }
  
  .files-grid {
    grid-template-columns: 1fr;
    padding: 12px;
  }
  
  .input-area {
    padding: 16px 20px;
  }
  
  .input-container {
    padding: 10px;
  }
  
  .message-input {
    font-size: 16px; /* Previene zoom su iOS */
  }
  
  .send-button {
    width: 36px;
    height: 36px;
  }
}

@media (max-width: 480px) {
  .chat-header {
    padding: 12px 16px;
  }
  
  .assistant-avatar {
    width: 36px;
    height: 36px;
  }
  
  .welcome-message {
    padding: 16px;
  }
  
  .welcome-content h2 {
    font-size: 1.25rem;
  }
  
  .welcome-content p {
    font-size: 0.9rem;
  }
  
  .messages-list {
    padding: 12px;
  }
  
  .message-content {
    gap: 8px;
  }
  
  .user-avatar,
  .assistant-avatar {
    width: 28px;
    height: 28px;
  }
  
  .query-code {
    font-size: 0.8rem;
    padding: 12px;
  }
  
  .input-area {
    padding: 12px 16px;
  }
  
  .input-container {
    padding: 8px;
    gap: 8px;
  }
  
  .send-button {
    width: 32px;
    height: 32px;
  }
  
  .download-btn {
    width: 28px;
    height: 28px;
  }
}

/* Scrollbar personalizzata per l'area messaggi */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Focus states migliorati */
.example-btn:focus,
.action-btn:focus,
.send-button:focus,
.download-btn:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

.message-input:focus {
  outline: none; /* Gestito dal container */
}

/* Stati di caricamento */
.send-button:disabled .loading-spinner {
  animation: spin 1s linear infinite;
}

/* Miglioramenti per l'accessibilità */
@media (prefers-reduced-motion: reduce) {
  .typing-dots span {
    animation: none;
  }
  
  .loading-spinner {
    animation: none;
  }
  
  .message-enter-active,
  .message-leave-active {
    transition: none;
  }
  
  .send-button,
  .action-btn,
  .example-btn,
  .file-card,
  .download-btn {
    transition: none;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .input-container {
    border-width: 3px;
  }
  
  .message-user .message-body {
    border-width: 2px;
  }
  
  .query-section,
  .result-section {
    border-width: 2px;
  }
}

/* Print styles */
@media print {
  .chat-header,
  .input-area {
    display: none;
  }
  
  .home-container {
    height: auto;
    box-shadow: none;
    border: 1px solid #000;
  }
  
  .messages-container {
    overflow: visible;
  }
  
  .download-btn {
    display: none;
  }
}

/* Accessibilità per screen readers */
.download-btn[aria-label] {
  position: relative;
}

/* Stato hover per i file cards migliorato */
.file-card:hover .download-btn {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

/* Miglioramento visivo per file senza download */
.file-card:not(:has(.download-btn)) {
  opacity: 0.8;
}

/* Loading state per il download */
.download-btn.loading {
  opacity: 0.7;
  cursor: not-allowed;
}

.download-btn.loading svg {
  animation: spin 1s linear infinite;
}
</style>