<template>
  <transition name="modal-fade">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-content glass-panel promo-container">
        <button class="close-btn" @click="$emit('close')">×</button>
        
        <header class="pricing-header">
          <h2>{{ t.pricing.title }}</h2>
          <p>{{ t.pricing.subtitle }}</p>
        </header>

        <div class="pricing-cards">
          <!-- Free Plan -->
          <div class="pricing-card basic">
            <div class="card-body">
              <h3 class="plan-name">{{ t.pricing.free.name }}</h3>
              <p class="plan-desc">{{ t.pricing.free.desc }}</p>
              <div class="price">
                <span class="currency">¥</span>
                <span class="amount">0</span>
                <span class="period">/{{ t.pricing.free.period }}</span>
              </div>
              <ul class="features">
                <li v-for="f in t.pricing.free.features" :key="f"><span class="check">✓</span> {{ f }}</li>
              </ul>
            </div>
            <button class="plan-btn disabled" disabled>{{ t.pricing.action.current }}</button>
          </div>

          <!-- VIP Premium Plan -->
          <div class="pricing-card premium">
            <div class="recommend-badge">🔥 {{ t.pricing.vip.recommend }}</div>
            <div class="card-body">
              <h3 class="plan-name">{{ t.pricing.vip.name }}</h3>
              <p class="plan-desc">{{ t.pricing.vip.desc }}</p>
              <div class="price">
                <span class="currency">¥</span>
                <span class="amount">{{ t.pricing.vip.price }}</span>
                <span class="period">/{{ t.pricing.vip.period }}</span>
                <span class="limit-tag">{{ t.pricing.vip.tag }}</span>
              </div>
              <ul class="features">
                <li v-for="f in t.pricing.vip.features" :key="f"><span class="check">✓</span> {{ f }}</li>
              </ul>
            </div>
            <button class="plan-btn primary" @click="handleBuy" :disabled="loading">
              {{ loading ? t.pricing.action.loading : t.pricing.action.upgrade }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue';
import { api } from '../api';
import { useI18n } from '../i18n';

const emit = defineEmits(['close']);
const { t } = useI18n();
const loading = ref(false);

const handleBuy = async () => {
    loading.value = true;
    try {
        const { url } = await api.createCheckoutSession();
        window.location.href = url;
    } catch (e) {
        alert(e.message || (locale.value === 'zh' ? '支付系统启动失败，请稍后尝试' : 'Failed to launch payment system.'));
        loading.value = false;
    }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.promo-container {
  max-width: 900px;
  width: 100%;
  padding: 48px;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.close-btn {
  position: absolute;
  top: 20px;
  right: 24px;
  background: transparent;
  border: none;
  font-size: 2rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: color 0.2s;
  z-index: 10;
}

.close-btn:hover {
  color: var(--text-primary);
}

.pricing-header {
  text-align: center;
  margin-bottom: 48px;
}

.pricing-header h2 {
  font-size: 2.25rem;
  font-weight: 800;
  margin-bottom: 16px;
  letter-spacing: -1px;
}

.pricing-header p {
  color: var(--text-secondary);
  font-size: 1.1rem;
}

.pricing-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.pricing-card {
  border-radius: 24px;
  padding: 40px;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: transform 0.3s ease;
}

.pricing-card:hover {
  transform: translateY(-8px);
}

.pricing-card.basic {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.pricing-card.premium {
  background: linear-gradient(145deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  box-shadow: 0 20px 40px rgba(37, 99, 235, 0.2);
}

.recommend-badge {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 99px;
  font-size: 0.8rem;
  font-weight: 600;
}

.plan-name {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.plan-desc {
  font-size: 0.95rem;
  opacity: 0.7;
  margin-bottom: 24px;
}

.price {
  margin-bottom: 32px;
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.currency {
  font-size: 1.5rem;
  font-weight: 700;
}

.amount {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1;
}

.period {
  opacity: 0.5;
  font-size: 1rem;
}

.limit-tag {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  margin-left: 8px;
}

.features {
  list-style: none;
  padding: 0;
  margin: 0 0 40px 0;
  flex-grow: 1;
}

.features li {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  font-size: 1rem;
}

.check {
  color: #10b981;
  font-weight: bold;
}

.premium .check {
  color: #fbbf24;
}

.plan-btn {
  width: 100%;
  padding: 16px;
  border-radius: 99px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.plan-btn.disabled {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.plan-btn.primary {
  background: white;
  color: #2563eb;
  border: none;
}

.plan-btn.primary:hover {
  transform: scale(1.02);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.plan-btn.primary:active {
  transform: scale(0.98);
}

/* Animations */
.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.3s ease;
}
.modal-fade-enter-from, .modal-fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .promo-container {
    padding: 24px;
    margin: 10px;
  }
  .pricing-cards {
    grid-template-columns: 1fr;
  }
  .pricing-header h2 {
    font-size: 1.5rem;
  }
}
</style>
