<template>
  <section class="hero">
    <div class="hero-content">
      <transition name="slide-up">
        <div class="badge-wrapper" v-if="loading">
          <span class="badge pulse-animation">{{ t.hero.parsing }}</span>
        </div>
      </transition>
      
      <h1 class="title">
        {{ t.hero.titleLine1 }}<br/>
        <span class="text-gradient">{{ t.hero.titleLine2 }}</span>
      </h1>
      <p class="subtitle">
        {{ t.hero.subtitle }}
      </p>
      
      <div class="search-container glass-panel">
        <div class="input-wrapper">
          <div class="search-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          </div>
          <input 
            v-model="url" 
            type="text" 
            :placeholder="t.hero.inputPlaceholder"
            @keyup.enter="handleParse"
            :disabled="loading"
            class="url-input"
          />
          <button 
            v-if="url"
            @click="clearInput" 
            class="clear-btn"
            :disabled="loading"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
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

      <transition name="fade">
        <div class="error-msg" v-if="localError">
          {{ localError }}
        </div>
      </transition>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from '../i18n';

// 接收父组件传递的状态
const props = defineProps({
  loading: Boolean // 后端是否正在解析中
});

// 定义向父组件发送的事件
const emit = defineEmits(['parse', 'clear']);

// 本地响应式变量
const url = ref('');         // 输入框绑定的 URL 文本
const localError = ref(''); // 本地校验错误信息
const { t } = useI18n();     // 国际化文案引用

/**
 * 触发解析逻辑：进行基础校验后发送事件给父组件
 */
const handleParse = () => {
  const rawText = url.value.trim();
  if (!rawText) return;
  
  // 优化：从可能包含文字的粘贴内容中提取 URL (适配抖音/快手等平台的分享文案)
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const matches = rawText.match(urlRegex);
  
  let finalUrl = rawText;
  
  if (matches && matches.length > 0) {
      finalUrl = matches[0];
  } else if (!rawText.startsWith('http')) {
      localError.value = t.value.app.errorInvalidUrl;
      return;
  }
  
  localError.value = '';
  // 更新输入框为提取后的纯净 URL，提升用户感官
  url.value = finalUrl;
  
  // 通知父组件开始解析该 URL
  emit('parse', finalUrl);
};

/**
 * 清除输入：清空文本框并通知父组件重置状态
 */
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
  padding: 100px 24px;
  position: relative;
}

.hero-content {
  max-width: 900px;
  width: 100%;
  text-align: center;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.badge-wrapper {
  margin-bottom: 24px;
}

.badge {
  background: rgba(236, 72, 153, 0.1);
  color: var(--color-primary);
  padding: 8px 20px;
  border-radius: 100px;
  font-size: 0.85rem;
  font-weight: 700;
  border: 1px solid rgba(236, 72, 153, 0.2);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: inline-block;
}

.pulse-animation {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 0.8; }
  50% { opacity: 1; box-shadow: 0 0 20px rgba(236, 72, 153, 0.3); }
  100% { opacity: 0.8; }
}

.title {
  font-size: 5rem;
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -0.04em;
  margin-bottom: 28px;
  color: #fff;
}

.subtitle {
  font-size: 1.4rem;
  color: rgba(255, 255, 255, 0.6);
  max-width: 640px;
  margin: 0 auto 48px;
  line-height: 1.5;
  font-weight: 400;
}

.search-container {
  display: flex;
  width: 100%;
  max-width: 720px;
  background: rgba(255, 255, 255, 0.04);
  padding: 8px;
  border-radius: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
}

.search-container:focus-within {
  background: rgba(255, 255, 255, 0.07);
  box-shadow: 0 0 0 4px var(--color-primary-glow), 0 20px 50px rgba(0, 0, 0, 0.4);
  transform: translateY(-2px);
}

.input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 8px;
}

.search-icon {
  color: rgba(255, 255, 255, 0.3);
  display: flex;
  margin-left: 12px;
}

.url-input {
  flex: 1;
  background: transparent;
  border: none;
  padding: 12px 0;
  font-size: 1.25rem;
  color: #fff;
  outline: none;
}

.url-input::placeholder {
  color: rgba(255, 255, 255, 0.2);
}

.clear-btn {
  color: rgba(255, 255, 255, 0.3);
  padding: 8px;
  border-radius: 50%;
  display: flex;
  transition: all 0.2s ease;
}

.clear-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.action-btn {
  background: var(--gradient-primary);
  color: white;
  padding: 0 36px;
  height: 64px;
  border-radius: 16px;
  font-size: 1.15rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 180px;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: var(--shadow-primary);
}

.action-btn:hover:not(:disabled) {
  transform: scale(1.02);
  filter: brightness(1.1);
}

.action-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  filter: grayscale(0.5);
}

.loader-ring {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-msg {
  margin-top: 24px;
  color: #ef4444;
  font-size: 0.95rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Transitions */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

@media (max-width: 768px) {
  .title {
    font-size: 3.25rem;
    letter-spacing: -0.02em;
  }
  
  .subtitle {
    font-size: 1.15rem;
  }

  .search-container {
    flex-direction: column;
    padding: 16px;
    gap: 16px;
  }
  
  .input-wrapper {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 14px;
    padding: 8px 12px;
  }

  .url-input {
    font-size: 1.1rem;
  }

  .action-btn {
    width: 100%;
  }
}
</style>
