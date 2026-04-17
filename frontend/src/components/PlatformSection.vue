<template>
  <section class="platforms-section">
    <div class="section-title">
      <h2>{{ t.platforms.title }}</h2>
      <p>{{ t.platforms.subtitle }}</p>
    </div>
    
    <div class="platforms-grid">
      <div class="platform-item glass-panel" v-for="p in translatedPlatforms" :key="p.name">
        <span class="p-name">{{ p.name }}</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from '../i18n';

const { t, i18n } = useI18n();

const platforms = [
  { name: 'YouTube' },
  { name: 'Bilibili' },
  { name: '抖音 / TikTok' },
  { name: 'Twitter / X' },
  { name: 'Instagram' },
  { name: 'Facebook' },
  { name: 'Twitch' },
  { name: 'Vimeo' },
  { name: 'Reddit' },
  { name: 'SoundCloud' },
  { name: 'Pinterest' }
];

const translatedPlatforms = computed(() => {
  return [
    ...platforms,
    { name: i18n.current === 'zh' ? '全网更多站点...' : 'More Sites...' }
  ];
});
</script>

<style scoped>
.platforms-section {
  padding: 60px 0 20px 0;
  text-align: center;
}

.section-title {
  margin-bottom: 40px;
}

.section-title h2 {
  font-size: 2rem;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.section-title p {
  color: var(--text-secondary);
}

.platforms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.platform-item {
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(255, 255, 255, 0.015);
  transition: all 0.2s;
  cursor: default;
}

.platform-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--accent-purple);
  transform: scale(1.02);
}

.p-name {
  font-weight: 600;
  color: var(--text-secondary);
}

.platform-item:hover .p-name {
  color: var(--text-primary);
}
</style>
