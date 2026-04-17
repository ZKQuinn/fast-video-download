<template>
  <section class="hero">
    <div class="hero-bg">
       <div class="glow glow-1"></div>
       <div class="glow glow-2"></div>
    </div>
    
    <div class="hero-content">
      <h1 class="title">
        Download <span class="text-gradient">Any Video</span><br/>
        Anywhere.
      </h1>
      <p class="subtitle">
        支持 1800+ 平台，一键下载高清视频。纯粹、极速、无广告。
      </p>
      
      <div class="search-container glass-panel">
        <input 
          v-model="url" 
          type="text" 
          placeholder="粘贴想要下载的视频链接 (如 YouTube, B站, 抖音等)..."
          @keyup.enter="handleParse"
        />
        <button class="btn-parse" @click="handleParse" :disabled="loading">
          {{ loading ? '解析中...' : '开始解析' }}
        </button>
      </div>
      
      <div class="platforms-hint">
        <span class="hint-text">Supported Platforms:</span>
        <span class="tags">YouTube · Bilibili · 抖音 · TikTok · Twitter · X</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';

const url = ref('');
const loading = ref(false);

const emit = defineEmits(['parse']);

const handleParse = () => {
    if (!url.value.trim() || loading.value) return;
    loading.value = true;
    emit('parse', url.value.trim());
    
    // Simulate loading finish for now
    setTimeout(() => {
        loading.value = false;
    }, 1000);
};
</script>

<style scoped>
.hero {
  position: relative;
  min-height: 80vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding-top: 70px; /* navbar height */
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -1;
  overflow: hidden;
}

.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: float 10s infinite ease-in-out alternate;
}

.glow-1 {
  width: 400px;
  height: 400px;
  background: var(--accent-purple);
  top: 10%;
  left: 20%;
  animation-delay: 0s;
}

.glow-2 {
  width: 300px;
  height: 300px;
  background: var(--accent-pink);
  bottom: 20%;
  right: 20%;
  animation-delay: -5s;
}

@keyframes float {
  0% { transform: translateY(0) scale(1); }
  100% { transform: translateY(-30px) scale(1.1); }
}

.hero-content {
  width: 100%;
  max-width: 800px;
  padding: 0 24px;
  text-align: center;
  z-index: 1;
}

.title {
  font-size: 4.5rem;
  font-weight: 800;
  letter-spacing: -2px;
  line-height: 1.1;
  margin-bottom: 24px;
}

.subtitle {
  font-size: 1.25rem;
  color: var(--text-secondary);
  font-weight: 400;
  margin-bottom: 48px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.search-container {
  display: flex;
  padding: 8px;
  border-radius: 20px;
  margin-bottom: 32px;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.search-container:focus-within {
  border-color: var(--accent-purple);
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2), 0 10px 40px rgba(0, 0, 0, 0.3);
}

input {
  flex: 1;
  background: transparent;
  border: none;
  padding: 16px 24px;
  font-size: 1.1rem;
  color: var(--text-primary);
  outline: none;
}

input::placeholder {
  color: var(--text-muted);
}

.btn-parse {
  background: var(--gradient-cta);
  color: white;
  font-weight: 600;
  font-size: 1.1rem;
  padding: 16px 32px;
  border-radius: 14px;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
}

.btn-parse:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(240, 147, 251, 0.4);
}

.btn-parse:active:not(:disabled) {
  transform: translateY(0);
}

.btn-parse:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.platforms-hint {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  font-size: 0.9rem;
}

.hint-text {
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: 0.8rem;
}

.tags {
  color: var(--text-secondary);
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 768px) {
  .title { font-size: 3rem; }
  .search-container { flex-direction: column; padding: 12px; }
  input { padding: 12px; margin-bottom: 8px; font-size: 1rem; }
  .btn-parse { width: 100%; padding: 14px; }
  .glow-1, .glow-2 { width: 200px; height: 200px; }
}
</style>
