<script setup>
import { ref } from 'vue'
import axios from 'axios'

const selectedFile = ref(null)
const isUploading = ref(false)
const uploadProgress = ref(0)
const statusMessage = ref('')
const statusType = ref('')
const apiUrl = 'http://localhost:8000'

const triggerFileInput = () => fileInput.value.click()
const fileInput = ref(null)

const handleFileSelect = (e) => {
  selectedFile.value = e.target.files[0] || null
  clearStatus()
}

const uploadFile = async () => {
  if (!selectedFile.value) return

  isUploading.value = true
  uploadProgress.value = 0
  clearStatus()

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    await axios.post(`${apiUrl}/upload-file/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        uploadProgress.value = Math.round((event.loaded * 100) / event.total)
      }
    })
    showStatus('File caricato con successo!', 'success')
    selectedFile.value = null
  } catch (err) {
    showStatus('Errore durante il caricamento', 'error')
  } finally {
    isUploading.value = false
  }
}

const clearStatus = () => { statusMessage.value = ''; statusType.value = '' }
const showStatus = (msg, type) => { statusMessage.value = msg; statusType.value = type }

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const sizes = ['B','KB','MB','GB']
  const i = Math.floor(Math.log(bytes)/Math.log(1024))
  return (bytes/Math.pow(1024,i)).toFixed(1) + ' ' + sizes[i]
}
</script>

<template>
  <div class="file-upload">
    <input type="file" ref="fileInput" @change="handleFileSelect" hidden />

    <div class="drop-zone" @click="triggerFileInput">
      <p v-if="!selectedFile">Clicca qui per caricare un file!</p>
      <p v-if="!selectedFile">Formati supportati: [pdf, msg, eml, xls, xlsx, xlsm, xlsb, odf, ods, odt,
                                jpg, jpeg, png, gif, docx, csv, txt, text]</p>
      <p v-else>{{ selectedFile.name }} ({{ formatFileSize(selectedFile.size) }})</p>
    </div>

    <div v-if="isUploading" class="progress-bar">
      <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
      <span>{{ uploadProgress }}%</span>
    </div>

    <div class="actions">
      <button @click="uploadFile" :disabled="!selectedFile || isUploading">Carica</button>
      <button @click="selectedFile = null" :disabled="!selectedFile || isUploading">Cancella</button>
    </div>

    <div v-if="uploadProgress === 100 && isUploading" class="status">
      Sto caricando il file nel db...
    </div>
    <div v-if="statusMessage" :class="['status', statusType]">{{ statusMessage }}</div>
  </div>
</template>

<style scoped>
.file-upload {
  display:flex; 
  flex-direction:column; 
  gap:12px; width:100%; 
  max-width:400px; 
  margin:0 auto;
  padding-top: 40px;
  font-family: sans-serif; 
  color:#fff;
}

.drop-zone {
  padding:40px; 
  border:2px dashed #666; 
  border-radius:8px; 
  text-align:center; 
  cursor:pointer;
  background:#2a2b35; 
  transition:0.3s;
}

.drop-zone:hover { 
  border-color:#0d6efd; 
  background:#3b3c45; 
}

.progress-bar { 
  position:relative; 
  height:8px; 
  background:#444; 
  border-radius:4px; 
  overflow:hidden; 
}

.progress-fill { 
  height:100%; 
  background:#0d6efd; 
  transition:width 0.3s; 
}

.actions { 
  display:flex; 
  gap:10px; 
  justify-content:center; 
}

button {
  padding:8px 16px; 
  border:none; 
  border-radius:6px; 
  cursor:pointer; 
  background:#0d6efd; 
  color:#fff;
}

button:disabled { background:#555; cursor:not-allowed; }

/* Status messages */
.status { text-align:center; padding:8px; border-radius:6px; }
.status.success { background:#22c55e; color:#fff; }
.status.error { background:#ef4444; color:#fff; }

</style>
