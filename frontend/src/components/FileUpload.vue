<script>
import axios from 'axios'

export default {
  name: 'FileUpload',
  data() {
    return {
      selectedFile: null,
      isUploading: false,
      uploadProgress: 0,
      statusMessage: '',
      statusType: '',
      isDragOver: false,
      uploadedFiles: [],
      apiUrl: 'http://localhost:8000' 
    }
  },
  
  methods: {
    triggerFileInput() {
      this.$refs.fileInput.click()
    },
    
    handleFileSelect(event) {
      const file = event.target.files[0]
      if (file) {
        this.selectedFile = file
        this.clearStatus()
      }
    },
    
    handleDrop(event) {
      event.preventDefault()
      this.isDragOver = false
      
      const files = event.dataTransfer.files
      if (files.length > 0) {
        this.selectedFile = files[0]
        this.clearStatus()
      }
    },
    
    async uploadFile() {
      if (!this.selectedFile) return
      
      this.isUploading = true
      this.uploadProgress = 0
      this.clearStatus()
      
      const formData = new FormData()
      formData.append('file', this.selectedFile)
      
      try {
        const response = await axios.post(`${this.apiUrl}/upload-file/`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            this.uploadProgress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
          }
        })
        
        this.showStatus('File caricato con successo! 🎉', 'success')
        this.clearSelection()
        
      } catch (error) {
        console.error('Errore durante il caricamento:', error)
        this.showStatus(
          error.response?.data?.detail || 'Errore durante il caricamento del file',
          'error'
        )
      } finally {
        this.isUploading = false
        this.uploadProgress = 0
      }
    },
    
    clearSelection() {
      this.selectedFile = null
      this.$refs.fileInput.value = ''
      this.clearStatus()
    },
    
    showStatus(message, type) {
      this.statusMessage = message
      this.statusType = type
      
      setTimeout(() => {
        this.clearStatus()
      }, 5000)
    },
    
    clearStatus() {
      this.statusMessage = ''
      this.statusType = ''
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },
    
    formatDate(dateString) {
      return new Date(dateString).toLocaleString('it-IT')
    }
  }
}
</script>


