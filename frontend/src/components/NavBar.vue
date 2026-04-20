<template>
  <nav class="navbar glass-panel">
    <div class="nav-content">
      <div class="logo" @click="$emit('clear')">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">Fast Video <span class="text-gradient">Download</span></span>
      </div>
      
      <div class="nav-links">
        <!-- 会员/用户状态 -->
        <div v-if="user" class="user-info">
          <div class="user-badge" :class="{ 'is-vip': user.is_vip }">
             <span v-if="user.is_vip">👑 </span>{{ user.is_vip ? t.navbar.vip : t.navbar.free }}
          </div>
          <div class="user-menu" :class="{ 'vip-glow': user.is_vip }" @click="showDropdown = !showDropdown">
            <span v-if="user.is_vip" class="crown-icon">👑</span>
            <span class="username">{{ user.username }}</span>
            <div v-if="showDropdown" class="dropdown glass-panel">
               <div class="dropdown-item quota">{{ t.navbar.quota }} {{ user.daily_download_count }} / {{ user.is_vip ? '∞' : '5' }}</div>
               <div v-if="!user.is_vip" @click="handleUpgrade" class="dropdown-item highlight">{{ t.navbar.upgrade }}</div>
               <div @click="handleLogout" class="dropdown-item danger">{{ t.navbar.logout }}</div>
            </div>
          </div>
        </div>
        
        <div v-else class="auth-buttons">
          <button @click="$emit('open-auth', 'login')" class="login-btn secondary">
            {{ t.auth.login }}
          </button>
          <button @click="$emit('open-auth', 'register')" class="login-btn">
            {{ t.auth.register }}
          </button>
        </div>

        <button @click="i18n.toggle()" class="lang-btn">
          {{ i18n.current === 'zh' ? 'EN' : '中' }}
        </button>

        <a href="https://github.com/ZKQuinn" target="_blank" class="github-link mobile-hide">
          {{ t.navbar.github }}
        </a>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useI18n } from '../i18n';
import { api } from '../api';

const props = defineProps(['user']);
const emit = defineEmits(['open-auth', 'logout', 'clear', 'refresh-user', 'open-pricing']);

const { t, i18n } = useI18n();
const showDropdown = ref(false);

const handleLogout = () => {
    api.clearToken();
    emit('logout');
    showDropdown.value = false;
};

const handleUpgrade = () => {
    emit('open-pricing');
    showDropdown.value = false;
};
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
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-badge {
  font-size: 0.7rem;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
  text-transform: uppercase;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.user-badge.is-vip {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  border: none;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.user-menu {
  position: relative;
  cursor: pointer;
  font-weight: 600;
  color: var(--text-primary);
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
}
.user-menu:hover {
  background: rgba(255, 255, 255, 0.1);
}

.user-menu.vip-glow {
  border: 1px solid rgba(245, 158, 11, 0.3);
  background: rgba(245, 158, 11, 0.05);
}

.user-menu.vip-glow:hover {
  box-shadow: 0 0 15px rgba(245, 158, 11, 0.2);
  background: rgba(245, 158, 11, 0.08);
}

.crown-icon {
  margin-right: 6px;
  filter: drop-shadow(0 0 5px rgba(245, 158, 11, 0.5));
}

.dropdown {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 200px;
  padding: 8px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  animation: dropdownFade 0.2s ease;
}

@keyframes dropdownFade {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.dropdown-item {
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.dropdown-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.dropdown-item.quota {
  color: var(--text-secondary);
  font-size: 0.8rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  margin-bottom: 4px;
}

.dropdown-item.highlight {
  color: #f59e0b;
  font-weight: 700;
}

.dropdown-item.danger {
  color: #ef4444;
}

.auth-buttons {
  display: flex;
  gap: 8px;
}

.login-btn {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  color: white;
  padding: 8px 20px;
  border: none;
  border-radius: 99px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(236, 72, 113, 0.2);
}

.login-btn.secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: none;
  color: var(--text-primary);
}

.login-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(236, 72, 113, 0.3);
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
