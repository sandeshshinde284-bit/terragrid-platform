<template>
  <div class="ask-map-screen">
    <Header />

    <div class="chat-container">
      <div v-if="!appStore.isBackendMockModeEnabled" class="phase2-center-container">
        <div class="phase2-card glass-panel">
          <div class="phase2-icon">🤖</div>
          <div class="phase2-tag">PHASE 2 ROADMAP</div>
          <h2>Conversational GIS Intelligence</h2>
          <p>
            The natural language AI assistant (powered by Gemini & RAG) for conversational disaster querying is scheduled for delivery in <strong>Phase 2</strong>.
          </p>
          <div class="phase2-note">
            Real-time multi-hazard disaster monitoring and AI decision support are fully operational on the <strong>Dashboard</strong> and <strong>Incidents</strong> screens.
          </div>
          <router-link to="/" class="return-dashboard-btn">
            ← Return to Live Dashboard
          </router-link>
        </div>
      </div>

      <template v-else>
        <div class="messages-area">
          <div class="messages-list">
            <div class="message assistant-message">
              <div class="message-content">
                <p>👋 {{ $t('askTheMap.title') }}</p>
                <p>{{ $t('askTheMap.placeholder') }}</p>
              </div>
              <span class="timestamp">{{ currentTime }}</span>
            </div>

            <div class="examples-section">
              <p class="examples-label">{{ $t('askTheMap.examples') }}</p>
              <div class="example-buttons">
                <button 
                  v-for="(example, idx) in examples" 
                  :key="idx"
                  class="example-btn glass-panel"
                  @click="sendExample(example)"
                >
                  {{ example }}
                </button>
              </div>
            </div>

            <div v-for="msg in messages" :key="msg.id" :class="['message', msg.type + '-message']">
              <div class="message-content">{{ msg.text }}</div>
              <span class="timestamp">{{ msg.time }}</span>
            </div>

            <div v-if="isLoading" class="message assistant-message">
              <div class="message-content typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <div class="input-area glass-panel">
          <input 
            v-model="userInput"
            type="text"
            :placeholder="$t('askTheMap.placeholder')"
            class="chat-input"
            @keyup.enter="sendMessage"
            :disabled="isLoading"
          />
          <button 
            @click="sendMessage"
            class="send-btn"
            :disabled="!userInput.trim() || isLoading"
            title="Send message"
          >
            {{ $t('askTheMap.send') }} →
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import Header from '@/components/organisms/Header.vue'
import { useEventsStore, useAppStore } from '@/stores'

const eventsStore = useEventsStore()
const appStore = useAppStore()
const userInput = ref('')
const isLoading = ref(false)
const messagesListRef = ref<HTMLDivElement | null>(null)

interface Message {
  id: string
  type: 'user' | 'assistant'
  text: string
  time: string
}

const messages = ref<Message[]>([])

const currentTime = computed(() => {
  const now = new Date()
  return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
})

const examples = [
  'How many people are in evacuation zones?',
  'Show me safe routes for emergency response',
  'What is the threat level in this area?',
  'Which incidents are accelerating fastest?',
]

const qaDatabase = [
  {
    query: 'evacuation',
    response: 'There are currently 8 active evacuation zones affecting approximately 245,000 people. Zone A in Santa Rosa is at 95% capacity. Recommended routes are available through the Map screen.'
  },
  {
    query: 'safe route',
    response: 'Primary safe routes: Route 101 North (priority), Highway 37 East, and local roads through residential areas. All routes are monitored and updated every 15 minutes. Current travel times: 40-60 minutes to safe zone.'
  },
  {
    query: 'threat',
    response: 'Current threat assessment: CRITICAL in 3 zones, HIGH in 5 zones, MEDIUM in 12 zones. The Landslide incident near San Jose poses the highest risk with a 87/100 threat score. Trend: accelerating at +2.1 km²/h.'
  },
  {
    query: 'accelerating',
    response: 'Fastest-growing incidents: Landslide (+2.1 km²/h), Fire near Santa Cruz (+1.8 km²/h), Flood in Russian River (+1.5 km²/h). Estimated growth in next 6 hours: 50-80 km² additional coverage. Forecasted affected population: 380,000+.'
  },
  {
    query: 'population',
    response: 'Total affected population: 285,000. Breakdown: 120,000 in active danger zones, 165,000 in precautionary zones. Vulnerable groups: 45,000 elderly, 38,000 children. Evacuation rate: 72% complete.'
  },
  {
    query: 'forecast',
    response: '6-hour forecast: Area growth +35-45 km², Population at risk +60,000, New secondary incidents possible +2-3. Confidence: 84%. Based on historical patterns and current trend analysis.'
  },
]

const findResponse = (query: string): string => {
  const lowerQuery = query.toLowerCase()
  
  for (const qa of qaDatabase) {
    if (lowerQuery.includes(qa.query)) {
      return qa.response
    }
  }
  
  return `I found your question: "${query}". Based on current disaster data: The area is experiencing ${eventsStore.allIncidents.length} active incidents affecting ${eventsStore.totalAffectedPopulation.toLocaleString()} people across ${eventsStore.totalAffectedArea.toFixed(0)} km². Please check the Dashboard for real-time updates.`
}

const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return
  
  const userMessage: Message = {
    id: Date.now().toString(),
    type: 'user',
    text: userInput.value,
    time: formatTime(new Date()),
  }
  
  messages.value.push(userMessage)
  userInput.value = ''
  isLoading.value = true
  
  await nextTick()
  if (messagesListRef.value) {
    messagesListRef.value.scrollTop = messagesListRef.value.scrollHeight
  }
  
  // Simulate processing delay
  setTimeout(() => {
    const response = findResponse(userMessage.text)
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      text: response,
      time: formatTime(new Date()),
    }
    
    messages.value.push(assistantMessage)
    isLoading.value = false
    
    nextTick(() => {
      if (messagesListRef.value) {
        messagesListRef.value.scrollTop = messagesListRef.value.scrollHeight
      }
    })
  }, 800)
}