<template>
  <div class="file-upload-container">
    <div class="upload-section">
      <div class="section-header">
        <h2>📁 Caricamento File</h2>
        <p class="section-subtitle">Trascina i tuoi file qui o clicca per selezionare</p>
      </div>
      
      <!-- Area di caricamento file -->
      <div class="upload-area">
        <input
          type="file"
          id="fileInput"
          ref="fileInput"
          @change="handleFileSelect"
          style="display: none"
          multiple
        />
        
        <div
          class="drop-zone"
          :class="{ 
            'drag-over': isDragOver,
            'has-file': selectedFile
          }"
          @click="triggerFileInput"
          @drop="handleDrop"
          @dragover.prevent="isDragOver = true"
          @dragleave="isDragOver = false"
        >
          <div class="drop-zone-content">
            <div class="upload-icon" :class="{ 'pulse': isDragOver }">
              <svg v-if="!selectedFile" width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="currentColor" opacity="0.1"/>
                <path d="m14,2l6,6v12a2,2 0 0,1 -2,2H6a2,2 0 0,1 -2,-2V4a2,2 0 0,1 2,-2h8" stroke="currentColor" stroke-width="2" fill="none"/>
                <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" fill="none"/>
                <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
                <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2"/>
                <polyline points="10,9 9,9 8,9" stroke="currentColor" stroke-width="2"/>
              </svg>
              <svg v-else width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" fill="#22c55e" opacity="0.1"/>
                <path d="m9 12 2 2 4-4" stroke="#22c55e" stroke-width="2" fill="none"/>
              </svg>
            </div>
            
            <div class="drop-zone-text">
              <p v-if="!selectedFile" class="main-text">
                Clicca per selezionare un file
              </p>
              <p v-if="!selectedFile" class="sub-text">
                o trascinalo direttamente qui
              </p>
              <div v-else class="selected-file">
                <p class="file-name">{{ selectedFile.name }}</p>
                <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Progress bar -->
      <div v-if="isUploading" class="progress-container">
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: uploadProgress + '%' }"
          ></div>
        </div>
        <span class="progress-text">{{ uploadProgress }}%</span>
      </div>

      <!-- Pulsanti di azione -->
      <div class="action-buttons">
        <button
          @click="uploadFile"
          :disabled="!selectedFile || isUploading"
          class="btn btn-primary"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2"/>
            <polyline points="7 10 12 15 17 10" stroke="currentColor" stroke-width="2"/>
            <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2"/>
          </svg>
          {{ isUploading ? 'Caricamento...' : 'Carica File' }}
        </button>
        
        <button
          @click="clearSelection"
          :disabled="!selectedFile || isUploading"
          class="btn btn-secondary"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
            <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
          </svg>
          Cancella
        </button>
      </div>

      <!-- Messaggio di stato -->
      <transition name="status">
        <div v-if="statusMessage" :class="['status-message', statusType]">
          <div class="status-icon">
            <svg v-if="statusType === 'success'" width="24" height="24" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.1"/>
              <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
            </svg>
            <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.1"/>
              <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
              <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          {{ statusMessage }}
        </div>
      </transition>
    </div>

    <!-- Lista file caricati -->
    <div class="files-section">
      <div class="section-header">
        <h3>📋 File Caricati</h3>
      </div>

      <div v-if="uploadedFiles.length === 0" class="no-files">
        <div class="no-files-icon">📂</div>
        <p>Nessun file caricato</p>
        <small>I tuoi file caricati appariranno qui</small>
      </div>
      
      <div v-else class="files-grid">
        <transition-group name="file-item">
          <div
            v-for="file in uploadedFiles"
            :key="file.filename"
            class="file-card"
          >
            <div class="file-icon">📄</div>
            <div class="file-details">
              <h4 class="file-name">{{ file.filename }}</h4>
              <div class="file-meta">
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
                <span class="file-date">{{ formatDate(file.created) }}</span>
              </div>
            </div>
          </div>
        </transition-group>
      </div>
    </div>
  </div>
</template>

<style scoped>
.file-upload-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  box-sizing: border-box;
}

/* Responsive per dispositivi piccoli */
@media (max-width: 768px) {
  .file-upload-container {
    padding: 15px;
    min-height: calc(100vh - 30px);
  }
}

@media (max-width: 480px) {
  .file-upload-container {
    padding: 10px;
  }
}

