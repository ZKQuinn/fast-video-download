<template>
  <section class="features-section">
    <div class="features-grid">
      <div class="feature-card glass-panel" v-for="(feat, idx) in features" :key="idx">
        <div class="icon-wrapper">
            <span class="icon">{{ feat.icon }}</span>
        </div>
        <h3 class="title">{{ feat.title }}</h3>
        <p class="desc">{{ feat.desc }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from '../i18n';

const { t } = useI18n();

const features = computed(() => [
  {
    icon: '⚡',
    title: t.value.features.f1.title,
    desc: t.value.features.f1.desc
  },
  {
    icon: '🔒',
    title: t.value.features.f2.title,
    desc: t.value.features.f2.desc
  },
  {
    icon: '✨',
    title: t.value.features.f3.title,
    desc: t.value.features.f3.desc
  }
]);
</script>

<style scoped>
.features-section {
  padding: 60px 0;
  margin-top: 40px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.feature-card {
  padding: 32px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  background: rgba(255, 255, 255, 0.02);
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3), inset 0 0 0 1px rgba(255,255,255,0.1);
  background: rgba(255, 255, 255, 0.04);
}

.icon-wrapper {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: 20px;
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
}

.title {
  font-size: 1.2rem;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.desc {
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 0.95rem;
}
</style>
