<template>
  <section class="hero">
    <div class="hero-content">
      <div class="badge-wrapper" v-if="loading">
        <span class="badge pulse-animation">{{ t.hero.parsing }}</span>
      </div>
      <h1 class="title">
        {{ t.hero.titleLine1 }}<br/>
        <span class="text-gradient">{{ t.hero.titleLine2 }}</span>
      </h1>
      <p class="subtitle">
        {{ t.hero.subtitle }}
      </p>
      
      <div class="search-container glass-panel">
        <input 
          v-model="url" 
          type="text" 
          :placeholder="t.hero.inputPlaceholder"
          @keyup.enter="handleParse"
          :disabled="loading"
          class="url-input"
        />
        <div class="button-group">
          <button 
            v-if="url"
            @click="clearInput" 
            class="clear-btn"
            :disabled="loading"
          >
            {{ t.hero.clearBtn }}
          </button>
          <button 
            @click="handleParse" 
            class="action-btn"
            :class="{ 'btn-loading': loading }"
            :disabled="loading || !url.trim()"
          >
            <span v-if="!loading" class="btn-text">{{ t.hero.downloadBtn }}</span>
            <span v-else class="loader-ring"></span>
          </button>
        </div>
      </div>

      <div class="error-msg" v-if="localError">
        {{ localError }}
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from '../i18n';

const props = defineProps({
  loading: Boolean
});

const emit = defineEmits(['parse', 'clear']);

const url = ref('');
const localError = ref('');
const { t } = useI18n();

const handleParse = () => {
  if (!url.value.trim()) return;
  
  const isValidUrl = url.value.startsWith('http://') || url.value.startsWith('https://') || url.value.includes('douyin') || url.value.includes('bilibili');
  
  if (url.value.trim().length < 5) {
      localError.value = t.value.app.errorInvalidUrl;
      return;
  }
  
  localError.value = '';
  emit('parse', url.value.trim());
};

const clearInput = () => {
  url.value = '';
  localError.value = '';
  emit('clear');
};
</script>

<style scoped>
.hero {
  min-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px 24px;
  position: relative;
  overflow: hidden;
}

.hero-content {
  max-width: 800px;
  width: 100%;
  padding-top: 60px;
  text-align: center;
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.badge-wrapper {
  margin-bottom: 24px;
}

.badge {
  background: rgba(102, 126, 234, 0.15);
  color: #818cf8;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.3);
  display: inline-block;
}

.pulse-animation {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 1; box-shadow: 0 0 15px rgba(102, 126, 234, 0.4); }
  100% { opacity: 0.6; }
}

.title {
  font-size: 4.5rem;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -2px;
  margin-bottom: 24px;
  color: var(--text-primary);
}

.subtitle {
  font-size: 1.25rem;
  color: var(--text-secondary);
  max-width: 600px;
  margin: 0 auto 40px;
  line-height: 1.6;
}

.search-container {
  display: flex;
  width: 100%;
  max-width: 680px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 8px;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.search-container:focus-within {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15);
}

.url-input {
  flex: 1;
  background: transparent;
  border: none;
  padding: 0 24px;
  font-size: 1.1rem;
  color: var(--text-primary);
  outline: none;
}

.url-input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.button-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.clear-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.95rem;
  padding: 0 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.clear-btn:hover:not(:disabled) {
  color: rgba(255, 255, 255, 0.8);
}

.action-btn {
  background: var(--gradient-primary);
  color: white;
  border: none;
  padding: 0 40px;
  height: 56px;
  border-radius: 14px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 160px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.action-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loader-ring {
  display: inline-block;
  width: 24px;
  height: 24px;
  border: 3px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-msg {
  margin-top: 16px;
  color: #f87171;
  font-size: 0.95rem;
  background: rgba(248, 113, 113, 0.1);
  padding: 8px 16px;
  border-radius: 8px;
}

@media (max-width: 768px) {
  .title {
    font-size: 3rem;
  }
  
  .search-container {
    flex-direction: column;
    padding: 16px;
    background: transparent;
    border: none;
    gap: 16px;
  }
  
  .search-container:focus-within {
    box-shadow: none;
    background: transparent;
  }

  .url-input {
    width: 100%;
    height: 60px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 0 20px;
  }
  
  .button-group {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
  }

  .action-btn {
    flex: 1;
    height: 60px;
  }

  .clear-btn {
    padding: 0 20px;
    font-size: 1rem;
  }
}
</style>
