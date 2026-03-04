<template>
  <div class="chat-page">
    <el-container>
      <el-header>
        <div class="header-content">
          <el-button @click="$router.push('/')" icon="ArrowLeft" circle></el-button>
          <h1>{{ sceneName ? `Scene: ${sceneName}` : 'Free Practice' }}</h1>
        </div>
      </el-header>
      <el-main>
        <el-row :gutter="20">
          <!-- Left: Chat Area -->
          <el-col :span="14">
            <el-card class="chat-card">
              <template #header>
                <div class="card-header">
                  <span>💬 Conversation</span>
                  <el-button @click="clearHistory" size="small">Clear History</el-button>
                </div>
              </template>
              
              <!-- Message List -->
              <div class="message-list" ref="messageList">
                <div 
                  v-for="(msg, index) in messages" 
                  :key="index" 
                  class="message"
                  :class="msg.role"
                >
                  <div class="avatar">
                    <el-avatar :icon="msg.role === 'user' ? 'User' : 'Service'" />
                  </div>
                  <div class="content">
                    <div class="text">{{ msg.text }}</div>
                    <div v-if="msg.audio" class="audio-player">
                      <audio :src="msg.audio" controls></audio>
                    </div>
                  </div>
                </div>
                
                <!-- Loading -->
                <div v-if="isLoading" class="message ai">
                  <div class="avatar">
                    <el-avatar icon="Service" />
                  </div>
                  <div class="content">
                    <el-skeleton :rows="2" animated />
                  </div>
                </div>
              </div>
              
              <!-- Input Area -->
              <div class="input-area">
                <el-input
                  v-model="inputText"
                  placeholder="Type a message or click mic to speak..."
                  @keyup.enter="sendText"
                  :disabled="isRecording"
                >
                  <template #append>
                    <el-button 
                      @click="toggleRecording" 
                      :type="isRecording ? 'danger' : 'primary'"
                      :icon="isRecording ? 'VideoPause' : 'Microphone'"
                    >
                      {{ isRecording ? 'Stop' : 'Record' }}
                    </el-button>
                    <el-button type="success" @click="sendText">Send</el-button>
                  </template>
                </el-input>
              </div>
            </el-card>
          </el-col>
          
          <!-- Right: Settings -->
          <el-col :span="10">
            <!-- Scene Hints -->
            <el-card v-if="sceneData" class="scene-hints-card" style="margin-bottom: 20px;">
              <template #header>
                <div class="card-header">
                  <span>💡 Scene Hints</span>
                </div>
              </template>
              <div class="scene-hints">
                <p><strong>Your Role:</strong> {{ sceneData.userRole.name }}</p>
                <p><strong>AI Role:</strong> {{ sceneData.aiRole.name }}</p>
                <el-divider content-position="left">Suggested Topics</el-divider>
                <el-tag v-for="topic in sceneData.suggestedTopics" :key="topic" style="margin: 2px;">{{ topic }}</el-tag>
              </div>
            </el-card>

            <!-- Voice Clone -->
            <el-card class="voice-clone-card" style="margin-bottom: 20px;">
              <template #header>
                <div class="card-header">
                  <span>🎵 Voice Clone</span>
                </div>
              </template>
              
              <el-upload
                ref="uploadRef"
                drag
                action="#"
                :http-request="uploadVoice"
                :before-upload="beforeUpload"
                :on-success="handleUploadSuccess"
                :on-error="handleUploadError"
                accept=".mp3,.wav,.flac"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  Drag audio here or <em>click to upload</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    MP3/WAV/FLAC, max 10MB, 10s~5min
                  </div>
                </template>
              </el-upload>
              
              <el-input
                v-model="newRoleName"
                placeholder="Name this voice (e.g. British Teacher)"
                style="margin-top: 15px;"
                :disabled="isUploading"
              >
                <template #append>
                  <el-button type="primary" @click="createRole" :loading="isUploading">
                    Create
                  </el-button>
                </template>
              </el-input>
            </el-card>
            
            <!-- Role List -->
            <el-card class="roles-card" style="margin-bottom: 20px;">
              <template #header>
                <div class="card-header">
                  <span>🎭 My Voices</span>
                  <el-button size="small" @click="loadRoles" circle>
                    <el-icon><refresh /></el-icon>
                  </el-button>
                </div>
              </template>
              
              <el-empty v-if="roles.length === 0" description="No custom voices yet" />
              
              <div v-else class="role-list">
                <div
                  v-for="role in roles"
                  :key="role.id"
                  class="role-item"
                  :class="{ active: selectedRoleId === role.id }"
                  @click="selectRole(role.id)"
                >
                  <div class="role-info">
                    <div class="role-name">{{ role.name }}</div>
                    <div class="role-meta">
                      <el-tag size="small" type="info">{{ role.language || 'Unknown' }}</el-tag>
                      <span class="role-time">{{ formatDate(role.created_at) }}</span>
                    </div>
                  </div>
                  <div class="role-actions">
                    <el-button
                      size="small"
                      type="primary"
                      @click.stop="testVoice(role)"
                      plain
                    >
                      Test
                    </el-button>
                    <el-button
                      size="small"
                      type="danger"
                      @click.stop="deleteRole(role.id)"
                      plain
                      circle
                    >
                      <el-icon><delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>
            </el-card>
            
            <!-- Settings -->
            <el-card class="settings-card">
              <template #header>
                <div class="card-header">
                    <span>⚙️ Settings</span>
                    <el-tag :type="connectionStatus === 'connected' ? 'success' : 'danger'">
                        {{ connectionStatus === 'connected' ? 'Connected' : 'Disconnected' }}
                    </el-tag>
                </div>
              </template>
              
              <el-form label-position="top">
                <el-form-item label="LLM Provider">
                  <el-radio-group v-model="settings.provider" @change="onProviderChange">
                    <el-radio label="aliyun">Qwen (Cloud)</el-radio>
                    <el-radio label="ollama">Ollama (Local)</el-radio>
                  </el-radio-group>
                </el-form-item>
                
                <el-form-item label="LLM Model">
                  <el-select v-model="settings.model" placeholder="Select model" style="width: 100%;">
                    <el-option v-for="m in currentModels" :key="m" :label="m" :value="m" />
                  </el-select>
                </el-form-item>

                <el-form-item label="Voice Source">
                  <el-radio-group v-model="voiceSourceType">
                    <el-radio label="system">System Voice</el-radio>
                    <el-radio label="custom">Custom Voice</el-radio>
                  </el-radio-group>
                </el-form-item>
                
                <el-form-item v-if="voiceSourceType === 'system'" label="System Voice">
                  <el-select v-model="settings.voice" placeholder="Select voice" style="width: 100%;">
                    <el-option label="龙安洋 / Longanyang (Male, zh+en)" value="longanyang" />
                    <el-option label="龙安欢 / Longanhuan (Female, zh+en)" value="longanhuan" />
                  </el-select>
                </el-form-item>
                
                <el-form-item v-if="voiceSourceType === 'custom'" label="Custom Voice">
                  <el-select
                    v-model="selectedRoleId"
                    placeholder="Select voice"
                    style="width: 100%;"
                    @change="onRoleChange"
                  >
                    <el-option
                      v-for="role in roles"
                      :key="role.id"
                      :label="role.name"
                      :value="role.id"
                    />
                  </el-select>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, reactive, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Refresh, Delete, ArrowLeft } from '@element-plus/icons-vue'