.upload-section, .files-section {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 40px;
  margin-bottom: 30px;
  box-shadow: 
    0 20px 25px -5px rgba(0, 0, 0, 0.1),
    0 10px 10px -5px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

@media (max-width: 768px) {
  .upload-section, .files-section {
    padding: 25px;
    border-radius: 20px;
  }
}

@media (max-width: 480px) {
  .upload-section, .files-section {
    padding: 20px;
    border-radius: 16px;
  }
}

.section-header {
  text-align: center;
  margin-bottom: 30px;
}

.section-header h2 {
  color: #1f2937;
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: -0.025em;
}

@media (max-width: 768px) {
  .section-header h2 {
    font-size: 1.75rem;
  }
}

@media (max-width: 480px) {
  .section-header h2 {
    font-size: 1.5rem;
  }
}

.section-header h3 {
  color: #1f2937;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

@media (max-width: 768px) {
  .section-header h3 {
    font-size: 1.25rem;
  }
}

.section-subtitle {
  color: #6b7280;
  font-size: 1rem;
  margin: 0;
}

@media (max-width: 480px) {
  .section-subtitle {
    font-size: 0.9rem;
  }
}

.drop-zone {
  border: 3px dashed #e5e7eb;
  border-radius: 16px;
  padding: 60px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  position: relative;
  overflow: hidden;
}

@media (max-width: 768px) {
  .drop-zone {
    padding: 40px 15px;
    border-radius: 12px;
  }
}

@media (max-width: 480px) {
  .drop-zone {
    padding: 30px 10px;
  }
}

.drop-zone::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  transition: left 0.5s;
}

.drop-zone:hover::before {
  left: 100%;
}

.drop-zone:hover,
.drop-zone.drag-over {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -3px rgba(59, 130, 246, 0.2);
}

.drop-zone.has-file {
  border-color: #10b981;
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.upload-icon {
  color: #6b7280;
  transition: all 0.3s ease;
}

.drop-zone:hover .upload-icon,
.drop-zone.drag-over .upload-icon {
  color: #3b82f6;
  transform: scale(1.1);
}

.drop-zone.has-file .upload-icon {
  color: #10b981;
}

.pulse {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.drop-zone-text .main-text {
  color: #374151;
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

@media (max-width: 480px) {
  .drop-zone-text .main-text {
    font-size: 1.1rem;
  }
}

.drop-zone-text .sub-text {
  color: #6b7280;
  font-size: 1rem;
  margin: 0;
}

@media (max-width: 480px) {
  .drop-zone-text .sub-text {
    font-size: 0.9rem;
  }
}

.selected-file .file-name {
  color: #10b981;
  font-weight: 600;
  font-size: 1.1rem;
  margin: 0;
}

.selected-file .file-size {
  color: #6b7280;
  font-size: 0.9rem;
  margin: 0;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 15px;
  margin: 30px 0;
}

@media (max-width: 480px) {
  .progress-container {
    flex-direction: column;
    gap: 10px;
  }
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  border-radius: 4px;
  transition: width 0.3s ease;
  position: relative;
  overflow: hidden;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-text {
  color: #374151;
  font-weight: 600;
  min-width: 40px;
  text-align: right;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
  flex-wrap: wrap;
}

@media (max-width: 480px) {
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  min-width: 140px;
  justify-content: center;
}

@media (max-width: 480px) {
  .btn {
    width: 100%;
    max-width: 280px;
  }
}

.btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}

.btn:hover::before {
  left: 100%;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  box-shadow: 0 4px 15px 0 rgba(59, 130, 246, 0.4);
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px 0 rgba(59, 130, 246, 0.5);
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  color: #374151;
  box-shadow: 0 4px 15px 0 rgba(0, 0, 0, 0.1);
}

.btn-secondary:hover:not(:disabled) {
  background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px 0 rgba(0, 0, 0, 0.15);
}

.btn-secondary:disabled {
  background: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
}

.status-message {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  padding: 16px 20px;
  border-radius: 12px;
  font-weight: 500;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.status-message.success {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #065f46;
  border: 1px solid #10b981;
}

.status-message.error {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #991b1b;
  border: 1px solid #ef4444;
}

.status-icon {
  flex-shrink: 0;
}

/* Transizioni */
.status-enter-active, .status-leave-active {
  transition: all 0.3s ease;
}

.status-enter-from, .status-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.no-files {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.no-files-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.no-files p {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0 0 8px 0;
}

.no-files small {
  font-size: 1rem;
  opacity: 0.7;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

@media (max-width: 768px) {
  .files-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
}

.file-card {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 16px;
}

.file-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px 0 rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}

.file-icon {
  font-size: 32px;
  opacity: 0.7;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  color: #1f2937;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  word-break: break-word;
}

.file-meta {
  display: flex;
  gap: 12px;
  color: #6b7280;
  font-size: 0.875rem;
  flex-wrap: wrap;
}

@media (max-width: 480px) {
  .file-meta {
    flex-direction: column;
    gap: 4px;
  }
}

.file-item-enter-active, .file-item-leave-active {
  transition: all 0.5s ease;
}

.file-item-enter-from, .file-item-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.file-item-move {
  transition: transform 0.5s ease;
}
</style>