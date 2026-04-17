<template>
  <div class="app-container">
    <NavBar />
    
    <main>
      <HeroSection @parse="handleParse" @clear="handleClear" :loading="loading" />
      
      <div class="content-wrapper">
        <div v-if="globalError" class="global-error glass-panel">
          <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          {{ globalError }}
        </div>
        
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
const parsedVideo = ref(null);
const currentUrl = ref('');
const globalError = ref('');
const loading = ref(false);

const showResult = computed(() => parsedVideo.value !== null);

const handleParse = async (url) => {
  globalError.value = '';
  parsedVideo.value = null;
  currentUrl.value = url;
  loading.value = true;
  
  try {
    const data = await api.parseVideo(url);
    
    // Wait for Vue to finish any pending DOM updates before setting new data
    await nextTick();
    
    parsedVideo.value = data;
    
    // Scroll to result after next render cycle
    await nextTick();
    const resultEl = document.querySelector('.video-result');
    if (resultEl) {
      resultEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  } catch (err) {
    globalError.value = err.message || t.value.app.defaultError;
  } finally {
    loading.value = false;
  }
};

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
}

main {
  flex: 1;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  width: 100%;
}

.global-error {
  max-width: 800px;
  margin: 0 auto 40px auto;
  padding: 20px;
  color: #f87171;
  display: flex;
  align-items: center;
  gap: 12px;
  border-color: rgba(248, 113, 113, 0.2);
  background: rgba(248, 113, 113, 0.05);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