const sendExample = (example: string) => {
  userInput.value = example
  nextTick(() => {
    sendMessage()
  })
}

onMounted(() => {
  if (eventsStore.allIncidents.length === 0) {
    // [STRICT LIVE MODE] eventsStore.initMockData()
  }
})
</script>

<style scoped>
.ask-map-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.chat-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  gap: 16px;
}

.messages-area {
  flex: 1;
  min-height: 0;
  background: transparent;
  border-radius: 8px;
  overflow: hidden;
}

.messages-list {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  flex-direction: column;
  gap: 4px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  align-self: flex-end;
  max-width: 70%;
}

.user-message .message-content {
  background: var(--accent-cyan-soft);
  border: 1px solid var(--accent-cyan);
  border-radius: 8px;
  padding: 12px 16px;
  color: var(--text-primary);
  word-wrap: break-word;
}

.assistant-message {
  align-self: flex-start;
  max-width: 70%;
}

.assistant-message .message-content {
  background: rgba(30, 64, 175, 0.1);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  padding: 12px 16px;
  color: var(--text-primary);
}

.message-content p {
  margin: 0;
  line-height: 1.5;
}

.message-content p:not(:last-child) {
  margin-bottom: 8px;
}

.message-content.typing {
  display: flex;
  gap: 4px;
  align-items: center;
  height: 24px;
}

.message-content.typing span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-secondary);
  animation: bounce 1.4s infinite;
}

.message-content.typing span:nth-child(2) {
  animation-delay: 0.2s;
}

.message-content.typing span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-10px);
  }
}

.timestamp {
  font-size: 11px;
  color: var(--text-muted);
  padding: 0 4px;
}

.user-message .timestamp {
  text-align: right;
}

.examples-section {
  align-self: center;
  width: 100%;
  text-align: center;
  padding: 20px 0;
}

.examples-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.example-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  justify-items: center;
}

.example-btn {
  padding: 12px 16px;
  border: 2px solid var(--accent-cyan);
  background: rgba(30, 144, 255, 0.1);
  color: var(--accent-cyan);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: normal;
  text-align: center;
  max-width: 240px;
  line-height: 1.4;
  text-transform: none;
}

.example-btn:hover {
  background: rgba(30, 144, 255, 0.2);
  border-color: var(--accent-cyan);
  color: #ffffff;
  box-shadow: 0 0 12px rgba(30, 144, 255, 0.3);
}

.input-area {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid var(--glass-border);
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid var(--accent-cyan);
  border-radius: 6px;
  background: rgba(30, 144, 255, 0.05);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  outline: none;
  transition: all 200ms ease;
}

.chat-input::placeholder {
  color: var(--text-muted);
}

.chat-input:focus {
  border-color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.1);
  box-shadow: 0 0 12px rgba(30, 144, 255, 0.2);
}

.chat-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #1e40af, #0ea5e9);
  border: none;
  color: #ffffff;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(30, 64, 175, 0.3);
}

.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #1e3a8a, #0284c7);
  box-shadow: 0 4px 16px rgba(30, 64, 175, 0.5);
  transform: translateY(-2px);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-cyan);
  color: var(--bg-dark);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .user-message,
  .assistant-message {
    max-width: 85%;
  }

  .example-buttons {
    grid-template-columns: 1fr;
  }

  .example-btn {
    width: 100%;
    max-width: none;
  }

  .input-area {
    flex-direction: column;
  }

  .send-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .ask-map-screen {
    padding: 8px;
    gap: 8px;
  }

  .messages-list {
    padding: 12px;
    gap: 12px;
  }

  .user-message,
  .assistant-message {
    max-width: 95%;
  }

  .message-content {
    font-size: 13px;
  }

  .input-area {
    padding: 12px;
    gap: 8px;
  }

  .chat-input {
    padding: 10px 12px;
    font-size: 13px;
  }

  .send-btn {
    padding: 10px 16px;
    font-size: 12px;
  }

  .examples-label {
    font-size: 11px;
    margin-bottom: 8px;
  }

  .example-buttons {
    gap: 8px;
  }
}

/* ===== PHASE 2 ROADMAP STYLES ===== */
.phase2-center-container {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 420px;
  padding: 40px 20px;
}

.phase2-card {
  max-width: 520px;
  width: 100%;
  padding: 40px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(15, 23, 42, 0.75);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 16px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}

.phase2-icon {
  font-size: 48px;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 12px rgba(14, 165, 233, 0.4));
}

.phase2-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 800;
  padding: 5px 14px;
  border-radius: 999px;
  background: rgba(14, 165, 233, 0.2);
  color: var(--accent-cyan);
  border: 1px solid rgba(14, 165, 233, 0.4);
  letter-spacing: 1px;
  margin-bottom: 16px;
}

.phase2-card h2 {
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 12px 0;
}

.phase2-card p {
  font-size: 14px;
  line-height: 1.6;
  color: #cbd5e1;
  margin: 0 0 18px 0;
}

.phase2-note {
  font-size: 12px;
  line-height: 1.5;
  color: #94a3b8;
  background: rgba(30, 41, 59, 0.6);
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 24px;
}

.return-dashboard-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
  background: linear-gradient(135deg, #1e40af, #0ea5e9);
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s ease;
  border: 1px solid var(--accent-cyan);
}

.return-dashboard-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(14, 165, 233, 0.4);
}
</style>
