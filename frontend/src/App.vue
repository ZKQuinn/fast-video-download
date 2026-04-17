<template>
  <div class="app-container">
    <NavBar />
    
    <main>
      <HeroSection @parse="handleParse" />
      
      <div class="content-wrapper">
        <div v-if="globalError" class="global-error glass-panel">
          <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          {{ globalError }}
        </div>
        
        <VideoResult 
          v-if="videoData" 
          :video="videoData" 
          :url="currentUrl"
        />

        <div v-if="!videoData">
          <FeatureSection />
          <PlatformSection />
        </div>
      </div>
    </main>

    <FooterSection />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import NavBar from './components/NavBar.vue';
import HeroSection from './components/HeroSection.vue';
import VideoResult from './components/VideoResult.vue';
import FeatureSection from './components/FeatureSection.vue';
import PlatformSection from './components/PlatformSection.vue';
import FooterSection from './components/FooterSection.vue';
import { api } from './api';

const videoData = ref(null);
const currentUrl = ref('');
const globalError = ref('');

const handleParse = async (url) => {
  globalError.value = '';
  videoData.value = null;
  currentUrl.value = url;
  
  try {
    const data = await api.parseVideo(url);
    videoData.value = data;
    // Auto scroll to result smoothly
    setTimeout(() => {
        window.scrollTo({
            top: window.innerHeight * 0.7,
            behavior: 'smooth'
        });
    }, 100);
  } catch (err) {
    globalError.value = err.message || '解析失败，请检查链接或稍后重试。';
  }
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
