<!--
  Fast Video Download - 前端界面
  版权所有 © 2024 保留所有权利
  本项目仅用于技术学习和研究目的。请用户遵守当地法律法规。
-->
<template>
  <div class="app-container">
    <!-- Background Decoration -->
    <div class="bg-glow"></div>
    
    <NavBar />
    
    <main>
      <HeroSection @parse="handleParse" @clear="handleClear" :loading="loading" />
      
      <div class="content-wrapper">
        <transition name="fade">
          <div v-if="globalError" class="global-error glass-panel">
            <div class="error-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            </div>
            <div class="error-text">
              {{ globalError }}
            </div>
            <button @click="globalError = ''" class="close-error">×</button>
          </div>
        </transition>
        
        <VideoResult 
          v-if="showResult" 
          :video="parsedVideo" 
          :url="currentUrl"
        />

        <template v-if="!showResult">
          <FeatureSection />
          <PlatformSection />
        </template>
      </div>
    </main>

    <FooterSection />
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';
import { useI18n } from './i18n';
import NavBar from './components/NavBar.vue';
import HeroSection from './components/HeroSection.vue';
import VideoResult from './components/VideoResult.vue';
import FeatureSection from './components/FeatureSection.vue';
import PlatformSection from './components/PlatformSection.vue';
import FooterSection from './components/FooterSection.vue';
import { api } from './api';

const { t } = useI18n();

// 响应式状态定义
const parsedVideo = ref(null); // 解析后的视频数据对象
const currentUrl = ref('');    // 当前正在处理的 URL
const globalError = ref('');   // 全局错误提示文本
const loading = ref(false);    // 是否处于解析/加载状态

// 计算属性：是否显示解析结果面板
const showResult = computed(() => parsedVideo.value !== null);

/**
 * 处理视频解析事件
 * @param {string} url 用户输入的视频链接
 */
const handleParse = async (url) => {
  // 重置状态
  globalError.value = '';
  parsedVideo.value = null;
  currentUrl.value = url;
  loading.value = true;
  
  try {
    // 调用 API 接口进行后端解析
    const data = await api.parseVideo(url);
    
    // 等待 Vue 完成数据清理产生的 DOM 更新
    await nextTick();
    
    // 设置新数据
    parsedVideo.value = data;
    
    // 渲染完成后，平滑滚动到结果区域
    await nextTick();
    const resultEl = document.querySelector('.video-result');
    if (resultEl) {
      resultEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  } catch (err) {
    // 捕获错误并显示，若无具体信息则显示默认错误
    globalError.value = err.message || t.value.app.defaultError;
  } finally {
    loading.value = false;
  }
};

/**
 * 处理清除事件：清空所有解析状态回到初始首页
 */
const handleClear = () => {
  parsedVideo.value = null;
  globalError.value = '';
  currentUrl.value = '';
};
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

.bg-glow {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: -1;
  background: 
    radial-gradient(circle at 15% 15%, rgba(236, 72, 153, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 85% 85%, rgba(37, 99, 235, 0.08) 0%, transparent 40%);
}

main {
  flex: 1;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px 80px;
  width: 100%;
}

.global-error {
  max-width: 800px;
  margin: 0 auto 40px auto;
  padding: 16px 20px;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.15);
  display: flex;
  align-items: center;
  gap: 16px;
}

.error-icon {
  color: #ef4444;
  flex-shrink: 0;
}

.error-text {
  flex: 1;
  font-size: 0.95rem;
}

.close-error {
  background: transparent;
  border: none;
  color: var(--color-foreground);
  opacity: 0.5;
  font-size: 1.5rem;
  cursor: pointer;
}

.close-error:hover {
  opacity: 1;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>
