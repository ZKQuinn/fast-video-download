<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="auth-modal glass-panel anim-slide-up">
      <div class="modal-header">
        <h2>{{ isLogin ? t.auth.login : t.navbar.register }}</h2>
        <p class="subtitle">{{ isLogin ? t.auth.loginSubtitle : t.auth.registerSubtitle }}</p>
      </div>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="input-group">
          <label>{{ t.auth.email }}</label>
          <input 
            v-model="username" 
            type="email" 
            :placeholder="t.auth.emailPlaceholder" 
            required 
          />
        </div>
        
        <div class="input-group">
          <label>{{ t.auth.password }}</label>
          <input 
            v-model="password" 
            type="password" 
            :placeholder="t.auth.passwordPlaceholder" 
            required 
          />
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="loader"></span>
          <span v-else>{{ isLogin ? t.auth.loginAction : t.auth.registerAction }}</span>
        </button>
      </form>

      <div class="modal-footer">
        <button @click="isLogin = !isLogin" class="switch-btn">
          {{ isLogin ? t.auth.switchRegister : t.auth.switchLogin }}
        </button>
      </div>
      
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { api } from '../api';
import { useI18n } from '../i18n';

const emit = defineEmits(['close', 'success']);
const { t } = useI18n();

const isLogin = ref(true);
const username = ref('');
const password = ref('');
const error = ref('');
const loading = ref(false);

const handleSubmit = async () => {
  error.value = '';
  loading.value = true;
  
  try {
    if (isLogin.value) {
      await api.login(username.value, password.value);
    } else {
      await api.register(username.value, password.value);
      // 注册成功后自动登录
      await api.login(username.value, password.value);
    }
    emit('success');
    emit('close');
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.auth-modal {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  position: relative;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header {
  text-align: center;
  margin-bottom: 30px;
}

h2 {
  font-size: 1.75rem;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
}

input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px 16px;
  border-radius: 12px;
  color: #fff;
  transition: all 0.3s ease;
}

input:focus {
  outline: none;
  border-color: var(--color-primary);
  background: rgba(255, 255, 255, 0.08);
}

.submit-btn {
  margin-top: 10px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  color: white;
  padding: 14px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(236, 72, 153, 0.3);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(236, 72, 153, 0.4);
}

.switch-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  margin-top: 20px;
  width: 100%;
}

.switch-btn:hover {
  color: var(--color-primary);
}

.error-msg {
  color: #ef4444;
  font-size: 0.8rem;
  text-align: center;
}

.close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 1.5rem;
  opacity: 0.5;
  cursor: pointer;
}

.close-btn:hover {
  opacity: 1;
}

.loader {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin { to { transform: rotate(360deg); } }

.anim-slide-up {
  animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