import axios from 'axios'

export default {
  name: 'ChatPage',
  components: {
    UploadFilled,
    Refresh,
    Delete,
    ArrowLeft
  },
  setup() {
    const route = useRoute()
    const sceneId = route.query.scene
    const sceneName = ref('')
    const sceneData = ref(null)

    const API_BASE = 'http://127.0.0.1:8000/api'

    const messages = ref([])
    const inputText = ref('')
    const isLoading = ref(false)
    const isRecording = ref(false)
    const connectionStatus = ref('disconnected')
    const messageList = ref(null)
    
    const settings = reactive({
      provider: 'aliyun',
      model: 'qwen3.5-flash',
      voice: 'longanyang'
    })
    
    const currentModels = ref([])
    let allModels = {
      aliyun: [],
      ollama: []
    }
    
    // Load models from API
    const loadModels = async () => {
      try {
        const res = await axios.get(`${API_BASE}/chat/models`)
        allModels = res.data.providers
        updateCurrentModels()
      } catch (err) {
        console.error('Failed to load models', err)
      }
    }
    
    const updateCurrentModels = () => {
      currentModels.value = allModels[settings.provider] || []
      if (!currentModels.value.includes(settings.model) && currentModels.value.length > 0) {
        settings.model = currentModels.value[0]
      }
    }
    
    const onProviderChange = () => {
      updateCurrentModels()
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
          type: 'config',
          provider: settings.provider,
          model: settings.model
        }))
      }
    }
    
    let websocket = null
    let mediaRecorder = null
    let audioChunks = []
    
    // ===== Buffered Audio Playback (5-second buffer) =====
    // Instead of playing tiny chunks immediately (which causes stuttering),
    // we buffer audio for 5 seconds then play it all at once for smooth output.
    let pendingAudioChunks = []     // current round's buffered audio
    let bufferTimer = null          // 5-second delay timer
    let audioPlaybackStarted = false // whether we've started playing this round
    let currentPlaybackAudio = null  // the currently playing Audio element
    
    const AUDIO_BUFFER_DELAY_MS = 5000  // 5 seconds
    
    /**
     * Called when an audio chunk arrives from WebSocket.
     * Collects chunks and starts a 5s timer on the first one.
     */
    const bufferAudioChunk = (blob) => {
      pendingAudioChunks.push(blob)
      
      // Start 5-second timer on first chunk
      if (!bufferTimer && !audioPlaybackStarted) {
        console.log('[Audio] First chunk received, starting 5s buffer...')
        bufferTimer = setTimeout(() => {
          bufferTimer = null
          playBufferedAudio()
        }, AUDIO_BUFFER_DELAY_MS)
      }
    }
    
    /**
     * Merge all buffered chunks into one blob and play smoothly.
     */
    const playBufferedAudio = () => {
      if (audioPlaybackStarted || pendingAudioChunks.length === 0) return
      
      audioPlaybackStarted = true
      console.log(`[Audio] Playing ${pendingAudioChunks.length} buffered chunks`)
      
      const combinedBlob = new Blob(pendingAudioChunks, { type: 'audio/mp3' })
      const audioUrl = URL.createObjectURL(combinedBlob)
      
      currentPlaybackAudio = new Audio(audioUrl)
      currentPlaybackAudio.onended = () => {
        URL.revokeObjectURL(audioUrl)
        currentPlaybackAudio = null
      }
      currentPlaybackAudio.onerror = () => {
        URL.revokeObjectURL(audioUrl)
        currentPlaybackAudio = null
      }
      currentPlaybackAudio.play().catch((e) => {
        console.warn('[Audio] Playback failed:', e)
      })
    }
    
    /**
     * Called when a round completes. If buffer timer hasn't fired yet,
     * cancel it and play immediately (all audio is ready).
     */
    const flushAudioBuffer = () => {
      if (bufferTimer) {
        clearTimeout(bufferTimer)
        bufferTimer = null
      }
      if (!audioPlaybackStarted) {
        playBufferedAudio()
      }
    }
    
    /**
     * Reset audio state for the next round of conversation.
     */
    const resetAudioState = () => {
      pendingAudioChunks = []
      audioPlaybackStarted = false
      if (bufferTimer) {
        clearTimeout(bufferTimer)
        bufferTimer = null
      }
    }
    
    // Voice clone
    const roles = ref([])
    const newRoleName = ref('')
    const isUploading = ref(false)
    const uploadedFile = ref(null)
    const voiceSourceType = ref('system')
    const selectedRoleId = ref('')
    const selectedVoiceId = ref('')
    
    const getActiveVoice = () => {
        return voiceSourceType.value === 'custom' && selectedVoiceId.value 
            ? selectedVoiceId.value 
            : settings.voice;
    }

    const loadSceneInfo = async () => {
      if (sceneId) {
        try {
          const res = await axios.get(`${API_BASE}/scenes/${sceneId}`)
          sceneData.value = res.data
          sceneName.value = res.data.name
        } catch (err) {
          console.error('Failed to load scene info', err)
        }
      }
    }

    const connectWebSocket = () => {
      const wsUrl = `ws://127.0.0.1:8000/api/ws/chat`
      websocket = new WebSocket(wsUrl)
      
      websocket.onopen = () => {
        connectionStatus.value = 'connected'
        console.log('WebSocket connected')
        
        // Send initial config
        const config = {
          type: 'config',
          voice: getActiveVoice(),
          provider: settings.provider,
          model: settings.model,
        }
        if (sceneId) {
          config.scene_id = sceneId
        }
        websocket.send(JSON.stringify(config))
        
        // Add AI opening line for scene mode
        if (sceneData.value && sceneData.value.aiRole && sceneData.value.aiRole.openingLine) {
          messages.value.push({ role: 'ai', text: sceneData.value.aiRole.openingLine })
        }
      }
      
      websocket.onclose = () => {
        connectionStatus.value = 'disconnected'
        console.log('WebSocket disconnected')
        setTimeout(connectWebSocket, 3000)
      }
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      
      websocket.onmessage = (event) => {
        if (event.data instanceof Blob) {
          // ===== TTS Audio Chunk → Buffer for delayed playback =====
          bufferAudioChunk(event.data)
          
          // Also store for the message's replay audio player
          const lastMsg = messages.value[messages.value.length - 1]
          if (lastMsg && lastMsg.role === 'ai') {
            if (!lastMsg._audioChunks) {
              lastMsg._audioChunks = []
            }
            lastMsg._audioChunks.push(event.data)
            
            // Update the combined audio URL for the inline player
            const combinedBlob = new Blob(lastMsg._audioChunks, { type: 'audio/mp3' })
            if (lastMsg.audio) {
              URL.revokeObjectURL(lastMsg.audio)
            }
            lastMsg.audio = URL.createObjectURL(combinedBlob)
          }
        } else {
          const data = JSON.parse(event.data)
          
          if (data.type === 'stt_result') {
            // Speech recognized → show user message
            messages.value.push({ role: 'user', text: data.text })
            isLoading.value = false
            scrollToBottom()
            
          } else if (data.type === 'llm_chunk') {
            // Streaming LLM chunk → append to last AI message (typewriter effect)
            const lastMsg = messages.value[messages.value.length - 1]
            if (lastMsg && lastMsg.role === 'ai' && !lastMsg._done) {
              lastMsg.text += data.text
            } else {
              // First chunk → create new AI message + reset audio state
              resetAudioState()
              messages.value.push({ 
                role: 'ai', 
                text: data.text, 
                audio: null,
                _done: false,
                _audioChunks: [],
              })
            }
            isLoading.value = false
            scrollToBottom()
            
          } else if (data.type === 'llm_done') {
            // LLM finished generating
            const lastMsg = messages.value[messages.value.length - 1]
            if (lastMsg && lastMsg.role === 'ai') {
              lastMsg._done = true
            }
            
          } else if (data.type === 'llm_response') {
            // Legacy: full LLM response (fallback compatibility)
            messages.value.push({ role: 'ai', text: data.text, audio: null })
            scrollToBottom()
            
          } else if (data.type === 'complete') {
            // ===== Round complete → flush audio buffer and play =====
            flushAudioBuffer()
            isLoading.value = false
            scrollToBottom()
            
          } else if (data.type === 'error') {
            ElMessage.error(data.message)
            isLoading.value = false
            
          } else if (data.type === 'history_cleared') {
            ElMessage.success('History cleared')
          }
        }
      }
    }
    
    const scrollToBottom = () => {
      nextTick(() => {
        if (messageList.value) {
          messageList.value.scrollTop = messageList.value.scrollHeight
        }
      })
    }
    
    const sendText = () => {
      if (!inputText.value.trim() || !websocket) return
      
      messages.value.push({ role: 'user', text: inputText.value })
      
      websocket.send(JSON.stringify({
        type: 'message',
        content: inputText.value,
        voice: getActiveVoice(),
        provider: settings.provider,
        model: settings.model,
      }))
      
      inputText.value = ''
      isLoading.value = true
      scrollToBottom()
    }
    
    const clearHistory = () => {
      messages.value = []
      
      // Stop any currently playing audio and reset buffer
      if (currentPlaybackAudio) {
        currentPlaybackAudio.pause()
        currentPlaybackAudio = null
      }
      resetAudioState()
      
      if (websocket) {
        websocket.send(JSON.stringify({ type: 'clear_history' }))
      }
      if (sceneData.value && sceneData.value.aiRole && sceneData.value.aiRole.openingLine) {
        messages.value.push({ role: 'ai', text: sceneData.value.aiRole.openingLine })
      }
    }
    
    const toggleRecording = async () => {
      if (isRecording.value) {
        mediaRecorder.stop()
        isRecording.value = false
      } else {
        try {
          // Send current config before recording
          if (websocket && websocket.readyState === WebSocket.OPEN) {
             websocket.send(JSON.stringify({ 
               type: 'config', 
               voice: getActiveVoice(),
               provider: settings.provider,
               model: settings.model,
             }))
          }

          const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
              channelCount: 1,
              sampleRate: 16000,
            }
          })
          
          // Use webm format (browser default, whisper can handle it)
          mediaRecorder = new MediaRecorder(stream, {
            mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
              ? 'audio/webm;codecs=opus' 
              : 'audio/webm'
          })
          audioChunks = []
          
          mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
              audioChunks.push(event.data)
            }
          }
          
          mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
            if (websocket && websocket.readyState === WebSocket.OPEN) {
              websocket.send(audioBlob)
              isLoading.value = true
            }
            
            // Stop media stream tracks
            stream.getTracks().forEach(track => track.stop())
          }
          
          mediaRecorder.start()
          isRecording.value = true
          ElMessage.info('Recording...')
        } catch (error) {
          ElMessage.error('Cannot access microphone: ' + error.message)
        }
      }
    }
    
    // --- Voice Clone ---
    
    const beforeUpload = (file) => {
      const isValidType = ['.mp3', '.wav', '.flac'].includes(
        file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
      )
      const isValidSize = file.size / 1024 / 1024 < 10
      
      if (!isValidType) {
        ElMessage.error('Only MP3/WAV/FLAC supported')
        return false
      }
      if (!isValidSize) {
        ElMessage.error('File must be under 10MB')
        return false
      }
      
      uploadedFile.value = file
      return true
    }
    
    const uploadVoice = async (options) => {
      options.onSuccess()
    }
    
    const handleUploadSuccess = () => {}
    const handleUploadError = () => {}

    const createRole = async () => {
      if (!uploadedFile.value) {
        ElMessage.warning('Please upload an audio file first')
        return
      }
      if (!newRoleName.value.trim()) {
        ElMessage.warning('Please enter a voice name')
        return
      }
      
      isUploading.value = true
      
      try {
        const formData = new FormData()
        formData.append('file', uploadedFile.value)
        formData.append('name', newRoleName.value)
        
        await axios.post(`${API_BASE}/voice/clone`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        ElMessage.success('Voice cloned successfully!')
        newRoleName.value = ''
        uploadedFile.value = null
        
        await loadRoles()
        
      } catch (error) {
        ElMessage.error('Voice clone failed: ' + (error.response?.data?.detail || error.message))
      } finally {
        isUploading.value = false
      }
    }
    
    const loadRoles = async () => {
      try {
        const response = await axios.get(`${API_BASE}/voice/roles`)
        roles.value = response.data.roles || []
      } catch (error) {
        console.error('Failed to load roles:', error)
      }
    }
    
    const selectRole = (roleId) => {
      selectedRoleId.value = roleId
      const role = roles.value.find(r => r.id === roleId)
      if (role) {
        selectedVoiceId.value = role.voice_id
        voiceSourceType.value = 'custom'
      }
    }
    
    const onRoleChange = (roleId) => {
      const role = roles.value.find(r => r.id === roleId)
      if (role) {
        selectedVoiceId.value = role.voice_id
      }
    }
    
    const deleteRole = async (roleId) => {
      try {
        await ElMessageBox.confirm('Delete this voice?', 'Confirm', {
          type: 'warning'
        })
        
        await axios.delete(`${API_BASE}/voice/roles/${roleId}`)
        ElMessage.success('Deleted')
        
        if (selectedRoleId.value === roleId) {
          selectedRoleId.value = ''
          selectedVoiceId.value = ''
        }
        
        await loadRoles()
        
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('Delete failed: ' + error.message)
        }
      }
    }
    
    const testVoice = async (role) => {
      try {
        const formData = new FormData()
        formData.append('text', 'Hello, this is a test of my custom voice.')
        
        const response = await axios.post(
          `${API_BASE}/voice/roles/${role.id}/test`,
          formData,
          { responseType: 'blob' }
        )
        
        const audioUrl = URL.createObjectURL(response.data)
        const audio = new Audio(audioUrl)
        audio.play()
        
      } catch (error) {
        ElMessage.error('Test failed: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    onMounted(async () => {
      await loadSceneInfo()
      connectWebSocket()
      loadRoles()
      loadModels()
    })
    
    onUnmounted(() => {
      if (websocket) {
        websocket.close()
      }
      // Clean up audio resources
      if (currentPlaybackAudio) {
        currentPlaybackAudio.pause()
        currentPlaybackAudio = null
      }
      resetAudioState()
    })
    
    return {
      sceneName,
      sceneData,
      messages,
      inputText,
      isLoading,
      isRecording,
      connectionStatus,
      messageList,
      settings,
      currentModels,
      sendText,
      clearHistory,
      toggleRecording,
      onProviderChange,
      
      roles,
      newRoleName,
      isUploading,
      voiceSourceType,
      selectedRoleId,
      beforeUpload,
      uploadVoice,
      handleUploadSuccess,
      handleUploadError,
      createRole,
      loadRoles,
      selectRole,
      onRoleChange,
      deleteRole,
      testVoice,
      formatDate
    }
  }
}
</script>

