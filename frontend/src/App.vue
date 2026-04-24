<!--
  Fast Video Download - 前端界面
  版权所有 © 2024 保留所有权利
  本项目仅用于技术学习和研究目的。请用户遵守当地法律法规。
-->
<template>
  <div class="app-container">
    <!-- Background Decoration -->
    <div class="bg-glow"></div>
    
    <NavBar 
      :user="user"
      @open-auth="(mode) => { authMode = mode; showAuthModal = true; }" 
      @open-pricing="showPricingModal = true"
      @logout="user = null" 
      @refresh-user="fetchUser"
      @clear="handleClear"
    />
    
    <main>
      <AgentChat />

      <section class="legacy-mode-section">
        <div class="mode-heading">
          <span>传统模式</span>
          <h2>直接解析下载</h2>
        </div>
        <HeroSection @parse="handleParse" @clear="handleClear" :loading="loading" />
      </section>
      
      <div class="content-wrapper">
        <transition name="fade">
          <div v-if="globalError" class="global-error glass-panel">
            <div class="error-icon">
              <!-- ... Error SVG ... -->
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
          @open-pricing="showPricingModal = true"
        />

        <template v-if="!showResult">
          <FeatureSection />
          <PlatformSection />
        </template>
      </div>
    </main>

    <FooterSection />

    <!-- Auth Modal -->
    <AuthModal 
      v-if="showAuthModal" 
      :mode="authMode"
      @close="showAuthModal = false" 
      @success="fetchUser"
    />

    <!-- Pricing Modal -->
    <PricingModal 
      v-if="showPricingModal"
      @close="showPricingModal = false"
    />

    <!-- Payment Toast Notification -->
    <transition name="slide-fade">
      <div v-if="paymentStatus" class="payment-toast glass-panel" :class="paymentStatus">
        <div class="toast-icon">
          <span v-if="paymentStatus === 'success'">🎉</span>
          <span v-else>⚠️</span>
        </div>
        <div class="toast-content">
          <h4>{{ paymentStatus === 'success' ? t.app.paymentSuccess : t.app.paymentCancel }}</h4>
        </div>
        <button @click="paymentStatus = null" class="close-toast">×</button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue';
import { useI18n } from './i18n';
import NavBar from './components/NavBar.vue';
import AuthModal from './components/AuthModal.vue';
import PricingModal from './components/PricingModal.vue';
import AgentChat from './components/AgentChat.vue';
import HeroSection from './components/HeroSection.vue';
import VideoResult from './components/VideoResult.vue';
import FeatureSection from './components/FeatureSection.vue';
import PlatformSection from './components/PlatformSection.vue';
import FooterSection from './components/FooterSection.vue';
import { api } from './api';

const { t } = useI18n();

// 响应式状态定义
const user = ref(null);
const showAuthModal = ref(false);
const authMode = ref('login');
const showPricingModal = ref(false);
const parsedVideo = ref(null);
const currentUrl = ref('');
const globalError = ref('');
const loading = ref(false);

const showResult = computed(() => parsedVideo.value !== null);
const paymentStatus = ref(null); // 'success', 'cancel', or null

const fetchUser = async () => {
  try {
    const data = await api.getMe();
    user.value = data;
  } catch (e) {
    user.value = null;
  }
};

onMounted(() => {
    fetchUser();
    checkPaymentStatus();
});

const checkPaymentStatus = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const payment = urlParams.get('payment');
  
  if (payment === 'success') {
    paymentStatus.value = 'success';
    // 支付成功后主动刷新用户信息
    fetchUser();
    // 3秒后自动关闭
    setTimeout(() => paymentStatus.value = null, 5000);
  } else if (payment === 'cancel') {
    paymentStatus.value = 'cancel';
    setTimeout(() => paymentStatus.value = null, 5000);
  }
  
  // 清理 URL 参数，防止刷新页面再次提示
  if (payment) {
    const newUrl = window.location.origin + window.location.pathname;
    window.history.replaceState({}, document.title, newUrl);
  }
};

const handleParse = async (url) => {
  if (!user.value) {
      showAuthModal.value = true;
      return;
  }
  
  globalError.value = '';
  parsedVideo.value = null;
  currentUrl.value = url;
  loading.value = true;
  
  try {
    const data = await api.parseVideo(url);
    await nextTick();
    parsedVideo.value = data;
    await nextTick();
    const resultEl = document.querySelector('.video-result');
    if (resultEl) resultEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // 解析成功后刷新用户信息（更新额度）
    fetchUser();
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

.legacy-mode-section {
  position: relative;
}

.mode-heading {
  width: min(1180px, calc(100% - 40px));
  margin: 0 auto -56px;
  padding-top: 8px;
  position: relative;
  z-index: 12;
}

.mode-heading span {
  color: rgba(255, 255, 255, 0.48);
  font-size: 0.8rem;
  font-weight: 800;
}

.mode-heading h2 {
  margin-top: 4px;
  font-size: 1.35rem;
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

/* Payment Toast Styles */
.payment-toast {
  position: fixed;
  top: 90px;
  right: 24px;
  z-index: 1000;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 320px;
  border-left: 4px solid transparent;
}

.payment-toast.success {
  border-left-color: #10b981;
}

.payment-toast.cancel {
  border-left-color: #f59e0b;
}

.toast-icon {
  font-size: 1.5rem;
}

.toast-content h4 {
  margin: 0;
  font-size: 1rem;
}

.toast-content p {
  margin: 4px 0 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.close-toast {
  background: transparent;
  border: none;
  color: var(--color-foreground);
  opacity: 0.5;
  font-size: 1.25rem;
  cursor: pointer;
  margin-left: auto;
}

.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1);
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>
