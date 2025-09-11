<template>
  <div class="file-upload-container">
    <div class="upload-section">
      <h2>Caricamento File</h2>
      
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
          :class="{ 'drag-over': isDragOver }"
          @click="triggerFileInput"
          @drop="handleDrop"
          @dragover.prevent="isDragOver = true"
          @dragleave="isDragOver = false"
        >
          <div class="upload-icon">📁</div>
          <p v-if="!selectedFile">
            Clicca per selezionare un file o trascinalo qui
          </p>
          <p v-else class="selected-file">
            File selezionato: {{ selectedFile.name }}
          </p>
        </div>
      </div>

      <!-- Pulsante di caricamento -->
      <div class="action-buttons">
        <button
          @click="uploadFile"
          :disabled="!selectedFile || isUploading"
          class="upload-btn"
        >
          {{ isUploading ? 'Caricamento...' : 'Carica File' }}
        </button>
        
        <button
          @click="clearSelection"
          :disabled="!selectedFile || isUploading"
          class="clear-btn"
        >
          Cancella
        </button>
      </div>

      <!-- Progress bar -->
      <div v-if="isUploading" class="progress-bar">
        <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
      </div>

      <!-- Messaggio di stato -->
      <div v-if="statusMessage" :class="['status-message', statusType]">
        {{ statusMessage }}
      </div>
    </div>

    <!-- Lista file caricati -->
    <div class="files-section">
      <h3>File Caricati</h3>
      <!--<button @click="loadFiles" class="refresh-btn">Aggiorna Lista</button>-->

      <div v-if="uploadedFiles.length === 0" class="no-files">
        Nessun file caricato
      </div>
      
      <div v-else class="files-list">
        <div
          v-for="file in uploadedFiles"
          :key="file.filename"
          class="file-item"
        >
          <div class="file-info">
            <strong>{{ file.filename }}</strong>
            <small>{{ formatFileSize(file.size) }} - {{ formatDate(file.created) }}</small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

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
  
  /*mounted() {
    this.loadFiles()
  },*/
  
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
        
        this.showStatus('File caricato con successo!', 'success')
        this.clearSelection()
        //this.loadFiles() // Ricarica la lista dei file
        
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
    
    /*async loadFiles() {
      try {
        const response = await axios.get(`${this.apiUrl}/files/`)
        this.uploadedFiles = response.data.files
      } catch (error) {
        console.error('Errore nel caricamento dei file:', error)
        this.showStatus('Errore nel caricamento della lista file', 'error')
      }
    },*/
    
    showStatus(message, type) {
      this.statusMessage = message
      this.statusType = type
      
      // Cancella il messaggio dopo 5 secondi
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

<style scoped>
.file-upload-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.upload-section {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.upload-section h2 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.drop-zone {
  border: 3px dashed #007bff;
  border-radius: 10px;
  padding: 60px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.drop-zone:hover,
.drop-zone.drag-over {
  border-color: #0056b3;
  background: #f0f8ff;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.selected-file {
  color: #007bff;
  font-weight: bold;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
}

.upload-btn, .clear-btn, .refresh-btn {
  padding: 12px 30px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s;
}

.upload-btn {
  background: #007bff;
  color: white;
}

.upload-btn:hover:not(:disabled) {
  background: #0056b3;
}

.upload-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.clear-btn {
  background: #6c757d;
  color: white;
}

.clear-btn:hover:not(:disabled) {
  background: #545b62;
}

.refresh-btn {
  background: #28a745;
  color: white;
  margin-bottom: 20px;
}

.refresh-btn:hover {
  background: #218838;
}

.progress-bar {
  width: 100%;
  height: 10px;
  background: #e9ecef;
  border-radius: 5px;
  margin-top: 20px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #007bff;
  transition: width 0.3s ease;
}

.status-message {
  margin-top: 20px;
  padding: 15px;
  border-radius: 5px;
  text-align: center;
  font-weight: bold;
}

.status-message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.files-section {
  background: white;
  border-radius: 10px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.files-section h3 {
  color: #333;
  margin-bottom: 20px;
}

.no-files {
  text-align: center;
  color: #6c757d;
  font-style: italic;
  padding: 40px;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.file-item {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 5px;
  border-left: 4px solid #007bff;
}

.file-info strong {
  display: block;
  margin-bottom: 5px;
  color: #333;
}

.file-info small {
  color: #6c757d;
}
</style>