<style scoped>
.chat-page {
  height: 100vh;
}

.el-header {
  background-color: #409EFF;
  color: white;
  line-height: 60px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
}

.el-main {
  padding: 20px;
  background-color: #f5f7fa;
}

.chat-card {
  height: calc(100vh - 140px);
}

.settings-card {
  max-height: calc(100vh - 140px);
  overflow-y: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.message-list {
  height: calc(100vh - 300px);
  overflow-y: auto;
  padding: 10px;
}

.message {
  display: flex;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message .avatar {
  flex-shrink: 0;
}

.message .content {
  max-width: 70%;
  margin: 0 10px;
}

.message.user .content {
  text-align: right;
}

.message .text {
  background-color: #f0f2f5;
  padding: 10px 15px;
  border-radius: 8px;
  display: inline-block;
  white-space: pre-wrap;
  word-break: break-word;
}

.message.user .text {
  background-color: #409EFF;
  color: white;
}

.audio-player {
  margin-top: 10px;
}

.input-area {
  margin-top: 20px;
}

/* Voice clone styles */
.voice-clone-card .el-upload {
  width: 100%;
}

.voice-clone-card .el-upload-dragger {
  padding: 20px;
}

.role-list {
  max-height: 400px;
  overflow-y: auto;
}

.role-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.role-item:hover {
  border-color: #409EFF;
  background-color: #ecf5ff;
}

.role-item.active {
  border-color: #409EFF;
  background-color: #ecf5ff;
}

.role-info {
  flex: 1;
}

.role-name {
  font-weight: bold;
  margin-bottom: 5px;
}

.role-meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.role-time {
  color: #999;
  font-size: 12px;
}

.role-actions {
  display: flex;
  gap: 5px;
}
</style>