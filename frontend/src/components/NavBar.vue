<template>
  <nav class="navbar glass-panel">
    <div class="nav-content">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">Fast Video <span class="text-gradient">Download</span></span>
      </div>
      <div class="nav-links">
        <button @click="i18n.toggle()" class="lang-btn">
          {{ i18n.current === 'zh' ? 'EN' : '中' }}
        </button>
        <a href="https://github.com/ZKQuinn" target="_blank" class="github-link">
          {{ t.navbar.github }}
        </a>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useI18n } from '../i18n';
const { t, i18n } = useI18n();
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 70px;
  border-radius: 0;
  border-left: none;
  border-right: none;
  border-top: none;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.3s ease;
}

.nav-content {
  width: 100%;
  max-width: 1200px;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.logo-icon {
  font-size: 1.5rem;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 12px;
}

.lang-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  font-size: 0.9rem;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 44px;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.github-link {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: color 0.2s ease;
  padding: 8px 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
}

.github-link:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.1);
}
</style>
